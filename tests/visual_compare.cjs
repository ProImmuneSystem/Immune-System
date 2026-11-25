// Compares the actual built Jekyll files with the public WordPress website.
const { chromium } = require('playwright');
const fs = require('fs');
const paths = ['/', '/category/immune-cells/', '/2026/11/24/nk-cells/', '/2026/11/25/pga-poly-ingredients-pga-k-zinc-selenium/'];
(async () => {
  fs.mkdirSync('compare', {recursive:true});
  const browser = await chromium.launch({headless:true});
  for (const width of [1440,390]) {
    for (const [i,path] of paths.entries()) {
      for (const [name,base] of [['original','https://proimmunesystem.wordpress.com'],['mirror','http://127.0.0.1:8765/Immune-System']]) {
        const page = await browser.newPage({viewport:{width,height:900}, deviceScaleFactor:1});
        const response = await page.goto(base+path,{waitUntil:'domcontentloaded',timeout:60000});
        if (!response || response.status()>=400) throw Error(`${base+path} returned ${response && response.status()}`);
        await page.evaluate(() => { for (const img of document.images) img.loading = 'eager'; });
        await page.waitForTimeout(1200);
        await page.addStyleTag({content:'#marketingbar,.marketing-bar,#actionbar {display:none!important}'});
        await page.screenshot({path:`compare/${i}-${name}-${width}.png`,fullPage:true});
        await page.close();
      }
    }
  }
  await browser.close();
})().catch(err=>{console.error(err);process.exit(1)});
