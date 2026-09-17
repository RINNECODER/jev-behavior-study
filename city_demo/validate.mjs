// Independent offline replay: re-execute recorded raw model choices, never call the API.
import {readFile,readdir} from 'node:fs/promises';import assert from 'node:assert/strict';
const root=new URL('./',import.meta.url);let episodes=0,calls=0;
for(const version of ['pilot-v1','pilot-v2']){
 let names;try{names=await readdir(new URL(`records/${version}/`,root));}catch{continue;}
 const engine=await import(`./records/${version}/source/engine.mjs`);
 for(const name of names.filter(n=>/^(destination|explore|delivery)-.*\.json$/.test(n))){
  const record=JSON.parse(await readFile(new URL(`records/${version}/${name}`,root),'utf8'));const city=new engine.City(record.config);
  for(const decision of record.decisions){
   for(const call of decision.result.calls){assert.equal(Object.keys(call.payload.questions).length,1);if(call.valid){assert.equal(call.response.model,'jev-1.13.0');for(const k of ['input_tokens','output_tokens'])assert(Number.isInteger(call.response.usage[k])&&call.response.usage[k]>=0);}calls++;}
   const tick=Math.round(decision.application_time/engine.DT);while(city.tick<tick&&city.status==='running')city.step();
   if(decision.applied){assert.equal(city.status,'running');const raw=Object.assign({},...decision.result.calls.map(c=>Object.fromEntries(Object.entries(c.response.answers).map(([k,a])=>[k,a.choice]))));assert.deepEqual(raw,decision.answers);engine.applyAnswers(city,record.config.driver,raw);}
  }
  while(city.tick<Math.round(record.final.t/engine.DT)&&city.status==='running')city.step();
  if(city.status==='running')city.status=record.final.status;
  assert.deepEqual(city.snapshot(),record.final,name);assert.deepEqual(city.events,record.events,name);episodes++;
 }
}
console.log(`Verified ${episodes} complete traces and ${calls} per-question call records; final physics and events reproduce exactly.`);
