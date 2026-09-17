import {City,DT,PERIOD,payloads,applyAnswers} from './engine.mjs';
export class Run {
 constructor(config,request,{now=()=>performance.now(),onDecision=()=>{}}={}){
  this.config={seed:42,challenge:'destination',driver:'direct',timing:'realtime',maxDecisions:160,...config};this.city=new City(this.config);this.request=request;this.now=now;this.onDecision=onDecision;this.started=now();this.lastWall=this.started;this.accumulator=0;this.nextDecision=0;this.pending=false;this.decisions=[];this.frames=[this.city.snapshot()];this.active=true;
 }
 recordStep(){this.city.step();if(this.city.tick%2===0)this.frames.push(this.city.snapshot());}
 update(){
  if(!this.active)return;
  const now=this.now(),elapsed=(now-this.lastWall)/1000;this.lastWall=now;
  if(this.config.timing==='realtime'){
   this.accumulator+=elapsed;
   while(this.accumulator+1e-9>=DT&&this.city.status==='running'){this.recordStep();this.accumulator-=DT;}
  }
  if(this.city.status!=='running'){this.active=false;return;}
  if(!this.pending&&this.city.t+1e-8>=this.nextDecision){
   if(this.decisions.length>=this.config.maxDecisions){this.stop('decision_limit');return;}
   this.decide();
  }
 }
 async decide(){
  this.pending=true;const observed=this.city.t,wall=this.now();const before=this.city.snapshot();let result;
  try{result=await this.request(payloads(this.city.observation(),this.config.driver));}catch(e){result={valid:false,error:String(e),calls:[]};}
  // Catch up to wall time BEFORE installing the returned control.
  if(this.config.timing==='realtime'&&this.active)this.update();
  const row={index:this.decisions.length,observation_time:observed,application_time:this.city.t,observation_age_s:this.city.t-observed,wall_latency_ms:this.now()-wall,before,result,applied:false};
  if(this.active&&this.city.status==='running'){
   if(!result.valid)this.stop('api_error');
   else{
    try{const answers=Object.assign({},...result.calls.map(r=>Object.fromEntries(Object.entries(r.response.answers).map(([k,a])=>[k,a.choice]))));applyAnswers(this.city,this.config.driver,answers);row.answers=answers;row.applied=true;
     if(this.config.timing==='paused')for(let i=0;i<Math.round(PERIOD/DT)&&this.city.status==='running';i++)this.recordStep();
    }catch(e){row.error=String(e);this.stop('invalid_response');}
   }
  }
  row.after=this.city.snapshot();this.decisions.push(row);this.nextDecision=this.config.timing==='paused'?this.city.t:observed+PERIOD;this.pending=false;this.onDecision(row);
  if(this.city.status!=='running')this.active=false;
 }
 stop(reason='stopped'){this.active=false;if(this.city.status==='running')this.city.status=reason;}
 export(){return {schema:'jev-city-v1',config:this.config,wall_elapsed_ms:this.now()-this.started,final:this.city.snapshot(),events:this.city.events,decisions:this.decisions,frames:this.frames};}
}
export async function requestDecision(payloads){const r=await fetch('/api/decide',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({payloads})});if(!r.ok)throw Error((await r.json()).error||`HTTP ${r.status}`);return r.json();}
