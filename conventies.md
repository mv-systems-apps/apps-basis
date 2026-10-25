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
Het datumdeel is altijd de datum van de dag waarop je het stempel zet, ook als de
vorige versie van een andere dag is; het volgnummer telt in hex (…009, 00A, 00B).
check_app.py waarschuwt als een nieuw stempel daarvan afwijkt (sinds 25-10-2026:
tot dan bleef het datumdeel ongemerkt op 16-10 staan en telde het nummer decimaal).

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

  Events en trends houden in IndexedDB een kopie om te lezen, bijgewerkt bij elk
  lezen en opslaan; events met de stempel (wijzigingstijd en grootte) van het
  bestand, trends met alleen of het bestand bestaat. Zonder toestemming tonen ze
  die kopie en kun je gewoon bewerken; pas bij het **opslaan** vragen ze om
  toegang (annuleren kost dus geen vraag). 'Opnieuw inlezen' vraagt om toegang
  en leest het bestand. Events schrijft nooit uit de kopie naar een bestand;
  trends schrijft wel de tabel uit de kopie (plus de wijziging), en wist de
  kopie daarom vóór elke schrijfactie: lukt het bijwerken erna niet, dan is er
  geen kopie in plaats van een oude.
  Events telt alleen een kopie **met stempel**; trends een kopie die er is. Is er
  geen (de eerste start, of in events een oude kopie van voor 1352898-003), dan
  vraagt de app eerst om toegang en leest hij het bestand; pas daarna is er een
  kopie. Dat geldt in events ook zonder werkmap: ook daar geen kopie zonder
  stempel, zodat je nooit een verouderde lijst ziet die er gewoon uitziet. Het
  moment van de kopie staat er altijd, met en zonder toegang, en verder niets: 'vandaag 17:45', 'gisteren 09:12' of '14-10-2026 20:03'
  (dezelfde functie kopieTijd in beide apps, op de kalenderdag).

  **De tabel is het bestand.** Een wijziging (een event, een meting) gaat eerst
  naar het bestand en komt pas in de tabel als hij er staat. Wat niet is
  opgeslagen, staat alleen in het venster waarin je het invoert. Er bestaat dus
  geen 'niet opgeslagen' tabel, geen balk boven de tabel en geen waarschuwing
  bij afsluiten.
  **Trends: alleen Trends schrijft in zijn bestanden** (trends 1352898-020). Bij
  het opslaan leest of vergelijkt trends het bestand dus niet: het schrijft de
  tabel met de ene wijziging erin (en één keer per dag eerst de backup). Een
  wijziging buiten trends om wordt bij de volgende opslag overschreven;
  Vernieuwen leest het bestand weer in. Geen botsingen, geen Toch opslaan, ook
  niet voor de bronnenlijst. Vangnet: trends schrijft nooit vanuit een tabel of
  bronnenlijst die het bestand niet volledig weergeeft (geen leeskopie, het
  lezen mislukte, een bestand dat geen object met metingen is, of "bronnen" dat
  geen lijst is); dan leest het eerst het bestand, of slaat het niets op en zegt
  dat. Inlezen dat is ingehaald (een ander bestand of 'meer metingen per dag'
  ingesteld, Vernieuwen, of een opslag die de tabel intussen zette) wordt
  weggegooid, en een lopende schrijfactie naar hetzelfde bestand wacht het eerst
  af. Wat trends niet kan lezen of niet kent (een waarde zonder getal, een
  sleutel die geen datum is, een dubbel tijdstip, een onbekend veld of element
  in de bronnenlijst) toont het niet, maar schrijft het ongewijzigd terug, ook
  na herstel uit de backup; behalve een regel voor precies de meting die je zet
  of verwijdert. Een dag waarvan een dubbele meting is weggelaten, blijft ook na
  een opslag één meting tonen, en opent gewoon als bewerken (024). Opslaan terwijl de
  tabel nog laadt, wacht eerst op de tabel, zodat de vraag om een andere meting van die
  dag te overschrijven niet wegvalt (024). Na middernacht, of als de app 's ochtends
  uit de achtergrond terugkomt, tekent hij tabel en grafiek opnieuw met de nieuwe dag; met
  een open venster pas na het sluiten. Een eigen periode die tot vandaag liep, schuift mee
  (025). De bronnenlijst wordt na elkaar geschreven: opslaan, verwijderen
  en de volgorde rekenen elk met de lijst van het moment dat ze aan de beurt
  zijn; Vernieuwen gooit een lezing weg als er intussen is geschreven
  (trends 1352898-021 t/m -023). Tijdens het opslaan staat er na
  een kwart seconde een draaiend rondje op de knop waarop je tikte (trends 019,
  events 036: Opslaan, de prullenbak, Ongedaan maken). Wat
  hieronder over een bestand dat buiten de app is gewijzigd, geldt voor events.
  Events voegt niets samen (sinds 034). Vlak voor het schrijven leest het het
  bestand opnieuw; alleen als dat precies de tekst is die de app laatst las of
  schreef (bij het venster: die van het moment van openen; zonder toegang: de
  leeskopie), gaat de wijziging erin. Een andere tijd met dezelfde inhoud is
  geen wijziging. Is het anders, dan schrijft events niets (ook geen backup) en
  zegt het venster '<bestand> is buiten de app gewijzigd (20 → 0 regels). Niet
  opgeslagen.', met in de melding [Verder bewerken] [Opnieuw inlezen] (oranje, met
  de focus; sinds 038 'Verder bewerken', zodat er geen twee knoppen Annuleren met
  een andere betekenis onder elkaar staan). Verder bewerken laat het venster en je
  invoer staan; opnieuw opslaan geeft dezelfde melding. Opnieuw inlezen sluit het
  venster zonder je wijziging, zet het bestand van nu in beeld, houdt het filter
  dat je had, en zet de focus op +. Ongedaan maken doet hetzelfde in de melding op
  de plek van de stapbalk ([Annuleren] [Opnieuw inlezen]; 'Niet ongedaan
  gemaakt.'). Instellingen: stuit het opslaan van de configuratie op een gewijzigd
  eventsbestand, dan dezelfde oranje melding; Opnieuw inlezen leest daar alleen het
  eventsbestand en laat het formulier staan. De vernieuwknop in Instellingen vraagt
  eerst als je in het formulier iets wijzigde. Ctrl+S (ook met Caps Lock) slaat
  alleen op als het bewerkvenster bovenaan staat. Na Opnieuw inlezen (ook Instellingen › Opnieuw inlezen)
  noemt een melding boven de lijst het verschil in regels (of 'de inhoud is
  anders'), en bij minder regels de backup. Bij het vragen om toegang (opslaan op
  de leeskopie) blijft de leeskopie in beeld als het bestand afwijkt; pas Opnieuw
  inlezen zet het bestand van nu in beeld (035). Gewoon inlezen (opstarten)
  vervangt de leeskopie niet door een leeg of veel kleiner bestand. Een bestand
  dat buiten de app is weggehaald: opslaan zegt 'staat niet meer in de werkmap',
  met [Verder bewerken] of [Annuleren] en [Nieuw bestand] (zie 040 en 041).
  Een nieuw event wordt altijd toegevoegd; events ontdubbelt niet stil.
  Events leest bestanden via arrayBuffer, zodat een BOM blijft (text() haalt hem
  weg). Sinds 037: is het bestand bij gewoon inlezen veel kleiner dan de leeskopie
  (leeg, of van 10 of meer naar minder dan de helft), dan blijft de leeskopie in
  beeld en als basis, met een melding; Opnieuw inlezen zet eerst de leeskopie in
  naam_backup_groot en noemt dat. Een grotere naam_backup_groot wordt nooit door een
  kleinere vervangen. Lukt het bijwerken van de leeskopie niet, dan wordt de oude
  gewist en staat er een melding. Een mislukte schrijfactie wordt afgebroken (abort).
  Sinds 039: bij het opstarten en koppelen laadt events eerst de leeskopie (zonder
  hem te tonen), zodat ook dan een leeg, veel kleiner of verdwenen bestand wordt
  gezien: de leeskopie blijft in beeld, met een melding, en opslaan maakt niet stil
  een nieuw bestand. Is er al een grotere naam_backup_groot, dan gaat de recentere
  versie naar naam_backup_groot_JJJJMMDD-UUMMSS; de melding noemt waar hij staat. Een
  bestand dat geen geldige UTF-8 is, wordt niet gelezen en niet geschreven (bewerken
  uit, met een melding). Na het opslaan van de configuratie staat die ook in de
  leeskopie; is de configuratie na het vragen om toegang anders dan in het venster,
  dan schrijft events niets en vult het venster zich opnieuw. Past het
  scheidingsteken niet bij het bestand, dan zegt opslaan dat (niet 'buiten de app
  gewijzigd'); kies je in Instellingen een teken waarmee elke regel te lezen is,
  dan schrijft events alleen de configuratie.
  Sinds 040: is het bestand weg, dan heet de keuze [Nieuw bestand] (niet 'Opnieuw
  inlezen': er valt niets in te lezen); de melding noemt de backup. Meldingen die om
  een keuze vragen bij het inlezen (veel kleiner, weg) staan boven de lijst met hun
  eigen knop. Na een tik op Opnieuw inlezen of Nieuw bestand staan de knoppen meteen
  uit, met het rondje; een tweede tik doet niets. Het rondje staat ook op
  Instellingen › Opslaan en Filter › Als standaard, en blijft in volle kleur, ook als
  de telefoon de hover na een tik laat staan. Knopteksten in een melding mogen over
  twee regels. Stapregel en meldingen worden alleen bij een andere tekst opnieuw
  opgebouwd (schermlezer).
  Sinds 041: Nieuw bestand bij een verdwenen bestand zet eerst wat de app nog had
  (de leeskopie) in naam_backup_groot, en de melding zegt waar; lukt dat niet, dan
  blijft de leeskopie in beeld. Een naam_backup_groot die er al is en groter of
  onleesbaar is, blijft staan; de nieuwe gaat dan naar naam_backup_groot_JJJJMMDD-
  UUMMSS. Mislukt Opnieuw inlezen, dan gaan de knoppen in de melding weer aan.
  Sinds 042: een bestaande naam_backup_groot met andere inhoud wordt nooit
  overschreven, ook niet door een grotere; een nieuwe versie gaat ernaast onder een
  vrije naam (_JJJJMMDD-UUMMSS, zo nodig met -2, -3). Instellingen zegt bij een
  verdwenen bestand hetzelfde als het venster ([Nieuw bestand]; het formulier
  blijft). Mislukt het lezen om een andere reden dan toegang (de sync houdt het
  bestand vast), dan blijft de leeskopie in beeld met de melding en de knop
  Opnieuw inlezen. Kies je een ander eventsbestand, dan hoort de oude leeskopie
  niet meer bij de configuratie en wordt hij gewist; een leeskopie onthoudt ook de
  werkmap. Het scheidingsteken wordt ook in het categorieveld gecontroleerd; een
  leeg bestand heeft geen halve omzetting. De configuratie moet UTF-8 zijn;
  stuurtekens (een tab) worden een spatie. Toch opslaan van de configuratie gaat
  niet door als de backup van de versie van buiten mislukt. Ontkoppelen kan niet
  tijdens opslaan of inlezen. Bij een scheidingsteken- of UTF-8-probleem biedt de
  stapmelding alleen Annuleren.
  Sinds 043: backups kopiëren de bytes zoals ze er staan (ook een ANSI-bestand).
  Een configuratie die geen UTF-8 is, wordt niet gelezen en ook vanuit Instellingen
  niet overschreven. Bestaat een backupbestand maar is het even niet te lezen (de
  sync houdt het vast), dan geldt het niet als afwezig: _backup_groot komt ernaast,
  een dagbackup wordt die keer overgeslagen (de dag blijft open). Een leeskopie uit
  een andere map wordt bij het opslaan van de configuratie niet aan deze map
  gehangen. Een tab als scheidingsteken of of-teken (met de hand gezet) blijft een
  tab; in andere teksten wordt een stuurteken een spatie. Sinds 044: een ander
  stuurteken (een regelovergang) als scheidingsteken of of-teken wordt overgeslagen
  en gemeld. De blokkade voor een configuratie die geen UTF-8 is, vervalt zodra die
  configuratie weg is of er een andere werkmap wordt gekozen. Sinds 045 leest events
  vlak voor het schrijven van de configuratie wat er nu op schijf staat: is dat geen
  UTF-8, dan wordt het nooit overschreven, wat de app eerder ook onthield.
  Sinds 046: een melding die alleen informeert (na Opnieuw inlezen: 'opnieuw
  ingelezen: …', 'staat niet meer in de werkmap … Opslaan maakt een nieuw bestand')
  staat boven de lijst met een ✕ en blijft tot je die aantikt of tot het volgende
  inlezen of opslaan. Waarschuwingen (veel kleiner, weg, geen UTF-8, backup mislukt,
  scheidingsteken) hebben geen ✕ en blijven tot het is opgelost.
  Sinds 047: een opslag vraagt het bestand één keer bij de werkmap op; lezen,
  de controle vlak voor het schrijven en het schrijven gebruiken dat adres (op
  Android is elke vraag aan de map een trage stap). Bestond het bestand bij het
  lezen niet, dan kijkt de controle opnieuw in de map. App-status toont onder
  'Laatste opslag' de duur in seconden: totaal en per stap (toegang, lezen,
  backup, controle, schrijven), en bij een geweigerde opslag de reden.
  Opslaan mislukt: het venster blijft open met 'Opslaan mislukt.' (bij
  verwijderen 'Verwijderen mislukt.'); de knoppen blijven [Annuleren]
  [Opslaan]. Annuleren staat altijd links van de bevestigknop. Eerst de knop,
  dan de melding; melding en knoppen schuiven in beeld. Tijdens het opslaan
  gaat het venster niet dicht. Waarden die trends niet kan lezen (geen getal,
  geen datum, twee sleutels voor hetzelfde tijdstip) meldt het bij het inlezen,
  in één melding; ze blijven ongewijzigd in het bestand staan. Kapotte JSON in
  events, of in trends met een tabel die het bestand niet weergeeft: niet
  opslaan, en 'Vernieuwen biedt de back-up aan'.
  Is een nieuwe dagbackup veel kleiner dan de vorige (leeg, of van 10 of meer naar
  minder dan de helft), dan gaat de vorige eerst naar naam_backup_groot.
  Vlak vóór het schrijven vergelijkt events nog eens de stempel: is het bestand
  sinds het lezen veranderd, dan schrijft het niets en volgt dezelfde melding. Lukt het
  schrijven maar mislukt alleen het teruglezen, dan geldt het als geslaagd.
  Regeleindes (CRLF/LF), een BOM en een ontbrekend slotregeleinde blijven zoals ze
  waren; lege regels vallen bij het opslaan weg. Commentaar en kopjes bestaan niet
  (meer, sinds 033): een regel die met -- begint is een gewone regel. De
  configuratie en backupnamen kunnen niet als eventsbestand worden gekozen.
  Scheidingsteken in events: staat het nieuwe teken al in een event, dan
  weigert het instellingenvenster het (met het aantal en een voorbeeld); ook een
  onbegrepen regel met dat teken blokkeert het omzetten (030). Is het
  omzetten niet afgemaakt of mist het teken, dan kan er niet bewerkt worden tot
  het bestand weer klopt; ook als geen enkele regel te lezen is (037). Een
  onafgemaakte omzetting onthoudt events per bestand in IndexedDB (sepHalf:<naam>).
  Kies je in Instellingen het teken waarop het bestand echt staat, dan schrijft
  events alleen de configuratie (037). Toch opslaan van de configuratie weigert als
  op schijf een ander scheidingsteken of bestand staat dan de app kent (037).
  Een bestand dat één geheel is (events_cfg.json) kan niet worden
  samengevoegd: daar vergelijkt de app de stempel, en bij een botsing zegt het
  venster dat; Toch opslaan zet eerst de versie van buiten in de backup (ook
  als er die dag al een was). Sluiten na zo'n botsing, langs welke weg ook
  (Annuleren, terug, naast het venster), leest het bestand opnieuw in.
  Zonder venster: ongedaan maken en opnieuw in events (een melding op de plek
  van de stapbalk) en de volgorde van de bronnen in trends (de balk onderaan).
  Een wijziging buiten de app wordt niet bij terugkeer gecontroleerd; je leest
  zelf opnieuw in (events: Instellingen › Opnieuw inlezen, trends: Vernieuwen).
  Geen herstelbuffer en geen downloadroute: een browser zonder File System
  Access (Chrome voor Android, Firefox) kan geen werkmap koppelen; events zegt
  dat in één regel en toont hooguit een eerder bewaarde kopie. Een
  achtergebleven herstelrij uit een oudere versie ruimt events bij het
  opstarten op.

  Oranje meldingen: één korte zin wat er is, daarna de knoppen. Annuleren alleen
  waar je echt kiest; nooit een knop die stil een wijziging weggooit.

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
  In de trends-grafiek heeft paars twee tinten: het doel lavendel (`#b48ef0`,
  gestreept), de regressielijn oudroze (`#d19ac0`, doorgetrokken). Sinds 026 is
  Regressie de vierde veegweergave: een trendkaart met grenzen op 2σ en 3σ die met
  de lijn meelopen (σ = spreiding rond de lijn, grenzen vanaf 5 punten), de punten
  en de tabelrijen gekleurd naar hun afstand tot de lijn, een witte pijl met de
  helling en r² in de kop, en in Analyse de tabs Statistieken en Regressie (geen
  Kaart). Sinds 027: per dag en per meting ook Regressie XmR (grenzen 2,66 en
  1,77 × r̄ rond de lijn); is de helling niet aantoonbaar (95%, t × standaardfout),
  dan een ? achter de pijl en een gestreepte lijn; bij een bron met doel en
  een aantoonbare trend naar het doel toe is Prognose de laatste veegweergave (de
  lijn gestippeld door tot het doel, de datum rechts onder de grafiek in de kleur
  van de lijn en in Analyse; alleen een prognose na vandaag telt). Sinds 029 staat de
  naam van de weergave niet meer in de kop maar eronder, met een stipje per
  weergave waartussen je kunt vegen; in Analyse is die naam de titel (vet, 18 px, in de kleur van de
  kaart, het aantal rechts, de kop in een tint van die kleur, de actieve tab in die kleur),
  ingekort (Regr, Prog)
  als hij niet naast het aantal past. De basiskaart heet x̄±σ. De regelkaarten (x̄±σ,
  XmR, Range) turquoise, de kleur van x̄; de trendkaarten oudroze. Een doel
  buiten de schaal wordt niet getekend. Een nieuwe lijn krijgt een kleur die nog
  niet in de grafiek staat.
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
  de cfg. Commentaar bestaat niet (sinds events 033): een regel die met `--`
  begint, is voor de app en de macro een gewone regel (met geldige velden een
  event, anders een onbegrepen regel die ongewijzigd blijft staan). Lege regels
  slaan beide over. Een veld dat de app niet anders hoeft te maken (een
  categorie als "hoog" of "02") gaat letterlijk terug. Wat de macro niet aankan,
  laat de configuratie niet toe: een type zonder teken, een letter, cijfer of
  `` ` `` `\` `"` `${` als scheidingsteken, die laatste vier ook niet als of-teken,
  een paasdag buiten -99..99 en een categorie onder 1. Voor de datumsleutel van
  meetmomenten, zie "Vaste regels".
- **Een bestand dat er was en nu weg is, wordt niet stil opnieuw gemaakt** (events):
  dan zegt het venster dat het bestand niet meer in de werkmap staat.

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
