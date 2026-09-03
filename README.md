# Meal Planning with AI Agents

A HelloFresh-inspired meal planning system for Swedish households, powered by Claude Code's multi-agent architecture. Plan your week's meals through a structured 5-phase workflow with specialized AI agents that research recipes in parallel, generate shopping lists, compile recipes, and create optimized prep plans — then optionally publish the whole week to Notion.

## How It Works

```
You: "Planera mat för veckan — vi vill ha hög protein, snabba vardagsrätter"
                              ↓
         ┌──────────────────────────────────────┐
         │     Phase 1: Brainstorming Agent      │
         │   Generates 10-20 meal candidates     │
         └──────────────┬───────────────────────┘
                        ↓ You pick dishes
    ┌───────────────────────────────────────────────┐
    │        Phase 2: Parallel Recipe Research       │
    │  ┌─────────┐ ┌─────────┐ ┌─────────┐         │
    │  │Researcher│ │Researcher│ │Researcher│  × N   │
    │  │ Dish #1  │ │ Dish #2  │ │ Dish #3  │        │
    │  └─────────┘ └─────────┘ └─────────┘         │
    │  Each compares 3-5 sources for best quality   │
    │  + Recipe Creator for custom dishes           │
    └───────────────────┬───────────────────────────┘
                        ↓ You approve
         ┌──────────────────────────────────────┐
         │   Phase 3: Shopping List Generator    │
         │  Pools & normalizes all ingredients   │
         └──────────────┬───────────────────────┘
                        ↓ You approve
         ┌──────────────────────────────────────┐
         │      Phase 4: Recipe Compiler         │
         │  Standardizes & scales all recipes    │
         └──────────────┬───────────────────────┘
                        ↓ (continues automatically)
         ┌──────────────────────────────────────┐
         │     Phase 5: Meal Prep Optimizer      │
         │  Time-optimized cooking timeline      │
         └──────────────┬───────────────────────┘
                        ↓ optional
         ┌──────────────────────────────────────┐
         │      Export to Notion (Inhandling)    │
         │  Overview page + subpages per section │
         └──────────────────────────────────────┘
```

Phases 1–3 each have a **mandatory stop point** — the system never proceeds without your explicit approval. Phase 4 flows straight into Phase 5, and the Notion export is offered as an optional final step.

## Features

- **Multi-agent orchestration** — Specialized agents for each phase, with parallel recipe research
- **Quality-first recipe sourcing** — Compares multiple sources (Köket, Tasteline, Arla, international) to find the best recipe, not just the first one
- **Custom recipe creation** — AI writes professional-quality recipes when no good source exists
- **Smart shopping lists** — Pools ingredients across all recipes, normalizes units, categorizes by store section
- **Standardized recipe collection** — Compiles every recipe into one consistent format, scaled to your portions
- **Optimized meal prep** — Parallelizes cooking tasks (oven + stovetop + cold prep) to minimize total time
- **Notion export** — Publishes a finished week to the Notion *Inhandling* database as an overview page with subpages for the shopping list, each recipe, and the meal-prep plan
- **Enforced recipe format** — Every instruction step repeats the amount inline (`**1,5 dl** mjölk`), so you never scroll back to the ingredient list mid-cook. A `PostToolUse` hook normalizes formatting and blocks recipes that break the standard, rather than relying on prompt adherence
- **Swedish-first** — All output in Swedish with metric units and Swedish grocery store names

## Getting Started

### Prerequisites

- [Claude Code](https://claude.com/claude-code) installed
- Clone this repository

### Usage

**Interactive (recommended):**
```bash
cd food
claude
# Then say: "Planera mat för veckan" or use /meal-planning-hello-fresh
```

**With orchestrator agent:**
```bash
claude --agent meal-planning-orchestrator
```

**Create a custom recipe:**
```
/create-recipe kycklingfajitas 6
```

**Verify recipes against the standard:**
```
/verify-recipes 2026-06-08
```

**Export a finished week to Notion:**
```
/export-to-notion 2026-06-08
```
Requires the Notion connector to be enabled in Claude Code. Run it as the optional final
step after Phase 5, or standalone on any existing week folder.

## Project Structure

```
.claude/
├── agents/                          # Specialized AI agents
│   ├── meal-planning-orchestrator   # Coordinates the full workflow
│   ├── brainstorming-agent          # Phase 1: meal ideation
│   ├── recipe-researcher            # Phase 2: parallel recipe search
│   ├── recipe-creator               # Phase 2: custom recipe writing
│   ├── shopping-list-generator      # Phase 3: pooled shopping list
│   ├── recipe-compiler              # Phase 4: standardized recipe collection
│   ├── meal-prep-optimizer          # Phase 5: prep timeline
│   └── codebase-workflow-analyzer   # Meta: improve the workflow itself
├── rules/                           # Path-scoped conventions
│   ├── recipe-style.md              # The recipe standard (enforced by hook)
│   └── recipe-examples.md           # Few-shot gold recipe + good/bad pairs
├── hooks/                           # Deterministic validation
│   ├── validate_recipe.py           # Normalizes + validates one recipe
│   ├── validate_week.py             # Shopping list ↔ recipe cross-check
│   ├── recipe_guard.sh              # PostToolUse
│   └── subagent_recipe_gate.sh      # SubagentStop
├── skills/
│   ├── meal-planning-hello-fresh/   # Main workflow skill
│   │   ├── SKILL.md                 # Orchestration instructions
│   │   ├── reference.md             # Sources, units, categories
│   │   └── examples.md              # Output format examples
│   ├── create-recipe/               # /create-recipe command
│   │   └── SKILL.md
│   └── export-to-notion/            # /export-to-notion command
│       └── SKILL.md
YYYY-MM-DD/                          # Weekly meal plans (date folders)
├── 01-brainstorming.md
├── 02-receptval.md
├── recept-*.md                      # Custom recipes
├── 03-handlingslista.md             # Pooled shopping list
├── 04-alla-recept.md                # Standardized recipe collection
└── 05-meal-prep-plan.md             # Optimized prep timeline
```

## Agent Architecture

| Agent | Phase | Model | Purpose | Runs in Parallel? |
|---|---|---|---|---|
| `brainstorming-agent` | 1 | Sonnet | Generate meal candidates | No |
| `recipe-researcher` | 2 | Sonnet | Find best recipe per dish | **Yes (one per dish)** |
| `recipe-creator` | 2 | Inherit | Write custom recipes | Per recipe |
| `shopping-list-generator` | 3 | Sonnet | Pool ingredients | No |
| `recipe-compiler` | 4 | Sonnet | Standardize & scale all recipes | No |
| `meal-prep-optimizer` | 5 | Inherit | Optimize prep timeline | No |

The Notion export runs as the `export-to-notion` **skill** in the main conversation (not a subagent), since the Notion connector isn't guaranteed inside subagents.

The **key innovation** is Phase 2: instead of searching for recipes sequentially, the orchestrator spawns one `recipe-researcher` agent per dish, all running in parallel. Each researcher independently compares 3-5 sources to find the highest quality recipe.

## Customization

### Defaults

- **Portions**: 6 per recipe
- **Meals**: Lunch + dinner
- **Protein**: High protein, varied (not low-carb, not vegan)
- **Language**: Swedish

Override any default by telling the system your preferences in Phase 1.

### Recipe Sources (Priority Order)

1. Köket.se, Tasteline, Arla, Landleys Kök, Mitt Kök
2. International sources for authentic cuisine (Serious Eats, Woks of Life, etc.)
3. ICA, Coop (secondary)

### Extending the System

Use the `codebase-workflow-analyzer` agent to design new agents:
```
Use the codebase-workflow-analyzer to create a budget optimizer agent
```

## Example Output

See [2026-06-08/](2026-06-08/) for an example week showing the current output format — recipe selection, pooled shopping list (`03`), standardized recipe collection (`04`), and meal-prep plan (`05`), including a custom recipe.

## License

MIT
