---
paths:
  - "recipe/**/*.md"
  - "**/recept-*.md"
  - "**/04-alla-recept.md"
  - "**/05-meal-prep-plan.md"
---

# Receptstandard (obligatorisk)

Alla receptfiler följer denna standard. Den kontrolleras maskinellt av
`.claude/hooks/validate_recipe.py` efter varje `Write`/`Edit` — avvikelser skickas
tillbaka som fel som ska rättas, inte förklaras bort.

Se `.claude/rules/recipe-examples.md` för ett komplett exempel och bra/dåligt-par.

## Regel 1 — mängden står i instruktionen (viktigast)

Läsaren står vid spisen och scrollar inte tillbaka till ingredienslistan.
**Första gången en ingrediens används i ett steg ska mängden stå med i steget**,
fetmarkerad:

- ✅ `Häll **1,5 dl** mjölk över **1 dl** ströbröd och låt svälla 10 min.`
- ❌ `Häll mjölken över ströbrödet och låt svälla 10 min.`

Senare hänvisningar till samma ingrediens behöver ingen mängd
(`Rör ner brödblandningen i färsen`).

Undantag — ingrediensen behöver ingen mängd i steget om ingredienslistan anger
`efter smak`, `valfritt`, `till servering`, `till stekning` eller `att servera till`.
Behövs undantag i övriga fall: sätt `<!-- no-qty: [kort motivering] -->` sist på
ingrediensraden.

## Regel 2 — varje ingrediens används

Varje ingrediens i listan ska nämnas i minst ett steg. Ingredienser som inte
används är antingen bortglömda i instruktionen eller överblivna från skalning.

## Regel 3 — ingrediensrader

Format: `- <mängd> <enhet> <ingrediens> (<ev. förberedelse>)` — mängden först.

```
- 1,5 dl mjölk
- 800 g blandfärs (50/50 nöt och fläsk)
- 1 gul lök (finriven)
- salt och svartpeppar efter smak
```

- **Mängd först**, inte `- Mjölk — 1,5 dl`.
- **Decimalkomma**, inte punkt: `1,2 kg` — aldrig `1.2 kg`.
- **Mellanslag mellan siffra och enhet**: `28 g` — aldrig `28g`.
- **Bråk som tecken**: `½`, `¼`, `¾` — inte `1/2`.
- **Intervall med tankstreck**: `1,6–1,8 kg`, `4–5 min`.
- **Tillåtna enheter**: g, kg, ml, cl, dl, l, msk, tsk, krm, st, klyfta/klyftor,
  knippe, näve, nypa, paket, burk, förp, skiva/skivor, kruka.
- **Normalisera**: `1000 g` → `1 kg`, `10 dl` → `1 l`, `100 cl` → `1 l`.

## Regel 4 — filstruktur

Exakt dessa rubriker, i denna ordning:

```markdown
# Recept — <Rättens namn> för <X> portioner

<1–2 meningar om rätten och vad som gör den bra>

## Ingredienser (<X> portioner)

### <Kategori, t.ex. Bas / Protein / Sås / Tillbehör>
- <ingrediensrader enligt Regel 3>

## Gör så här

### 1) <Stegrubrik>
- <instruktion enligt Regel 1>

### 2) <Stegrubrik>
- ...

## Matlåda / förvaring
- Kyl: <hållbarhet>
- Frys: <hållbarhet + tips>
- Uppvärmning: <bästa metod>

## Källor
- <källnamn>: <URL>
```

Portionsantalet i `# Recept — ... för X portioner`, i `## Ingredienser (X portioner)`
och i filnamnets `-<X>p.md` ska vara samma tal.

## Regel 5 — instruktionernas innehåll

- **Konkret, inte vagt**: `Stek på medelhög värme 4–5 min tills gyllenbrun`,
  inte `stek tills klart`.
- **Temperaturer i °C**, alltid. Ange innertemperatur för kött (`till 68 °C i mitten`).
- **Tider i minuter/timmar**, alltid specifika.
- **Proffston**: skriv som en kock, inte som en matblogg. Inga tomma ord.
- **Svenska** genomgående.

## Filnamn

`recept-<namn-med-bindestreck>-<portioner>p.md`, t.ex. `recept-kycklingfajitas-6p.md`.
