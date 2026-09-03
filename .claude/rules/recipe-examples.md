---
paths:
  - "recipe/**/*.md"
  - "**/recept-*.md"
  - "**/04-alla-recept.md"
---

# Receptexempel (few-shot)

Följ `.claude/rules/recipe-style.md`. Detta är mönstret att kopiera.

## Komplett exempel (guldstandard)

```markdown
# Recept — Ugnsbakad lax med dillpotatis och senapscrème för 6 portioner

Laxen bakas långsamt på låg ugnstemperatur så den blir silkig istället för torr.
Senapscrèmen görs på crème fraiche som inte skär sig när den möter varm fisk.

## Ingredienser (6 portioner)

### Lax
- 1,2 kg laxfilé (i bit, benfri, med skinn)
- 2 msk olivolja
- 2 tsk flingsalt
- 1 tsk svartpeppar (nymalen)
- 1 citron (skalet finrivet + saft)

### Dillpotatis
- 1,5 kg färskpotatis
- 30 g smör
- 1 knippe dill (grovhackad)
- 1 tsk salt

### Senapscrème
- 3 dl crème fraiche
- 2 msk dijonsenap
- 1 msk honung
- 1 msk vitvinsvinäger
- salt och svartpeppar efter smak

## Gör så här

### 1) Förbered laxen
- Sätt ugnen på 120 °C.
- Torka **1,2 kg** laxfilé med hushållspapper och lägg den med skinnsidan ner i en
  ugnsform.
- Pensla med **2 msk** olivolja, strö över **2 tsk** flingsalt och **1 tsk**
  svartpeppar och riv över skalet från **1** citron.

### 2) Baka
- Baka laxen i mitten av ugnen 25–30 min, till 48 °C i den tjockaste delen.
- Fisken är klar när köttet nätt och jämnt släpper mellan flagorna — den fortsätter
  efterkoka någon grad utanför ugnen.

### 3) Dillpotatisen
- Koka **1,5 kg** färskpotatis i saltat vatten 15–18 min tills en sticka går lätt igenom.
- Häll av vattnet, låt ångan gå av 1 min och vänd ner **30 g** smör, **1 knippe**
  hackad dill och **1 tsk** salt.

### 4) Senapscrème
- Blanda **3 dl** crème fraiche med **2 msk** dijonsenap, **1 msk** honung och
  **1 msk** vitvinsvinäger.
- Smaka av med salt och peppar och pressa i saft från citronen.

### 5) Servera
- Dela laxen i portionsbitar direkt i formen och servera med potatisen och crèmen.

## Matlåda / förvaring
- Kyl: 3 dagar. Förvara crèmen separat så potatisen inte blir blöt.
- Frys: laxen fryses ogärna — gör hellre halv sats.
- Uppvärmning: 100 °C i ugn 10 min, eller ät kall som laxsallad.

## Källor
- Köket.se — Långbakad lax: https://www.koket.se/langbakad-lax
```

## Bra/dåligt-par

### Par 1 — mängd i steget

- ❌ `Häll mjölken över ströbrödet och låt svälla 10 minuter.`
- ✅ `Häll **1,5 dl** mjölk över **1 dl** ströbröd och låt svälla 10 min.`

*Varför:* läsaren står vid spisen med händerna i färsen. Utan mängden i steget måste
hon scrolla tillbaka till listan mitt i momentet. Detta är hela poängen med Regel 1 —
mängden hör till handlingen, inte bara till inköpet.

### Par 2 — ingrediensrad

- ❌ `- Mjölk — 1,5 dl` / `- **1 dl**ströbröd` / `- 1.2 kg kycklingfilé`
- ✅ `- 1,5 dl mjölk` / `- 1 dl ströbröd` / `- 1,2 kg kycklingfilé`

*Varför:* mängden först gör listan skannbar när man handlar och när man dubblar satsen.
Decimalkomma är svensk standard, och `1.2` läses som `12` av den som skummar. Ett enda
format i alla filer betyder att receptsamlingen (`04-alla-recept.md`) kan slås ihop
utan att formatet spretar.

### Par 3 — instruktionens precision

- ❌ `Stek kycklingen tills den är klar. Tillsätt grädden och låt koka ihop.`
- ✅ `Stek **800 g** kycklingfilé i omgångar på hög värme 3–4 min per sida, till 72 °C
  i mitten. Tillsätt **2 dl** vispgrädde och låt koka ihop 5 min tills såsen täcker
  baksidan av en sked.`

*Varför:* "tills den är klar" flyttar bedömningen till läsaren, som då antingen
torrsteker kycklingen eller serverar den rå. Temperatur, tid och ett visuellt tecken
gör steget möjligt att utföra rätt första gången — och gör receptet skalbart, eftersom
mängden i steget visar hur mycket som ska ner i pannan per omgång.

### Par 4 — oanvänd ingrediens

- ❌ Ingredienslistan innehåller `- 2 msk tomatpuré` men inget steg nämner tomatpuré.
- ✅ Antingen används den i ett steg (`Fräs ner **2 msk** tomatpuré 1 min så den
  karamelliserar`) eller stryks den ur listan.

*Varför:* en oanvänd ingrediens är antingen ett glömt steg eller en rest från
portionsskalning. Båda ger fel handlingslista och en läsare som står med en öppnad
tub tomatpuré och ingen aning om när den ska in.
