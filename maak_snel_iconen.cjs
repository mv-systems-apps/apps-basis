#!/usr/bin/env node
/* Zet de iconen van de snelkoppelingen om van SVG naar PNG (192 x 192).
   Chrome op Android neemt voor snelkoppelingen alleen PNG; de SVG is de bron.
   Draaien:  node ../apps-basis/maak_snel_iconen.cjs <map van de app>
   Leest <map>/snelkoppelingen/*.svg en schrijft ernaast <naam>.png. */
const fs = require('fs'), path = require('path');
const { chromium } = require('playwright');
const map = path.resolve(process.argv[2] || '.'), dir = path.join(map, 'snelkoppelingen');
if (!fs.existsSync(dir)) { console.error('geen map snelkoppelingen in ' + map); process.exit(1); }
(async () => {
  const b = await chromium.launch(), p = await b.newPage({viewport: {width: 192, height: 192}});
  for (const f of fs.readdirSync(dir).filter(f => f.endsWith('.svg')).sort()) {
    await p.setContent(`<html><body style="margin:0">${fs.readFileSync(path.join(dir, f), 'utf8')}</body></html>`);
    const uit = path.join(dir, f.replace(/\.svg$/, '.png'));
    await (await p.$('svg')).screenshot({path: uit, omitBackground: false});
    console.log('  ' + path.relative(map, uit));
  }
  await b.close();
})();
