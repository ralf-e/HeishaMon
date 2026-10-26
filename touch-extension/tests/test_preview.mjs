import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import assert from 'node:assert/strict';
import {fileURLToPath} from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const html=fs.readFileSync(path.join(root,'docs/Display_Vorschau.html'),'utf8');
const script=html.match(/<script>([\s\S]*?)<\/script>/)[1];
class Element {
  children=[];textContent='';dataset={};
  replaceChildren(){this.children=[]}
  append(...children){this.children.push(...children)}
}
const ids=Object.fromEntries(['title','mode','stats','body','pos','modeedit','reboot','rx'].map(k=>['#'+k,new Element()]));
const buttons=['prev','next','groups','home'].map(k=>{const e=new Element();e.dataset.nav=k;return e});
let writes=0,storageFail=false;const store=new Map();
const localStorage={getItem:k=>store.get(k)??null,setItem:(k,v)=>{if(storageFail)throw Error('write failure');store.set(k,v);writes++}};
const context=vm.createContext({localStorage,document:{
  querySelector:s=>ids[s],querySelectorAll:()=>buttons,createElement:()=>new Element()
},setTimeout,clearTimeout,setInterval,clearInterval});
vm.runInContext(script,context);
assert.equal(ids['#body'].children.length,20);
assert.deepEqual(ids['#body'].children.filter(r=>['HK1 Vorlauf Ist','HK1 Vorlauf Soll','HK2 Vorlauf Ist','HK2 Vorlauf Soll','Puffer'].includes(r.children[1].textContent)).map(r=>r.children[0].textContent),['46','36','42','37','43']);
assert.deepEqual(ids['#body'].children.filter(r=>['HK1 Vorlauf Ist','HK1 Vorlauf Soll','HK2 Vorlauf Ist','HK2 Vorlauf Soll','Puffer'].includes(r.children[1].textContent)).map(r=>r.children[1].textContent),['Puffer','HK1 Vorlauf Ist','HK1 Vorlauf Soll','HK2 Vorlauf Ist','HK2 Vorlauf Soll']);
vm.runInContext("nav('groups')",context);assert.equal(ids['#body'].children.length,6);
ids['#body'].children[1].onclick();assert.match(ids['#pos'].textContent,/144/);assert.equal(ids['#body'].children.length,20);assert.equal(ids['#body'].children[0].children[0].textContent,'0');
vm.runInContext("for(let i=0;i<30;i++)nav('next')",context);
assert.equal(ids['#pos'].textContent,'141-144 / 144');assert.equal(ids['#body'].children.length,4);
ids['#body'].children[0].onclick();assert.match(ids['#stats'].textContent,/Wertdetails/);
vm.runInContext("nav('prev')",context);assert.equal(ids['#pos'].textContent,'141-144 / 144');
vm.runInContext("nav('home')",context);assert.equal(ids['#body'].children.length,20);
assert.deepEqual(ids['#body'].children.filter(r=>['HK1 Vorlauf Ist','HK1 Vorlauf Soll','HK2 Vorlauf Ist','HK2 Vorlauf Soll','Puffer'].includes(r.children[1].textContent)).map(r=>r.children[0].textContent),['46','36','42','37','43']);
assert.deepEqual(ids['#body'].children.filter(r=>['HK1 Vorlauf Ist','HK1 Vorlauf Soll','HK2 Vorlauf Ist','HK2 Vorlauf Soll','Puffer'].includes(r.children[1].textContent)).map(r=>r.children[1].textContent),['Puffer','HK1 Vorlauf Ist','HK1 Vorlauf Soll','HK2 Vorlauf Ist','HK2 Vorlauf Soll']);
const overview=JSON.parse(fs.readFileSync(path.join(root,'docs/overview.json'),'utf8'));
const firmware=fs.readFileSync(path.join(root,'extension/hmx.cpp'),'utf8');
assert.deepEqual(overview.map(r=>r.status||r.id),[0,44,'timer',1,6,5,7,46,14,'hk1',36,42,'hk2',37,43,'ww',10,9,8,26]);
assert.deepEqual(firmware.match(/overviewKinds\[\] = \{([^}]*)\}/)[1].split(',').map(Number),overview.map(r=>({ww:1,hk1:2,hk2:3,timer:4}[r.status]||0)));
assert.deepEqual(ids['#body'].children.map(r=>r.children[1].textContent),overview.map(r=>r.label));
assert.deepEqual(firmware.match(/overviewIds\[\] = \{([^}]*)\}/)[1].split(',').map(Number),overview.map(r=>r.id));
ids['#modeedit'].onclick();assert.match(ids['#stats'].textContent,/Betriebsart/);
ids['#body'].children[1].onclick();assert.match(ids['#mode'].textContent,/WAHL: LISTEN ONLY/);assert.equal(writes,1);
ids['#reboot'].onclick();assert.match(ids['#mode'].textContent,/WAHL: LISTEN ONLY/);
vm.runInContext('selectMode(true)',context);assert.equal(writes,1);
vm.runInContext('selectMode(false)',context);assert.equal(writes,2);assert.match(ids['#mode'].textContent,/AUTO/);
storageFail=true;vm.runInContext('selectMode(true)',context);assert.match(ids['#mode'].textContent,/SPEICHERFEHLER/);
storageFail=false;vm.runInContext('selectMode(true)',context);assert.match(ids['#mode'].textContent,/WAHL/);
ids['#rx'].onclick({target:ids['#rx']});assert.match(ids['#stats'].textContent,/ALT/);
console.log('Preview navigation: overview, groups, 144 topics, last page, details, back, persistent touch mode, restart, storage failure, stale data OK');

vm.runInContext('modeMenu=false;deviceInfo=false;demoModelRaw="C2 D3 0B 35 65 B2 D3 0B 96 65";render()',context);
assert.equal(ids['#title'].textContent,'WH-MDC09J3E5');
ids['#title'].onclick();assert.match(ids['#body'].children[0].textContent,/WH-MDC09J3E5/);
assert.match(ids['#body'].children[0].textContent,/Kennung: C2 D3/);
vm.runInContext("nav('prev')",context);assert.equal(ids['#body'].children.length,20);
ids['#mode'].onclick();assert.match(ids['#stats'].textContent,/Betriebsart/);
vm.runInContext("nav('prev')",context);assert.equal(ids['#body'].children.length,20);
vm.runInContext('demoModelRaw="00 00 00 00 00 00 00 00 00 00";render()',context);
assert.equal(ids['#title'].textContent,'Modell unbekannt');
ids['#title'].onclick();assert.match(ids['#body'].children[0].textContent,/Keine sichere Modellzuordnung/);
vm.runInContext('deviceInfo=false;demoModelRaw="malformed";render()',context);
assert.equal(ids['#title'].textContent,'Modellkennung ungueltig');
vm.runInContext('demoModelRaw=modelCatalogue.rows[0].key;modelCatalogue.rows.push(modelCatalogue.rows[0]);render()',context);
assert.equal(ids['#title'].textContent,'Modell mehrdeutig');
vm.runInContext('modelCatalogue.rows.pop();render()',context);
console.log('Model header/info, return navigation, short mode click, unknown/invalid/ambiguous models OK');

vm.runInContext('deviceInfo=false;modeMenu=false;demoModelRaw="C2 D3 0B 35 65 B2 D3 0B 96 65";render()',context);
vm.runInContext("nav('groups')",context);ids['#body'].children[1].onclick();
vm.runInContext("nav('next')",context);assert.equal(ids['#pos'].textContent,'21-40 / 144');
ids['#body'].children[0].onclick();assert.match(ids['#stats'].textContent,/Wertdetails/);
ids['#title'].onclick();assert.match(ids['#body'].children[0].textContent,/HeishaMon: Local build/);
assert.match(ids['#body'].children[0].textContent,/Firmwarebasis: b3ef43691f21/);
vm.runInContext("nav('prev')",context);assert.match(ids['#stats'].textContent,/Wertdetails/);
vm.runInContext("nav('prev')",context);assert.equal(ids['#pos'].textContent,'21-40 / 144');
console.log('Device info returns to detail/list page; upstream and extension versions separate OK');
