/* Bewijst dat een wijziging alleen commentaar raakt: vergelijkt twee versies
   van een app-bestand zonder commentaar.

   Gebruik:  node zelfde_code.js oud.html nieuw.html   (of twee .js-bestanden)
   De oude versie haal je uit git:  git show HEAD:events.html > /tmp/oud.html

   Per <script>: de tokens (soort en waarde) moeten gelijk zijn; witruimte en
   commentaar tellen niet. In <style> telt commentaar ook niet. De rest van de
   pagina moet byte voor byte gelijk zijn -- hoog het versiestempel dus pas NA
   deze vergelijking op.
   Nodig: acorn (npm i acorn), een hulpmiddel voor de ontwikkelaar; de apps
   zelf gebruiken het niet. Exitcode 0 = gelijk, 1 = verschil. */
const fs = require('fs'), acorn = require('acorn');
const bestanden = process.argv.slice(2);
/* Een los .js-bestand (een service worker) is als geheel een script. */
const alsPagina = t => /\.js$/.test(bestanden[0]) ? '<script>' + t + '</script>' : t;
const [a, b] = bestanden.map(f => alsPagina(fs.readFileSync(f, 'utf8')));
const RE = /(<script\b[^>]*>)([\s\S]*?)(<\/script>)/g;
const delen = s => { const buiten = [], scripts = []; let i = 0, m;
  RE.lastIndex = 0;
  while ((m = RE.exec(s))) { buiten.push(s.slice(i, m.index) + m[1]); scripts.push(m[2]); i = m.index + m[0].length - m[3].length; }
  buiten.push(s.slice(i)); return { buiten, scripts }; };
const tokens = src => { const t = []; for (const k of acorn.tokenizer(src, { ecmaVersion: 'latest', sourceType: 'script', allowHashBang: true }))
  t.push(k.type.label + ':' + (k.value === undefined ? '' : String(k.value))); return t; };
/* Buiten de scripts: CSS-commentaar binnen <style> telt niet, en witruimte in
   <style> telt als een spatie (in CSS maakt de hoeveelheid niet uit). */
const zonderCssCommentaar = t => t.replace(/(<style\b[^>]*>)([\s\S]*?)(<\/style>)/g,
  (m, o, css, d) => o + css.replace(/\/\*[\s\S]*?\*\//g, ' ').replace(/\s+/g, ' ').trim() + d);
const A = delen(a), B = delen(b); let fout = 0;
const buitenA = zonderCssCommentaar(A.buiten.join('\u0000')), buitenB = zonderCssCommentaar(B.buiten.join('\u0000'));
if (buitenA !== buitenB) {
  const k = [...buitenA].findIndex((c, i) => c !== buitenB[i]);
  console.log('VERSCHIL buiten de scripts, bij:', JSON.stringify(buitenA.slice(Math.max(0, k - 40), k + 40)));
  fout++;
}
if (A.scripts.length !== B.scripts.length) { console.log('ander aantal scripts'); fout++; }
let n = 0;
A.scripts.forEach((s, i) => { const x = tokens(s), y = tokens(B.scripts[i] || ''); n += x.length;
  const k = x.findIndex((v, j) => v !== y[j]);
  if (k >= 0 || x.length !== y.length) { console.log('VERSCHIL in script', i, 'bij token', k, x[k], '<>', y[k]); fout++; } });
console.log(fout ? 'NIET gelijk' : `gelijk: ${A.scripts.length} scripts, ${n} tokens, alleen commentaar verschilt`);
process.exit(fout ? 1 : 0);
