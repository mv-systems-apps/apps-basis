# Leesmij

Deze app is er één van drie: **golf-score**, **trends** en **events**.
Ze zijn zelfstandig — geen gedeelde bestanden op runtime — maar volgen
dezelfde regels.

Die regels staan in de repo **`apps-basis`**:

- `conventies.md` — werkwijze, vaste regels, app-shell/PWA, bewuste verschillen
  tussen de apps, bekende valkuilen.
- `check_app.py` — controleert een app tegen die conventies.

`check_app.py` kan ook gedeelde codeblokken vergelijken met een referentie in
een map `blokken/`. Die map bestaat nog niet, en geen van de drie apps
markeert een blok met `/* == basis: naam == */ … /* == einde basis == */`.
De controle doet dus niets tot zo'n markering er wél staat; vanaf dat moment
hoort er een `blokken/<naam>.js` naast te liggen.

## Voor je begint te wijzigen

1. Lees `conventies.md`. Werk je met een AI-assistent: upload dat bestand als
   eerste, vóór de app zelf.
2. Controleer de huidige versie van het bestand (er kunnen parallelle sessies
   lopen).

## Na een wijziging

1. Versiestempel ophogen — bij **elke** wijziging aan de app zelf. Met de hand,
   niet via een script. Een wijziging die niet in de app-bestanden landt (een
   losse test, een leesmij) krijgt geen nieuw stempel: dat zou een
   nieuwe-versie-melding geven voor een uitgave waarin voor de gebruiker niets
   anders is.
2. `python3 check_app.py <app>.html --basis <pad naar apps-basis>`
3. Committen en pushen naar de eigen repo onder `mv-systems-apps`. Vanaf de
   telefoon kan dat met de GitHub-app; het kan ook vanuit de sessie gebeuren,
   en dan is er niets meer zelf te uploaden.

## Bestandsnamen

De service worker heet `sw-<stam>.js` — de naam van het app-bestand zonder
`.html`, dus bijvoorbeeld `sw-golf-score.js` — en niet `sw.js`. De naam is vrij (alleen de
map bepaalt de scope) en uniek per app, zodat de drie bestanden elkaar niet
overschrijven zodra ze bij elkaar komen te staan.
