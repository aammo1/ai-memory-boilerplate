#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["requests", "pillow"]
# ///
"""Offline regression checks: no credentials, API requests or production writes."""
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import requests
from PIL import Image

import kie_generate as kie


def response(data=None, content=b"", error=None):
    result = Mock(content=content)
    result.json.return_value = data
    result.raise_for_status.side_effect = error
    return result


class GenerationRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="kie-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.ref = self.root / "ref.png"
        image = io.BytesIO()
        Image.new("RGB", (4, 4), "red").save(image, format="PNG")
        self.image = image.getvalue()
        self.ref.write_bytes(self.image)
        self.args = ["--product-dir", str(self.root), "--out", "noir/01.png",
                     "--prompt", "approved prompt", "--refs", str(self.ref)]
        self.post = self.enterContext(patch.object(kie.requests, "post"))
        self.get = self.enterContext(patch.object(kie.requests, "get"))
        self.enterContext(patch.object(kie, "load_api_key", return_value="offline-test-key"))
        self.enterContext(patch.object(kie.time, "sleep"))
        self.enterContext(patch.object(kie, "upload_local_image", return_value="https://example.invalid/ref.png"))
        self.post.return_value = response({"data": {"taskId": "task-1"}})
        self.successful_download()

    def successful_download(self):
        self.get.side_effect = [response({"data": {"state": "success", "resultJson":
                              json.dumps({"resultUrls": ["https://example.invalid/result.png"]})}}),
                               response(content=self.image)]

    def state(self):
        return json.loads((self.root / "launch-state.json").read_text())

    def test_success_and_completed_skip_preserve_other_metadata(self):
        kie.save_state(self.root / "launch-state.json", {"store": "zehri", "steps": {"7": {"status": "pending"}}})
        kie.main(self.args)
        self.assertEqual(self.state()["images"]["noir/01.png"]["status"], "completed")
        self.assertEqual(self.state()["store"], "zehri")
        self.assertEqual(self.state()["steps"]["7"]["status"], "pending")
        self.post.reset_mock()
        self.get.reset_mock()
        kie.main(self.args)
        self.post.assert_not_called()
        self.get.assert_not_called()

    def test_lost_create_response_blocks_resubmission_and_can_adopt(self):
        self.post.side_effect = requests.Timeout()
        with self.assertRaisesRegex(RuntimeError, "outcome unknown"):
            kie.main(self.args)
        self.assertEqual(self.state()["images"]["noir/01.png"]["status"], "submission-unknown")
        with self.assertRaisesRegex(RuntimeError, "no automatic resubmit"):
            kie.main(self.args)
        self.assertEqual(self.post.call_count, 1)
        kie.main(self.args + ["--adopt-task-id", "verified-task"])
        self.assertEqual(self.state()["images"]["noir/01.png"]["taskId"], "verified-task")
        self.assertEqual(self.post.call_count, 1)

    def test_process_interruption_after_submission_keeps_intent(self):
        self.post.side_effect = KeyboardInterrupt()
        with self.assertRaises(KeyboardInterrupt):
            kie.main(self.args)
        self.assertEqual(self.state()["images"]["noir/01.png"]["status"], "submitting")
        with self.assertRaisesRegex(RuntimeError, "no automatic resubmit"):
            kie.main(self.args)
        self.assertEqual(self.post.call_count, 1)

    def test_poll_failure_resumes_same_task_without_post(self):
        self.get.side_effect = requests.Timeout()
        with self.assertRaises(requests.Timeout):
            kie.main(self.args)
        self.assertEqual(self.state()["images"]["noir/01.png"]["taskId"], "task-1")
        self.successful_download()
        kie.main(self.args)
        self.assertEqual(self.post.call_count, 1)

    def test_changed_prompt_or_reference_cannot_reuse_output(self):
        kie.main(self.args)
        changed = self.args.copy()
        changed[changed.index("approved prompt")] = "different prompt"
        with self.assertRaisesRegex(RuntimeError, "Changed or legacy"):
            kie.main(changed)
        self.ref.write_bytes(b"changed reference")
        with self.assertRaisesRegex(RuntimeError, "Changed or legacy"):
            kie.main(self.args)
        self.assertEqual(self.post.call_count, 1)

    def test_invalid_or_http_error_download_never_marks_completed(self):
        for download in [response(content=b"<html>error</html>"),
                         response(error=requests.HTTPError())]:
            self.successful_download()
            poll = self.get.side_effect
            # Rebuild a success poll followed by a bad download for the saved task.
            self.get.side_effect = [next(poll), download]
            with self.assertRaises((OSError, requests.HTTPError)):
                kie.main(self.args)
            self.assertEqual(self.state()["images"]["noir/01.png"]["status"], "processing")
            self.assertFalse((self.root / "noir/01.png").exists())
        self.assertEqual(self.post.call_count, 1)

    def test_terminal_failure_requires_explicit_retry_and_keeps_history(self):
        self.get.side_effect = [response({"data": {"state": "fail"}})]
        with self.assertRaisesRegex(RuntimeError, "Provider task failed"):
            kie.main(self.args)
        with self.assertRaisesRegex(RuntimeError, "--retry-failed"):
            kie.main(self.args)
        self.successful_download()
        self.post.return_value = response({"data": {"taskId": "task-2"}})
        kie.main(self.args + ["--retry-failed"])
        entry = self.state()["images"]["noir/01.png"]
        self.assertEqual(entry["taskId"], "task-2")
        self.assertEqual(entry["attempts"][0]["taskId"], "task-1")
        self.assertEqual(self.post.call_count, 2)

    def test_corrupt_completed_file_redownloads_without_regeneration(self):
        kie.main(self.args)
        (self.root / "noir/01.png").write_bytes(b"broken image")
        self.successful_download()
        kie.main(self.args)
        self.assertEqual(self.post.call_count, 1)
        self.assertEqual((self.root / "noir/01.png").read_bytes(), self.image)

    def test_rejects_path_escape_reserved_output_and_untracked_file(self):
        for output in ["../escape.png", "/tmp/escape.png", "launch-state.json", ".launch-state.lock"]:
            args = self.args.copy()
            args[args.index("noir/01.png")] = output
            with self.assertRaises(ValueError):
                kie.main(args)
        (self.root / "noir").mkdir()
        (self.root / "noir/01.png").write_bytes(self.image)
        with self.assertRaisesRegex(RuntimeError, "Untracked"):
            kie.main(self.args)
        self.post.assert_not_called()

    def test_legacy_records_do_not_silently_resubmit(self):
        kie.save_state(self.root / "launch-state.json", {"images": {"noir/01.png": {"status": "failed"}}})
        with self.assertRaisesRegex(RuntimeError, "legacy"):
            kie.main(self.args)
        self.post.assert_not_called()

    def test_second_process_cannot_enter_locked_product(self):
        code = "import fcntl,sys; f=open(sys.argv[1],'a'); fcntl.flock(f,fcntl.LOCK_EX); print('locked',flush=True); sys.stdin.read()"
        child = subprocess.Popen([sys.executable, "-c", code, str(self.root / ".launch-state.lock")],
                                 stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
        try:
            self.assertEqual(child.stdout.readline().strip(), "locked")
            with self.assertRaisesRegex(RuntimeError, "busy"):
                kie.main(self.args)
            self.post.assert_not_called()
        finally:
            child.communicate(input="", timeout=5)
        kie.main(self.args)

    def test_atomic_replace_failure_leaves_original_state_intact(self):
        path = self.root / "launch-state.json"
        kie.save_state(path, {"original": True})
        with patch.object(kie.os, "replace", side_effect=OSError("simulated replace failure")):
            with self.assertRaises(OSError):
                kie.save_state(path, {"original": False})
        self.assertEqual(json.loads(path.read_text()), {"original": True})
        self.assertEqual(list(self.root.glob(".launch-state.json.*")), [])

    def test_batch_mode_generates_multiple_slots_and_skips_completed(self):
        batch_file = self.root / "batch.json"
        batch_file.write_text(json.dumps([
            {"out": "noir/01.png", "mode": "store", "prompt": "hero prompt", "refs": [str(self.ref)]},
            {"out": "ads_folder/ad_01.png", "mode": "ad", "prompt": "ad prompt", "refs": [str(self.ref)]},
        ]))
        self.post.side_effect = [
            response({"data": {"taskId": "task-b1"}}),
            response({"data": {"taskId": "task-b2"}}),
        ]
        self.get.side_effect = [
            response({"data": {"state": "success", "resultJson": json.dumps({"resultUrls": ["https://example.invalid/1.png"]})}}),
            response(content=self.image),
            response({"data": {"state": "success", "resultJson": json.dumps({"resultUrls": ["https://example.invalid/2.png"]})}}),
            response(content=self.image),
        ]
        kie.main(["--product-dir", str(self.root), "--batch", str(batch_file)])
        self.assertEqual(self.state()["images"]["noir/01.png"]["status"], "completed")
        self.assertEqual(self.state()["images"]["ads_folder/ad_01.png"]["status"], "completed")
        self.assertEqual(self.post.call_count, 2)
        # Re-running the same batch skips both completed images without network calls
        self.post.reset_mock()
        self.get.reset_mock()
        kie.main(["--product-dir", str(self.root), "--batch", str(batch_file)])
        self.post.assert_not_called()
        self.get.assert_not_called()


if __name__ == "__main__":
    unittest.main()
