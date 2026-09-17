'use strict';
const $=id=>document.getElementById(id), data=window.CLASSIC_DATA;
const names={unassisted:'Jev original',assisted:'Jev + exact route facts',verified:'Jev + route facts + verifier',oracle:'Exact planner only'};
let mode='replay',selected=null,frames=[],initial=null,index=0,playing=false,busy=false,timer=null,liveId=null,server=false;
function stop(){playing=false;clearTimeout(timer);}
function message(s){$('message').textContent=s;$('message').hidden=!s;}
function state(){return index?frames[index-1].state:initial;}
function render(){
 const s=state(),d=index?frames[index-1].decision:null,ctx=$('board').getContext('2d'),cell=60;
 ctx.fillStyle='#0d3328';ctx.fillRect(0,0,720,720);ctx.strokeStyle='#355646';
 for(let i=0;i<=12;i++){ctx.beginPath();ctx.moveTo(i*cell,0);ctx.lineTo(i*cell,720);ctx.moveTo(0,i*cell);ctx.lineTo(720,i*cell);ctx.stroke();}
 const square=(p,c,inset=5)=>{ctx.fillStyle=c;ctx.fillRect(p[0]*cell+inset,p[1]*cell+inset,cell-2*inset,cell-2*inset);};
 if(s){if(s.food)square(s.food,'#f18b78',10);[...s.snake].reverse().forEach((p,i)=>square(p,i===s.snake.length-1?'#c2ff68':'#99d849'));}
 $('board').setAttribute('aria-label',s?`Classic Snake, ${s.score} foods, ${s.moves} moves, ${s.status}`:'No game started');
 $('food').textContent=s?.score??'—';$('moves').textContent=s?.moves??'—';$('latency').textContent=d?.answer?Math.round(d.latency_ms)+' ms':d?'No call':'—';$('tokens').textContent=d?.usage.input_tokens??'—';
 $('board-status').textContent=s?.status.replaceAll('_',' ')||'Ready';$('arena-label').textContent='Classic · solid boundaries';$('frame').textContent=`${index} / ${frames.length} frames`;
 $('seek').max=frames.length;$('seek').value=index;$('seek').disabled=mode==='live'||busy;
 $('play').querySelector('span').textContent=playing?'Pause':busy?'Thinking…':mode==='live'?'Start live':'Play';$('play').disabled=busy&&!playing;
 $('step').disabled=busy||(mode==='replay'&&index>=frames.length)||(mode==='live'&&s&&s.status!=='playing');
 for(const id of ['controller','run','live-seed','live-mode','replay-mode'])$(id).disabled=busy;
 $('decision-source').textContent=d?(d.answer?'Jev proposal: '+d.proposal:'Code-only move'):'No decision yet';
 for(const el of document.querySelectorAll('[data-action]')){const a=el.dataset.action,p=d?.answer?.probabilities?.[a];el.classList.toggle('selected',d?.action===a);el.querySelector('span').textContent=d?`${p===undefined?'No model':Math.round(p*100)+'%'} · route ${d.oracle.costs[a]??'invalid'}`:'—';}
 $('decision-note').textContent=d?`Executed ${d.action}. ${d.overridden?'CODE OVERRIDE. ':''}${d.usage.input_tokens} input / ${d.usage.output_tokens} output tokens. Planner ${d.planner_ms.toFixed(1)} ms. Shortest actions: ${d.oracle.optimal.join(', ')}.`:'Advance to inspect the proposal, exact route lengths and executed action.';
 $('download').disabled=!s;
}
function load(){stop();selected=data?.runs.find(r=>r.id===$('run').value)||null;initial=selected?.initial;frames=selected?.frames||[];index=0;liveId=null;
 if(selected){$('run-note').textContent=`${names[selected.profile]} · seed ${selected.seed} · ${selected.final.score} foods in ${selected.final.moves} moves · ${selected.final.status.replaceAll('_',' ')}. Held-out study; eight-food cap.`;history.replaceState(null,'','?profile='+selected.profile+'&run='+selected.id);}render();}
function populate(){stop();const runs=data?.runs.filter(r=>r.profile===$('controller').value)||[];$('run').replaceChildren(...runs.map(r=>{const o=document.createElement('option');o.value=r.id;o.textContent=`Seed ${r.seed} · ${r.final.score} foods`;return o;}));if(mode==='replay')load();else{frames=[];initial=null;index=0;liveId=null;render();}}
function setMode(next){if(busy)return;stop();mode=next;frames=[];initial=null;index=0;liveId=null;
 for(const m of ['replay','live']){$(m+'-mode').classList.toggle('active',mode===m);$(m+'-mode').setAttribute('aria-pressed',mode===m);}
 $('run-label').hidden=mode==='live';$('seed-label').hidden=mode!=='live';$('speed').disabled=mode==='live';$('best').hidden=mode==='live';$('mode-caption').textContent=mode==='live'?'Fresh API decisions, one move at a time.':'Frozen held-out games.';
 if(mode==='replay'){message('');load();}else{message(server?'Press Start live. Model profiles make paid API calls.':'Run locally: python -m snake_demo.research.server');$('run-note').textContent='Fresh live game; excluded from the research totals.';render();}}
async function api(path,body){const r=await fetch(path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});const v=await r.json();if(!r.ok)throw Error(v.error||'Request failed');return v;}
async function step(){if(busy)return;if(mode==='replay'){index=Math.min(index+1,frames.length);render();return;}busy=true;render();try{if(!server)throw Error('Live mode requires the local research server on port 8766.');if(!liveId){const seed=Number($('live-seed').value);if(!Number.isInteger(seed)||seed<0||seed>=2**32)throw Error('Invalid seed');const r=await api('/api/start',{profile:$('controller').value,seed});liveId=r.id;initial=r.state;frames=[];index=0;}const r=await api('/api/step',{id:liveId,moves:state().moves});frames.push(r);index++;message('');}catch(e){stop();message(e.message);if(initial){frames.push({state:{...state(),status:'api_error'},error:e.message});index=frames.length;}}finally{busy=false;render();}}
async function tick(){if(!playing)return;await step();if(!playing)return;if((mode==='replay'&&index>=frames.length)||(mode==='live'&&state()?.status!=='playing')){stop();render();return;}const d=index?frames[index-1].decision:null;timer=setTimeout(tick,mode==='live'?0:$('speed').value==='recorded'?Math.max(40,d?.latency_ms||80):Number($('speed').value));}
$('play').onclick=()=>{if(playing){stop();render();return;}if(busy)return;if(mode==='replay'&&index>=frames.length)index=0;if(mode==='live'&&state()?.status!=='playing'){liveId=null;frames=[];initial=null;index=0;}playing=true;tick();};
$('step').onclick=()=>{stop();step();};$('seek').oninput=()=>{stop();index=Number($('seek').value);render();};$('controller').onchange=populate;$('run').onchange=load;
$('replay-mode').onclick=()=>setMode('replay');$('live-mode').onclick=()=>setMode('live');
$('best').onclick=()=>{const r=data.runs.filter(r=>r.profile===$('controller').value).sort((a,b)=>b.final.score-a.final.score||a.final.moves-b.final.moves)[0];if(r){$('run').value=r.id;load();message('Selected highest score, then fewest moves. This is a selected example.');}};
$('download').onclick=()=>{const b=new Blob([JSON.stringify({profile:$('controller').value,initial,frames},null,2)],{type:'application/json'});const url=URL.createObjectURL(b);const a=document.createElement('a');a.href=url;a.download='classic-'+(selected?.id||'live')+'.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);};
if(data){for(const [profile,m]of Object.entries(data.metrics)){const row=document.createElement('tr');for(const text of [names[profile],`${m.successes}/${m.episodes}`,m.stats.valid_calls?`${m.stats.model_shortest}/${m.stats.valid_calls}`:'No model',String(m.stats.overrides||0)]){const td=document.createElement('td');td.textContent=text;row.append(td);}$('result-rows').append(row);}$('study-count').textContent='64 held-out games. Shortest means current food, not global multi-food optimality. See report for uncertainty and assistance.';const params=new URLSearchParams(location.search);if(names[params.get('profile')])$('controller').value=params.get('profile');populate();if([...$('run').options].some(o=>o.value===params.get('run'))){$('run').value=params.get('run');load();}}else{message('Research dataset is not yet built.');render();}
if(['localhost','127.0.0.1'].includes(location.hostname)&&location.port==='8766')fetch('/api/config').then(r=>r.json()).then(()=>{server=true;}).catch(()=>{});
