# ai-memory-boilerplate

A lightweight, **3-file external memory system + on-demand skill** for AI coding agents (**Antigravity, Claude Code, Codex, DSH, OpenCode, Cursor**).

Most AI memory setups fail because they force models to maintain 6+ folders, strict YAML frontmatter, manual folder indexes, and fragile cross-vault `[[wikilinks]]`. Models get "checklist fatigue" and break links.

**`ai-memory-boilerplate`** strips external memory down to what actually works: **3 plain Markdown files**, **per-project `AGENTS.md` isolation** (no global config pollution), and an **on-demand skill (`ai-memory-kit`)** you can call from any folder on your machine.

---

## How It Works

```text
your-memory-folder/
├── AGENTS.md                # Boot rules when opening the memory folder directly
├── PROFILE.md               # Identity, store/project paths table, and AI style rules
├── TODO.md                  # Single open task queue + recent completed changelog
├── LAUNCH-PIPELINE.md       # End-to-end 10-step product launch SOP (Steps 0 to 10)
├── 03 - Reference Heroes/   # Store Hero 01 style reference images
└── tools/
    ├── kie_generate.py      # Crash-safe, batch-capable Kie.ai image generator (with flock locking)
    └── test_kie_generate.py # 13 offline regression tests (zero API cost)
```

### Why This Architecture Works Better
1. **Zero Global Pollution:** No global `~/.claude/CLAUDE.md` or `~/.dsh/AGENTS.md` forcing your side-projects to load unrelated rules. Only projects you choose connect to your memory.
2. **Call From Any Folder (`ai-memory-kit` skill):** Open any random folder on your laptop and say *"use `ai-memory-kit`"* to check tasks, save a decision, or register a new project on demand.
3. **Resumable Pipelines (`PIPELINE.md` + `state.json`):** Multi-step workflows track step completion on disk so a crashed session resumes at the exact unfinished step without repeating paid API calls.
4. **Git-Backed in 5 Seconds:** Because the whole memory is just 3 Markdown files, `git diff` and `git push` give you instant version history and off-device backups.

---

## Quick Start (1 Command)

Requirements: **Python 3.10+** and **Git**.

```bash
# 1. Clone this repository
git clone https://github.com/YOUR_USERNAME/ai-memory-boilerplate.git
cd ai-memory-boilerplate

# 2. Initialize your memory folder and install the on-demand skill
python3 scripts/setup.py --memory-dir "$HOME/Work/ai-memory" --name "Your Name" --install-skill
```

What `setup.py` does:
- Creates `$HOME/Work/ai-memory` with `AGENTS.md`, `PROFILE.md`, `TODO.md`, `LAUNCH-PIPELINE.md`, `03 - Reference Heroes/`, and `tools/kie_generate.py` (never overwrites existing files unless `--force` is passed).
- Initializes a Git repository inside `$HOME/Work/ai-memory`.
- Installs the **`ai-memory-kit`** skill into `~/.agents/skills/ai-memory-kit/SKILL.md` pointing to your new memory folder.

```bash
# Run offline unit tests for the Kie.ai batch & recovery generator (13 tests, 0 API calls)
uv run --script tools/test_kie_generate.py
```

---

## 3 Ways to Use Your Memory

### 1. On-Demand From Any Folder (Via the Skill)
Open **any** folder on your laptop in your AI tool and type:
- *"use `ai-memory-kit` and check my open tasks"*
- *"use `ai-memory-kit` and save a task to finish the auth refactor tomorrow"*
- *"use `ai-memory-kit` and register this project in `PROFILE.md` so it can use `PIPELINE.md`"*

### 2. Automatic Per-Project Connection (No Symlinks)
If you want a specific project repository to load your memory automatically every time you open it, paste these 5 lines at the top of that project's local `AGENTS.md`:

```markdown
## External Memory & Workflow
Shared cross-session memory lives in ~/Work/ai-memory:
- System Map & Preferences: ~/Work/ai-memory/PROFILE.md
- Open Tasks & Log: ~/Work/ai-memory/TODO.md
- 10-Step Product Launch SOP: ~/Work/ai-memory/LAUNCH-PIPELINE.md
```

### 3. Direct Memory Management
Open your `$HOME/Work/ai-memory` folder directly in your AI tool or Obsidian to plan across all your projects at once.

---

## Customizing `LAUNCH-PIPELINE.md` for Your Domain

`templates/LAUNCH-PIPELINE.md.template` includes the complete **10-step E-Commerce Product Launch Pipeline (Steps 0 to 10)** with:
- **Step 0 (Resume & State Check):** Reads a per-product `launch-state.json` under an exclusive `flock` lock so interrupted runs never repeat completed work.
- **Step 1 & 2 (Photos & Marketing Plan):** Direct per-store Obsidian marketing vault targeting (no fragile symlinks).
- **Step 3 (Staging Folder Tree):** Standardized `staging/<product_name>/` + color variant subfolders + `ads_folder/`.
- **Steps 4, 5 & 6 (Kie.ai Gallery & Static Ads + Token-Saving Gate):** Includes `tools/kie_generate.py` (supports single-image and `--batch` mode, input SHA-256 fingerprinting, `--adopt-task-id`, and `--retry-failed`) and always asks which specific gallery positions and ads to generate before spending API credits.
- **Steps 7, 8, 9 & 10 (Review Gate -> Catalog -> Landing Page Sections -> Paused Meta Ads Drafts):** Hard human approval stops before live catalog uploads, code changes, deployments, or ad creation.

---

## Repository Structure

```text
ai-memory-boilerplate/
├── README.md                              # Documentation
├── LICENSE                                # MIT License
├── scripts/
│   ├── setup.py                           # CLI installer (creates memory folder, copies tools, installs skill)
│   └── verify.py                          # Read-only health & secret-leak checker
├── skill/
│   └── ai-memory-kit/
│       └── SKILL.md.template              # On-demand skill template for ~/.agents/skills/
├── templates/
│   ├── AGENTS.md.template                 # Memory workspace boot instructions
│   ├── PROFILE.md.template                # Identity, store/project paths table, and AI preferences
│   ├── TODO.md.template                   # Open tasks queue and recent completed log
│   └── LAUNCH-PIPELINE.md.template        # Full 10-step product launch pipeline (Steps 0 to 10)
└── tools/
    ├── kie_generate.py                    # Crash-safe, batch-capable Kie.ai image generator
    └── test_kie_generate.py               # 13 offline unit tests for recovery, locking, and batch mode
```

## License

MIT License — free for personal and commercial use.
