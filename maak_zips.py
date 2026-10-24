#!/usr/bin/env python3
"""Een back-upzip per app, rechtstreeks uit de clone-map.

Per app zijn eigen map, dus zijn eigen index.html, manifest.json, icon.svg en
update_cache_version.py -- die namen komen in alle drie de repo's voor en mogen
nooit door elkaar lopen. Daarom wordt hier per app apart gelopen en wordt na het
inpakken teruggelezen welke app er werkelijk in zit: klopt de titel in
index.html niet met de app, dan staat dat in de uitvoer.

In de zip komen precies de bestanden die in git staan, met hun submappen (zoals
tests/ van golf), in de vorm waarin ze nu in de werkmap staan. Wat niet in git
staat, komt er nooit in: zo belandt een lokale backup met namen
(tests/rondes_backup.json) niet in een zip. Is de map geen git-clone, dan alleen
de losse bestanden in de hoofdmap, zoals voorheen.

In elke zip komt een LEESMIJ.txt met het commit waar de inhoud bij hoort, het
versiestempel, en of er op dat moment nog niet-gecommitte wijzigingen in de
werkmap stonden.

Gebruik (vanuit de map apps-basis, met de clones ernaast):
    python3 maak_zips.py
    python3 maak_zips.py --uit ~/backups        andere doelmap
    python3 maak_zips.py --clones /pad/naar     als de clones elders staan
"""

import argparse
import json
import re
import subprocess
import zipfile
from datetime import date
from pathlib import Path

MAANDEN = ['januari', 'februari', 'maart', 'april', 'mei', 'juni', 'juli',
           'augustus', 'september', 'oktober', 'november', 'december']

APPS = {
    'events': {
        'hoofd': 'events.html',
        'stempel': 'onderaan het instellingenscherm',
        'extra': ('events-tests.cjs is de node-regressietest. Draaien met:\n'
                  '  node events-tests.cjs   vanuit deze map.\n\n'
                  'zelftest.html draai je in de browser; die moet via http of https\n'
                  'geopend worden, niet rechtstreeks vanaf schijf. zt_run.js doet dat\n'
                  'voor je in Chromium, mutant.js rekent na of de tests werkelijk\n'
                  'iets toetsen.\n'),
    },
    'golf-score': {
        'hoofd': 'golf-score.html',
        'stempel': 'onderaan Instellingen',
        'extra': ('De twee Word-documenten zijn de handleidingen; README.md\n'
                  'beschrijft de app. tests/ is de testsuite: lees eerst\n'
                  'tests/LEESMIJ.md en tests/CONTROLELIJST.md. Alles draaien:\n'
                  '  python3 tests/run-alles.py   (ongeveer 50 minuten)\n'),
    },
    'trends': {
        'hoofd': 'trends.html',
        'stempel': 'onderaan het Bronnen-paneel',
        'extra': ('uitleg-grafieken.pdf (en .md) legt elke grafiek en elke regel\n'
                  'van het statistiekenvenster uit: berekening en interpretatie.\n\n'
                  'trends-tests.cjs is de node-regressietest. Draaien met:\n'
                  '  node trends-tests.cjs   vanuit deze map.\n'),
    },
    'apps-basis': {
        'hoofd': None,
        'stempel': None,
        'extra': ('Dit is geen app maar de gedeelde basis: conventies.md is de\n'
                  'afsprakenlijst voor alle drie de apps, check_app.py controleert\n'
                  'een app daarop en waarschuwt als het versiestempel vergeten is.\n'
                  'Draaien met:\n'
                  '  python3 check_app.py <app>.html --basis <deze map>\n'
                  'maak_zips.py maakt deze zips; nieuwe-chat.txt is de startinstructie\n'
                  'voor een verse sessie.\n'),
    },
}


def git(pad, *args):
    r = subprocess.run(['git', '-C', str(pad), *args], capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else ''


def bestanden_van(bron):
    """De bestanden voor de zip, als (pad, naam in de zip). In een clone wat git
    volgt, met submappen; anders alleen de losse bestanden in de hoofdmap."""
    gevolgd = git(bron, 'ls-files', '-z')
    if gevolgd:
        namen = sorted(n for n in gevolgd.split('\0') if n)
        return [(bron / n, n) for n in namen if (bron / n).is_file()]
    return [(q, q.name) for q in sorted(bron.iterdir())
            if q.is_file() and not q.name.startswith('.')]


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--uit', default=None, help='doelmap voor de zips')
    p.add_argument('--clones', default=None, help='map waarin de clones staan')
    args = p.parse_args()

    hier = Path(__file__).resolve().parent
    clones = Path(args.clones).expanduser().resolve() if args.clones else hier.parent
    naar = Path(args.uit).expanduser().resolve() if args.uit else hier.parent
    naar.mkdir(parents=True, exist_ok=True)

    vandaag = date.today()
    datum = vandaag.strftime('%Y%m%d')
    mooi = f'{vandaag.day} {MAANDEN[vandaag.month - 1]} {vandaag.year}'

    for naam, cfg in APPS.items():
        bron = clones / naam
        if not bron.is_dir():
            print(f'{naam:28} OVERGESLAGEN: {bron} bestaat niet')
            continue

        commit = git(bron, 'rev-parse', '--short', 'HEAD') or '(geen git)'
        vuil = git(bron, 'status', '--porcelain')
        stempel = None
        if cfg['hoofd'] and (bron / cfg['hoofd']).exists():
            m = re.search(r'Versie ([0-9A-F]+-[0-9A-F]+)',
                          (bron / cfg['hoofd']).read_text(encoding='utf-8'))
            stempel = m.group(1) if m else '(geen stempel gevonden)'

        regels = [
            f'{naam} — werkmap, {mooi}',
            '=' * (len(naam) + len(mooi) + 12),
            '',
            'Precies wat er op dat moment op GitHub stond:',
            f'  github.com/mv-systems-apps/{naam}   commit {commit}',
            '',
        ]
        if stempel:
            regels += [f'Versiestempel:  {stempel}  ({cfg["stempel"]})', '']
        if vuil:
            regels += ['LET OP: in de werkmap stonden nog niet-gecommitte wijzigingen:',
                       *('  ' + r for r in vuil.splitlines()), '']
        regels += [cfg['extra'],
                   'De gedeelde regels voor deze app staan in',
                   'github.com/mv-systems-apps/apps-basis (conventies.md, check_app.py).',
                   '']

        doel = naar / f'{naam}-{datum}.zip'
        bestanden = bestanden_van(bron)
        with zipfile.ZipFile(doel, 'w', zipfile.ZIP_DEFLATED) as z:
            for q, naam_in_zip in bestanden:
                z.write(q, naam_in_zip)
            z.writestr('LEESMIJ.txt', '\n'.join(regels))

        # Terugkijken: zit er werkelijk de JUISTE app in?
        with zipfile.ZipFile(doel) as z:
            inzit = z.namelist()
            titel = manifest = '(niet aanwezig)'
            if 'index.html' in inzit:
                t = re.search(r'<title>([^<]*)</title>',
                              z.read('index.html').decode('utf-8'))
                titel = t.group(1) if t else '(geen titel)'
            if 'manifest.json' in inzit:
                d = json.loads(z.read('manifest.json'))
                manifest = f'{d.get("name")} -> {d.get("start_url")}'
        print(f'{doel.name:28} {len(inzit):2} bestanden, {doel.stat().st_size // 1024:5} kB'
              f'  | index: {titel:12} | manifest: {manifest}')


if __name__ == '__main__':
    main()
