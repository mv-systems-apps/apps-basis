"""Controleert de veiligheidsregel van check_app.py (conventies.md, Veiligheid; 22-11-2026):
elke pagina heeft direct na <meta charset> de vaste CSP en de referrer-regel, en laadt
niets van buiten. Eerst de goede pagina, dan per soort fout een kapotte variant die
check_app moet weigeren. Daarna, als de apps ernaast staan, de echte pagina's.

  python3 test_veiligheid.py            (vanuit apps-basis, met de apps in de map erboven)
"""
import os, re, sys, importlib.util, glob
sys.dont_write_bytecode = True   # geen __pycache__ in de repo
HIER = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location('check_app', os.path.join(HIER, 'check_app.py'))
ca = importlib.util.module_from_spec(spec); spec.loader.exec_module(ca)

fouten = []
def check(naam, echt, verwacht):
    ok = echt == verwacht
    print(f"  {'ok  ' if ok else 'FOUT'} {naam}" + ('' if ok else f": {echt!r} — verwacht {verwacht!r}"))
    if not ok: fouten.append(naam)

def meldingen(html):
    ca.fouten.clear(); ca.check_veiligheid_pagina(html, 'p.html'); return list(ca.fouten)

GOED = ('<!DOCTYPE html><html><head>\n<meta charset="utf-8">\n'
        f'<meta http-equiv="Content-Security-Policy" content="{ca.CSP_VAST}">\n'
        '<meta name="referrer" content="no-referrer">\n<title>x</title><script>1</script></head><body></body></html>')
check('de goede pagina: geen meldingen', meldingen(GOED), [])
check('een extern https-adres achter connect-src mag', meldingen(GOED.replace("connect-src 'self'", "connect-src 'self' https://api.voorbeeld.nl")), [])
check('een joker voor subdomeinen van een vast domein mag (thuis: OneDrive)', meldingen(GOED.replace("connect-src 'self'", "connect-src 'self' https://graph.microsoft.com https://*.1drv.com")), [])
for naam, kapot in [
    ('zonder CSP', re.sub(r'<meta http-equiv[^>]*>\n', '', GOED)),
    ('zonder referrer-regel', GOED.replace('<meta name="referrer" content="no-referrer">\n', '')),
    ('referrer anders', GOED.replace('no-referrer', 'origin')),
    ('CSP met een extra bron bij script-src', GOED.replace("script-src 'self'", "script-src 'self' https://cdn.voorbeeld.nl")),
    ('CSP met http-adres bij connect-src', GOED.replace("connect-src 'self'", "connect-src 'self' http://x.nl")),
    ('CSP met * bij connect-src', GOED.replace("connect-src 'self'", "connect-src 'self' https://*")),
    ('CSP met *.topdomein bij connect-src', GOED.replace("connect-src 'self'", "connect-src 'self' https://*.com")),
    ('CSP met * midden in een adres', GOED.replace("connect-src 'self'", "connect-src 'self' https://a.*.nl")),
    ('CSP zonder default-src', GOED.replace("default-src 'none'; ", '')),
    ('CSP niet direct na meta charset', GOED.replace('<meta charset="utf-8">\n', '<meta charset="utf-8">\n<script>0</script>\n')),
    ('CSP pas in de body', GOED.replace(f'<meta http-equiv="Content-Security-Policy" content="{ca.CSP_VAST}">\n', '').replace('<body>', f'<body><meta http-equiv="Content-Security-Policy" content="{ca.CSP_VAST}">')),
    ('een script van buiten', GOED.replace('<script>1</script>', '<script src="https://cdn.voorbeeld.nl/x.js"></script>')),
    ('een stylesheet van buiten', GOED.replace('<title>', '<link rel="stylesheet" href="//fonts.voorbeeld.nl/a.css"><title>')),
    ('@import', GOED.replace('<title>', '<style>@import "a.css";</style><title>')),
]:
    check(f'geweigerd: {naam}', len(meldingen(kapot)) > 0, True)

# de echte pagina's van de apps die ernaast staan
for app in sorted(glob.glob(os.path.join(HIER, '..', '*', '*.html'))):
    map_ = os.path.basename(os.path.dirname(app))
    if os.path.basename(app) not in (map_ + '.html', 'index.html'): continue
    check(f'{map_}/{os.path.basename(app)}: CSP en referrer-regel', meldingen(open(app, encoding='utf-8').read()), [])

print("\n" + ("GEEN FOUTEN" if not fouten else f"{len(fouten)} FOUT(EN): " + ', '.join(fouten)))
sys.exit(1 if fouten else 0)
