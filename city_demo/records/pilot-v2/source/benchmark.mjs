import {mkdir,writeFile,readFile} from 'node:fs/promises';import {createHash} from 'node:crypto';import {Run} from './runner.mjs';
const out=process.argv[2];if(!out)throw Error('Usage: node city_demo/benchmark.mjs city_demo/records/pilot-v1');
const readiness=await fetch('http://127.0.0.1:8768/api/status');if(!readiness.ok||!(await readiness.json()).live)throw Error('Live proxy unavailable; no experiment started');
await mkdir(out,{recursive:false});const hashes={};for(const name of ['engine.mjs','runner.mjs','PROTOCOL.md','server.py','benchmark.mjs'])hashes[name]=createHash('sha256').update(await readFile(new URL(name,import.meta.url))).digest('hex');
const protocol={started:new Date().toISOString(),seed:42,hashes,episodes:[]};
for(const challenge of ['destination','explore','delivery'])for(const driver of ['direct','maneuver'])for(const timing of ['paused','realtime'])protocol.episodes.push({seed:42,challenge,driver,timing,maxDecisions:160});
await writeFile(out+'/manifest.json',JSON.stringify(protocol,null,2));
const summary=[];for(const config of protocol.episodes){
 const name=`${config.challenge}-${config.driver}-${config.timing}`;console.log('START',name);
 const run=new Run(config,async payloads=>{const r=await fetch('http://127.0.0.1:8768/api/decide',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({payloads})});if(!r.ok)throw Error('Proxy HTTP '+r.status);return r.json();});
 await new Promise(resolve=>{const timer=setInterval(()=>{run.update();if(!run.active&&!run.pending){clearInterval(timer);resolve();}},10);});
 const data=run.export();await writeFile(`${out}/${name}.json`,JSON.stringify(data));const row={...config,...data.final,decisions:data.decisions.length,calls:data.decisions.reduce((n,d)=>n+d.result.calls.length,0)};summary.push(row);await writeFile(out+'/summary.json',JSON.stringify(summary,null,2));console.log('END',name,row.status,'distance',row.distance.toFixed(1),'decisions',row.decisions);
}
