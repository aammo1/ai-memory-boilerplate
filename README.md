# ai-memory-boilerplate

A lightweight, **3-file external memory system + on-demand skill** for AI coding agents (**Antigravity, Claude Code, Codex, DSH, OpenCode, Cursor**).

Most AI memory setups fail because they force models to maintain 6+ folders, strict YAML frontmatter, manual folder indexes, and fragile cross-vault `[[wikilinks]]`. Models get "checklist fatigue" and break links.

**`ai-memory-boilerplate`** strips external memory down to what actually works: **3 plain Markdown files**, **per-project `AGENTS.md` isolation** (no global config pollution), and an **on-demand skill (`ai-memory-kit`)** you can call from any folder on your machine.

---

## How It Works

```text
your-memory-folder/
├── AGENTS.md        # Boot rules when opening the memory folder directly
├── PROFILE.md       # Who you are, your projects/paths table, and AI style rules
├── TODO.md          # Single open task queue + recent completed changelog
└── PIPELINE.md      # Reusable multi-step workflow SOP (with resumable state.json)
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
- Creates `$HOME/Work/ai-memory` with `AGENTS.md`, `PROFILE.md`, `TODO.md`, and `PIPELINE.md` (never overwrites existing files unless `--force` is passed).
- Initializes a Git repository inside `$HOME/Work/ai-memory`.
- Installs the **`ai-memory-kit`** skill into `~/.agents/skills/ai-memory-kit/SKILL.md` pointing to your new memory folder.

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
- Standard Workflow Pipeline: ~/Work/ai-memory/PIPELINE.md
```

### 3. Direct Memory Management
Open your `$HOME/Work/ai-memory` folder directly in your AI tool or Obsidian to plan across all your projects at once.

---

## Customizing `PIPELINE.md` for Your Domain

`templates/PIPELINE.md` includes a ready-to-adapt multi-step workflow with:
- **Step 0 (Resume & State Check):** Reads a per-item `state.json` so interrupted runs never repeat completed work.
- **Cost / Token Gate:** Requires the agent to ask which specific items/variations to generate before spending external API credits.
- **Human Review & Live Deployment Gates:** Requires explicit user confirmation before mutating live production systems or source code.

You can adapt the steps in `PIPELINE.md` for:
- **E-Commerce Product Launches** (Research -> Creative assets -> Catalog upload -> Landing page -> Ad drafts)
- **SaaS Feature Shipping** (Spec -> DB migration -> Backend API -> UI -> E2E tests -> Prod deploy)
- **Content / Agency Pipelines** (Brief -> Draft -> Visuals -> Review -> Publish)

---

## Repository Structure

```text
ai-memory-boilerplate/
├── README.md                        # Documentation
├── LICENSE                          # MIT License
├── scripts/
│   ├── setup.py                     # Interactive / CLI installer
│   └── verify.py                    # Read-only health & secret-leak checker
├── skill/
│   └── ai-memory-kit/
│       └── SKILL.md.template        # On-demand skill template for ~/.agents/skills/
└── templates/
    ├── AGENTS.md.template           # Memory workspace boot instructions
    ├── PROFILE.md.template          # Identity, project paths table, and AI preferences
    ├── TODO.md.template             # Open tasks queue and recent completed log
    └── PIPELINE.md.template         # Adaptable multi-step workflow with state.json tracking
```

## License

MIT License — free for personal and commercial use.
