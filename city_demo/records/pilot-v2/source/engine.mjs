// One deterministic fixed-step simulator, shared by browser and Node benchmark.
export const DT=.05, PERIOD=.6, ROADS=[-80,0,80], LIMIT=110;
export const clamp=(v,a,b)=>Math.max(a,Math.min(b,v));
export const wrap=a=>Math.atan2(Math.sin(a),Math.cos(a));
export const unit=a=>({x:Math.sin(a),z:-Math.cos(a)});
export function random(seed){let n=seed>>>0;return()=>{n=(Math.imul(n,1664525)+1013904223)>>>0;return n/4294967296;};}
const nearest=v=>ROADS.reduce((a,b)=>Math.abs(v-b)<Math.abs(v-a)?b:a);
export const cardinal=a=>Math.round(a/(Math.PI/2)+4)%4;
export const HEADINGS=['north','east','south','west'];
export function signal(t,x,z,axis){const p=((t+(x+z)/8)%24+24)%24;return (axis==='z'?p<10:p>=12&&p<22)?'green':'red';}
export class City {
 constructor({seed=42,challenge='destination',duration=90}={}){
  this.seed=seed;this.challenge=challenge;this.duration=duration;this.t=0;this.tick=0;this.car={x:3.5,z:60,heading:0,speed:0};this.action={steer:0,throttle:0,brake:0};this.status='running';this.events=[];this.distance=0;this.collisions=0;this.redLights=0;this.speedingSeconds=0;this.visited=new Set();this.stops=0;this.lastIntersection=null;this.executorHeading=0;this.turnTarget=null;
  const r=random(seed);this.traffic=Array.from({length:6},(_,i)=>({id:i,x:i%2? -95+r()*190:ROADS[i%3]+3.5,z:i%2?ROADS[i%3]+3.5:-95+r()*190,heading:i%2?Math.PI/2:0,speed:3+r()*2}));
  // Matched seeds alter traffic, not objective difficulty.
  this.goals=challenge==='delivery'?[{x:3.5,z:-55},{x:58,z:-76.5},{x:76.5,z:55}]:[{x:58,z:3.5}];
 }
 setAction(a){for(const k of ['steer','throttle','brake'])if(!Number.isFinite(a[k]))throw Error('Non-finite control');this.action={steer:clamp(a.steer,-1,1),throttle:clamp(a.throttle,0,1),brake:clamp(a.brake,0,1)};this.maneuver=null;}
 setManeuver(a){if(!['north','east','south','west','stop'].includes(a.direction)||![0,4,8].includes(a.speed))throw Error('Invalid maneuver');this.maneuver=a;}
 assisted(){
  const c=this.car, j={x:nearest(c.x),z:nearest(c.z)}, d=Math.hypot(c.x-j.x,c.z-j.z);
  if(this.turnTarget&&Math.abs(wrap(c.heading-this.turnTarget.heading))<.12){this.executorHeading=this.turnTarget.heading;this.turnTarget=null;}
  const desired=HEADINGS.indexOf(this.maneuver.direction)*Math.PI/2;
  if(!this.turnTarget&&this.maneuver.direction!=='stop'&&d<9&&Math.abs(wrap(desired-this.executorHeading))>.2){this.turnTarget={heading:desired,x:j.x,z:j.z};}
  const h=this.turnTarget?.heading??this.executorHeading, f=unit(h), right=unit(h+Math.PI/2);
  let target;
  if(this.turnTarget)target={x:this.turnTarget.x+f.x*18+right.x*3.5,z:this.turnTarget.z+f.z*18+right.z*3.5};
  else if(Math.abs(f.z)>.5)target={x:nearest(c.x)+right.x*3.5,z:c.z+f.z*12};
  else target={x:c.x+f.x*12,z:nearest(c.z)+right.z*3.5};
  const error=wrap(Math.atan2(target.x-c.x,-(target.z-c.z))-c.heading);
  const speed=this.maneuver.direction==='stop'?0:this.maneuver.speed;
  return {steer:clamp(2*error,-1,1),throttle:clamp((speed-c.speed)*.6,0,1),brake:clamp((c.speed-speed)*.6,0,1)};
 }
 step(){
  if(this.status!=='running')return;
  const c=this.car,old={...c};this.action=this.maneuver?this.assisted():this.action;const a=this.action;
  c.speed=clamp(c.speed+(a.throttle*3-a.brake*7-.12*c.speed)*DT,0,14);
  c.heading=wrap(c.heading+c.speed/2.7*Math.tan(a.steer*.5)*DT);const f=unit(c.heading);c.x+=f.x*c.speed*DT;c.z+=f.z*c.speed*DT;
  const trafficBefore=this.traffic.map(o=>({...o}));
  for(const other of this.traffic){
   const u=unit(other.heading),j={x:nearest(other.x),z:nearest(other.z)},axis=Math.abs(u.z)>.5?'z':'x';
   const dist=(j.x-other.x)*u.x+(j.z-other.z)*u.z;
   other.cruiseSpeed??=other.speed;
   let target=other.cruiseSpeed;
   // Environment traffic reacts to a leader, including the ego car. This never changes ego controls.
   for(const leader of [...trafficBefore,old]){
    if(leader.id===other.id)continue;
    const dx=leader.x-other.x,dz=leader.z-other.z,ahead=dx*u.x+dz*u.z,lateral=Math.abs(dx*u.z-dz*u.x);
    if(ahead>0&&ahead<20&&lateral<2.5){const speedAlong=Math.max(0,leader.speed*Math.cos(leader.heading-other.heading));target=Math.min(target,Math.max(0,speedAlong+(ahead-7)*.7));}
   }
   if(dist>7&&dist<22&&signal(this.t,j.x,j.z,axis)==='red')target=Math.min(target,Math.max(0,(dist-10)*.8));
   other.speed=clamp(other.speed+clamp(target-other.speed,-7*DT,2*DT),0,other.cruiseSpeed);
   other.x+=u.x*other.speed*DT;other.z+=u.z*other.speed*DT;
   if(other.x>108)other.x=-108;if(other.z< -108)other.z=108;
  }
  this.tick++;this.t=this.tick*DT;this.distance+=Math.hypot(c.x-old.x,c.z-old.z);if(c.speed>10)this.speedingSeconds+=DT;
  const j={x:nearest(c.x),z:nearest(c.z)},inJ=Math.abs(c.x-j.x)<7&&Math.abs(c.z-j.z)<7,key=`${j.x},${j.z}`;
  if(inJ&&this.lastIntersection!==key){this.visited.add(key);const axis=Math.abs(f.z)>.5?'z':'x';if(signal(this.t,j.x,j.z,axis)==='red'){this.redLights++;this.events.push({t:this.t,type:'red_light',intersection:j});}this.lastIntersection=key;}
  if(!inJ)this.lastIntersection=null;
  const onRoad=Math.abs(c.x-nearest(c.x))<=5.7||Math.abs(c.z-nearest(c.z))<=5.7;
  const hit=this.traffic.find(o=>Math.hypot(o.x-c.x,o.z-c.z)<3.6);
  if(!onRoad||Math.abs(c.x)>LIMIT||Math.abs(c.z)>LIMIT||hit){this.collisions++;this.events.push({t:this.t,type:hit?'traffic_collision':'curb_collision'});this.status='collision';}
  if(this.status==='running'&&this.challenge!=='explore'){const goal=this.goals[this.stops];if(goal&&Math.hypot(c.x-goal.x,c.z-goal.z)<6&&c.speed<2){this.stops++;this.events.push({t:this.t,type:'stop_reached'});if(this.stops===this.goals.length)this.status='completed';}}
  if(this.status==='running'&&this.t>=this.duration)this.status=this.challenge==='explore'&&this.distance>=150&&this.visited.size>=2?'completed':'time_limit';
 }
 advance(seconds){const n=Math.round(seconds/DT);for(let i=0;i<n;i++)this.step();}
 observation(){
  const c=this.car,h=cardinal(c.heading),f=unit(h*Math.PI/2),right=unit(h*Math.PI/2+Math.PI/2),axis=h%2?'x':'z';
  let intersections=ROADS.flatMap(x=>ROADS.map(z=>({x,z,forward:(x-c.x)*f.x+(z-c.z)*f.z,lateral:(x-c.x)*right.x+(z-c.z)*right.z}))).filter(j=>j.forward> -7&&Math.abs(j.lateral)<12).sort((a,b)=>a.forward-b.forward);
  const j=intersections[0];
  return {units:'meters, seconds, radians; x east, z south; heading 0 north, positive clockwise; right-hand traffic',time:this.t,challenge:this.challenge,vehicle:{...c,heading_name:HEADINGS[h]},speed_limit_mps:10,roads:{centers:ROADS,half_width:7,lane_center_offset:3.5,boundary:LIMIT},next_intersection:j?{...j,signal:signal(this.t,j.x,j.z,axis)}:null,nearby_traffic:this.traffic.filter(o=>Math.hypot(o.x-c.x,o.z-c.z)<55).map(({id,x,z,heading,speed})=>({id,x,z,heading,speed})),destinations:this.challenge==='explore'?[]:this.goals.slice(this.stops),objective:this.challenge==='explore'?'Travel at least 150m and visit two distinct intersections within 90s without a collision.':'Reach each destination and slow below 2 m/s within 6m of it.',previous_controls:{...this.action},actuation:'Steering -1 full left, 0 centered, +1 full right; steering angle=0.5*steer rad. Wheelbase=2.7m. Throttle acceleration=3m/s², brake=7m/s², drag=0.12*speed. Decisions at least 0.6s apart.'};
 }
 snapshot(){return {seed:this.seed,challenge:this.challenge,t:this.t,car:{...this.car},traffic:this.traffic.map(o=>({...o})),goals:this.goals,stops:this.stops,status:this.status,distance:this.distance,collisions:this.collisions,redLights:this.redLights,speedingSeconds:this.speedingSeconds,visited:[...this.visited],action:{...this.action}};}
}
export function payloads(observation,driver){
 const common='Drive in a simulated city. Stay on right-hand lanes, avoid traffic and curbs, obey red lights and the 10 m/s speed limit, and accomplish the stated objective. No route planner or safety filter will correct your choice. ';
 const questions=driver==='direct'?{
  steering:{instructions:common+'Which steering input should be held next?',criteria:{hard_left:'Steer -1',left:'Steer -0.3',straight:'Steer 0',right:'Steer +0.3',hard_right:'Steer +1'}},
  pedals:{instructions:common+'Which pedal input should be held next?',criteria:{accelerate:'Throttle 0.7, brake 0',coast:'Throttle 0, brake 0',brake:'Throttle 0, brake 0.8'}}
 }:{
  direction:{instructions:common+'Which cardinal direction should the lane-following controller take at the next junction? Code maintains the lane and executes the turn, but does not plan routes or stop for hazards. Choose stop to stop.',criteria:{north:'Go north',east:'Go east',south:'Go south',west:'Go west',stop:'Stop'}},
  speed:{instructions:common+'What target speed should the lane-following controller track next?',criteria:{stop:'0 m/s',slow:'4 m/s',cruise:'8 m/s'}}
 };
 return Object.entries(questions).map(([id,q])=>({model:'jev-1.13.0',state:observation,questions:{[id]:{type:'choice',...q}}}));
}
export function applyAnswers(city,driver,answers){
 if(driver==='direct'){const steer={hard_left:-1,left:-.3,straight:0,right:.3,hard_right:1}[answers.steering];const pedal={accelerate:[.7,0],coast:[0,0],brake:[0,.8]}[answers.pedals];if(steer===undefined||!pedal)throw Error('Invalid model action');city.setAction({steer,throttle:pedal[0],brake:pedal[1]});}
 else city.setManeuver({direction:answers.direction,speed:{stop:0,slow:4,cruise:8}[answers.speed]});
}
