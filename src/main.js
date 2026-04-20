import * as THREE from 'three';
import { OBJLoader }        from 'three/addons/loaders/OBJLoader.js';
import { OrbitControls }    from 'three/addons/controls/OrbitControls.js';
import { mergeVertices }    from 'three/addons/utils/BufferGeometryUtils.js';
import { Muxer, ArrayBufferTarget } from 'mp4-muxer';
import Psd from '@webtoon/psd';

// ─── Renderer ─────────────────────────────────────────────────────────────────

const renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
renderer.setPixelRatio(window.devicePixelRatio);
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.shadowMap.enabled = true;
renderer.shadowMap.type    = THREE.PCFSoftShadowMap;
renderer.toneMapping       = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.0;
renderer.outputColorSpace  = THREE.SRGBColorSpace;
document.getElementById('canvas-container').appendChild(renderer.domElement);

const scene  = new THREE.Scene();
scene.background = new THREE.Color(0x080808);

const camera = new THREE.PerspectiveCamera(45, innerWidth / innerHeight, 0.01, 1000);
camera.position.set(0, 1, 4);

const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping  = true;
controls.dampingFactor  = 0.05;
controls.autoRotate     = true;
controls.autoRotateSpeed = 1.0;

// ─── Lights ───────────────────────────────────────────────────────────────────

const ambientLight = new THREE.AmbientLight(0xffffff, 0.5); scene.add(ambientLight);
const keyLight     = new THREE.DirectionalLight(0xffffff, 2);
keyLight.position.set(5, 8, 5); keyLight.castShadow = true;
keyLight.shadow.mapSize.set(2048, 2048); scene.add(keyLight);
const fillLight = new THREE.DirectionalLight(0x8888ff, 0.8); fillLight.position.set(-5, 3, -3); scene.add(fillLight);
const rimLight  = new THREE.DirectionalLight(0xffaa44, 0.6); rimLight.position.set(0, -2, -5);  scene.add(rimLight);

const ground = new THREE.Mesh(new THREE.PlaneGeometry(40, 40), new THREE.ShadowMaterial({ opacity: 0.3 }));
ground.rotation.x = -Math.PI / 2; ground.position.y = -0.001; ground.receiveShadow = true; scene.add(ground);

// ─── Projection GLSL (shared for both model slots A and B) ────────────────────

const PROJ_VERT = `
  varying vec3 vLocalPos; varying vec3 vNormal; varying vec2 vUv;
  void main() {
    vLocalPos = position;
    vNormal   = normalize(normalMatrix * normal);
    vUv       = uv;
    gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0);
  }`;

const PROJ_FRAG = `
  #define PI 3.14159265359
  uniform sampler2D tMap;
  uniform int   uProjection;        // 0=UV 1=PlanarX 2=PlanarY 3=PlanarZ 4=Cyl 5=Sph 6=Tri 7=Cubic
  uniform vec3  uBoundsMin, uBoundsSize;
  uniform vec2  uTiling, uOffset, uAnimOffset;
  uniform float uRotation, uOpacity;
  uniform int   uBlendMode;         // 0=Normal 1=Multiply 2=Add 3=Screen 4=Overlay
  uniform vec3  uBaseColor, uKeyPos;
  uniform float uKeyIntensity, uAmbientIntensity;
  varying vec3 vLocalPos, vNormal; varying vec2 vUv;

  vec2 xfUV(vec2 uv) {
    uv = uv * uTiling + uOffset + uAnimOffset;
    float c=cos(uRotation),s=sin(uRotation); uv-=.5; uv=mat2(c,-s,s,c)*uv; uv+=.5;
    return uv;
  }
  vec4 S(vec2 uv){ return texture2D(tMap, xfUV(uv)); }

  vec3 bNorm(vec3 b,vec3 t,float a){return mix(b,t,a);}
  vec3 bMul (vec3 b,vec3 t,float a){return mix(b,b*t,a);}
  vec3 bAdd (vec3 b,vec3 t,float a){return mix(b,min(b+t,vec3(1.)),a);}
  vec3 bScr (vec3 b,vec3 t,float a){return mix(b,1.-(1.-b)*(1.-t),a);}
  vec3 bOvr (vec3 b,vec3 t,float a){
    vec3 r=mix(2.*b*t,1.-2.*(1.-b)*(1.-t),step(.5,b)); return mix(b,r,a);
  }

  void main(){
    vec3 norm=normalize(vNormal);
    vec3 np=(vLocalPos-uBoundsMin)/max(uBoundsSize,vec3(.001));
    float diff=max(dot(norm,normalize(uKeyPos)),0.)*uKeyIntensity;
    vec3 color=uBaseColor*(uAmbientIntensity+diff);

    vec4 tx;
    if(uProjection==0) tx=S(vUv);
    else if(uProjection==1) tx=S(np.yz);
    else if(uProjection==2) tx=S(np.xz);
    else if(uProjection==3) tx=S(np.xy);
    else if(uProjection==4){ float a=atan(vLocalPos.z,vLocalPos.x); tx=S(vec2(a/(2.*PI)+.5,np.y)); }
    else if(uProjection==5){ vec3 d=normalize(vLocalPos); tx=S(vec2(atan(d.z,d.x)/(2.*PI)+.5, asin(clamp(d.y,-1.,1.))/PI+.5)); }
    else if(uProjection==6){
      vec3 w=abs(norm); w=pow(w,vec3(6.)); w/=dot(w,vec3(1.));
      tx=S(np.yz)*w.x+S(np.xz)*w.y+S(np.xy)*w.z;
    } else {
      vec3 an=abs(norm); vec2 uv;
      if(an.x>=an.y&&an.x>=an.z) uv=norm.x>0.?np.yz:vec2(1.-np.y,np.z);
      else if(an.y>=an.x&&an.y>=an.z) uv=norm.y>0.?np.xz:vec2(np.x,1.-np.z);
      else uv=norm.z>0.?np.xy:vec2(1.-np.x,np.y);
      tx=S(uv);
    }

    float alpha=tx.a*uOpacity; vec3 tl=tx.rgb*(uAmbientIntensity+diff);
    if(uBlendMode==0) color=bNorm(color,tl,alpha);
    else if(uBlendMode==1) color=bMul(color,tx.rgb,alpha);
    else if(uBlendMode==2) color=bAdd(color,tl,alpha);
    else if(uBlendMode==3) color=bScr(color,tx.rgb,alpha);
    else if(uBlendMode==4) color=bOvr(color,tx.rgb,alpha);
    gl_FragColor=vec4(color,1.);
  }`;

// ─── Material Factories ───────────────────────────────────────────────────────

let currentFaceSide = THREE.DoubleSide;
let zFightFix       = false;

function fx(mat) {
  if (zFightFix) { mat.polygonOffset=true; mat.polygonOffsetFactor=-1; mat.polygonOffsetUnits=-1; }
  return mat;
}

function buildMat(type, roughness=0.5, metalness=0.1) {
  const s = currentFaceSide;
  switch(type) {
    case 'standard': return fx(new THREE.MeshStandardMaterial({color:0xdddddd,roughness,metalness,side:s}));
    case 'wireframe':return fx(new THREE.MeshBasicMaterial({color:0x44aaff,wireframe:true}));
    case 'normals':  return fx(new THREE.MeshNormalMaterial({side:s}));
    case 'toon': {
      const g=new THREE.DataTexture(new Uint8Array([64,128,200,255]),1,1); g.needsUpdate=true;
      return fx(new THREE.MeshToonMaterial({color:0x88ccff,gradientMap:g,side:s}));
    }
    case 'xray':return fx(new THREE.MeshBasicMaterial({color:0x00ffff,transparent:true,opacity:.18,depthWrite:false,side:s}));
    case 'depth':return fx(new THREE.MeshDepthMaterial({depthPacking:THREE.RGBADepthPacking,side:s}));
    case 'hologram':return fx(new THREE.ShaderMaterial({
      uniforms:{time:{value:0},color:{value:new THREE.Color(0x00ffcc)}},
      vertexShader:`varying vec3 vN,vP; void main(){vN=normalize(normalMatrix*normal);vP=position;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.);}`,
      fragmentShader:`uniform float time;uniform vec3 color;varying vec3 vN,vP;
      void main(){float f=pow(1.-abs(dot(vN,vec3(0,0,1))),2.5);float sc=step(.5,fract(vP.y*8.-time*1.5));gl_FragColor=vec4(color*(f+.3),f*.9+sc*.15);}`,
      transparent:true,side:s,depthWrite:false}));
    case 'clay':return fx(new THREE.MeshStandardMaterial({color:0xc8a882,roughness:.95,metalness:0,side:s}));
    default: return fx(new THREE.MeshStandardMaterial({color:0xaaaaaa,side:s}));
  }
}

function buildProjMat(tex, p, bMin, bSize) {
  return fx(new THREE.ShaderMaterial({
    uniforms: {
      tMap:{value:tex}, uProjection:{value:p.projection},
      uBoundsMin:{value:bMin.clone()}, uBoundsSize:{value:bSize.clone()},
      uTiling:{value:new THREE.Vector2(p.tilingX,p.tilingY)},
      uOffset:{value:new THREE.Vector2(p.offsetX,p.offsetY)},
      uAnimOffset:{value:new THREE.Vector2(0,0)},
      uRotation:{value:p.rotation}, uOpacity:{value:p.opacity},
      uBlendMode:{value:p.blendMode},
      uBaseColor:{value:new THREE.Color(0xdddddd)},
      uKeyPos:{value:keyLight.position},
      uKeyIntensity:{value:keyLight.intensity},
      uAmbientIntensity:{value:ambientLight.intensity},
    },
    vertexShader:PROJ_VERT, fragmentShader:PROJ_FRAG,
    side:currentFaceSide, transparent:false,
  }));
}

// ─── Slot: reusable texture/material params ────────────────────────────────────

function makeSlot() {
  return {
    shader:'standard', roughness:0.5, metalness:0.1,
    tex:null, texEnabled:false,
    params:{ projection:2, blendMode:0, opacity:1, tilingX:1, tilingY:1, offsetX:0, offsetY:0, rotation:0 },
    boundsMin:new THREE.Vector3(), boundsSize:new THREE.Vector3(),
    anim:{ enabled:false, speedX:0.1, speedY:0, accX:0, accY:0 },
  };
}

const slotA = makeSlot();  // primary model
const slotB = makeSlot();  // stack model

function getMat(slot) {
  return (slot.tex && slot.texEnabled)
    ? buildProjMat(slot.tex, slot.params, slot.boundsMin, slot.boundsSize)
    : buildMat(slot.shader, slot.roughness, slot.metalness);
}

function applySlotMat(group, slot) {
  if (!group) return;
  const mat = getMat(slot);
  group.traverse(c => {
    if (c.isMesh) { c.material=mat; c.castShadow=true; c.receiveShadow=true; }
  });
}

function updateSlotUniforms(group, slot) {
  if (!group || !slot.tex || !slot.texEnabled) return;
  group.traverse(c => {
    if (c.isMesh && c.material.uniforms) {
      const u=c.material.uniforms;
      u.uProjection.value=slot.params.projection;
      u.uTiling.value.set(slot.params.tilingX, slot.params.tilingY);
      u.uOffset.value.set(slot.params.offsetX, slot.params.offsetY);
      u.uRotation.value=slot.params.rotation;
      u.uOpacity.value=slot.params.opacity;
      u.uBlendMode.value=slot.params.blendMode;
      u.uKeyIntensity.value=keyLight.intensity;
      u.uAmbientIntensity.value=ambientLight.intensity;
    }
  });
}

// ─── State ────────────────────────────────────────────────────────────────────

let modelA = null;   // primary loaded OBJ
let modelB = null;   // stack loaded OBJ

// Array
const arr = { enabled:false, cols:1, rows:1, gap:0.2, rotJoin:false, rotAxis:'y', rotDeg:0 };
let arrayGroup = null;

// Stack
const stack = { enabled:false, dir:1, gap:0.5 };

// ─── Bounds Helper ────────────────────────────────────────────────────────────

function localBounds(model) {
  const box = new THREE.Box3();
  model.traverse(c => {
    if (c.isMesh) { c.geometry.computeBoundingBox(); if(c.geometry.boundingBox) box.union(c.geometry.boundingBox); }
  });
  return box;
}

function centerAndFit(model, slot) {
  const box=new THREE.Box3().setFromObject(model);
  const center=box.getCenter(new THREE.Vector3()), size=box.getSize(new THREE.Vector3());
  const maxDim=Math.max(size.x,size.y,size.z), scale=2/maxDim;
  model.scale.setScalar(scale);
  model.position.sub(center.multiplyScalar(scale));
  const box2=new THREE.Box3().setFromObject(model);
  model.position.y-=box2.min.y;
  const lb=localBounds(model);
  slot.boundsMin.copy(lb.min);
  slot.boundsSize.copy(lb.getSize(new THREE.Vector3()));
  const fitDist=(maxDim*scale)*1.5/Math.tan((camera.fov/2)*(Math.PI/180));
  camera.position.set(0,(maxDim*scale)*.5,fitDist);
  controls.target.set(0,(maxDim*scale)*.3,0);
  controls.update();
}

// ─── Array Builder ────────────────────────────────────────────────────────────

function buildArray() {
  if (arrayGroup) { scene.remove(arrayGroup); arrayGroup=null; }
  if (!modelA) return;

  if (!arr.enabled || (arr.cols===1 && arr.rows===1)) {
    modelA.visible=true;
    return;
  }

  modelA.visible=false;
  arrayGroup=new THREE.Group();

  const box=new THREE.Box3().setFromObject(modelA);
  const sz=box.getSize(new THREE.Vector3());
  const stepX=sz.x*(1+arr.gap), stepZ=sz.z*(1+arr.gap);
  const offX=(arr.cols-1)*stepX*0.5, offZ=(arr.rows-1)*stepZ*0.5;

  for(let col=0; col<arr.cols; col++) {
    for(let row=0; row<arr.rows; row++) {
      const clone=modelA.clone();
      clone.position.set(col*stepX-offX, 0, row*stepZ-offZ);
      if(arr.rotJoin) {
        const idx=row*arr.cols+col;
        const a=idx*arr.rotDeg*Math.PI/180;
        if(arr.rotAxis==='y') clone.rotation.y=a;
        else if(arr.rotAxis==='x') clone.rotation.x=a;
        else clone.rotation.z=a;
      }
      arrayGroup.add(clone);
    }
  }

  applySlotMat(arrayGroup, slotA);
  scene.add(arrayGroup);
}

function getActiveA() { return (arr.enabled && arrayGroup) ? arrayGroup : modelA; }

// ─── Stack Positioner ─────────────────────────────────────────────────────────

function positionStack() {
  if (!modelB || !stack.enabled) return;

  const srcBox=new THREE.Box3().setFromObject(getActiveA() || new THREE.Object3D());
  const bBox=new THREE.Box3().setFromObject(modelB);
  const bSz=bBox.getSize(new THREE.Vector3());
  const bCenter=bBox.getCenter(new THREE.Vector3());

  // Center XZ
  modelB.position.x=-bCenter.x;
  modelB.position.z=-bCenter.z;

  if(stack.dir>0) {
    // Above: bottom of B sits on top of A + gap
    modelB.position.y=srcBox.max.y+stack.gap-bBox.min.y;
  } else {
    // Below: top of B sits below bottom of A - gap
    modelB.position.y=srcBox.min.y-stack.gap-bBox.max.y;
  }
}

// ─── Apply Materials (convenience wrappers) ───────────────────────────────────

function applyA() { applySlotMat(getActiveA(), slotA); }
function applyB() { applySlotMat(modelB, slotB); }

// ─── PSD / Texture Loaders ────────────────────────────────────────────────────

async function parsePSD(buf) {
  const psd=Psd.parse(buf), pixels=await psd.composite();
  const c=document.createElement('canvas');
  c.width=psd.width; c.height=psd.height;
  c.getContext('2d').putImageData(new ImageData(new Uint8ClampedArray(pixels.buffer),psd.width,psd.height),0,0);
  const t=new THREE.CanvasTexture(c);
  t.colorSpace=THREE.SRGBColorSpace; t.wrapS=t.wrapT=THREE.RepeatWrapping;
  return t;
}

async function loadTexFile(file) {
  const ext=file.name.split('.').pop().toLowerCase();
  if(ext==='psd') return parsePSD(await file.arrayBuffer());
  if(['mov','mp4','webm'].includes(ext)) {
    const vid=document.createElement('video');
    Object.assign(vid,{src:URL.createObjectURL(file),loop:true,muted:true,playsInline:true,crossOrigin:'anonymous'});
    await new Promise((res,rej)=>{ vid.onloadeddata=res; vid.onerror=()=>rej(new Error('Video failed — try WebM/VP9 for alpha')); });
    vid.play();
    const t=new THREE.VideoTexture(vid);
    t.colorSpace=THREE.SRGBColorSpace; t.wrapS=t.wrapT=THREE.RepeatWrapping;
    t._video=vid;
    return t;
  }
  return new Promise((res,rej)=>{
    new THREE.TextureLoader().load(URL.createObjectURL(file), t=>{ t.colorSpace=THREE.SRGBColorSpace; t.wrapS=t.wrapT=THREE.RepeatWrapping; res(t); },undefined,rej);
  });
}

// ─── Geometry Repair ──────────────────────────────────────────────────────────

function repairGeo(model, statusEl) {
  if(!model) return;
  let count=0;
  model.traverse(c=>{
    if(!c.isMesh) return;
    try { c.geometry=mergeVertices(c.geometry,0.0001); } catch(e){}
    c.geometry.computeVertexNormals();
    count++;
  });
  applyA();
  if(statusEl) { statusEl.textContent=`Repaired ${count} mesh(es)`; statusEl.style.color='#7fa'; }
}

function flipNormals(model) {
  if(!model) return;
  model.traverse(c=>{
    if(!c.isMesh) return;
    const n=c.geometry.attributes.normal;
    if(n) { for(let i=0;i<n.count;i++) n.setXYZ(i,-n.getX(i),-n.getY(i),-n.getZ(i)); n.needsUpdate=true; }
    const idx=c.geometry.index;
    if(idx) { for(let i=0;i<idx.count;i+=3){ const t=idx.getX(i+1); idx.setX(i+1,idx.getX(i+2)); idx.setX(i+2,t); } idx.needsUpdate=true; }
  });
  applyA();
}

// ─── Video Export ─────────────────────────────────────────────────────────────

async function exportVideo() {
  const fps      = parseInt(document.getElementById('vid-fps').value);
  const dur      = parseFloat(document.getElementById('vid-dur').value);
  const resStr   = document.getElementById('vid-res').value;
  const [vW,vH]  = resStr.split('x').map(Number);
  const total    = Math.round(dur*fps);

  const progWrap = document.getElementById('vid-progress-wrap');
  const progBar  = document.getElementById('vid-progress-bar');
  const progTxt  = document.getElementById('vid-progress-txt');
  progWrap.style.display='block';
  progTxt.textContent='Initializing encoder…';

  // Snapshot for restore
  const origW=renderer.domElement.width, origH=renderer.domElement.height;
  const origAspect=camera.aspect;

  // Orbit params for deterministic camera rotation
  const tgt   = controls.target.clone();
  const rel   = camera.position.clone().sub(tgt);
  const dist  = rel.length();
  const elev  = Math.asin(rel.y/dist);
  const initAz= Math.atan2(rel.x,rel.z);
  const azPerSec = controls.autoRotate ? controls.autoRotateSpeed*2*Math.PI/60 : 0;

  renderer.setSize(vW,vH,false);
  camera.aspect=vW/vH; camera.updateProjectionMatrix();

  // Setup muxer + encoder
  const target=new ArrayBufferTarget();
  const muxer=new Muxer({ target, video:{codec:'avc',width:vW,height:vH}, fastStart:'in-memory' });

  const enc=new VideoEncoder({
    output:(chunk,meta)=>muxer.addVideoChunk(chunk,meta),
    error:e=>console.error('VideoEncoder:',e),
  });
  enc.configure({ codec:'avc1.42003e', width:vW, height:vH, bitrate:10_000_000, framerate:fps });

  for(let i=0;i<total;i++) {
    const t=i/fps, delta=1/fps;

    // Advance camera
    const az=initAz+azPerSec*t;
    camera.position.x=tgt.x+dist*Math.cos(elev)*Math.sin(az);
    camera.position.z=tgt.z+dist*Math.cos(elev)*Math.cos(az);
    camera.position.y=tgt.y+dist*Math.sin(elev);
    camera.lookAt(tgt); camera.updateMatrixWorld();

    // Advance hologram
    if(slotA.shader==='hologram'&&!slotA.texEnabled) {
      getActiveA()?.traverse(c=>{ if(c.isMesh&&c.material.uniforms?.time) c.material.uniforms.time.value=t; });
    }
    if(slotB.shader==='hologram'&&!slotB.texEnabled) {
      modelB?.traverse(c=>{ if(c.isMesh&&c.material.uniforms?.time) c.material.uniforms.time.value=t; });
    }

    // Advance texture animations
    [{ slot:slotA, grp:getActiveA() }, { slot:slotB, grp:modelB }].forEach(({slot,grp})=>{
      if(!slot.anim.enabled||!slot.tex||!slot.texEnabled||!grp) return;
      const ax=slot.anim.speedX*t, ay=slot.anim.speedY*t;
      grp.traverse(c=>{ if(c.isMesh&&c.material.uniforms?.uAnimOffset) c.material.uniforms.uAnimOffset.value.set(ax,ay); });
    });

    renderer.render(scene,camera);

    const frame=new VideoFrame(renderer.domElement,{ timestamp:Math.round(t*1_000_000), duration:Math.round(delta*1_000_000) });
    enc.encode(frame,{keyFrame:i%fps===0}); frame.close();

    const pct=Math.round((i+1)/total*100);
    progBar.style.width=`${pct}%`;
    progTxt.textContent=`Encoding ${pct}% (${i+1}/${total} frames)`;
    if(i%8===0) await new Promise(r=>setTimeout(r,0)); // yield to UI
  }

  await enc.flush();
  muxer.finalize();

  const blob=new Blob([target.buffer],{type:'video/mp4'});
  const url=URL.createObjectURL(blob);
  const a=document.createElement('a');
  a.href=url; a.download=`wintermute_${Date.now()}.mp4`; a.click();
  URL.revokeObjectURL(url);

  // Restore viewport
  renderer.setSize(origW,origH,false);
  camera.aspect=origAspect; camera.updateProjectionMatrix();
  progWrap.style.display='none';
}

// ─── OBJ Loader ───────────────────────────────────────────────────────────────

const objLoader=new OBJLoader();

function loadOBJ(file, onDone) {
  const r=new FileReader();
  r.onload=evt=>{
    try {
      const obj=objLoader.parse(evt.target.result);
      onDone(null, obj);
    } catch(e) { onDone(e); }
  };
  r.readAsText(file);
}

// ─── UI Wiring ────────────────────────────────────────────────────────────────

const statusA     = document.getElementById('status-a');
const statusB     = document.getElementById('status-b');
const texStatA    = document.getElementById('tex-status-a');
const texStatB    = document.getElementById('tex-status-b');
const repairStat  = document.getElementById('repair-status');
const vidCtrlsA   = document.getElementById('video-controls-a');
const vidCtrlsB   = document.getElementById('video-controls-b');

// Model A
document.getElementById('obj-input-a').addEventListener('change', e=>{
  const f=e.target.files[0]; if(!f) return;
  statusA.textContent=`Loading…`; statusA.style.color='#aaa';
  loadOBJ(f,(err,obj)=>{
    if(err){ statusA.textContent=`Error: ${err.message}`; statusA.style.color='#f77'; return; }
    if(modelA){ scene.remove(modelA); }
    modelA=obj;
    centerAndFit(modelA, slotA);
    applySlotMat(modelA, slotA);
    scene.add(modelA);
    buildArray();
    positionStack();
    const n=[]; obj.traverse(c=>{ if(c.isMesh) n.push(c); });
    statusA.textContent=`${f.name} — ${n.length} mesh(es)`;
    statusA.style.color='#7af';
  });
});

// Model B (stack)
document.getElementById('obj-input-b').addEventListener('change', e=>{
  const f=e.target.files[0]; if(!f) return;
  statusB.textContent=`Loading…`; statusB.style.color='#aaa';
  loadOBJ(f,(err,obj)=>{
    if(err){ statusB.textContent=`Error: ${err.message}`; statusB.style.color='#f77'; return; }
    if(modelB){ scene.remove(modelB); }
    const lb=localBounds(obj); slotB.boundsMin.copy(lb.min); slotB.boundsSize.copy(lb.getSize(new THREE.Vector3()));
    // Scale B to match A if possible
    if(modelA){ const bxA=new THREE.Box3().setFromObject(modelA); const szA=bxA.getSize(new THREE.Vector3()); const mxA=Math.max(szA.x,szA.y,szA.z); const bxB=new THREE.Box3().setFromObject(obj); const szB=bxB.getSize(new THREE.Vector3()); const mxB=Math.max(szB.x,szB.y,szB.z); obj.scale.setScalar(mxA/mxB); }
    modelB=obj;
    applySlotMat(modelB, slotB);
    scene.add(modelB);
    if(stack.enabled) positionStack();
    else modelB.visible=false;
    const n=[]; obj.traverse(c=>{ if(c.isMesh) n.push(c); });
    statusB.textContent=`${f.name} — ${n.length} mesh(es)`;
    statusB.style.color='#fa7';
  });
});

// Array controls
document.getElementById('arr-toggle').addEventListener('change', e=>{ arr.enabled=e.target.checked; buildArray(); positionStack(); });
document.getElementById('arr-cols').addEventListener('input', e=>{ arr.cols=parseInt(e.target.value)||1; document.getElementById('arr-cols-val').textContent=arr.cols; buildArray(); });
document.getElementById('arr-rows').addEventListener('input', e=>{ arr.rows=parseInt(e.target.value)||1; document.getElementById('arr-rows-val').textContent=arr.rows; buildArray(); });
document.getElementById('arr-gap').addEventListener('input', e=>{ arr.gap=parseFloat(e.target.value); document.getElementById('arr-gap-val').textContent=arr.gap.toFixed(2); buildArray(); });
document.getElementById('arr-rot-join').addEventListener('change', e=>{ arr.rotJoin=e.target.checked; buildArray(); });
document.getElementById('arr-rot-axis').addEventListener('change', e=>{ arr.rotAxis=e.target.value; buildArray(); });
document.getElementById('arr-rot-deg').addEventListener('input', e=>{ arr.rotDeg=parseFloat(e.target.value); document.getElementById('arr-rot-deg-val').textContent=`${arr.rotDeg}°`; buildArray(); });

// Stack controls
document.getElementById('stack-toggle').addEventListener('change', e=>{
  stack.enabled=e.target.checked;
  if(modelB){ modelB.visible=stack.enabled; if(stack.enabled) positionStack(); }
});
document.getElementById('stack-dir').addEventListener('change', e=>{ stack.dir=parseInt(e.target.value); positionStack(); });
document.getElementById('stack-gap').addEventListener('input', e=>{ stack.gap=parseFloat(e.target.value); document.getElementById('stack-gap-val').textContent=stack.gap.toFixed(1); positionStack(); });

// Mesh repair
document.getElementById('face-cull').addEventListener('change', e=>{ currentFaceSide=e.target.value==='front'?THREE.FrontSide:e.target.value==='back'?THREE.BackSide:THREE.DoubleSide; applyA(); applyB(); });
document.getElementById('zfight-toggle').addEventListener('change', e=>{ zFightFix=e.target.checked; applyA(); applyB(); });
document.getElementById('repair-btn').addEventListener('click', ()=>repairGeo(modelA,repairStat));
document.getElementById('flip-normals-btn').addEventListener('click', ()=>{ flipNormals(modelA); repairStat.textContent='Normals flipped'; repairStat.style.color='#fa7'; });

// Shader A
document.getElementById('shader-a').addEventListener('change', e=>{ slotA.shader=e.target.value; applyA(); });
// Shader B
document.getElementById('shader-b').addEventListener('change', e=>{ slotB.shader=e.target.value; applyB(); });

// Lighting
function bindLight(id,valId,dec,fn){ const s=document.getElementById(id),d=document.getElementById(valId); s.addEventListener('input',()=>{ const v=parseFloat(s.value); d.textContent=v.toFixed(dec); fn(v); }); }
bindLight('light-intensity','light-intensity-val',1,v=>{ keyLight.intensity=v; updateSlotUniforms(getActiveA(),slotA); updateSlotUniforms(modelB,slotB); });
bindLight('ambient','ambient-val',1,v=>{ ambientLight.intensity=v; updateSlotUniforms(getActiveA(),slotA); updateSlotUniforms(modelB,slotB); });
bindLight('roughness','roughness-val',2,v=>{ slotA.roughness=v; if(!slotA.texEnabled) applyA(); });
bindLight('metalness','metalness-val',2,v=>{ slotA.metalness=v; if(!slotA.texEnabled) applyA(); });

// Texture wiring for a given slot
function wireTexSlot(ids, slot, grpFn, statEl, vidCtrl) {
  document.getElementById(ids.file).addEventListener('change', async e=>{
    const f=e.target.files[0]; if(!f) return;
    statEl.textContent='Loading…'; statEl.style.color='#aaa';
    if(slot.tex?._video){ slot.tex._video.pause(); slot.tex._video=null; }
    if(slot.tex){ slot.tex.dispose(); slot.tex=null; }
    try {
      slot.tex=await loadTexFile(f);
      statEl.textContent=`${f.name}`; statEl.style.color='#7fa';
      document.getElementById(ids.toggle).checked=true; slot.texEnabled=true;
      slot.anim.accX=slot.anim.accY=0;
      applySlotMat(grpFn(), slot);
      if(slot.tex._video) vidCtrl.style.display='flex'; else vidCtrl.style.display='none';
    } catch(e2){ statEl.textContent=`Error: ${e2.message}`; statEl.style.color='#f77'; }
  });
  document.getElementById(ids.toggle).addEventListener('change', e=>{ slot.texEnabled=e.target.checked; applySlotMat(grpFn(), slot); });
  document.getElementById(ids.proj).addEventListener('change', e=>{ slot.params.projection=parseInt(e.target.value); applySlotMat(grpFn(), slot); });
  document.getElementById(ids.blend).addEventListener('change', e=>{ slot.params.blendMode=parseInt(e.target.value); updateSlotUniforms(grpFn(), slot); });
  document.getElementById(ids.clear).addEventListener('click', ()=>{
    if(slot.tex?._video){ slot.tex._video.pause(); } if(slot.tex){ slot.tex.dispose(); slot.tex=null; }
    slot.texEnabled=false; slot.anim.accX=slot.anim.accY=0;
    document.getElementById(ids.toggle).checked=false;
    vidCtrl.style.display='none';
    statEl.textContent='No texture'; statEl.style.color='#555';
    applySlotMat(grpFn(), slot);
  });
  if(ids.vidPlay) {
    document.getElementById(ids.vidPlay).addEventListener('click', ()=>{
      const vid=slot.tex?._video; if(!vid) return;
      if(vid.paused){ vid.play(); document.getElementById(ids.vidPlay).textContent='⏸ Pause'; }
      else { vid.pause(); document.getElementById(ids.vidPlay).textContent='▶ Play'; }
    });
    document.getElementById(ids.vidLoop).addEventListener('click', ()=>{
      const vid=slot.tex?._video; if(!vid) return;
      vid.loop=!vid.loop; document.getElementById(ids.vidLoop).textContent=`Loop ${vid.loop?'ON':'OFF'}`;
    });
  }
  // Sliders
  function sl(id,valId,dec,fn){ const s=document.getElementById(id),d=document.getElementById(valId); if(!s) return; s.addEventListener('input',()=>{ const v=parseFloat(s.value); d.textContent=v.toFixed(dec); fn(v); }); }
  sl(ids.opacity, ids.opacityVal, 2, v=>{ slot.params.opacity=v; updateSlotUniforms(grpFn(),slot); });
  sl(ids.tilX,    ids.tilXVal,    1, v=>{ slot.params.tilingX=v; updateSlotUniforms(grpFn(),slot); });
  sl(ids.tilY,    ids.tilYVal,    1, v=>{ slot.params.tilingY=v; updateSlotUniforms(grpFn(),slot); });
  sl(ids.offX,    ids.offXVal,    2, v=>{ slot.params.offsetX=v; updateSlotUniforms(grpFn(),slot); });
  sl(ids.offY,    ids.offYVal,    2, v=>{ slot.params.offsetY=v; updateSlotUniforms(grpFn(),slot); });
  sl(ids.animSX,  ids.animSXVal,  2, v=>{ slot.anim.speedX=v; });
  sl(ids.animSY,  ids.animSYVal,  2, v=>{ slot.anim.speedY=v; });
  const rotEl=document.getElementById(ids.rot);
  if(rotEl) rotEl.addEventListener('input', e=>{ const d=parseFloat(e.target.value); document.getElementById(ids.rotVal).textContent=`${d}°`; slot.params.rotation=d*Math.PI/180; updateSlotUniforms(grpFn(),slot); });
  const atEl=document.getElementById(ids.animToggle);
  if(atEl) atEl.addEventListener('change', e=>{ slot.anim.enabled=e.target.checked; if(!e.target.checked){ slot.anim.accX=slot.anim.accY=0; updateSlotUniforms(grpFn(),slot); } });
  const arEl=document.getElementById(ids.animReset);
  if(arEl) arEl.addEventListener('click', ()=>{ slot.anim.accX=slot.anim.accY=0; });
}

wireTexSlot({
  file:'tex-file-a', toggle:'tex-toggle-a', proj:'proj-a', blend:'blend-a', clear:'clear-tex-a',
  opacity:'tex-opacity-a', opacityVal:'tex-opacity-a-val',
  tilX:'tiling-x-a', tilXVal:'tiling-x-a-val', tilY:'tiling-y-a', tilYVal:'tiling-y-a-val',
  offX:'offset-x-a', offXVal:'offset-x-a-val', offY:'offset-y-a', offYVal:'offset-y-a-val',
  rot:'tex-rot-a', rotVal:'tex-rot-a-val',
  animToggle:'anim-toggle-a', animReset:'anim-reset-a',
  animSX:'anim-sx-a', animSXVal:'anim-sx-a-val', animSY:'anim-sy-a', animSYVal:'anim-sy-a-val',
  vidPlay:'vid-play-a', vidLoop:'vid-loop-a',
}, slotA, ()=>getActiveA(), texStatA, vidCtrlsA);

wireTexSlot({
  file:'tex-file-b', toggle:'tex-toggle-b', proj:'proj-b', blend:'blend-b', clear:'clear-tex-b',
  opacity:'tex-opacity-b', opacityVal:'tex-opacity-b-val',
  tilX:'tiling-x-b', tilXVal:'tiling-x-b-val', tilY:'tiling-y-b', tilYVal:'tiling-y-b-val',
  offX:'offset-x-b', offXVal:'offset-x-b-val', offY:'offset-y-b', offYVal:'offset-y-b-val',
  rot:'tex-rot-b', rotVal:'tex-rot-b-val',
  animToggle:'anim-toggle-b', animReset:'anim-reset-b',
  animSX:'anim-sx-b', animSXVal:'anim-sx-b-val', animSY:'anim-sy-b', animSYVal:'anim-sy-b-val',
  vidPlay:'vid-play-b', vidLoop:'vid-loop-b',
}, slotB, ()=>modelB, texStatB, vidCtrlsB);

// Camera / export
document.getElementById('shader-a');
document.getElementById('auto-rotate').addEventListener('change', e=>{ const v=parseFloat(e.target.value); controls.autoRotate=v>0; controls.autoRotateSpeed=v; });
document.getElementById('reset-camera').addEventListener('click', ()=>{ if(modelA) centerAndFit(modelA,slotA); else{ camera.position.set(0,1,4); controls.target.set(0,0,0); controls.update(); } });

document.getElementById('export-png-btn').addEventListener('click', ()=>{
  const resStr=document.getElementById('export-res').value;
  const[ew,eh]=resStr.split('x').map(Number);
  const origW=renderer.domElement.width, origH=renderer.domElement.height, origA=camera.aspect;
  renderer.setSize(ew,eh,false); camera.aspect=ew/eh; camera.updateProjectionMatrix();
  renderer.render(scene,camera);
  const a=document.createElement('a'); a.download=`wintermute_${resStr}_${Date.now()}.png`; a.href=renderer.domElement.toDataURL('image/png'); a.click();
  renderer.setSize(origW,origH,false); camera.aspect=origA; camera.updateProjectionMatrix();
  statusA.textContent=`PNG exported`; statusA.style.color='#af7';
});

document.getElementById('export-vid-btn').addEventListener('click', ()=>{
  if(!window.VideoEncoder){ alert('VideoEncoder (WebCodecs) not available — try Chrome or Edge'); return; }
  exportVideo().catch(e=>{ console.error(e); alert(`Export failed: ${e.message}`); document.getElementById('vid-progress-wrap').style.display='none'; });
});

// ─── Animate Loop ─────────────────────────────────────────────────────────────

const clock=new THREE.Clock(); let prevT=0;

function animate() {
  requestAnimationFrame(animate);
  const t=clock.getElapsedTime(), dt=t-prevT; prevT=t;

  // Hologram time
  if(slotA.shader==='hologram'&&!slotA.texEnabled) getActiveA()?.traverse(c=>{ if(c.isMesh&&c.material.uniforms?.time) c.material.uniforms.time.value=t; });
  if(slotB.shader==='hologram'&&!slotB.texEnabled) modelB?.traverse(c=>{ if(c.isMesh&&c.material.uniforms?.time) c.material.uniforms.time.value=t; });

  // Texture animation scroll (per-slot)
  [{ slot:slotA, grp:getActiveA() }, { slot:slotB, grp:modelB }].forEach(({slot,grp})=>{
    if(!slot.anim.enabled||!slot.tex||!slot.texEnabled||!grp) return;
    slot.anim.accX+=slot.anim.speedX*dt;
    slot.anim.accY+=slot.anim.speedY*dt;
    grp.traverse(c=>{ if(c.isMesh&&c.material.uniforms?.uAnimOffset) c.material.uniforms.uAnimOffset.value.set(slot.anim.accX,slot.anim.accY); });
  });

  // Video texture sync
  if(slotA.tex?.isVideoTexture) slotA.tex.needsUpdate=true;
  if(slotB.tex?.isVideoTexture) slotB.tex.needsUpdate=true;

  controls.update();
  renderer.render(scene,camera);
}

window.addEventListener('resize', ()=>{ camera.aspect=innerWidth/innerHeight; camera.updateProjectionMatrix(); renderer.setSize(innerWidth,innerHeight); });
animate();
