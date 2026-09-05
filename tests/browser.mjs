// Optional QA: point PUPPETEER_MODULE at puppeteer-core and CHROME_PATH at Chrome.
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import {pathToFileURL} from 'node:url';
const {default:puppeteer}=await import(pathToFileURL(process.env.PUPPETEER_MODULE).href);
const base=process.env.PREVIEW_URL||'http://127.0.0.1:8788';
const browser=await puppeteer.launch({executablePath:process.env.CHROME_PATH,headless:true,args:['--no-proxy-server']});
const results=[];
await fs.mkdir('.local/qa',{recursive:true});
try{
  for(const width of [1440,390]){
    const page=await browser.newPage();await page.setCacheEnabled(false);const errors=[];const external=[];
    page.on('pageerror',e=>errors.push(e.message));
    page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});
    page.on('request',r=>{if(!r.url().startsWith(base)&&!r.url().startsWith('data:'))external.push(r.url());});
    await page.setViewport({width,height:1000});
    assert.equal((await page.goto(base,{waitUntil:'networkidle0'})).status(),200);
    // Fixed authored DOM probes only. No contributed text is executed as code.
    assert.equal(await page.$eval('.filters',e=>e.hidden),false,'Search UI must be enabled');
    const total=await page.$$eval('[data-workflow]',xs=>xs.length);
    await page.type('#search','documentation');
    assert.equal(await page.$$eval('[data-workflow]:not([hidden])',xs=>xs.length),1);
    await page.$eval('#search',e=>{e.value='no-such-workflow';e.dispatchEvent(new Event('input'));});
    assert.equal(await page.$eval('#empty',e=>e.hidden),false);
    await page.$eval('#search',e=>{e.value='';e.dispatchEvent(new Event('input'));});
    await page.select('#category','research');
    assert.equal(await page.$$eval('[data-workflow]:not([hidden])',xs=>xs.length),1);
    await page.select('#category','');
    assert.equal(await page.$$eval('[data-workflow]:not([hidden])',xs=>xs.length),total);
    const state=await page.evaluate(()=>({overflow:document.documentElement.scrollWidth>innerWidth,font:getComputedStyle(document.body).fontFamily,background:getComputedStyle(document.body).backgroundColor,h1:document.querySelector('h1').innerText}));
    assert.equal(state.overflow,false);assert.equal(state.background,'rgb(238, 241, 232)');
    await page.screenshot({path:'.local/qa/home-'+width+'.png',fullPage:true});
    await page.goto(base+'/workflows/release-notes-digest/',{waitUntil:'networkidle0'});
    assert.equal(await page.$eval('.copy-tools',e=>e.hidden),false,'Copy skill controls must be enabled');
    await page.click('[data-copy]');
    await page.waitForFunction(()=>document.querySelector('.copy-status').textContent.length>0);
    assert.match(await page.$eval('.copy-status',e=>e.textContent),/Copied/);
    // Denied clipboard access is deliberately injected to exercise the fallback.
    await page.evaluate(()=>Object.defineProperty(navigator,'clipboard',{configurable:true,value:{writeText:async()=>{throw new Error('denied');}}}));
    await page.click('[data-copy]');
    await page.waitForFunction(()=>document.querySelector('.copy-status').textContent.includes('Select'));
    assert.equal(await page.$eval('#skill-text',e=>e.closest('details').open),true);
    assert.equal(await page.$eval('#skill-text',e=>e.selectionEnd-e.selectionStart===e.value.length),true);
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
    await page.screenshot({path:'.local/qa/workflow-'+width+'.png',fullPage:true});
    assert.deepEqual(errors,[]);assert.deepEqual(external,[]);
    results.push({width,workflow_count:total,search:'pass',...state,errors,external});
    await page.close();
  }
  // Sweep every generated reading route, also without JavaScript.
  const catalog=await (await fetch(base+'/catalog.json')).json();
  for(const route of ['/', '/contribute/', ...catalog.workflows.map(w=>w.page_url), '/404.html']){
    const page=await browser.newPage();await page.setCacheEnabled(false);
    const violations=[];
    page.on('console',m=>{if(m.type()==='error')violations.push(m.text());});
    page.on('pageerror',e=>violations.push(e.message));
    const response=await page.goto(base+route,{waitUntil:'networkidle0'});
    assert.equal(response.status(),200);
    if(process.env.REQUIRE_RELEASE_HEADERS){
      assert.match(response.headers()['content-security-policy'],/frame-ancestors 'none'/);
      assert.equal(response.headers()['x-content-type-options'],'nosniff');
    }
    assert.equal(await page.$$eval('h1',xs=>xs.length),1);
    assert.deepEqual(violations,[]);
    await page.setJavaScriptEnabled(false);
    await page.reload({waitUntil:'networkidle0'});
    assert.equal(await page.$$eval('h1',xs=>xs.length),1);
    assert.ok((await page.$eval('main',e=>e.textContent)).trim().length>20);
    await page.close();
  }
  await fs.writeFile('.local/qa/browser.json',JSON.stringify(results,null,2)+'\n');
  console.log(JSON.stringify(results,null,2));
}finally{await browser.close();}
