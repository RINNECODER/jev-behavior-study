'use strict';
const $=id=>document.getElementById(id);
const data=window.SNAKE_DATA;
let mode='replay',selected=null,index=0,playing=false,timer=null,liveId=null,busy=false,liveFrames=[],liveInitial=null,server=false,hasKey=false,loadVersion=0;
const labels={jev_direct:'Jev direct',jev_guarded:'Jev guarded',baseline:'Pathfinding baseline'};
const endings={playing:'In progress',target_reached:'Eight-food target reached',board_filled:'Board filled',step_limit:'200-move limit',no_food_limit:'50 moves without food',wall_collision:'Wall collision',body_collision:'Body collision',obstacle_collision:'Obstacle collision',api_error:'API error · game interrupted'};
function outcome(s){if(!s)return '';if(s.status==='target_reached')return `${s.target}-food target reached`;if(s.status==='step_limit')return `${s.max_steps}-move limit`;return endings[s.status]||s.status;}
function message(text){$('message').textContent=text||'';$('message').hidden=!text;}
function stop(){playing=false;clearTimeout(timer);$('play').querySelector('span').textContent=mode==='live'?'Start live':'Play';}
function frames(){return mode==='live'?liveFrames:(selected?.frames||[]);}
function initial(){return mode==='live'?liveInitial:selected?.initial;}
function state(){const base=initial();return base?{...base,...(index?frames()[index-1]?.state:{})}:null;}
function draw(s){
 const canvas=$('board'),ctx=canvas.getContext('2d'),size=canvas.width,cell=size/12;
 ctx.fillStyle='#0d3328';ctx.fillRect(0,0,size,size);
 ctx.strokeStyle='#355646';ctx.lineWidth=1;
 for(let i=0;i<=12;i++){ctx.beginPath();ctx.moveTo(i*cell,0);ctx.lineTo(i*cell,size);ctx.stroke();ctx.beginPath();ctx.moveTo(0,i*cell);ctx.lineTo(size,i*cell);ctx.stroke();}
 if(!s)return;
 const square=(p,color,inset=5)=>{ctx.fillStyle=color;ctx.beginPath();ctx.roundRect(p[0]*cell+inset,p[1]*cell+inset,cell-inset*2,cell-inset*2,5);ctx.fill();};
 for(const p of s.obstacles){square(p,'#466156',4);ctx.strokeStyle='#6a8174';ctx.lineWidth=2;ctx.beginPath();ctx.moveTo(p[0]*cell+19,p[1]*cell+19);ctx.lineTo((p[0]+1)*cell-19,(p[1]+1)*cell-19);ctx.moveTo((p[0]+1)*cell-19,p[1]*cell+19);ctx.lineTo(p[0]*cell+19,(p[1]+1)*cell-19);ctx.stroke();}
 if(s.food)square(s.food,'#f18b78',9);
 [...s.snake].reverse().forEach((p,i)=>square(p,i===s.snake.length-1?'#c2ff68':'#99d849',5));
 const h=s.snake[0],cx=h[0]*cell+cell/2,cy=h[1]*cell+cell/2,angle={north:0,east:Math.PI/2,south:Math.PI,west:-Math.PI/2}[s.heading];
 ctx.save();ctx.translate(cx,cy);ctx.rotate(angle);ctx.fillStyle='#1c3a20';ctx.beginPath();ctx.arc(-8,-9,3.2,0,7);ctx.arc(8,-9,3.2,0,7);ctx.fill();ctx.restore();
 $('board').setAttribute('aria-label',`Snake at ${h[0]}, ${h[1]}, facing ${s.heading}. Food collected ${s.score}. ${outcome(s)}.`);
}
function render(){
 const s=state(),entry=index?frames()[index-1]:null,d=entry?.decision;
 draw(s);$('food').textContent=s?.score??'—';$('moves').textContent=s?.moves??'—';$('frame').textContent=`${index} / ${frames().length} frames`;
 $('seek').max=frames().length;$('seek').value=index;$('seek').disabled=mode==='live'||busy;
 $('latency').textContent=d?.source==='jev'?`${Math.round(d.latency_ms)} ms`:d?'No call':'—';
 $('tokens').textContent=d?d.usage.input_tokens.toLocaleString():'—';
 $('arena-label').textContent=s?`${data?.levels[s.level]?.label||s.level} · ${s.wrap?'wrapping edges':'solid boundaries'}`:'Recorded game';
 $('board-status').textContent=s?outcome(s):'No game loaded';
 $('play').querySelector('span').textContent=playing?'Pause':busy?'Thinking…':mode==='live'?(liveId&&s?.status==='playing'?'Resume':'Start live'):'Play';
 $('play').disabled=(busy&&!playing)||(!s&&mode==='replay');$('step').disabled=busy||(!s&&mode==='replay')||(mode==='replay'&&index>=frames().length)||(mode==='live'&&s&&s.status!=='playing');
 $('decision-source').textContent=!d?'No decision yet':d.source==='jev'?'Recorded Jev response':d.source==='forced_safe'?'Code: only safe move':d.source==='baseline'?'Deterministic baseline':'No safe move remains';
 if(mode==='live'&&d?.source==='jev')$('decision-source').textContent='Live Jev response';
 for(const el of document.querySelectorAll('[data-action]')){const a=el.dataset.action,p=d?.probabilities?.[a];el.classList.toggle('selected',d?.action===a);el.querySelector('span').textContent=p!==undefined?`${(p*100).toFixed(0)}%`:d?.action===a?'Selected':'—';}
 $('decision-note').textContent=entry?.error?`Interrupted: ${entry.error}. No fabricated move.`:d?`${d.action.toUpperCase()} · ${d.source==='jev'?`${d.usage.input_tokens} input / ${d.usage.output_tokens} output tokens · confidence ${Number(d.confidence).toFixed(2)}`:d.source==='forced_safe'?'One legal option; no API request':d.source==='baseline'?'Breadth-first pathfinding; no API request':'All next moves collide'}`:'Advance the replay to inspect a decision.';
 if(s)document.querySelector('#food + span').textContent=`Food / ${s.target}`;
 $('download').disabled=!s;
}
function populateRuns(){
 stop();liveId=null;liveInitial=null;liveFrames=[];index=0;loadVersion++;
 const matches=data?.runs.filter(r=>r.level===$('difficulty').value&&r.controller===$('controller').value)||[];
 $('run').replaceChildren(...matches.map(r=>{const o=document.createElement('option');o.value=r.id;o.textContent=`Seed ${r.seed} · ${r.score} food${r.phase==='endurance'?' · extended':''}`;return o;}));
 selected=matches[0]||null;
 if(mode==='replay')showRun();else{message(server?'Live games use the same rules. Jev controllers make paid API calls.':'Start the local server to play live: python -m snake_demo.server');render();}
}
function showRun(){stop();index=0;selected=data?.runs.find(r=>r.id===$('run').value)||selected;
 if(selected){$('run-note').textContent=`Seed ${selected.seed} · ${selected.score} food in ${selected.moves} moves · ${outcome(selected.final)}. Target ${selected.initial.target}, limit ${selected.initial.max_steps} moves. ${selected.forced_moves} forced safe moves.${selected.phase==='endurance'?' Selected endurance run; excluded from main averages.':''}`;message(null);const q=new URLSearchParams({level:selected.level,controller:selected.controller,run:selected.id});history.replaceState(null,'','?'+q);}else message('No recorded games match these settings.');render();}
function replayTick(){if(!playing)return;if(index>=frames().length){stop();render();return;}index++;render();
 const delay=$('speed').value==='recorded'?Math.max(40,frames()[index-1]?.decision?.latency_ms||80):Number($('speed').value);timer=setTimeout(replayTick,delay);}
async function api(path,body){const r=await fetch(path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});let result;try{result=await r.json();}catch{throw new Error('Local live server is unavailable. Saved replays still work.');}if(!r.ok)throw new Error(result.error||'Request failed');return result;}
async function startLive(){
 if(!server)throw new Error('Live mode needs the local server: python -m snake_demo.server');
 if($('controller').value!=='baseline'&&!hasKey)throw new Error('Set TYPESAFE_API_KEY on the local server, then restart it.');
 const seed=Number($('live-seed').value);if(!Number.isInteger(seed)||seed<0||seed>=2**32)throw new Error('Use an integer seed between 0 and 4294967295.');
 const r=await api('/api/start',{level:$('difficulty').value,controller:$('controller').value,seed});liveId=r.id;liveInitial=r.state;liveFrames=[];index=0;
 $('run-note').textContent=`Live seed ${seed} · API calls are logged locally. Pause stops requesting new moves.`;message(null);
}
async function liveStep(){
 if(busy)return;busy=true;lockSelectors(true);render();
 try{
  if(!liveId)await startLive();
  if(state().status!=='playing'){stop();return;}
  const r=await api('/api/step',{id:liveId,moves:state().moves});liveFrames.push({state:r.state,decision:r.decision});index=liveFrames.length;
  if(r.state.status!=='playing')stop();
 }catch(e){message(e.message);stop();if(liveInitial){liveFrames.push({state:{...state(),status:'api_error'},error:e.message});index=liveFrames.length;}liveId=null;}
 finally{busy=false;lockSelectors(false);render();}
 if(playing)timer=setTimeout(liveStep,60);
}
function lockSelectors(lock){for(const id of ['difficulty','controller','run','live-seed','replay-mode','live-mode'])$(id).disabled=lock;}
function setMode(next){if(busy)return;stop();mode=next;index=0;liveId=null;liveInitial=null;liveFrames=[];
 $('replay-mode').classList.toggle('active',mode==='replay');$('live-mode').classList.toggle('active',mode==='live');$('replay-mode').setAttribute('aria-pressed',mode==='replay');$('live-mode').setAttribute('aria-pressed',mode==='live');
 $('run-label').hidden=mode==='live';$('seed-label').hidden=mode!=='live';$('best').hidden=mode==='live';$('speed').disabled=mode==='live';
 $('mode-caption').textContent=mode==='live'?'One API decision at a time.':'Load a run and watch every move.';
 if(mode==='replay')showRun();else{message(server?'Press Start live to begin. Jev controllers make paid API calls.':'For live play, run: python -m snake_demo.server');$('run-note').textContent='Live games are separate from the frozen benchmark.';render();}
}
$('difficulty').addEventListener('change',populateRuns);$('controller').addEventListener('change',populateRuns);$('run').addEventListener('change',showRun);
$('replay-mode').onclick=()=>setMode('replay');$('live-mode').onclick=()=>setMode('live');
$('play').onclick=async()=>{if(playing){stop();render();return;}if(busy)return;if(mode==='replay'){if(index>=frames().length)index=0;playing=true;replayTick();}else{if(state()?.status!=='playing'){liveId=null;liveInitial=null;liveFrames=[];index=0;}playing=true;await liveStep();}};
$('step').onclick=()=>{stop();if(mode==='replay'){index=Math.min(index+1,frames().length);render();}else liveStep();};
$('seek').oninput=()=>{stop();index=Number($('seek').value);render();};
$('best').onclick=()=>{const matches=data.runs.filter(r=>r.level===$('difficulty').value&&r.controller===$('controller').value).sort((a,b)=>b.score-a.score||a.moves-b.moves);if(!matches.length)return;$('run').value=matches[0].id;showRun();message('Selected best recorded score for this difficulty/controller; ties use fewer moves. This is not a typical-performance claim. Selected endurance runs, when available, have higher caps.');};
$('download').onclick=()=>{const payload=mode==='replay'?selected:{id:'live',controller:$('controller').value,initial:liveInitial,frames:liveFrames};if(!payload)return;const url=URL.createObjectURL(new Blob([JSON.stringify(payload,null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download=(payload.id||'snake-replay')+'.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);};
if(data){
 for(const [level,definition]of Object.entries(data.levels)){
  const tr=document.createElement('tr'),td=document.createElement('td'),b=document.createElement('button');b.className='level-button';b.textContent=definition.label;b.onclick=()=>{setMode('replay');$('difficulty').value=level;populateRuns();$('board').scrollIntoView({behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth',block:'center'});};td.append(b);tr.append(td);
  for(const c of ['jev_direct','jev_guarded','baseline']){const cell=document.createElement('td'),m=data.metrics.find(m=>m.level===level&&m.controller===c);if(m){cell.textContent=m.mean_food.toFixed(2);const small=document.createElement('small');small.textContent=`${m.target_successes}/${m.episodes} reached ${data.target}`;cell.append(small);}else cell.textContent='—';tr.append(cell);}$('result-rows').append(tr);
 }
 $('study-count').textContent=`${data.pilot?'PILOT ONLY · ':''}${data.episodes} main games${data.extended_episodes?' + '+data.extended_episodes+' selected extended':''} · ${(data.model_calls+(data.extended_model_calls||0)).toLocaleString()} recorded Jev decisions · ${data.api_error_episodes} interrupted games`;
 $('results-caption').textContent=`Mean food collected · ${data.target}-food target`;
 document.querySelector('#food + span').textContent=`Food / ${data.target}`;
 const params=new URLSearchParams(location.search);if(data.levels[params.get('level')])$('difficulty').value=params.get('level');if(labels[params.get('controller')])$('controller').value=params.get('controller');
 populateRuns();if(data.runs.some(r=>r.id===params.get('run')&&r.level===$('difficulty').value&&r.controller===$('controller').value)){$('run').value=params.get('run');showRun();}
}else{message('Recorded dataset is missing. Generate it with python -m snake_demo.analyze <run-directory>.');draw(null);$('play').disabled=true;$('step').disabled=true;}
if(['127.0.0.1','localhost'].includes(location.hostname))fetch('/api/config').then(r=>r.ok?r.json():null).then(config=>{server=!!config;hasKey=!!config?.live;}).catch(()=>{});
