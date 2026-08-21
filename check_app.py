#!/usr/bin/env python3
"""
check_app.py — controleert een single-file app tegen de gedeelde conventies.

Gebruik:
    python3 check_app.py golf-score.html
    python3 check_app.py ../trends/trends.html --basis .

Zoekt de service worker in dezelfde map als het opgegeven bestand: leidend is de
naam die de app zelf registreert (sw.js, sw-golf.js, ... — de naam is vrij, de map
bepaalt de scope).
Meldt alleen wat er misgaat. Exitcode 1 bij fouten, 0 als alles goed is.
"""

import sys, os, re, glob, shutil, subprocess, datetime

VOID = {'br','img','input','meta','link','hr','source','path','circle','line',
        'polyline','rect','polygon','use','ellipse','stop','area','col','base',
        'track','wbr','feoffset','fegaussianblur','femerge','femergenode'}

fouten, waarschuwingen = [], []

def fout(t): fouten.append(t)
def waarschuwing(t): waarschuwingen.append(t)


def strip_code(s):
    """HTML zonder script, style en commentaar."""
    s = re.sub(r'<script[^>]*>.*?</script>', '', s, flags=re.S | re.I)
    s = re.sub(r'<style[^>]*>.*?</style>', '', s, flags=re.S | re.I)
    return re.sub(r'<!--.*?-->', '', s, flags=re.S)


def functiebody(s, naam):
    """Ruwe body van een functie, via accolades tellen. None als niet gevonden."""
    m = re.search(r'function\s+' + re.escape(naam) + r'\s*\(', s)
    if not m:
        return None
    i = s.find('{', m.end())
    if i < 0:
        return None
    diep = 0
    for j in range(i, len(s)):
        if s[j] == '{':
            diep += 1
        elif s[j] == '}':
            diep -= 1
            if diep == 0:
                return s[i:j + 1]
    return s[i:]


def check_tagbalans(s):
    stapel, los = [], []
    for sluit, naam, _attrs, zelf in re.findall(
            r'<(/?)([a-zA-Z][a-zA-Z0-9]*)([^>]*?)(/?)>', strip_code(s)):
        n = naam.lower()
        if n in VOID or zelf:
            continue
        if sluit:
            if stapel and stapel[-1] == n:
                stapel.pop()
            else:
                los.append(n)
        else:
            stapel.append(n)
    if stapel:
        fout('niet gesloten tags: ' + ', '.join(stapel[:8]))
    if los:
        fout('losse sluittags: ' + ', '.join(los[:8]))


def check_js(s, pad):
    blokken = re.findall(r'<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>', s, flags=re.S | re.I)
    if not blokken:
        waarschuwing('geen inline scriptblok gevonden')
        return
    node = shutil.which('node')
    for i, b in enumerate(blokken):
        if node:
            tmp = pad + f'.blok{i}.js'
            with open(tmp, 'w', encoding='utf-8') as f:
                f.write(b)
            r = subprocess.run([node, '--check', tmp], capture_output=True, text=True)
            os.remove(tmp)
            if r.returncode:
                fout(f'JS-syntaxfout in scriptblok {i}:\n    ' +
                     r.stderr.strip().splitlines()[-1] if r.stderr.strip() else 'onbekend')
        else:
            try:
                compile('', '', 'exec')  # placeholder; zonder node geen JS-parser
            except Exception:
                pass
    if not node:
        waarschuwing('node niet gevonden — JS-syntaxcheck overgeslagen')


def check_ids(s):
    ids = re.findall(r'\bid\s*=\s*["\']([^"\']+)["\']', s)
    echt = [i for i in ids if '${' not in i and '+' not in i]
    dubbel = sorted({i for i in echt if echt.count(i) > 1})
    if dubbel:
        fout('dubbele id\'s: ' + ', '.join(dubbel[:8]))

    bekend = set(echt)
    gevraagd = set(re.findall(r'getElementById\(\s*["\']([^"\']+)["\']\s*\)', s))
    gevraagd |= set(re.findall(r'\$\(\s*["\']([^"\']+)["\']\s*\)', s))
    ontbreekt = sorted(i for i in gevraagd - bekend if '${' not in i)
    if ontbreekt:
        waarschuwing('id opgevraagd maar nergens in het bestand gezet: ' +
                     ', '.join(ontbreekt[:8]))


def check_handlers(s):
    gedefinieerd = set(re.findall(r'function\s+([A-Za-z_$][\w$]*)', s))
    gedefinieerd |= set(re.findall(r'(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*(?:async\s*)?(?:function|\()', s))
    ontbreekt = set()
    for h in re.findall(r'\bon[a-z]+\s*=\s*"([^"]+)"', s):
        for naam in re.findall(r'(?<![.\w$])([A-Za-z_$][\w$]*)\s*\(', h):
            if naam not in gedefinieerd and naam not in (
                    'if', 'return', 'this', 'alert', 'confirm', 'parseInt',
                    'parseFloat', 'Number', 'String', 'Boolean', 'Array', 'Object',
                    'setTimeout', 'requestAnimationFrame', 'event', 'window',
                    'document', 'console', 'Math', 'JSON', 'Date', 'typeof',
                    'var', 'let', 'const', 'else', 'for', 'while', 'switch', '_'):
                ontbreekt.add(naam)
    if ontbreekt:
        waarschuwing('inline handler roept onbekende functie aan: ' +
                     ', '.join(sorted(ontbreekt)[:8]))


def check_stempel(s):
    m = re.search(r'Versie ([0-9A-F]+-[0-9A-F]+)\s*<', s)
    if not m:
        fout('geen versiestempel gevonden (verwacht: Versie HEX(yyyymmdd)-NNN)')
        return None
    datumdeel, volgnr = m.group(1).split('-')
    if len(volgnr) != 3:
        fout(f'volgnummer moet drie hex-cijfers zijn, gevonden: {volgnr}')
    try:
        d = datetime.datetime.strptime(str(int(datumdeel, 16)), '%Y%m%d').date()
    except ValueError:
        fout(f'datumdeel {datumdeel} is geen geldige datum')
        return m.group(1)
    vandaag = datetime.date.today()
    if d > vandaag:
        fout(f'stempeldatum {d} ligt in de toekomst')
    elif (vandaag - d).days > 400:
        waarschuwing(f'stempeldatum {d} is meer dan een jaar oud')
    return m.group(1)


def check_sw(s, pad):
    map_ = os.path.dirname(os.path.abspath(pad))
    appnaam = os.path.basename(pad)
    # De service worker mag elke naam hebben (sw.js, sw-golf.js, ...); wat telt is
    # dat hij in dezelfde map staat, want die bepaalt de scope. Leidend is de naam
    # die de app zelf registreert.
    m = re.search(r'register\(\s*["\']([^"\']+)["\']', s)
    geregistreerd = m.group(1).lstrip('./') if m else None
    kandidaten = [os.path.basename(k) for k in sorted(glob.glob(os.path.join(map_, 'sw*.js')))]

    if geregistreerd:
        if geregistreerd not in kandidaten:
            fout(f'de app registreert "{geregistreerd}", maar dat bestand staat niet '
                 f'in dezelfde map' +
                 (f' (wel gevonden: {", ".join(kandidaten)})' if kandidaten else ''))
            return
        swnaam = geregistreerd
    elif len(kandidaten) == 1:
        swnaam = kandidaten[0]
        waarschuwing('geen serviceWorker.register() gevonden in de app')
    else:
        waarschuwing('geen service worker gevonden naast de app — PWA-controles '
                     'overgeslagen')
        return

    verwacht = 'sw-' + os.path.splitext(appnaam)[0] + '.js'
    if swnaam != verwacht:
        waarschuwing(f'de service worker heet "{swnaam}"; volgens de conventies '
                     f'"{verwacht}" (stam van het app-bestand)')

    if len(kandidaten) > 1:
        waarschuwing('meerdere service workers in de map (' + ', '.join(kandidaten) +
                     f'); gecontroleerd is {swnaam} — ruim de andere op')

    tekst = open(os.path.join(map_, swnaam), encoding='utf-8').read()

    m = re.search(r'CACHE(?:_VERSION|_NAME)?\s*=\s*["\']([^"\']+)["\']', tekst)
    cachenaam = m.group(1) if m else None
    if not cachenaam:
        waarschuwing(f'cachenaam niet gevonden in {swnaam}')

    if appnaam not in tekst:
        fout(f'{appnaam} staat niet in de precache-lijst van {swnaam}')

    if not re.search(r'\.put\s*\(', tekst):
        waarschuwing(f'{swnaam} lijkt geen stale-while-revalidate te doen '
                     '(geen cache.put)')

    prefixen = re.findall(r'CACHE_PREFIX\s*=\s*["\']([^"\']+)["\']', s)
    if not prefixen:
        prefixen = re.findall(r'startsWith\(\s*["\']([^"\']+)["\']', s)
        prefixen += re.findall(r'indexOf\(\s*["\']([^"\']+)["\']\s*\)\s*===?\s*0', s)
    prefixen = [p for p in prefixen if len(p) >= 4 and '-' in p]
    if not prefixen:
        waarschuwing('geen cache-prefix gevonden in checkAppUpdate')
    elif cachenaam and not any(cachenaam.startswith(p) for p in prefixen):
        fout(f'cache-prefix {prefixen} past niet bij de cachenaam "{cachenaam}" '
             f'in {swnaam}')

    body = functiebody(s, 'checkAppUpdate')
    if body is None:
        waarschuwing('checkAppUpdate ontbreekt in de app')
    elif '!==' in body and '>' not in body:
        waarschuwing('checkAppUpdate vergelijkt met !== in plaats van >; een oude '
                     'cache meldt dan ook een "nieuwe" versie')


def check_blokken(s, basis):
    blokdir = os.path.join(basis, 'blokken')
    gevonden = re.findall(
        r'/\* == basis: ([^=]+?) == \*/(.*?)/\* == einde basis == \*/', s, flags=re.S)
    for naam, inhoud in gevonden:
        naam = naam.strip()
        ref = os.path.join(blokdir, naam + '.js')
        if not os.path.exists(ref):
            fout(f'gedeeld blok "{naam}" heeft geen referentie in blokken/{naam}.js')
            continue
        norm = lambda t: '\n'.join(r.rstrip() for r in t.strip().splitlines() if r.strip())
        if norm(inhoud) != norm(open(ref, encoding='utf-8').read()):
            fout(f'gedeeld blok "{naam}" wijkt af van blokken/{naam}.js')


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    basis = '.'
    if '--basis' in sys.argv:
        basis = sys.argv[sys.argv.index('--basis') + 1]
    if not args:
        print(__doc__)
        return 2
    pad = args[0]
    if not os.path.exists(pad):
        print(f'bestand niet gevonden: {pad}')
        return 2
    s = open(pad, encoding='utf-8').read()

    check_tagbalans(s)
    check_js(s, pad)
    check_ids(s)
    check_handlers(s)
    stempel = check_stempel(s)
    check_sw(s, pad)
    check_blokken(s, basis)

    naam = os.path.basename(pad)
    if fouten:
        print(f'{naam} — {len(fouten)} fout(en):')
        for f in fouten:
            print('  FOUT  ' + f)
    for w in waarschuwingen:
        print('  let op ' + w)
    if not fouten and not waarschuwingen:
        print(f'{naam} — in orde' + (f' (versie {stempel})' if stempel else ''))
    elif not fouten:
        print(f'{naam} — geen fouten' + (f' (versie {stempel})' if stempel else ''))
    return 1 if fouten else 0


if __name__ == '__main__':
    sys.exit(main())
