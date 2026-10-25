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
    """Dubbele id's.

    Twee gevallen die apart beoordeeld moeten worden:

    * In de STATIEKE opmaak staan de elementen er allemaal tegelijk. Twee keer
      hetzelfde id is daar altijd fout: document.getElementById pakt dan de
      eerste en de tweede is onbereikbaar.
    * In een SCRIPT staat een id vaak in een stuk HTML dat per toestand wordt
      opgebouwd. Twee takken van dezelfde if-else dragen dan hetzelfde id,
      terwijl er in de DOM nooit meer dan een van de twee staat. Dat is geen
      fout, en het als fout melden maakte de hele uitvoer onbetrouwbaar: bij
      events stonden fDl en fLink er zo in, terwijl ze in alle vijf de
      toestanden precies een keer in de DOM staan.

    Vandaar: statiek is een fout, uit een script is een waarschuwing met de
    reden erbij, zodat het met het oog te beoordelen is.
    """
    def vaste_ids(tekst):
        ids = re.findall(r'\bid\s*=\s*["\']([^"\']+)["\']', tekst)
        return [i for i in ids if '${' not in i and '+' not in i]

    def dubbelen(tekst):
        echt = vaste_ids(tekst)
        return sorted({i for i in echt if echt.count(i) > 1})

    statiek = dubbelen(strip_code(s))
    if statiek:
        fout("dubbele id's in de statieke opmaak: " + ', '.join(statiek[:8]))

    scripts = '\n'.join(re.findall(r'<script[^>]*>(.*?)</script>', s, flags=re.S | re.I))
    uit_script = [i for i in dubbelen(scripts) if i not in statiek]
    if uit_script:
        waarschuwing(
            "id's die een script meer dan een keer opbouwt: " + ', '.join(uit_script[:8]) +
            ' — dat hoort zo als het om elkaar uitsluitende takken gaat; '
            'staan ze tegelijk in de DOM, dan is het wel fout')

    # Voor 'opgevraagd maar nergens gezet' telt het hele bestand mee: een id dat
    # een script opbouwt bestaat straks echt in de DOM.
    bekend = set(vaste_ids(s))
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


def check_nieuw_stempel(oud, nieuw, vandaag=None):
    """Een nieuw stempel volgt de afspraak (conventies.md): het datumdeel is de datum
    van VANDAAG, en het volgnummer begint elke dag bij 001 en telt in hex. Tot
    25-10-2026 bleef het datumdeel ongemerkt op 16-10 staan en telde het nummer
    decimaal door: deze controle keek alleen of het stempel omhoog was gegaan."""
    vandaag = vandaag or datetime.date.today()
    hexdag = format(int(vandaag.strftime('%Y%m%d')), 'X')
    try:
        oud_d, oud_n = oud.split('-'); d, n = nieuw.split('-')
        oud_n, nr = int(oud_n, 16), int(n, 16)
    except ValueError:
        return
    verwacht = f'{hexdag}-{(oud_n + 1 if oud_d == hexdag else 1):03X}'
    if d != hexdag:
        waarschuwing(f'nieuw stempel {nieuw}: het datumdeel hoort de datum van vandaag '
                     f'te zijn ({hexdag}) — verwacht {verwacht}')
    elif nieuw != verwacht:
        waarschuwing(f'nieuw stempel {nieuw}: het volgnummer telt per dag in hex vanaf 001 '
                     f'— verwacht {verwacht} (vorige: {oud})')


def check_stempel_vergeten(pad, stempel):
    """Is het app-bestand gewijzigd zonder dat het stempel omhoog ging?

    Het stempel gaat met de hand omhoog, en dat is bewust: een script verhoogt
    het ook bij een wijziging die niemand hoeft te zien, en dan staat er een
    melding tegenover niets. De keerzijde is dat het vergeten kan worden, en
    dan ziet de updatecontrole geen nieuwe versie en blijft de melding uit --
    precies waarom trends het ophogen eerder had geautomatiseerd. Daarom hier
    de controle in plaats van de automaat.

    Twee momenten waarop het mis kan zijn:
      * het bestand is gewijzigd maar nog niet gecommit (de gewone situatie als
        je dit script draait);
      * het is al gecommit zonder nieuw stempel (dan is HEAD de dader).

    Alles aan git is best-effort: geen git, geen repo, geen vorige versie --
    dan zegt deze controle niets. Nooit een FOUT, want een wijziging buiten de
    app-bestanden hoort juist GEEN nieuw stempel te krijgen; het is een
    waarschuwing om naar te kijken.
    """
    if not stempel or not shutil.which('git'):
        return
    map_ = os.path.dirname(os.path.abspath(pad))
    naam = os.path.basename(pad)

    def git(*args):
        r = subprocess.run(['git', '-C', map_, *args],
                           capture_output=True, text=True)
        return r.stdout if r.returncode == 0 else None

    prefix = git('rev-parse', '--show-prefix')
    if prefix is None:
        return
    inrepo = prefix.strip() + naam

    def stempel_in(ref):
        t = git('show', f'{ref}:{inrepo}')
        if t is None:
            return None, None
        m = re.search(r'Versie ([0-9A-F]+-[0-9A-F]+)\s*<', t)
        return (m.group(1) if m else None), t

    vuil = git('status', '--porcelain', '--', naam)
    if vuil:
        oud, tekst = stempel_in('HEAD')
        if tekst is not None and oud == stempel:
            waarschuwing(f'{naam} is gewijzigd maar het stempel staat nog op {stempel} '
                         '— met de hand ophogen voor je commit')
        elif tekst is not None and oud:
            check_nieuw_stempel(oud, stempel)
        return

    # Werkmap schoon: dan kan de laatste commit het stempel vergeten zijn.
    oud, tekst = stempel_in('HEAD~1')
    if tekst is None:
        return
    nu = git('show', f'HEAD:{inrepo}')
    if nu is not None and nu != tekst and oud == stempel:
        waarschuwing(f'de laatste commit wijzigde {naam} maar liet het stempel op '
                     f'{stempel} staan — een nieuwe versie wordt dan niet gemeld')


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
    check_stempel_vergeten(pad, stempel)
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
