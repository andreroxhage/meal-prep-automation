---
name: export-to-notion
description: Exporterar en färdig veckas matplanering till Notion-databasen 💸 Inhandling. Skapar en översiktssida med underliggande sidor för handlingslista och meal prep-plan, och länkar till befintliga recept i Recept-databasen istället för att duplicera dem. Använd som sista steg efter Fas 5, eller fristående på en befintlig veckomapp.
argument-hint: "[YYYY-MM-DD]"
---

# Exportera vecka till Notion (Inhandling)

Publicera en färdig veckas planering till Notion-databasen **💸 Inhandling** i en
strukturerad form: en översiktssida med underliggande sidor (subpages) för handlingslista
och meal prep-plan, plus **genvägar till recepten i Recept-databasen**.

**Detta körs i huvudkonversationen** (där Notion-MCP finns) — delegera INTE till en
subagent, eftersom subagenter inte garanterat har tillgång till Notion-MCP.

## 🔴 Grundregel: duplicera aldrig ett recept

Recept lever i **Recept**-databasen, inte i veckomapparna. En veckosida ska **hänvisa** till
receptet, aldrig innehålla en egen kopia av det.

- Finns receptet redan → länka med `<mention-page>`. Skapa **ingen** receptsubpage.
- Finns det inte → skapa det **i Recept-databasen** (inte som veckosubpage), och länka dit.
  Då är det återanvändbart nästa vecka.
- Veckans anpassningar (skalning, utbytta ingredienser) → **skrivs in i receptsidan**
  enligt steg 7, så det finns exakt ett recept per rätt.

Resultatet: veckosidan har bara två subpages — `Handlingslista` och `Meal prep-plan` —
medan recepten är genvägar.

## Fasta värden

- **Inhandling databas-id:** `2ad3a69e-7647-806c-bba0-d503a8f0f2a0`
- **Inhandling data source (förälder för veckosidor):**
  `collection://2ad3a69e-7647-80a2-89f3-000b0dfb831e`
- **Recept databas ("Recipes"):** `https://app.notion.com/p/b90e9acce8ee46009f77bceb1afe7f02`
- **Recept data source (förälder för nya recept):**
  `collection://ebeb4bdf-f600-4429-bf2b-68e0a78a623e`
- **Sidnamn:** alltid `Vecka YYYY-MM-DD` (veckans datum).

## Steg

1. **Hitta veckomapp.**
   - Om `$ARGUMENTS[0]` angetts: använd `YYYY-MM-DD/`.
   - Annars: lista alla `YYYY-MM-DD/`-mappar (Glob) och välj den senaste.
   - Kräv att `04-alla-recept.md` finns. Om `03-handlingslista.md` eller
     `05-meal-prep-plan.md` saknas: varna användaren men exportera det som finns.

2. **Läs källfilerna** i veckomappen:
   - `02-receptval.md` (innehåller källor och skalningsfaktorer — behövs i steg 4 och 7)
   - `03-handlingslista.md`
   - `04-alla-recept.md`
   - `05-meal-prep-plan.md`

3. **Läs Notion-markdownspecifikationen** via MCP-resursen
   `notion://docs/enhanced-markdown-spec` innan du genererar Notion-innehåll. Gissa aldrig
   syntaxen. (Skicka inte URI:n till `notion-fetch` — läs den som MCP-resurs.)

4. **🔍 Matcha varje rätt mot Recept-databasen (OBLIGATORISKT — hoppa aldrig över).**

   Splitta `04-alla-recept.md` på rubriker som matchar `^## \d+\.` → ett block per rätt.
   För **varje** rätt, innan något skapas:

   - Kör `notion-search` med rättens namn och
     `data_source_url: "collection://ebeb4bdf-f600-4429-bf2b-68e0a78a623e"`.
   - Sök även på kortformer och nyckelord — titlar skiljer sig ofta mellan veckofil och
     receptsida (`Tacosmakad kycklingwrap med crème fraîche` i veckan ≙ `Tacowrap` i
     databasen). Ett napp kräver inte identisk titel, bara att det är samma rätt.
   - Om `02-receptval.md` redan pekar på en Notion-URL för rätten: använd den direkt,
     ingen sökning behövs.
   - Titta även i tidigare veckosidor om rätten känns bekant — men **ett recept som bara
     finns inuti en gammal veckosida räknas INTE som befintligt recept.** Behandla det som
     "saknas" och skapa en riktig receptsida i steg 6.

   Bygg en tabell: rätt → `BEFINTLIG <url>` eller `SAKNAS`. **Visa tabellen för användaren
   innan du skriver något till Notion.**

5. **Bekräfta data sources.**
   - Använd som standard id:na under *Fasta värden*.
   - Om en create/fetch misslyckas: kör `notion-search "Inhandling"` respektive
     `notion-search "Recept"`, hämta databasen med `notion-fetch` och läs av aktuell
     data source-URL på nytt (skydd om id:t ändras).

6. **Skapa saknade recept i Recept-databasen** (inte som veckosubpages):
   - `parent`: `{ "type": "data_source_id", "data_source_id": "ebeb4bdf-f600-4429-bf2b-68e0a78a623e" }`
   - `properties`: `{ "title": "<rättens namn>" }` — verifiera det faktiska titelfältets
     namn med `notion-fetch` på data source först.
   - `content`: receptblocket från `04-alla-recept.md`.
   - Spara URL:en — den används för genvägen i steg 8.

7. **Skriv in veckans anpassningar i receptsidan.**

   Om veckans version skiljer sig från receptsidan (skalning, utbytt ingrediens), uppdatera
   **receptsidan** med `notion-update-page` (`command: "update_content"`, riktade
   search-and-replace-ersättningar) så att det finns exakt ett recept per rätt.

   - Uppdatera portionsangivelse, ingrediensmängder och de instruktionssteg som påverkas.
   - Nämn utbyten explicit i receptet (t.ex. "2,5 msk balsamvinäger *(ersätter 3 msk
     rödvinsvinäger)*") så att ändringen är spårbar.
   - **Fråga användaren först** om ändringen är stor nog att förändra rättens karaktär
     (byte av huvudprotein, annan tillagningsmetod) — då kan ett nytt, separat recept vara
     rätt istället för att skriva över originalet.

8. **Skapa översiktssidan** med `notion-create-pages`:
   - `parent`: `{ "type": "data_source_id", "data_source_id": "2ad3a69e-7647-80a2-89f3-000b0dfb831e" }`
   - `properties`: `{ "Name": "Vecka YYYY-MM-DD" }`
   - `content`: sammanfattning — veckans datum, antal rätter, totalt antal portioner, en
     rättlista med portioner + uppskattad tid, och veckans nyckeltal. Därefter:
     - En rubrik `## Recept` med **en `<mention-page>`-genväg per rätt**, med portioner och
       ev. anpassning på samma rad. Detta är den enda platsen recepten refereras.
     - En rubrik `## Innehåll` sist — undersidorna från steg 9 dyker automatiskt upp som
       klickbara länk-block direkt under den.
   - Under `## Innehåll`: skapa **ingen** manuell lista. Notion lägger själv till
     undersidorna som länk-block — en handskriven lista blir bara en dubblett.
   - Spara den returnerade sid-URL:en / id:t (= `page_id` för subpages).

9. **Skapa subpages** med `notion-create-pages`, `parent` =
   `{ "type": "page_id", "page_id": "<översiktssidans id>" }`:
   - `Handlingslista` ← innehåll från `03-handlingslista.md`
   - `Meal prep-plan` ← innehåll från `05-meal-prep-plan.md`
   - **Inga receptsubpages.** Recepten är genvägar under `## Recept`.

10. **Rapportera** översiktssidans URL, samt vilka recept som återanvändes respektive
    nyskapades. Rör inte de lokala filerna (radera eller ändra dem inte).

## Robusthet

- Konvertera markdown så det förblir Notion-kompatibelt enligt specen från steg 3.
- Om recept refererar till lokala filer (t.ex. `recept-…md`): behåll som vanlig text,
  skapa inga trasiga länkar.
- **Håll varje create-anrop litet.** Ett anrop med flera stora sidor kan trunkeras och
  underkännas som ogiltig JSON. Skapa en sida per anrop när innehållet är långt, och
  föredra punktlistor framför breda tabeller för långa listor (t.ex. handlingslistan).
- Om `notion-create-pages` returnerar `MCP tool call requires approval`: det är
  behörighetslagret, inte anropet. Försök inte om i det oändliga — rapportera till
  användaren att Notion-anslutningen behöver godkännas eller återanslutas.

## Notis om workflow

Detta är det valfria sista steget i matplaneringsworkflowet (efter Fas 5). Det kan också
köras fristående när som helst på en befintlig veckomapp via `/export-to-notion [YYYY-MM-DD]`.
