#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["requests", "pillow"]
# ///

import argparse
import base64
import fcntl
import hashlib
import io
import json
import mimetypes
import os
import sys
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path

import requests
from PIL import Image

UPLOAD_URL = "https://kieai.redpandaai.co/api/file-base64-upload"
CREATE_TASK_URL = "https://api.kie.ai/api/v1/jobs/createTask"
RECORD_INFO_URL = "https://api.kie.ai/api/v1/jobs/recordInfo"

def load_api_key():
    key = os.environ.get("KIE_API_KEY")
    if key:
        return key.strip()
    config_root = Path.home() / ".config"
    candidates = [config_root / "kie/kie.env"]
    if config_root.is_dir():
        for extra in sorted(config_root.glob("*/kie.env")):
            if extra not in candidates:
                candidates.append(extra)
    for candidate in candidates:
        if candidate.exists():
            for line in candidate.read_text().splitlines():
                if line.strip().startswith("KIE_API_KEY="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    sys.exit("ERROR: KIE_API_KEY not found in environment or ~/.config/kie/kie.env")

def upload_local_image(api_key: str, file_path: Path) -> str:
    mime, _ = mimetypes.guess_type(str(file_path))
    mime = mime or "image/jpeg"
    b64 = base64.b64encode(file_path.read_bytes()).decode("utf-8")
    payload = {
        "base64Data": f"data:{mime};base64,{b64}",
        "uploadPath": "product-assets",
        "fileName": f"{int(time.time())}_{file_path.name}"
    }
    r = requests.post(UPLOAD_URL, headers={"Authorization": f"Bearer {api_key}"}, json=payload, timeout=60)
    r.raise_for_status()
    data = r.json()
    url = (data.get("data") or {}).get("downloadUrl")
    if not url:
        raise RuntimeError("Reference upload did not return a download URL")
    return url


def timestamp():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def atomic_write(path, content):
    """Commit bytes in the same directory, never expose partially written JSON/images."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        directory_fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def save_state(path, state):
    atomic_write(path, (json.dumps(state, indent=2) + "\n").encode())


@contextmanager
def product_lock(product_dir):
    """All writers must share this inode; never unlink the lock file."""
    with (product_dir / ".launch-state.lock").open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise RuntimeError("Product state is busy; wait for the other writer") from None
        try:
            yield
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)


def validate_image(content):
    with Image.open(io.BytesIO(content)) as image:
        if image.format not in {"PNG", "JPEG", "WEBP"}:
            raise ValueError("Expected a PNG, JPEG or WebP image")
        image.verify()
    # Verification alone does not fully decode every format.
    with Image.open(io.BytesIO(content)) as image:
        image.load()


def request_fingerprint(args):
    references = []
    for ref in args.refs:
        if ref.startswith(("https://", "http://")):
            references.append({"url": ref})
        else:
            path = Path(ref).resolve(strict=True)
            references.append({"sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    request = {"mode": args.mode, "prompt": args.prompt, "aspect": args.aspect,
               "resolution": "1K", "refs": references}
    return hashlib.sha256(json.dumps(request, sort_keys=True).encode()).hexdigest()


def generate(args, product_dir, target_file):
    state_file = product_dir / "launch-state.json"
    state = json.loads(state_file.read_text()) if state_file.exists() else {"images": {}, "steps": {}}
    if not isinstance(state, dict) or not isinstance(state.setdefault("images", {}), dict):
        raise ValueError("Invalid launch-state.json: expected an object with an images object")
    images = state["images"]
    img_state = images.get(args.out, {})
    if not isinstance(img_state, dict):
        raise ValueError("Invalid image state")
    fingerprint = request_fingerprint(args)
    if img_state and img_state.get("fingerprint") != fingerprint:
        raise RuntimeError("Changed or legacy inputs: reconcile existing state; use a new output for an approved revision")
    if args.adopt_task_id and args.retry_failed:
        raise ValueError("Task adoption and retry are mutually exclusive")
    if args.adopt_task_id:
        if img_state.get("status") not in {"submitting", "submission-unknown"} or img_state.get("taskId"):
            raise RuntimeError("Adopt only a verified provider task for an uncertain submission")
        img_state.update(taskId=args.adopt_task_id, status="processing")
        save_state(state_file, state)
    if args.retry_failed:
        if img_state.get("status") != "failed" or not img_state.get("taskId"):
            raise RuntimeError("Retry requires a recorded terminal provider failure with task ID")
        history = list(img_state.get("attempts", []))
        history.append({key: value for key, value in img_state.items() if key != "attempts"})
        img_state = {"fingerprint": fingerprint, "attempts": history}
    elif img_state.get("status") == "failed":
        raise RuntimeError("Provider task failed; new paid generation requires explicit --retry-failed")
    if img_state.get("status") in {"submitting", "submission-unknown"}:
        raise RuntimeError("Submission outcome unknown: reconcile in Kie and use --adopt-task-id; no automatic resubmit")

    if img_state.get("status") == "completed" and target_file.exists():
        try:
            content = target_file.read_bytes()
            validate_image(content)
            if hashlib.sha256(content).hexdigest() != img_state.get("sha256"):
                raise ValueError("Output hash changed")
        except (OSError, ValueError, Image.DecompressionBombError):
            if not img_state.get("taskId"):
                raise RuntimeError("Invalid completed output with no task ID; reconcile manually") from None
        else:
            print(f"SKIP: {args.out} matches its completed request and validated image.")
            return
    if target_file.exists() and not img_state:
        raise RuntimeError("Untracked output exists; reconcile it or choose a new output name")

    api_key = load_api_key()
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    task_id = img_state.get("taskId")
    if not task_id:
        # Only a new slot or an explicitly approved terminal-failure retry can submit.
        if img_state.get("status"):
            raise RuntimeError("Existing state lacks a resumable task ID; reconcile before generating")
        ref_urls = [ref if ref.startswith(("http://", "https://")) else
                    upload_local_image(api_key, Path(ref).resolve()) for ref in args.refs]
        model = {"store": "nano-banana-2-1", "ad": "gpt-image-2-5-sunburst-image-to-image",
                 "ad-flare": "gpt-image-2-5-flare-image-to-image"}[args.mode]
        input_obj = {"prompt": args.prompt, "aspect_ratio": args.aspect, "resolution": "1K"}
        input_obj["image_input" if args.mode == "store" else "input_urls"] = ref_urls
        if args.mode == "store":
            input_obj["output_format"] = "png"
        # Durable intent FIRST: a crash or lost response is ambiguous, never permission to retry.
        img_state.update(status="submitting", fingerprint=fingerprint, model=model, submittedAt=timestamp())
        images[args.out] = img_state
        save_state(state_file, state)
        print(f"Submitting task ({model}) for {args.out}...")
        try:
            resp = requests.post(CREATE_TASK_URL, headers=headers,
                                 json={"model": model, "input": input_obj}, timeout=60)
            resp.raise_for_status()
            task_id = (resp.json().get("data") or {}).get("taskId")
            if not isinstance(task_id, str) or not task_id:
                raise ValueError("No task ID in create response")
        except Exception:
            img_state["status"] = "submission-unknown"
            save_state(state_file, state)
            raise RuntimeError("Submission outcome unknown; reconcile the provider task before retrying") from None
        img_state.update(status="processing", taskId=task_id)
        save_state(state_file, state)

    print(f"Polling taskId {task_id} for {args.out}...")
    for _ in range(90):
        time.sleep(4)
        poll = requests.get(RECORD_INFO_URL, headers=headers, params={"taskId": task_id}, timeout=30)
        poll.raise_for_status()
        data = poll.json().get("data") or {}
        status = str(data.get("state", "")).lower()
        if status == "success":
            result = data.get("resultJson")
            if isinstance(result, str):
                result = json.loads(result)
            urls = (result or {}).get("resultUrls") or []
            if not urls:
                raise ValueError("Successful task returned no image URL; retain its task ID and retry polling")
            download = requests.get(urls[0], timeout=60)
            download.raise_for_status()
            validate_image(download.content)
            atomic_write(target_file, download.content)
            img_state.update(status="completed", completedAt=timestamp(),
                             sha256=hashlib.sha256(download.content).hexdigest())
            save_state(state_file, state)
            print(f"SAVED: {target_file}")
            return
        if status in {"fail", "failed", "error"}:
            # Retain the ID; do not persist raw payloads or signed URLs in state/errors.
            img_state.update(status="failed", failedAt=timestamp())
            save_state(state_file, state)
            raise RuntimeError("Provider task failed; retained task ID for reconciliation")
    raise RuntimeError("Polling timed out; run the identical command to resume the saved task")


def validate_target_file(product_dir: Path, out_str: str) -> tuple[str, Path]:
    relative = Path(out_str)
    target_file = (product_dir / relative).resolve()
    if relative.is_absolute() or ".." in relative.parts or not target_file.is_relative_to(product_dir):
        raise ValueError("Output must stay inside the product directory")
    if relative.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp"}:
        raise ValueError("Output must be an image filename, never state or lock files")
    return relative.as_posix(), target_file


def main(argv=None):
    parser = argparse.ArgumentParser(description="Crash-aware, serialized Kie.ai image generation")
    parser.add_argument("--product-dir", required=True, help="Root folder of the product in Pictures")
    parser.add_argument("--batch", help="Path to JSON file containing a list of image jobs ({out, mode, prompt, aspect, refs})")
    parser.add_argument("--out", help="Relative output path (e.g. noir/01.png or ads_folder/ad_01.png)")
    parser.add_argument("--mode", choices=["store", "ad", "ad-flare"], default="store",
                        help="store = nano-banana-2-1 | ad = gpt-image-2-5-sunburst-image-to-image")
    parser.add_argument("--prompt", help="Generation prompt")
    parser.add_argument("--aspect", default="1:1", help="Aspect ratio (default 1:1)")
    parser.add_argument("--refs", nargs="+", help="1 or more local reference image paths or URLs")
    parser.add_argument("--adopt-task-id", help="Resume a verified task after an uncertain submission; never submits")
    parser.add_argument("--retry-failed", action="store_true", help="Explicitly authorize a new paid task after terminal failure")
    args = parser.parse_args(argv)
    product_dir = Path(args.product_dir).resolve(strict=True)
    if not product_dir.is_dir():
        raise ValueError("Product directory must exist")

    if args.batch:
        batch_items = json.loads(Path(args.batch).read_text())
        if not isinstance(batch_items, list) or not batch_items:
            raise ValueError("Batch file must contain a non-empty JSON list of jobs")
        jobs = []
        for item in batch_items:
            if not isinstance(item, dict) or not item.get("out") or not item.get("prompt") or not item.get("refs"):
                raise ValueError("Each batch job requires 'out', 'prompt', and 'refs'")
            norm_out, target_file = validate_target_file(product_dir, item["out"])
            job_args = argparse.Namespace(
                product_dir=str(product_dir),
                out=norm_out,
                mode=item.get("mode", "store"),
                prompt=item["prompt"],
                aspect=item.get("aspect", "1:1"),
                refs=item["refs"],
                adopt_task_id=item.get("adopt_task_id"),
                retry_failed=bool(item.get("retry_failed", False)),
            )
            jobs.append((job_args, target_file))
        with product_lock(product_dir):
            for job_args, target_file in jobs:
                generate(job_args, product_dir, target_file)
        return

    if not args.out or not args.prompt or not args.refs:
        raise ValueError("Single-image mode requires --out, --prompt, and --refs (or pass --batch)")
    args.out, target_file = validate_target_file(product_dir, args.out)
    with product_lock(product_dir):
        generate(args, product_dir, target_file)

if __name__ == "__main__":
    try:
        main()
    except requests.RequestException as exc:
        sys.exit(f"ERROR: network/HTTP failure ({type(exc).__name__}); retain state and retry the same task")
    except (OSError, ValueError, RuntimeError, Image.DecompressionBombError) as exc:
        sys.exit(f"ERROR: {exc}")
