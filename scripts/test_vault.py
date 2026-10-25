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
NEW_NICHE_SCRIPT = SCRIPTS_DIR / "new-niche.py"


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

    def test_new_niche_brand_new_user_and_second_store(self):
        fake_template = self.root / "fake-store-template"
        fake_template.mkdir()
        (fake_template / "AGENTS.md").write_text("# Store CRM Template\n", encoding="utf-8")
        (fake_template / "package.json").write_text('{"name": "store-crm-boilerplate"}\n', encoding="utf-8")

        projects_dir = self.root / "Projects"
        pictures_dir = self.root / "Pictures"
        config_dir = self.root / "config"

        # Pre-seed .env.local and .env.production.example in the target repo to verify .env.local takes priority
        glow_repo = projects_dir / "glow-skin"
        glow_repo.mkdir(parents=True)
        (glow_repo / "AGENTS.md").write_text("# Store CRM Template\n", encoding="utf-8")
        (glow_repo / "package.json").write_text('{"name": "store-crm-boilerplate"}\n', encoding="utf-8")
        (glow_repo / ".env.local").write_text(
            'CRM_PUBLIC_URL="http://localhost:3000"\nCATALOG_AGENT_KEY="local_secret_key_at_least_32_chars_long_123"\n',
            encoding="utf-8",
        )
        (glow_repo / ".env.production.example").write_text(
            'CRM_PUBLIC_URL="https://prod.example.ma"\nCATALOG_AGENT_KEY="prod_secret_key_at_least_32_chars_long_456"\n',
            encoding="utf-8",
        )

        # 1. Brand-new user (vault does not exist yet!)
        res1 = run_cli(
            NEW_NICHE_SCRIPT,
            "--store",
            "glow-skin",
            "--name",
            "Karim",
            "--memory-dir",
            str(self.vault),
            "--projects-dir",
            str(projects_dir),
            "--pictures-dir",
            str(pictures_dir),
            "--config-dir",
            str(config_dir),
            "--skills-dir",
            str(self.skills),
            "--store-template",
            str(fake_template),
            "--skip-npm",
        )
        self.assertEqual(res1.returncode, 0, msg=res1.stderr or res1.stdout)
        self.assertTrue((self.vault / "PROFILE.md").is_file())
        self.assertTrue((self.skills / "ai-memory-kit/SKILL.md").is_file())
        self.assertTrue((self.skills / "crm-catalog/SKILL.md").is_file())
        self.assertTrue((projects_dir / "glow-skin/package.json").is_file())
        self.assertIn("## External Memory & Workflow", (projects_dir / "glow-skin/AGENTS.md").read_text(encoding="utf-8"))
        self.assertTrue((pictures_dir / "glow-skin_pics/staging").is_dir())
        self.assertTrue((pictures_dir / "glow-skin_pics/uploaded").is_dir())
        self.assertTrue((config_dir / "glow-skin/catalog-agent.env").is_file())
        env_text = (config_dir / "glow-skin/catalog-agent.env").read_text(encoding="utf-8")
        self.assertIn("CRM_CATALOG_URL=http://localhost:3000", env_text)
        self.assertIn("CRM_CATALOG_KEY=local_secret_key_at_least_32_chars_long_123", env_text)
        prod_env_path = config_dir / "glow-skin/catalog-agent.prod.env"
        self.assertTrue(prod_env_path.is_file())
        prod_env_text = prod_env_path.read_text(encoding="utf-8")
        self.assertIn("CRM_CATALOG_URL=https://prod.example.ma", prod_env_text)
        self.assertIn("CRM_CATALOG_KEY=prod_secret_key_at_least_32_chars_long_456", prod_env_text)

        # 2. Existing user adding a 2nd store via the vault's bundled tools/new-niche.py
        vault_new_niche = self.vault / "tools/new-niche.py"
        res2 = run_cli(
            vault_new_niche,
            "--store",
            "car-gadgets",
            "--memory-dir",
            str(self.vault),
            "--projects-dir",
            str(projects_dir),
            "--pictures-dir",
            str(pictures_dir),
            "--config-dir",
            str(config_dir),
            "--store-template",
            str(fake_template),
            "--skip-npm",
        )
        self.assertEqual(res2.returncode, 0, msg=res2.stderr or res2.stdout)
        self.assertTrue((self.vault / "01 Products/car-gadgets").is_dir())
        self.assertTrue((self.vault / "02 Bases/car-gadgets_Marketing.base").is_file())
        self.assertTrue((projects_dir / "car-gadgets/package.json").is_file())
        self.assertTrue((config_dir / "car-gadgets/catalog-agent.env").is_file())

        profile_text = (self.vault / "PROFILE.md").read_text(encoding="utf-8")
        self.assertIn(str(projects_dir / "glow-skin"), profile_text)
        self.assertIn("`https://prod.example.ma`", profile_text)
        self.assertIn(str(projects_dir / "car-gadgets"), profile_text)
        self.assertIn("| **Catalog API Env (Production)** |", profile_text)
        self.assertIn(f"`{prod_env_path}`", profile_text)

        # 3. Older PROFILE.md without the production row gets it inserted after `Catalog API Env`
        profile_path = self.vault / "PROFILE.md"
        legacy = "\n".join(
            l for l in profile_text.splitlines() if not l.startswith("| **Catalog API Env (Production)** |")
        ) + "\n"
        profile_path.write_text(legacy, encoding="utf-8")
        res3 = run_cli(
            vault_new_niche,
            "--store",
            "glow-skin",
            "--memory-dir",
            str(self.vault),
            "--projects-dir",
            str(projects_dir),
            "--pictures-dir",
            str(pictures_dir),
            "--config-dir",
            str(config_dir),
            "--store-template",
            str(fake_template),
            "--skip-npm",
        )
        self.assertEqual(res3.returncode, 0, msg=res3.stderr or res3.stdout)
        rows = [l for l in profile_path.read_text(encoding="utf-8").splitlines() if l.startswith("| **Catalog API Env")]
        self.assertEqual(len(rows), 2, msg=rows)
        self.assertTrue(rows[1].startswith("| **Catalog API Env (Production)** |"))
        self.assertIn(f"`{prod_env_path}`", rows[1])

        verify_res = run_cli(VERIFY_SCRIPT, "--memory-dir", str(self.vault))
        self.assertEqual(verify_res.returncode, 0, msg=verify_res.stdout)

    def test_slug_normalization_harness_symlinks_and_update_skills(self):
        harness_home = self.root / "fake-home"
        for sub in [".claude", ".codex", ".gemini/config", ".gemini/antigravity-cli", ".cursor"]:
            (harness_home / sub).mkdir(parents=True)
        # A pre-existing real skill folder must be reported, not silently skipped
        (harness_home / ".cursor/skills/crm-catalog").mkdir(parents=True)

        # Underscores & uppercase normalize cleanly to hyphenated lowercase; 1-char slug fails
        bad = run_cli(SETUP_SCRIPT, "--memory-dir", str(self.vault), "--stores", "x")
        self.assertNotEqual(bad.returncode, 0)

        ok = run_cli(
            SETUP_SCRIPT,
            "--memory-dir",
            str(self.vault),
            "--name",
            "Yassine",
            "--stores",
            "My_Brand",
            "--skills-dir",
            str(self.skills),
            "--harness-home",
            str(harness_home),
            "--install-skill",
        )
        self.assertEqual(ok.returncode, 0, msg=ok.stderr or ok.stdout)
        self.assertTrue((self.vault / "01 Products/my-brand").is_dir())
        self.assertIn("WARNING:", ok.stdout)
        self.assertIn(str(harness_home / ".cursor/skills/crm-catalog"), ok.stdout)
        kit = (self.skills / "ai-memory-kit/SKILL.md").read_text(encoding="utf-8")
        self.assertNotIn("{{SKILLS_DIR}}", kit)
        self.assertIn(f"{self.skills.resolve()}/crm-catalog/SKILL.md", kit)

        for sub in [".claude/skills", ".codex/skills", ".gemini/config/skills", ".gemini/antigravity-cli/skills", ".cursor/skills"]:
            for skill_name in ["ai-memory-kit", "morocco-cod-marketing", "crm-catalog", "product-page-marketing-sections"]:
                link = harness_home / sub / skill_name
                if sub == ".cursor/skills" and skill_name == "crm-catalog":
                    self.assertFalse(link.is_symlink())
                    continue
                self.assertTrue(link.is_symlink(), msg=f"Missing symlink: {link}")
                self.assertEqual(link.resolve(), (self.skills / skill_name).resolve())

        # Modify a vault file and a skill file, then run --update-skills: skill refreshes, vault stays untouched
        todo_path = self.vault / "TODO.md"
        todo_path.write_text("# Custom User Todo\n", encoding="utf-8")
        crm_skill = self.skills / "crm-catalog/SKILL.md"
        crm_skill.write_text("stale content", encoding="utf-8")
        vault_tool = self.vault / "tools/new-niche.py"
        vault_tool.write_text("# old launcher\n", encoding="utf-8")

        upd = run_cli(
            SETUP_SCRIPT,
            "--memory-dir",
            str(self.vault),
            "--skills-dir",
            str(self.skills),
            "--harness-home",
            str(harness_home),
            "--update-skills",
        )
        self.assertEqual(upd.returncode, 0, msg=upd.stderr or upd.stdout)
        self.assertIn("overwrites the installed skill files", upd.stdout)
        self.assertEqual(vault_tool.read_bytes(), NEW_NICHE_SCRIPT.read_bytes())
        self.assertEqual((self.vault / "tools/new-niche.py.bak").read_text(encoding="utf-8"), "# old launcher\n")
        self.assertIn("SKIP (same)", upd.stdout)
        self.assertEqual(todo_path.read_text(encoding="utf-8"), "# Custom User Todo\n")
        self.assertIn("Store CRM Live Catalog", crm_skill.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
