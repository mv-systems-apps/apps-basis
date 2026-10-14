# Leesmij

Deze app is er één van drie: **golf-score**, **trends** en **events**.
Ze zijn zelfstandig — geen gedeelde bestanden op runtime — maar volgen
dezelfde regels.

Die regels staan in de repo **`apps-basis`**:

- `conventies.md` — werkwijze, vaste regels, app-shell/PWA, bewuste verschillen
  tussen de apps, bekende valkuilen.
- `check_app.py` — controleert een app tegen die conventies.
- `blokken/` — referentieversies van gedeelde codeblokken.

## Voor je begint te wijzigen

1. Lees `conventies.md`. Werk je met een AI-assistent: upload dat bestand als
   eerste, vóór de app zelf.
2. Controleer de huidige versie van het bestand (er kunnen parallelle sessies
   lopen).

## Na een wijziging

1. Versiestempel ophogen — bij **elke** wijziging.
2. `python3 check_app.py <app>.html --basis <pad naar apps-basis>`
3. Uploaden via de GitHub Android-app.

## Bestandsnamen

De service worker heet `sw-<stam>.js` — de naam van het app-bestand zonder
`.html`, dus bijvoorbeeld `sw-golf-score.js` — en niet `sw.js`. De naam is vrij (alleen de
map bepaalt de scope) en uniek per app, zodat de drie bestanden elkaar niet
overschrijven zodra ze bij elkaar komen te staan.
