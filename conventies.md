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
- **Versiestempel bij ELKE wijziging aan de app ophogen.** Handmatig, niet via
  een script: een script verhoogt het stempel ook bij een wijziging die niemand
  hoeft te zien, en dan staat er een nieuwe-versie-melding tegenover niets.
  Een wijziging die niet in de app-bestanden landt (een losse test, een
  leesmij, een hulpscript) krijgt dus géén nieuw stempel.
  `check_app.py` is het vangnet: dat waarschuwt als het app-bestand is
  gewijzigd terwijl het stempel nog op de oude waarde staat — vóór het
  committen én als de laatste commit het heeft laten staan. Trends hoogde het
  stempel daarom eerder via een script op; dat is er sinds dat vangnet uit.
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
`manifest.json`, `sw-<stam>.js`, `icon.svg`, `update_cache_version.py` en de
tests van die app (events en trends een `<app>-tests.cjs` naast de app, golf een
map `tests/`). De gedeelde leesmij staat hier in `apps-basis/leesmij.md`;
`maak_zips.py` legt in elke back-upzip een eigen `LEESMIJ.txt`.

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
  de achtergrond. Daardoor hoeft de service worker niet bij elke inhoudswijziging mee.
- **De drie service workers doen hetzelfde** (gelijkgetrokken op 16-10-2026), elk in
  de schrijfstijl van de eigen app. Wijzig je hier iets wezenlijks, doe het dan in alle
  drie en pas deze lijst aan:
  - alleen de eigen bestanden afhandelen (origin én pad), alleen uit de eigen cache lezen,
    alleen eigen oude caches opruimen;
  - **eerst de eigen cache, dan het netwerk**: zo weet het netwerkverzoek welke rol het
    heeft (verversing op de achtergrond of het antwoord zelf) en welke grens erbij hoort;
  - **één kopie per pad**: opzoeken en bewaren onder het pad zonder toevoeging achter
    het vraagteken, voor elk eigen bestand;
  - een verzoek met `cache: 'reload'` of `'no-store'` gaat altijd naar het netwerk en
    wordt niet bewaard (zonder netwerk: een foutcode, niet de oude kopie);
  - **drie tijdsgrenzen**, en een verzoek wordt bij de grens echt afgebroken:
    10 s bij een cachemisser en bij elke ophaalpoging van de installatie, 3 s bij een
    paginaverzoek dat de cache mist terwijl de app wel bewaard is (dan de bewaarde app),
    60 s voor de achtergrondverversing bij een cachetreffer;
  - de achtergrondverversing van de **pagina** gaat met `cache: 'no-cache'`: GitHub
    Pages laat een bestand 10 minuten bewaren, en anders kwam vlak na een push de
    oude versie terug in de cache;
  - staat er een verse kopie van de pagina in de cache, dan krijgt elk open venster het
    bericht `kopieVernieuwd`;
  - de installatie slaagt alleen als het app-bestand binnen is; een bijbestand dat niet
    binnenkomt, wordt overgenomen uit de nieuwste vorige eigen cache; een mislukte
    installatie laat geen lege cache achter en wist een bestaande niet;
  - geen `skipWaiting` bij installeren, alleen op verzoek van de app (`nuOverstappen`).
- **Cachenaam:** een teller, met de naam ervan afgeleid:
  `const CACHE_VERSION = 29;` en `const CACHE_NAME = 'trends-v' + CACHE_VERSION;`
  (prefix `golf-score-`, `trends-`, `events-`). `update_cache_version.py` hoogt alleen
  die teller op, en dat hoort zodra de service worker zelf wijzigt (of de lijst met
  appbestanden). Anders installeert de nieuwe in dezelfde cache waaruit de oude nog
  bedient. Voor een wijziging aan alleen de app is het niet nodig. Golf rekende tot
  16-10-2026 een hash uit over de appbestanden; daar zat de service worker zelf niet in,
  dus juist bij een wijziging daaraan bleef de naam gelijk.
- **Nieuwe-versie-melding:** `checkAppUpdate` vergelijkt het stempel van de
  draaiende app met het stempel in de kopie in de service-worker-cache.
  Vaste eisen:
  - alleen de cache lezen, geen netwerkverkeer;
  - direct bij het bericht `kopieVernieuwd` van de service worker, en als vangnet
    4 s na start en bij `visibilitychange`;
  - alleen de eigen cache-prefix (`golf-score-`, `trends-`, `events-`) — de
    cache is van het hele domein, dus de andere apps staan er ook in. Geen
    eigen cache betekent niets melden, en uitdrukkelijk GEEN terugval op alle
    caches: trends heeft die terugval er juist uitgehaald, omdat anders een
    kopie van een buurapp meebesliste over de melding;
  - van alle eigen caches het NIEUWSTE stempel nemen, niet de hoogst
    genummerde cache: dat nummer gaat alleen omhoog als de service worker zelf
    wijzigt, dus het nieuwste stempel staat er niet per se in. Een afgebroken
    installatie laat een lege huls met een hoger nummer achter, en daarop
    verviel de melding. Trends en events doen dit zo. **Golf-score wijkt hier
    bewust af**: die vraagt de actieve service worker om zijn eigen cachenaam
    (het gezaghebbende antwoord, zonder netwerk) en valt alleen terug op de
    eerste eigen cache die het bestand heeft;
  - alleen melden bij `>`, nooit bij `!==`: een blijven hangen oude cache zou
    anders melden dat er een "nieuwe" versie is die juist ouder is. Golf-score
    toont in dat geval een eigen tekst ("verouderde kopie in het geheugen");
  - een cache die niet te openen is of geen eigen bestand bevat, overslaan en
    met de rest doorgaan — niet de hele zoektocht afbreken;
  - geen cache, of geopend als los bestand (`file:`): stil niets doen.
- **Deelbaarheid:** een service worker onderschept alleen verzoeken binnen zijn
  eigen scope. Een gedeeld bestand uit een andere repo wordt dus niet gecachet
  en breekt offline. Daarom: geen runtime-afhankelijkheden tussen de apps.

---

## 4. Bewust verschillend

Deze verschillen zijn geen slordigheid. Niet gladstrijken, niet opnieuw
voorstellen om ze gelijk te trekken.

- **Opslag: waar staat de waarheid.** Eén principe voor alle drie: **lezen uit
  de browser, pas om toestemming vragen als er naar een bestand geschreven moet
  worden.** De browser onthoudt een toestemming voor een map maar tot de app
  dicht is (Edge op Android heeft geen 'Toestaan bij elk bezoek'), en ook alleen
  lezen vraagt toestemming. De echte keuze per app is waar de waarheid staat:

  | | golf-score | events | trends |
  |---|---|---|---|
  | waarheid | in de browser | het bestand in de werkmap | de bestanden in de werkmap |
  | naar een bestand | bij een backup | bij elke wijziging | bij elke wijziging |
  | waarom | geen toestemmingsvraag midden op de baan; de backupherinnering houdt het gat op hooguit één ronde | MacroDroid leest het bestand en moet de nieuwste stand zien; noodbewerking in een teksteditor | noodbewerking in een teksteditor; de bestanden zijn het archief |

  Events en trends schrijven elke wijziging meteen weg: elke nieuwe waarde of
  wijziging moet direct veilig staan. Golf doet dat per ronde, bij de backup.

  Events en trends houden in IndexedDB een kopie om te lezen, met de stempel
  (wijzigingstijd en grootte) van het bestand, bijgewerkt bij elk lezen en
  opslaan. Zonder toestemming tonen ze die kopie en kun je gewoon bewerken; pas
  bij het **opslaan** vragen ze om toegang (annuleren kost dus geen vraag). De
  botsingscontrole vergelijkt dan het bestand met de stempel uit de kopie: is
  het buiten de app gewijzigd (een noodbewerking), dan wordt er niets
  overschreven zonder vraag. 'Opnieuw inlezen' vraagt om toegang en leest het
  bestand. Uit de kopie wordt nooit naar een bestand geschreven.
  Alleen een kopie **met stempel** telt. Is er geen (de eerste start, of in
  events een oude kopie van voor 1352898-003), dan vraagt de app eerst om
  toegang en leest hij het bestand; pas daarna is er een kopie. Beide apps
  werken hierin gelijk. Dat geldt in events ook zonder werkmap: ook daar geen
  kopie zonder stempel, zodat je nooit een verouderde lijst ziet die er gewoon
  uitziet. Het moment van de kopie staat er altijd, met en zonder toegang, en
  verder niets: 'vandaag 17:45', 'gisteren 09:12' of '14-10-2026 20:03'
  (dezelfde functie kopieTijd in beide apps, op de kalenderdag).

  Terwijl de app open staat, kijken beide bij elke terugkeer naar de app
  (zichtbaarheid en focus) of een gelezen bestand buiten de app is gewijzigd.
  Zo ja, dan vragen ze eerst, zoals een editor: 'Opnieuw laden?' met 'Opnieuw
  laden' en 'Nee'. Tot je laadt staat er een balk dat je de versie van ervoor
  ziet, met opnieuw laden; dezelfde wijziging geeft geen tweede vraag. Niet
  zonder toegang, niet tijdens een eigen schrijfactie en niet over openstaande
  invoer heen (kijkExtern in beide). Overschrijf je daarna toch, dan gaat de
  versie van buiten eerst naar de backup, ook als er die dag al een was.

  De techniek in de browser verschilt bewust: golf bewaart zijn gegevens in
  localStorage, omdat opslaan daar direct af is (op de baan kan de app elk
  moment worden weggeveegd); events en trends gebruiken IndexedDB, voor de
  verwijzing naar de werkmap en voor de leeskopie. De drie apps delen één
  localStorage van ongeveer 5 MB; die is in de praktijk van golf.
- **Schrijfstijl van de code.** Golf en trends gebruiken `const`/`let` en
  `async`; events gebruikt `var` en `function` met promises. Nieuwe code volgt
  de stijl van het bestand waarin ze terechtkomt, niet die van de buurapp.
- **Kleuren.** Golf goud op groen, trends teal, events blauw. Per app eigen
  accentkleur; alleen typografie en tabelopmaak zijn gedeeld.
- **Installatiepogingen.** Golf probeert elk bestand bij een update tot drie keer
  (elk met de grens van 10 s), trends en events één keer. Golf gebruik je op de baan:
  bij wisselend bereik redt een directe nieuwe poging de update, anders komt de
  volgende kans pas bij de volgende opening. Trends en events gebruik je meestal
  thuis; daar zou het bij een verbinding die echt hangt alleen langer wachten zijn.

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
