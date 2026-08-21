# Conventies — golf-score, trends, events

Eén leidend document voor de drie apps. Woont in de repo `apps-basis`.
Bij een nieuwe chatsessie: dit bestand als eerste uploaden.

De drie apps zijn **zelfstandig**. Ze delen geen bestanden op runtime, alleen
regels. Wat hieronder staat geldt voor alle drie, behalve waar bij
"Bewust verschillend" iets anders staat.

---

## 1. Werkwijze

- **Ontwerp eerst.** Bij niet-triviale wijzigingen eerst een voorstel, pas
  bouwen na akkoord. Bij een bouwtraject elke stap apart voorleggen.
- **Versiestempel bij ELKE wijziging ophogen.** Handmatig, niet via een script.
- **Er werken vaak parallelle sessies aan hetzelfde bestand.** Vóór een
  wijziging de huidige versie controleren, en na de patch verifiëren dat de
  wijziging er echt in staat.
- **Na elke wijziging controleren:** `python3 check_app.py <app>.html`.
  Bij grotere ingrepen ook met de hand nalopen wat het script niet ziet.
- **Performance meteen goed.** Efficiënte patronen als standaard: één keer
  laden, één keer berekenen, alleen renderen wat nodig is. Wordt bewust de
  simpele-maar-zwaardere variant gekozen, dan dat ongevraagd melden.

### Versiestempel

Formaat: `HEX(yyyymmdd)-NNN`, drie hex-cijfers volgnummer, elke dag opnieuw
vanaf `001`. Voorbeeld: `13527CE-001` = 14-8-2026, eerste wijziging van die dag.

Beide delen hebben een vaste lengte, dus gewone tekstvergelijking sorteert
correct. Wijzigt het formaat ooit, dan moet de regex
`/Versie ([0-9A-F]+-[0-9A-F]+)/` overal mee — in golf staat die op twee plekken.

Plaats van het stempel per app:

| app | plaats |
|---|---|
| golf-score | onderaan Instellingen |
| trends | onderaan het Bronnen-paneel |
| events | onderaan de cfg-modal |

---

## 2. Vaste regels

- **Decimaalteken is overal een PUNT**, ook al is de UI Nederlands. Enige
  uitzondering: JSON-getallen in de Trends-export.
- **Nooit `−0.0` of `+0.0` tonen.** Eerst afronden op het getoonde aantal
  decimalen, dán het teken bepalen.
- **Drempels nooit hardcoden.** In golf altijd `getMinRoundsStat()`.
  Structurele drempels (trend 5+5, spreiding ≥3) zijn bewust niet gekoppeld.
- **Nieuwe storage-sleutels altijd toevoegen aan de reset.** Instellingen die
  standaard AAN staan: `!== 'off'`. Standaard UIT: `=== 'on'`.
- **Inklap-driehoekjes zijn SVG**, nooit het teken `▶` — per lettertype andere
  witruimte, en draaien om het midden oogt scheef. In golf via
  `arrowSvg(size, open, kleur, rotate)`; klasse-gestuurde pijltjes laten de
  óuder draaien, dus `rotate=false`.
- **Balken en vlakken: RECHTE hoeken.** Edge tekent een radius onbetrouwbaar
  (schuine snedes). Drie technieken geprobeerd, alle drie mislukt zolang er een
  radius in zat. Daarom `BALK_RX = 0`.
- **De UI is Nederlandstalig.** Ook meldingen en foutteksten.
- **Geen dubbeltik-sneltoetsen.** Bewerken en kiezen zijn expliciete acties.
- **Datumsleutel voor meetmomenten: `Dyyyymmdd[Thhmm]`.** Het tijd-deel is
  optioneel. Geldt voor **gedeelde databestanden** — het formaat waarmee twee
  apps elkaar moeten begrijpen: de databestanden van trends en de
  Dagresultaten-export van golf. Hóé een app zijn gegevens intern bewaart is
  zijn eigen zaak: golf houdt rondes in een lijst met `date` als `2026-08-20`
  (ISO mét streepjes) en `time` apart, en dat blijft zo — daar is geen
  sleutelvolgorde in het geding en `new Date()` kan er direct mee overweg. De
  `D`-vorm wordt pas opgebouwd bij het exporteren.
  Golf vult bij twee tijdloze rondes op dezelfde dag een oplopende kunstminuut
  in, zodat er geen meting wegvalt.
  Uitdrukkelijk **niet** voor events: die app slaat terugkerende patronen op
  (dag, maand en jaar als losse velden die onbekend mogen zijn), en daar zou
  één samengestelde sleutel juist kapotmaken waar de app voor bedoeld is.
  Trends blijft de oude sleutels (`yyyymmdd`, zonder `D`) lezen. Die
  terugvalcode is definitief en geen tijdelijke maatregel; bestaande bestanden
  hoeven dus niet omgezet te worden.
  **Waarom die `D`, en niet gewoon `yyyymmdd`:** JavaScript behandelt een sleutel
  als `"20260820"` als array-index en geeft die bij het doorlopen apart terug —
  eerst alle index-achtige sleutels oplopend, daarna pas de gewone stringsleutels
  in invoegvolgorde. Zodra er één sleutel met tijd bij komt (`"20260820T1030"`,
  niet index-achtig), splitst je verzameling dus in twee groepen en klopt de
  chronologie niet meer. De `D` brengt alles in dezelfde categorie, waarna één
  `sort()` op tekst de juiste volgorde geeft. Sneller is numeriek hier niet:
  gemeten op 5000 sleutels is sorteren een gelijkspel en opzoeken met `D` zelfs
  sneller, en beide blijven ver onder een milliseconde.
- **Rijselectie in plaats van een icoon per rij:** klik selecteert, één
  wijzig-knop in de kopregel bewerkt de selectie.

---

## 3. App-shell en PWA

Elke app-repo bevat: `<app>.html`, `index.html` (doorverwijzing),
`manifest.json`, `sw-<stam>.js`, `icon.svg`, `update_cache_version.py`,
`LEESMIJ.md`.

- **Naam van de service worker:** `sw-<stam>.js`, waarbij `<stam>` de naam van
  het app-bestand is zonder `.html` — dus `sw-golf-score.js`, `sw-trends.js` en
  `sw-events.js`, passend bij de cache-prefixen `golf-score-`, `trends-` en
  `events-`.
  De naam is vrij — alleen de **map** bepaalt de scope — en een unieke naam
  voorkomt dat de drie bestanden elkaar overschrijven zodra je ze bij elkaar
  zet (bijvoorbeeld bij het uploaden naar een chatsessie). Hernoemen doe je in
  de repo, niet pas bij het versturen: dat laatste is een handmatige stap die
  je over een jaar niet meer weet.
  Hernoemen gaat in deze volgorde:
  1. in de app `register('sw.js')` → `register('sw-<stam>.js')`;
  2. in `update_cache_version.py` de bestandsnaam aanpassen;
  3. versiestempel ophogen;
  4. de nieuwe `sw-<stam>.js` en de gewijzigde app in dezelfde upload; pas
     daarna de oude `sw.js` weghalen.
  Registreert de app een naam die er nog niet staat, dan mislukt de
  registratie: de oude service worker blijft draaien, maar de
  nieuwe-versie-melding werkt tot die tijd niet.
- **Layout:** vaste kop, vast onderdeel (tabbalk of niets), scrollend midden.
  Zo scrollt de navigatie niet weg op de telefoon.
- **Strategie van de service worker:** stale-while-revalidate. Serveer uit de cache, ververs op
  de achtergrond. Daardoor hoeft `sw.js` niet bij elke inhoudswijziging mee.
- **Cachenaam:** golf gebruikt een hash van de bestanden, trends en events een
  oplopend nummer. Beide voldoen; niet gelijktrekken.
- **Nieuwe-versie-melding:** `checkAppUpdate` vergelijkt het stempel van de
  draaiende app met het stempel in de kopie in de service-worker-cache.
  Vaste eisen:
  - alleen de cache lezen, geen netwerkverkeer;
  - pas 4 s na start, plus bij `visibilitychange`;
  - eerst filteren op de eigen cache-prefix (`golf-score-`, `trends-`,
    `events-`) — de cache is van het hele domein, dus de andere apps staan er
    ook in — met terugval op alle caches;
  - van alle treffers het NIEUWSTE stempel nemen en alleen melden bij
    `>`, nooit bij `!==`: een blijven hangen oude cache zou anders melden dat
    er een "nieuwe" versie is die juist ouder is;
  - geen cache, of geopend als los bestand (`file:`): stil niets doen.
- **Deelbaarheid:** een service worker onderschept alleen verzoeken binnen zijn
  eigen scope. Een gedeeld bestand uit een andere repo wordt dus niet gecachet
  en breekt offline. Daarom: geen runtime-afhankelijkheden tussen de apps.

---

## 4. Bewust verschillend

Deze verschillen zijn geen slordigheid. Niet gladstrijken, niet opnieuw
voorstellen om ze gelijk te trekken.

- **Opslag.** Golf houdt zijn gegevens in localStorage met handmatige backup:
  rechtstreeks naar bestanden schrijven vraagt telkens opnieuw toestemming, en
  een toestemmingsprompt midden op de baan is onacceptabel. De backup­herinnering
  staat op dagelijks of 1 nieuwe ronde, dus het gat is hooguit één ronde.
  Trends en events schrijven wél rechtstreeks naar bestanden (File System
  Access, werkmap of gekoppeld bestand), want daar zit je rustig.
- **Schrijfstijl van de code.** Golf en trends gebruiken `const`/`let` en
  `async`; events gebruikt `var` en `function` met promises. Nieuwe code volgt
  de stijl van het bestand waarin ze terechtkomt, niet die van de buurapp.
- **Kleuren.** Golf goud op groen, trends teal, events blauw. Per app eigen
  accentkleur; alleen typografie en tabelopmaak zijn gedeeld.
- **Cachenaam.** Zie hierboven.

---

## 5. Bekende valkuilen

- **Stale service-worker-cache is de eerste verdachte** bij een fout die
  onverklaarbaar lijkt. Meerdere "bugs" bleken een oude cache.
- **Sticky onder de kop:** de app-header is zélf sticky. Alles wat eronder moet
  plakken gebruikt `top: var(--header-h, 60px)`. Een voorouder-scan vindt de
  oorzaak niet, want de header is een buurman.
- **Horizontaal sleepbare elementen** moeten `stopPropagation` doen op
  `touchstart`/`touchmove`/`touchend`, anders pakt de document-brede swipe ze op.
- **Formaat van gedeelde databestanden ligt vast.** Het events-bestand wordt ook
  door een MacroDroid-macro gelezen: één record per regel, scheidingsteken uit
  de cfg. Voor de datumsleutel van meetmomenten, zie "Vaste regels".

---

## 6. Gedeelde blokken

Code wordt gekopieerd, niet gelinkt. Om te voorkomen dat kopieën stilletjes uit
elkaar lopen, krijgt een gedeeld blok markeringen:

```js
/* == basis: naam-van-het-blok == */
...
/* == einde basis == */
```

De referentie staat in `apps-basis/blokken/<naam>.js`. `check_app.py`
vergelijkt het gemarkeerde blok met die referentie en meldt het als ze
verschillen. Je hoeft dus niets te onthouden: vergeten kost niets, de volgende
controle vindt het alsnog.

Op dit moment zijn er nog geen gemarkeerde blokken. `checkAppUpdate` is de
eerste kandidaat, maar de drie versies verschillen nu nog in schrijfstijl en in
het element dat de melding toont. Pas als die echt identiek gemaakt zijn, heeft
markeren zin.
