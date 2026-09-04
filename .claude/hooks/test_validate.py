#!/usr/bin/env python3
"""Regressionstest for receptvalidatorn.

Kor: python3 .claude/hooks/test_validate.py

Testerna tacker det som ar heuristiskt och darmed skort: normaliseringen,
karnordsutvinningen och matchningen av ingredienser mot instruktionssteg.
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from validate_recipe import (  # noqa: E402
    extract_headwords,
    find_mention,
    normalize,
    validate,
)

failures: list[str] = []


def check(label: str, actual: object, expected: object) -> None:
    if actual != expected:
        failures.append(f"{label}\n    förväntat: {expected!r}\n    faktiskt:  {actual!r}")


# --------------------------------------------------------------------------
# Normalisering
# --------------------------------------------------------------------------

NORMALIZE_CASES = [
    ("- 1.2 kg kycklingfilé", "- 1,2 kg kycklingfilé"),
    ("- 2 burkar majs (à 340g)", "- 2 burkar majs (à 340 g)"),
    ("- 1/2 dl ströbröd", "- ½ dl ströbröd"),
    ("**1 dl**mjölk", "**1 dl** mjölk"),
    ("**1/2 dl**ströbröd", "**½ dl** ströbröd"),
    ("Grädda i 180°C i 25-30 minuter.", "Grädda i 180 °C i 25–30 minuter."),
    ("- 1000 g blandfärs", "- 1 kg blandfärs"),
    ("- 10 dl vatten", "- 1 l vatten"),
    ("- Mjölk — 1,5 dl", "- 1,5 dl mjölk"),
    ("- Blandfärs (50/50 nöt och fläsk) — 800 g", "- 800 g blandfärs (50/50 nöt och fläsk)"),
    ("- Gul lök — 1 st (finriven)", "- 1 st gul lök (finriven)"),
    # Far INTE roras:
    ("- Pensla med **2 msk** olja, strö över **2 tsk** salt", None),
    ("- Källa: https://example.se/recept-1.2-kg", None),
    ("- 1,5 dl mjölk", None),
    ("Vecka 2026-06-08", None),
]

for source, expected in NORMALIZE_CASES:
    result, _ = normalize(source)
    check(f"normalize({source!r})", result, expected if expected is not None else source)

# Normaliseringen ska vara idempotent.
for source, _ in NORMALIZE_CASES:
    once, _ = normalize(source)
    twice, fixes = normalize(once)
    check(f"normalize idempotent för {source!r}", (twice, fixes), (once, []))


# --------------------------------------------------------------------------
# Karnord
# --------------------------------------------------------------------------

HEADWORD_CASES = [
    ("mjölk", ["mjölk"]),
    ("gul lök", ["lök"]),
    ("stor bit ingefära", ["ingefära"]),
    ("vatten för konsistens", ["vatten"]),
    ("kycklinglår med ben och skinn", ["kycklinglår"]),
    ("rostade jordnötter", ["jordnötter"]),
    ("sriracha/chili", ["sriracha", "chili"]),
    ("crème fraiche", ["crème"]),
]

for name, expected in HEADWORD_CASES:
    check(f"extract_headwords({name!r})", extract_headwords(name), expected)


# --------------------------------------------------------------------------
# Matchning ingrediens -> steg (bojningar och sammansatta ord)
# --------------------------------------------------------------------------

MENTION_CASES = [
    ("Koka riset 12 min", ["jasminris"], True),          # efterled i sammansatt ord
    ("Krydda med salt och peppar", ["svartpeppar"], True),
    ("Fräs löken mjuk", ["lök"], True),                  # bestamd form
    ("Riv moroten grovt", ["morötter"], True),           # omljud i plural
    ("Vänd ner smöret", ["smör"], True),
    ("Blanda alla ingredienser", ["kokosmjölk"], False),  # ska INTE matcha
    ("Stek kycklingen", ["kycklinglårfilé"], True),
]

for step, heads, should_match in MENTION_CASES:
    found = find_mention(step, heads) is not None
    check(f"find_mention({step!r}, {heads!r})", found, should_match)


# --------------------------------------------------------------------------
# Hela filen
# --------------------------------------------------------------------------

GOOD = """# Recept — Testrätt för 4 portioner

En testrätt som följer standarden.

## Ingredienser (4 portioner)

### Bas
- 1,5 dl mjölk
- 500 g blandfärs
- salt och svartpeppar efter smak

## Gör så här

### 1) Blanda
- Häll **1,5 dl** mjölk över **500 g** blandfärs och rör ihop.
- Smaka av med salt och svartpeppar.

## Matlåda / förvaring
- Kyl: 3 dagar.

## Källor
- Test: https://example.com
"""

BAD_MISSING_AMOUNT = GOOD.replace(
    "- Häll **1,5 dl** mjölk över **500 g** blandfärs och rör ihop.",
    "- Häll mjölken över blandfärsen och rör ihop.",
)

BAD_UNUSED = GOOD.replace("- 500 g blandfärs", "- 500 g blandfärs\n- 2 msk tomatpuré")

BAD_PORTIONS = GOOD.replace("## Ingredienser (4 portioner)", "## Ingredienser (6 portioner)")


def errors_for(text: str, name: str = "recept-test-4p.md") -> list[str]:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / name
        path.write_text(text, encoding="utf-8")
        return validate(path, fix=False).errors


check("giltigt recept ger inga fel", errors_for(GOOD), [])
check("saknad mängd i steg upptäcks", len(errors_for(BAD_MISSING_AMOUNT)), 2)
check("oanvänd ingrediens upptäcks", len(errors_for(BAD_UNUSED)), 1)
check("portionsavvikelse upptäcks", len(errors_for(BAD_PORTIONS)), 1)

# no-check-markoren ska tysta Regel 2.
silenced = GOOD.replace(
    "- 500 g blandfärs", "- 500 g blandfärs\n- 2 msk tomatpuré <!-- no-check -->"
)
check("no-check-markören tystar Regel 2", errors_for(silenced), [])


# --------------------------------------------------------------------------

if failures:
    print(f"{len(failures)} test misslyckades:\n")
    for f in failures:
        print(f"  ✗ {f}")
    sys.exit(1)

print("Alla test godkända.")
