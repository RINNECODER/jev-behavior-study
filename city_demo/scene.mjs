import * as THREE from './vendor/three.module.js';
import {ROADS,random,signal,unit} from './engine.mjs';
export class CityView {
 constructor(host){
  this.host=host;this.scene=new THREE.Scene();this.scene.background=new THREE.Color('#c4d7df');this.scene.fog=new THREE.Fog('#c4d7df',110,300);
  this.camera=new THREE.PerspectiveCamera(48,1,.1,600);this.mode='follow';
  this.renderer=new THREE.WebGLRenderer({antialias:true,preserveDrawingBuffer:true});this.renderer.setPixelRatio(Math.min(devicePixelRatio,2));this.renderer.shadowMap.enabled=true;this.renderer.shadowMap.type=THREE.PCFSoftShadowMap;this.renderer.outputColorSpace=THREE.SRGBColorSpace;this.renderer.setClearColor('#c4d7df');host.prepend(this.renderer.domElement);
  this.scene.add(new THREE.HemisphereLight('#e4f5ff','#a39a7d',2.2));const sun=new THREE.DirectionalLight('#fff0d6',3);sun.position.set(-60,110,40);sun.castShadow=true;sun.shadow.mapSize.set(2048,2048);Object.assign(sun.shadow.camera,{left:-130,right:130,top:130,bottom:-130,far:300});sun.shadow.bias=-.0006;this.scene.add(sun);
  this.materials={};this.box(0,-.25,0,270,.4,270,'#aaad96');
  for(const line of ROADS){this.box(line,-.02,0,18,.12,225,'#cec9bc');this.box(0,-.02,line,225,.12,18,'#cec9bc');this.box(line,.06,0,14,.04,225,'#535958');this.box(0,.06,line,225,.04,14,'#535958');}
  for(const line of ROADS)for(let v=-109;v<110;v+=5){if(ROADS.some(x=>Math.abs(v-x)<9))continue;for(const side of [-.17,.17]){this.box(line+side,.09,v,.07,.02,3,'#d8c28a');this.box(v,.09,line+side,3,.02,.07,'#d8c28a');}for(const side of [-6.2,6.2]){this.box(line+side,.09,v,.09,.02,4.6,'#deddd4');this.box(v,.09,line+side,4.6,.02,.09,'#deddd4');}}
  this.lights=[];
  for(const x of ROADS)for(const z of ROADS){for(let a=-5.5;a<6;a+=1.5){for(const side of [-9,9]){this.box(x+a,.1,z+side,.7,.02,2,'#dddcd2');this.box(x+side,.1,z+a,2,.02,.7,'#dddcd2');}}
   for(const [dx,dz,axis] of [[6.8,9,'z'],[-9,6.8,'x']]){this.box(x+dx,2.6,z+dz,.15,5.2,.15,'#444f49');this.box(x+dx,5.1,z+dz,.8,1.8,.6,'#29352f');const orb=new THREE.Mesh(new THREE.SphereGeometry(.22,10,8),new THREE.MeshStandardMaterial({color:'#64c9a1',emissive:'#64c9a1',emissiveIntensity:.8}));orb.position.set(x+dx,5.5,z+dz+.33);this.scene.add(orb);this.lights.push({mesh:orb,x,z,axis});}
  }
  const r=random(871);const palettes=['#d5cdb9','#c5bca8','#e1daca','#b8b9b1','#e6ddc8'];
  // Stable procedural geometry; no model information encoded in decoration.
  for(let x=-110;x<=110;x+=20)for(let z=-110;z<=110;z+=20){if(ROADS.some(v=>Math.abs(x-v)<13||Math.abs(z-v)<13))continue;const height=9+r()*27,w=12+r()*3,d=12+r()*3,col=palettes[Math.floor(r()*palettes.length)];this.box(x,height/2,z,w,height,d,col);this.box(x,height+.25,z,w+.6,.5,d+.6,'#ded7c8');
   for(let y=3;y<height-1;y+=3.2)for(let a=-4;a<=4;a+=2.6){this.box(x+a,y,z+d/2+.03,1.2,1.7,.04,'#889390');this.box(x+w/2+.03,y,z+a,.04,1.7,1.2,'#889390');this.box(x+a,y,z-d/2-.03,1.2,1.7,.04,'#889390');this.box(x-w/2-.03,y,z+a,.04,1.7,1.2,'#889390');}
  }
  const leaves=new THREE.IcosahedronGeometry(2.2,1);
  for(const line of ROADS)for(let v=-106;v<110;v+=14){if(ROADS.some(a=>Math.abs(v-a)<13))continue;for(const s of [-11,11])for(const [x,z] of [[line+s,v],[v,line+s]]){this.box(x,1.4,z,.4,2.8,.4,'#8a7856');const tree=new THREE.Mesh(leaves,this.mat('#76845c'));tree.position.set(x,3.8,z);tree.scale.y=1.35;tree.castShadow=true;this.scene.add(tree);}}
  this.player=this.car('#214f43');this.cars=Array.from({length:6},(_,i)=>this.car(['#d4bd8e','#849da1','#9c6250','#d9d4c5','#465f70','#9d9c82'][i]));
  this.beacons=[];new ResizeObserver(()=>this.resize()).observe(host);this.resize();
 }
 mat(color){return this.materials[color]??=(new THREE.MeshStandardMaterial({color,roughness:.85}));}
 box(x,y,z,w,h,d,color,parent=this.scene){const mesh=new THREE.Mesh(new THREE.BoxGeometry(w,h,d),this.mat(color));mesh.position.set(x,y,z);mesh.castShadow=h>1;mesh.receiveShadow=true;parent.add(mesh);return mesh;}
 car(color){const g=new THREE.Group();this.box(0,.7,0,1.9,.6,4,color,g);this.box(0,1.2,.1,1.6,.65,2.1,color,g);this.box(0,1.26,-.99,1.43,.45,.04,'#8bacae',g);this.box(0,1.26,1.17,1.43,.4,.04,'#637e7e',g);for(const x of [-.99,.99]){this.box(x,.44,-1.2,.22,.67,.65,'#222b2a',g);this.box(x,.44,1.2,.22,.67,.65,'#222b2a',g);this.box(x*.68,.68,-2.02,.4,.18,.04,'#fff5ca',g);this.box(x*.68,.68,2.02,.4,.18,.04,'#cf6350',g);}this.scene.add(g);return g;}
 resize(){const w=this.host.clientWidth,h=this.host.clientHeight;this.camera.aspect=w/h;this.camera.updateProjectionMatrix();this.renderer.setSize(w,h);}
 render(state){if(!state)return;const c=state.car;this.player.position.set(c.x,0,c.z);this.player.rotation.y=-c.heading;
  state.traffic.forEach((o,i)=>{this.cars[i].position.set(o.x,0,o.z);this.cars[i].rotation.y=-o.heading;});
  for(const l of this.lights){const color=signal(state.t,l.x,l.z,l.axis)==='green'?'#61d5a8':'#ee725b';l.mesh.material.color.set(color);l.mesh.material.emissive.set(color);}
  if(!this.beacons.length)for(const goal of state.goals){const g=new THREE.Group();const m=new THREE.Mesh(new THREE.CylinderGeometry(.13,.13,30,12),new THREE.MeshBasicMaterial({color:'#74ded1',transparent:true,opacity:.65}));m.position.y=15;g.add(m);const ring=new THREE.Mesh(new THREE.TorusGeometry(3,.18,8,40),new THREE.MeshBasicMaterial({color:'#72e3cf'}));ring.rotation.x=Math.PI/2;ring.position.y=.16;g.add(ring);g.position.set(goal.x,0,goal.z);this.scene.add(g);this.beacons.push(g);}
  this.beacons.forEach((b,i)=>{const goal=state.goals[i];b.visible=Boolean(goal)&&i>=state.stops&&state.challenge!=='explore';if(goal)b.position.set(goal.x,0,goal.z);});
  if(state.goals.length>this.beacons.length){this.beacons.forEach(b=>this.scene.remove(b));this.beacons=[];}
  const f=unit(c.heading);if(this.mode==='map'){this.camera.position.set(20,240,130);this.camera.lookAt(0,0,0);}else{this.camera.position.set(c.x-f.x*13,7,c.z-f.z*13);this.camera.lookAt(c.x+f.x*12,1,c.z+f.z*12);}
  this.renderer.render(this.scene,this.camera);
 }
 capture(){return this.renderer.domElement.toDataURL('image/png');}
}
