# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this
repository. `AGENTS.md` is a symlink to this file, so other coding agents read the same
instructions — edit this file, not the symlink.

## Project Overview

This is a meal planning repository that implements a HelloFresh-like workflow for Swedish households. The system uses **multi-agent orchestration** to help with weekly meal planning through a structured 5-phase process: brainstorming → recipe selection → shopping list generation → recipe compilation → meal prep planning.

## Repository Structure

```
recipe/                              # Committed recipe library (not week-specific)
└── recept-<slug>-<portioner>p.md

YYYY-MM-DD/                          # Date-based meal planning folders (gitignored)
├── 01-brainstorming.md              # Meal preferences + candidate meals
├── 02-receptval.md                  # Selected recipes with links/sources
├── recept-*.md                      # Week-specific custom recipes
├── 03-handlingslista.md             # Pooled shopping list (generated on request)
├── 04-alla-recept.md                # All recipes in standardized format (generated on request)
└── 05-meal-prep-plan.md             # Optimized prep timeline (generated on request)

.claude/
├── rules/                           # Path-scoped conventions (load with matching files)
│   ├── recipe-style.md              # THE recipe standard — enforced by hook
│   └── recipe-examples.md           # Few-shot: gold recipe + good/bad pairs
├── hooks/
│   ├── validate_recipe.py           # Normalizes + validates a recipe file
│   ├── validate_week.py             # Cross-checks 03 shopping list against 04
│   ├── recipe_guard.sh              # PostToolUse wrapper
│   └── subagent_recipe_gate.sh      # SubagentStop wrapper
├── settings.json                    # Hook registration (committed)
├── agents/
│   ├── meal-planning-orchestrator.md  # Top-level orchestrator (use with claude --agent)
│   ├── brainstorming-agent.md         # Phase 1: meal candidate generation
│   ├── recipe-researcher.md           # Phase 2: parallel recipe research (one per dish)
│   ├── recipe-creator.md              # Phase 2: custom recipe creation
│   ├── shopping-list-generator.md     # Phase 3: pooled shopping list
│   ├── recipe-compiler.md             # Phase 4: standardized recipe compilation
│   └── meal-prep-optimizer.md         # Phase 5: time-optimized prep plan
├── skills/
│   ├── meal-planning-hello-fresh/     # Main workflow skill
│   │   ├── SKILL.md                   # Orchestration instructions
│   │   ├── reference.md               # Sources, units, categories
│   │   └── examples.md                # Output format examples
│   ├── create-recipe/                 # Custom recipe skill
│   │   └── SKILL.md                   # /create-recipe command
│   └── export-to-notion/              # Notion export skill (optional final step)
│       └── SKILL.md                   # /export-to-notion command
└── settings.local.json                # Local permission settings (gitignored)
```

## Multi-Agent Architecture

```
User
  ↓
[Main Conversation / Orchestrator]
  ├── Phase 1: brainstorming-agent (sonnet)
  ├── Phase 2: recipe-researcher × N (sonnet, PARALLEL — one per dish)
  │            + recipe-creator (on demand)
  ├── Phase 3: shopping-list-generator (sonnet)
  ├── Phase 4: recipe-compiler (sonnet)
  └── Phase 5: meal-prep-optimizer (inherit)
```

### Key Design Decisions

- **Parallel recipe research**: Phase 2 spawns one `recipe-researcher` agent per dish, all running in parallel. Each researcher compares 3-5 sources independently.
- **Subagents can't spawn subagents**: The main conversation acts as orchestrator. Alternatively, use `claude --agent meal-planning-orchestrator` for automated orchestration.
- **Skills preloaded into orchestrator**: The orchestrator agent has `meal-planning-hello-fresh` skill injected at startup via the `skills` field.

## Recipe Standard: Rules + Hooks (deterministic)

Recipe formatting is **not** left to prompt adherence. The convention lives in one
place and is enforced mechanically:

| Layer | File | What it does |
|---|---|---|
| Convention | `.claude/rules/recipe-style.md` | The recipe standard. Path-scoped — loads only when working with recipe files. |
| Few-shot | `.claude/rules/recipe-examples.md` | One gold recipe + good/bad pairs with reasoning. |
| Enforcement | `.claude/hooks/recipe_guard.sh` (PostToolUse on `Write`/`Edit`) | Normalizes mechanical issues in place, feeds remaining errors back to Claude. |
| Gate | `.claude/hooks/subagent_recipe_gate.sh` (SubagentStop) | `recipe-creator` / `recipe-compiler` can't finish while their recipes have errors. Releases after 2 blocked attempts so it can't loop. |
| Cross-check | `.claude/hooks/validate_week.py` | Every ingredient in `04` must appear in `03` with sufficient quantity. |
| Manual + CI | `/verify-recipes`, `.github/workflows/recipe-lint.yml` | Same validator on demand and on PRs (changed files only). |

**The rule that matters most:** every instruction step repeats the amount inline
(`Häll **1,5 dl** mjölk över **1 dl** ströbröd`), because the reader is standing at
the stove and won't scroll back to the ingredient list.

When the hook reports `RÄTTAT`, the file on disk was already changed — re-read it
before editing further. `FEL` must be fixed, not explained away. `TIPS` is advisory.

Recipes in `recipe/` predate the standard and are not yet migrated; convert one only
when asked, rather than running a mass migration.

## Core Workflow & Architecture

### Phase-Gated Process (CRITICAL)

The workflow has **mandatory stop points** between phases. Never proceed to the next phase without explicit user approval:

1. **Phase 1 (Brainstorming)**: Generate meal candidates based on preferences
   - Stop and wait: User selects dishes or provides own recipes

2. **Phase 2 (Recipe Selection)**: Parallel recipe research + custom recipe creation
   - Stop and wait: Ask "Vill du att jag skapar handlingslista nu?"

3. **Phase 3 (Shopping List)**: Generate pooled, consolidated shopping list
   - Stop and wait: Ask "Vill du att jag skapar receptsamling och meal prep-plan nu?"

4. **Phase 4 (Recipe Compilation)**: Compile all recipes into standardized format (`04-alla-recept.md`)
   - No stop point — continues directly to Phase 5

5. **Phase 5 (Meal Prep)**: Create optimized preparation timeline
   - Optional final step: Ask "Vill du exportera veckan till Notion (Inhandling)?" → run `export-to-notion`

### Export to Notion (optional final step)

After Phase 5, the week can be published to the Notion database **💸 Inhandling** via the
`export-to-notion` skill (`/export-to-notion [YYYY-MM-DD]`). This is optional, not a hard
phase gate, and can also be run standalone on any existing week folder.

- **Structure**: one overview page named `Vecka YYYY-MM-DD` (summary + linked table of
  contents), with **subpages** for the shopping list (`03`), one per recipe (parsed from
  `04`), and the meal-prep plan (`05`).
- **Must run in the main conversation** — Notion MCP isn't guaranteed inside subagents.
- **Inhandling data source** (parent for new pages):
  `collection://2ad3a69e-7647-80a2-89f3-000b0dfb831e` (database id
  `2ad3a69e-7647-806c-bba0-d503a8f0f2a0`, under the "Matlagning" page).
- See `.claude/skills/export-to-notion/SKILL.md` for the full procedure.

### Language & Units

- **Language**: Swedish only
- **Units**: Metric (g, kg, ml, dl, l, msk, tsk, st)
- **Normalization**: Convert to clearer units when appropriate (1000g → 1kg, 10dl → 1l)

### Recipe Sources Priority

**User is a professional chef - prioritize QUALITY over convenience**

1. **Best quality sources** (Swedish or international):
   - Köket.se (high-quality Swedish recipes, chef-tested)
   - Arla (especially for dairy-based dishes)
   - Mitt Kök (authentic Nordic cuisine)
   - Tasteline (professional Swedish chefs)
   - Landleys Kök (high-quality home cooking)
   - International sources when authenticity matters (e.g., Asian cuisine from authentic sources)

2. **Secondary sources**:
   - ICA, Coop (good for basic recipes but not priority)
   - Food blogs (if quality is demonstrably high)

3. **Search strategy**:
   - Compare multiple sources for each recipe
   - Prioritize recipes with professional chef backgrounds
   - Look for techniques and flavor profiles that elevate the dish
   - Balance quality with weekday feasibility (not too advanced)

4. **Always provide clickable links**

### Default Parameters

- **Portions**: 6 per recipe (unless specified otherwise)
- **Meals**: Lunch + dinner
- **Protein focus**: High protein but varied (not low-carb, not vegan)
- **Scaling**: Calculate ingredient scaling factors when portions differ from recipe

### Shopping List Generation (Phase 3)

- **Pool ingredients** across all selected recipes
- **Normalize units** for clarity
- **Use butiksvänliga names** (Swedish grocery store names)
- **Categorize**: Grönsaker, Frukt, Mejeri & Ägg, Kött & Fisk, Skafferi, Kryddor & Såser, Fryst, Bröd, Övrigt
- **Pantry assumptions**: List separately (salt, pepper, oils) - don't assume silently
- **Mark uncertainties**: Use "(verifiera)" instead of guessing

### Custom Recipes

When creating custom recipes, save as `YYYY-MM-DD/recept-<slug>-<portioner>p.md` and reference from `02-receptval.md` as "Eget recept: `recept-<slug>.md`". Use `/create-recipe` or the `recipe-creator` agent. The format is defined by `.claude/rules/recipe-style.md` and enforced by the recipe hook — see **Recipe Standard: Rules + Hooks** above.

### Meal Prep Planning (Phase 5)

Optimize for minimal total time by:
- Grouping similar tasks (chop all vegetables at once, cook all rice together)
- Parallelizing independent tasks (oven + stovetop + cold prep)
- Reusing bases/sauces when appropriate without sacrificing variety

## Specialized Agents

| Agent | Phase | Model | Purpose | Parallel? |
|---|---|---|---|---|
| `brainstorming-agent` | 1 | sonnet | Generate 10-20 meal candidates | No |
| `recipe-researcher` | 2 | sonnet | Find best recipe for ONE dish | **Yes — one per dish** |
| `recipe-creator` | 2 | inherit | Write custom recipe from scratch | Per recipe |
| `shopping-list-generator` | 3 | sonnet | Pool ingredients into shopping list | No |
| `recipe-compiler` | 4 | sonnet | Compile all recipes into standardized format | No |
| `meal-prep-optimizer` | 5 | inherit | Create time-optimized prep plan | No |
| `meal-planning-orchestrator` | All | inherit | Coordinate entire workflow | Top-level only |
| `codebase-workflow-analyzer` | — | sonnet | Analyze and improve the multi-agent workflow | No |

## Skills

| Skill | Invocation | Purpose |
|---|---|---|
| `meal-planning-hello-fresh` | Auto or `/meal-planning-hello-fresh` | Main workflow with orchestration |
| `create-recipe` | `/create-recipe [dish] [portions]` | Create a custom recipe |
| `export-to-notion` | `/export-to-notion [YYYY-MM-DD]` | Publish a finished week to Notion (Inhandling) as overview + subpages |
| `verify-recipes` | `/verify-recipes [YYYY-MM-DD\|fil]` | Run the recipe standard check and the shopping-list cross-check manually |

## Working with Date Folders

When starting a new week:
1. Create folder: `YYYY-MM-DD/` (use the Monday of that week)
2. Start with Phase 1 brainstorming
3. Follow the phase-gated workflow strictly
4. Reference previous weeks' folders for inspiration but start fresh each time
