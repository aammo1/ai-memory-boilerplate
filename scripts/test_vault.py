#!/usr/bin/env python3
"""Offline unit tests for setup.py and verify.py."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
SETUP_SCRIPT = SCRIPTS_DIR / "setup.py"
VERIFY_SCRIPT = SCRIPTS_DIR / "verify.py"


def run_cli(script: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(script), *args],
        capture_output=True,
        text=True,
        check=False,
    )


class UnifiedVaultTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="vault-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.vault = self.root / "my-vault"
        self.skills = self.root / "skills"

    def init_vault(self, stores="zehri,hellobaby"):
        res = run_cli(
            SETUP_SCRIPT,
            "--memory-dir",
            str(self.vault),
            "--name",
            "TestOperator",
            "--stores",
            stores,
            "--skills-dir",
            str(self.skills),
            "--install-skill",
        )
        self.assertEqual(res.returncode, 0, msg=res.stderr or res.stdout)

    def build_valid_note_text(self, cover_val='"[[03 Assets/Product images/boot.webp]]"') -> str:
        tpl_text = (self.vault / "00 Templates/Product Template.md").read_text(encoding="utf-8")
        text = tpl_text.replace('cover: ""', f"cover: {cover_val}", 1)
        return text + "\n# TEST PRODUCT\n\nBody text.\n"

    def test_initial_setup_and_verify_pass(self):
        self.init_vault("zehri,hellobaby")
        self.assertTrue((self.vault / "00 Templates/Product Template.md").is_file())
        self.assertTrue((self.vault / "01 Products/zehri").is_dir())
        self.assertTrue((self.vault / "01 Products/hellobaby").is_dir())
        self.assertTrue((self.vault / "02 Bases/Products_Marketing.base").is_file())
        self.assertTrue((self.vault / "02 Bases/zehri_Marketing.base").is_file())
        self.assertTrue((self.vault / "02 Bases/hellobaby_Marketing.base").is_file())
        self.assertTrue((self.vault / ".obsidian/types.json").is_file())
        self.assertTrue((self.vault / ".obsidian/plugins/good-bases/main.js").is_file())
        self.assertTrue((self.skills / "ai-memory-kit/SKILL.md").is_file())
        self.assertTrue((self.skills / "morocco-cod-marketing/SKILL.md").is_file())
        self.assertTrue((self.skills / "crm-catalog/SKILL.md").is_file())
        self.assertTrue((self.skills / "crm-catalog/scripts/catalog-agent-client.mjs").is_file())
        self.assertTrue((self.skills / "product-page-marketing-sections/SKILL.md").is_file())

        types_data = json.loads((self.vault / ".obsidian/types.json").read_text(encoding="utf-8"))
        self.assertEqual(len(types_data["types"]), 17)
        self.assertEqual(types_data["types"]["🛫 categories"], "multitext")
        self.assertEqual(types_data["types"]["🌟Action_plan"], "text")

        master_base = (self.vault / "02 Bases/Products_Marketing.base").read_text(encoding="utf-8")
        self.assertIn("name: All Products Table", master_base)
        self.assertIn("- file.folder", master_base)
        self.assertIn("name: zehri Products", master_base)
        self.assertIn("name: hellobaby Products", master_base)

        verify_res = run_cli(VERIFY_SCRIPT, "--memory-dir", str(self.vault))
        self.assertEqual(verify_res.returncode, 0, msg=verify_res.stdout)
        self.assertIn("PASS unified vault health check", verify_res.stdout)

    def test_add_store_updates_profile_and_master_base(self):
        self.init_vault("zehri")
        add_res = run_cli(SETUP_SCRIPT, "--memory-dir", str(self.vault), "--add-store", "cosmetics")
        self.assertEqual(add_res.returncode, 0, msg=add_res.stdout)

        self.assertTrue((self.vault / "01 Products/cosmetics").is_dir())
        self.assertTrue((self.vault / "02 Bases/cosmetics_Marketing.base").is_file())

        profile_text = (self.vault / "PROFILE.md").read_text(encoding="utf-8")
        self.assertIn("| `zehri` | `cosmetics` |", profile_text)
        self.assertIn("`01 Products/cosmetics/<product>.md`", profile_text)
        self.assertIn("cosmetics_Marketing.base", profile_text)

        master_base = (self.vault / "02 Bases/Products_Marketing.base").read_text(encoding="utf-8")
        self.assertIn("name: cosmetics Products", master_base)

        verify_res = run_cli(VERIFY_SCRIPT, "--memory-dir", str(self.vault))
        self.assertEqual(verify_res.returncode, 0, msg=verify_res.stdout)

    def test_verify_valid_product_note_and_catches_invalid_notes(self):
        self.init_vault("zehri")
        img_path = self.vault / "03 Assets/Product images/boot.webp"
        img_path.write_bytes(b"RIFF....WEBP")
        note_path = self.vault / "01 Products/zehri/SANS ESCALE.md"

        # 1. Valid note passes
        note_path.write_text(self.build_valid_note_text(), encoding="utf-8")
        res = run_cli(VERIFY_SCRIPT, "--memory-dir", str(self.vault))
        self.assertEqual(res.returncode, 0, msg=res.stdout)

        # 2. Broken cover image link fails
        note_path.write_text(
            self.build_valid_note_text('"[[03 Assets/Product images/missing.webp]]"'),
            encoding="utf-8",
        )
        res = run_cli(VERIFY_SCRIPT, "--memory-dir", str(self.vault))
        self.assertEqual(res.returncode, 1)
        self.assertIn("Broken cover image wikilink", res.stdout)

        # 3. Non-wikilink cover format fails
        note_path.write_text(
            self.build_valid_note_text('"03 Assets/Product images/boot.webp"'),
            encoding="utf-8",
        )
        res = run_cli(VERIFY_SCRIPT, "--memory-dir", str(self.vault))
        self.assertEqual(res.returncode, 1)
        self.assertIn("Invalid cover format", res.stdout)

        # 4. Missing required template property fails
        missing_prop_text = self.build_valid_note_text().replace('📝NOTES: ""\n', "")
        note_path.write_text(missing_prop_text, encoding="utf-8")
        res = run_cli(VERIFY_SCRIPT, "--memory-dir", str(self.vault))
        self.assertEqual(res.returncode, 1)
        self.assertIn("Missing required template property '📝NOTES'", res.stdout)

        # 5. Duplicate YAML frontmatter key fails
        dup_key_text = self.build_valid_note_text().replace('📝NOTES: ""', '📝NOTES: ""\n📝NOTES: "dup"')
        note_path.write_text(dup_key_text, encoding="utf-8")
        res = run_cli(VERIFY_SCRIPT, "--memory-dir", str(self.vault))
        self.assertEqual(res.returncode, 1)
        self.assertIn("Duplicate YAML frontmatter key '📝NOTES'", res.stdout)

    def test_verify_catches_secret_leak(self):
        self.init_vault("zehri")
        todo_path = self.vault / "TODO.md"
        todo_path.write_text(todo_path.read_text() + "\nKIE_API_KEY=1234567890abcdef12345678\n")
        res = run_cli(VERIFY_SCRIPT, "--memory-dir", str(self.vault))
        self.assertEqual(res.returncode, 1)
        self.assertIn("Possible secret value detected", res.stdout)


if __name__ == "__main__":
    unittest.main()
