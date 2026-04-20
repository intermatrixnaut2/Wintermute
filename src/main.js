import * as THREE from 'three';
import { OBJLoader } from 'three/addons/loaders/OBJLoader.js';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { mergeVertices } from 'three/addons/utils/BufferGeometryUtils.js';
import Psd from '@webtoon/psd';

// ─── Scene Setup ──────────────────────────────────────────────────────────────

const container = document.getElementById('canvas-container');

const renderer = new THREE.WebGLRenderer({
  antialias: true,
  preserveDrawingBuffer: true,
  alpha: false
});
renderer.setPixelRatio(window.devicePixelRatio);
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.0;
renderer.outputColorSpace = THREE.SRGBColorSpace;
container.appendChild(renderer.domElement);

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x080808);

const camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 0.01, 1000);
camera.position.set(0, 1, 4);

const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.dampingFactor = 0.05;
controls.autoRotate = true;
controls.autoRotateSpeed = 1.0;

// ─── Lighting ─────────────────────────────────────────────────────────────────

const ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
scene.add(ambientLight);

const keyLight = new THREE.DirectionalLight(0xffffff, 2);
keyLight.position.set(5, 8, 5);
keyLight.castShadow = true;
keyLight.shadow.mapSize.set(2048, 2048);
scene.add(keyLight);

const fillLight = new THREE.DirectionalLight(0x8888ff, 0.8);
fillLight.position.set(-5, 3, -3);
scene.add(fillLight);

const rimLight = new THREE.DirectionalLight(0xffaa44, 0.6);
rimLight.position.set(0, -2, -5);
scene.add(rimLight);

const ground = new THREE.Mesh(
  new THREE.PlaneGeometry(20, 20),
  new THREE.ShadowMaterial({ opacity: 0.3 })
);
ground.rotation.x = -Math.PI / 2;
ground.position.y = -0.001;
ground.receiveShadow = true;
scene.add(ground);

// ─── Projection GLSL ──────────────────────────────────────────────────────────

const PROJECTION_VERT = `
  varying vec3 vLocalPos;
  varying vec3 vNormal;
  varying vec2 vUv;

  void main() {
    vLocalPos = position;
    vNormal   = normalize(normalMatrix * normal);
    vUv       = uv;
    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
  }
`;

const PROJECTION_FRAG = `
  #define PI 3.14159265359

  uniform sampler2D tMap;
  // 0=UV 1=PlanarX 2=PlanarY 3=PlanarZ 4=Cyl 5=Sph 6=Triplanar 7=Cubic
  uniform int   uProjection;
  uniform vec3  uBoundsMin;
  uniform vec3  uBoundsSize;
  uniform vec2  uTiling;
  uniform vec2  uOffset;
  uniform vec2  uAnimOffset;   // accumulated animated scroll
  uniform float uRotation;
  uniform float uOpacity;
  uniform int   uBlendMode;    // 0=Normal 1=Multiply 2=Add 3=Screen 4=Overlay
  uniform vec3  uBaseColor;
  uniform vec3  uKeyPos;
  uniform float uKeyIntensity;
  uniform float uAmbientIntensity;

  varying vec3 vLocalPos;
  varying vec3 vNormal;
  varying vec2 vUv;

  vec2 xfUV(vec2 uv) {
    uv = uv * uTiling + uOffset + uAnimOffset;  // tiling → manual offset → animated scroll
    float c = cos(uRotation), s = sin(uRotation);
    uv -= 0.5;
    uv = mat2(c, -s, s, c) * uv;
    uv += 0.5;
    return uv;
  }

  vec4 sampleTex(vec2 uv) { return texture2D(tMap, xfUV(uv)); }

  // ── Blend modes ──────────────────────────────────────────────────────────────
  vec3 blendNormal  (vec3 b, vec3 t, float a) { return mix(b, t, a); }
  vec3 blendMultiply(vec3 b, vec3 t, float a) { return mix(b, b * t, a); }
  vec3 blendAdd     (vec3 b, vec3 t, float a) { return mix(b, min(b + t, vec3(1.0)), a); }
  vec3 blendScreen  (vec3 b, vec3 t, float a) { return mix(b, 1.0-(1.0-b)*(1.0-t), a); }
  vec3 blendOverlay (vec3 b, vec3 t, float a) {
    vec3 r = mix(2.0*b*t, 1.0-2.0*(1.0-b)*(1.0-t), step(0.5, b));
    return mix(b, r, a);
  }

  void main() {
    vec3 norm    = normalize(vNormal);
    vec3 normPos = (vLocalPos - uBoundsMin) / max(uBoundsSize, vec3(0.001));

    float diff  = max(dot(norm, normalize(uKeyPos)), 0.0) * uKeyIntensity;
    float light = uAmbientIntensity + diff;
    vec3  color = uBaseColor * light;

    // ── Projection UV ─────────────────────────────────────────────────────────
    vec4 texSample;

    if (uProjection == 0) {
      texSample = sampleTex(vUv);

    } else if (uProjection == 1) {
      texSample = sampleTex(normPos.yz);

    } else if (uProjection == 2) {
      texSample = sampleTex(normPos.xz);

    } else if (uProjection == 3) {
      texSample = sampleTex(normPos.xy);

    } else if (uProjection == 4) {
      float angle = atan(vLocalPos.z, vLocalPos.x);
      texSample   = sampleTex(vec2(angle / (2.0*PI) + 0.5, normPos.y));

    } else if (uProjection == 5) {
      vec3  d = normalize(vLocalPos);
      float u = atan(d.z, d.x) / (2.0*PI) + 0.5;
      float v = asin(clamp(d.y, -1.0, 1.0)) / PI + 0.5;
      texSample = sampleTex(vec2(u, v));

    } else if (uProjection == 6) {
      // Triplanar — soft blended seams, weighted by normal
      vec3 w  = abs(norm);
      w       = pow(w, vec3(6.0));
      w      /= dot(w, vec3(1.0));
      texSample = sampleTex(normPos.yz) * w.x
                + sampleTex(normPos.xz) * w.y
                + sampleTex(normPos.xy) * w.z;

    } else {
      // Cubic (7) — hard face snapping, no blending, clean seams on box-like shapes
      vec3 absN = abs(norm);
      vec2 cubeUV;
      if (absN.x >= absN.y && absN.x >= absN.z) {
        cubeUV = norm.x > 0.0 ? normPos.yz : vec2(1.0 - normPos.y, normPos.z);
      } else if (absN.y >= absN.x && absN.y >= absN.z) {
        cubeUV = norm.y > 0.0 ? normPos.xz : vec2(normPos.x, 1.0 - normPos.z);
      } else {
        cubeUV = norm.z > 0.0 ? normPos.xy : vec2(1.0 - normPos.x, normPos.y);
      }
      texSample = sampleTex(cubeUV);
    }

    // ── Blend onto base ───────────────────────────────────────────────────────
    float alpha = texSample.a * uOpacity;
    vec3  tex   = texSample.rgb * light;

    if      (uBlendMode == 0) color = blendNormal  (color, tex,            alpha);
    else if (uBlendMode == 1) color = blendMultiply(color, texSample.rgb,  alpha);
    else if (uBlendMode == 2) color = blendAdd     (color, tex,            alpha);
    else if (uBlendMode == 3) color = blendScreen  (color, texSample.rgb,  alpha);
    else if (uBlendMode == 4) color = blendOverlay (color, texSample.rgb,  alpha);

    gl_FragColor = vec4(color, 1.0);
  }
`;

// ─── Global Mesh State ────────────────────────────────────────────────────────

let currentFaceSide = THREE.DoubleSide;   // face culling
let zFightFix       = false;              // polygon offset for z-fighting

// ─── Material Library ─────────────────────────────────────────────────────────

function applyMeshFixes(mat) {
  if (zFightFix) {
    mat.polygonOffset      = true;
    mat.polygonOffsetFactor = -1;
    mat.polygonOffsetUnits  = -1;
  }
  return mat;
}

function buildMaterial(type, roughness = 0.5, metalness = 0.1) {
  const side = currentFaceSide;
  let mat;
  switch (type) {
    case 'standard':
      mat = new THREE.MeshStandardMaterial({ color: 0xdddddd, roughness, metalness, side }); break;
    case 'wireframe':
      mat = new THREE.MeshBasicMaterial({ color: 0x44aaff, wireframe: true }); break;
    case 'normals':
      mat = new THREE.MeshNormalMaterial({ side }); break;
    case 'toon': {
      const colors = new Uint8Array([64, 128, 200, 255]);
      const gradMap = new THREE.DataTexture(colors, colors.length / 4, 1);
      gradMap.needsUpdate = true;
      mat = new THREE.MeshToonMaterial({ color: 0x88ccff, gradientMap: gradMap, side }); break;
    }
    case 'xray':
      mat = new THREE.MeshBasicMaterial({ color: 0x00ffff, transparent: true, opacity: 0.18, depthWrite: false, side }); break;
    case 'depth':
      mat = new THREE.MeshDepthMaterial({ depthPacking: THREE.RGBADepthPacking, side }); break;
    case 'hologram':
      mat = new THREE.ShaderMaterial({
        uniforms: { time: { value: 0 }, color: { value: new THREE.Color(0x00ffcc) } },
        vertexShader: `
          varying vec3 vNormal; varying vec3 vPosition;
          void main() {
            vNormal = normalize(normalMatrix * normal); vPosition = position;
            gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0);
          }`,
        fragmentShader: `
          uniform float time; uniform vec3 color;
          varying vec3 vNormal; varying vec3 vPosition;
          void main() {
            float fresnel = pow(1.0 - abs(dot(vNormal, vec3(0,0,1))), 2.5);
            float scan = step(0.5, fract(vPosition.y * 8.0 - time * 1.5));
            gl_FragColor = vec4(color * (fresnel + 0.3), fresnel * 0.9 + scan * 0.15);
          }`,
        transparent: true, side, depthWrite: false
      }); break;
    case 'clay':
      mat = new THREE.MeshStandardMaterial({ color: 0xc8a882, roughness: 0.95, metalness: 0.0, side }); break;
    default:
      mat = new THREE.MeshStandardMaterial({ color: 0xaaaaaa, side });
  }
  return applyMeshFixes(mat);
}

// ─── Projection Material Builder ──────────────────────────────────────────────

function buildProjectionMaterial(texture, params, boundsMin, boundsSize) {
  const mat = new THREE.ShaderMaterial({
    uniforms: {
      tMap:              { value: texture },
      uProjection:       { value: params.projection },
      uBoundsMin:        { value: boundsMin.clone() },
      uBoundsSize:       { value: boundsSize.clone() },
      uTiling:           { value: new THREE.Vector2(params.tilingX, params.tilingY) },
      uOffset:           { value: new THREE.Vector2(params.offsetX, params.offsetY) },
      uAnimOffset:       { value: new THREE.Vector2(0, 0) },
      uRotation:         { value: params.rotation },
      uOpacity:          { value: params.opacity },
      uBlendMode:        { value: params.blendMode },
      uBaseColor:        { value: new THREE.Color(0xdddddd) },
      uKeyPos:           { value: keyLight.position },
      uKeyIntensity:     { value: keyLight.intensity },
      uAmbientIntensity: { value: ambientLight.intensity },
    },
    vertexShader:   PROJECTION_VERT,
    fragmentShader: PROJECTION_FRAG,
    side:           currentFaceSide,
    transparent:    false,
  });
  return applyMeshFixes(mat);
}

// ─── State ────────────────────────────────────────────────────────────────────

let currentModel    = null;
let currentShader   = 'standard';
let currentRoughness= 0.5;
let currentMetalness= 0.1;
let modelBoundsMin  = new THREE.Vector3();
let modelBoundsSize = new THREE.Vector3();

let currentTexture  = null;
let videoElement    = null;
let texEnabled      = false;

const texParams = {
  projection: 2,
  blendMode:  0,
  opacity:    1.0,
  tilingX:    1.0,
  tilingY:    1.0,
  offsetX:    0.0,
  offsetY:    0.0,
  rotation:   0.0,
};

// Texture animation
const animState = {
  enabled: false,
  speedX:  0.1,
  speedY:  0.0,
  accX:    0.0,
  accY:    0.0,
};

function getModelLocalBounds(model) {
  const box = new THREE.Box3();
  model.traverse(child => {
    if (child.isMesh) {
      child.geometry.computeBoundingBox();
      if (child.geometry.boundingBox) box.union(child.geometry.boundingBox);
    }
  });
  return box;
}

function applyMaterial(shader, roughness, metalness) {
  if (!currentModel) return;
  const mat = (currentTexture && texEnabled)
    ? buildProjectionMaterial(currentTexture, texParams, modelBoundsMin, modelBoundsSize)
    : buildMaterial(shader, roughness, metalness);

  currentModel.traverse(child => {
    if (child.isMesh) {
      child.material = mat;
      child.castShadow = true;
      child.receiveShadow = true;
    }
  });
}

function updateProjectionUniforms() {
  if (!currentModel || !currentTexture || !texEnabled) return;
  currentModel.traverse(child => {
    if (child.isMesh && child.material.uniforms) {
      const u = child.material.uniforms;
      u.uProjection.value      = texParams.projection;
      u.uTiling.value.set(texParams.tilingX, texParams.tilingY);
      u.uOffset.value.set(texParams.offsetX, texParams.offsetY);
      u.uRotation.value        = texParams.rotation;
      u.uOpacity.value         = texParams.opacity;
      u.uBlendMode.value       = texParams.blendMode;
      u.uKeyIntensity.value    = keyLight.intensity;
      u.uAmbientIntensity.value= ambientLight.intensity;
    }
  });
}

function centerAndFitModel(model) {
  const box    = new THREE.Box3().setFromObject(model);
  const center = box.getCenter(new THREE.Vector3());
  const size   = box.getSize(new THREE.Vector3());
  const maxDim = Math.max(size.x, size.y, size.z);
  const scale  = 2 / maxDim;

  model.scale.setScalar(scale);
  model.position.sub(center.multiplyScalar(scale));

  const box2 = new THREE.Box3().setFromObject(model);
  model.position.y -= box2.min.y;

  const localBox = getModelLocalBounds(model);
  modelBoundsMin.copy(localBox.min);
  modelBoundsSize.copy(localBox.getSize(new THREE.Vector3()));

  const fitDist = (maxDim * scale) * 1.5 / Math.tan((camera.fov / 2) * (Math.PI / 180));
  camera.position.set(0, (maxDim * scale) * 0.5, fitDist);
  controls.target.set(0, (maxDim * scale) * 0.3, 0);
  controls.update();
}

// ─── Geometry Repair ──────────────────────────────────────────────────────────

const repairStatusEl = document.getElementById('repair-status');

function repairMesh() {
  if (!currentModel) return;
  let fixed = 0, flipped = 0;

  currentModel.traverse(child => {
    if (!child.isMesh) return;
    let geo = child.geometry;

    // 1. Merge duplicate vertices (reduces z-fighting between overlapping faces)
    try {
      const before = geo.index ? geo.index.count / 3 : geo.attributes.position.count / 3;
      geo = mergeVertices(geo, 0.0001);
      const after = geo.index ? geo.index.count / 3 : geo.attributes.position.count / 3;
      fixed += before - after;
    } catch(e) {}

    // 2. Recompute vertex normals (fixes shading artifacts from bad export normals)
    geo.computeVertexNormals();

    child.geometry = geo;
    flipped++;
  });

  // Re-apply material so culling/fixes take effect
  applyMaterial(currentShader, currentRoughness, currentMetalness);

  repairStatusEl.textContent = `Repaired ${flipped} mesh(es) — removed ~${fixed} degenerate faces`;
  repairStatusEl.style.color = '#7fa';
}

function flipNormals() {
  if (!currentModel) return;
  currentModel.traverse(child => {
    if (!child.isMesh) return;
    const normals = child.geometry.attributes.normal;
    if (!normals) return;
    for (let i = 0; i < normals.count; i++) {
      normals.setXYZ(i, -normals.getX(i), -normals.getY(i), -normals.getZ(i));
    }
    normals.needsUpdate = true;
    // Also flip face winding if indexed
    const idx = child.geometry.index;
    if (idx) {
      for (let i = 0; i < idx.count; i += 3) {
        const tmp = idx.getX(i + 1);
        idx.setX(i + 1, idx.getX(i + 2));
        idx.setX(i + 2, tmp);
      }
      idx.needsUpdate = true;
    }
  });
  applyMaterial(currentShader, currentRoughness, currentMetalness);
  repairStatusEl.textContent = 'Normals flipped';
  repairStatusEl.style.color = '#fa7';
}

// ─── PSD Loader ───────────────────────────────────────────────────────────────

async function loadPSD(arrayBuffer) {
  const psd     = Psd.parse(arrayBuffer);
  const pixels  = await psd.composite();
  const canvas  = document.createElement('canvas');
  canvas.width  = psd.width;
  canvas.height = psd.height;
  canvas.getContext('2d').putImageData(
    new ImageData(new Uint8ClampedArray(pixels.buffer), psd.width, psd.height), 0, 0
  );
  const tex = new THREE.CanvasTexture(canvas);
  tex.colorSpace = THREE.SRGBColorSpace;
  tex.wrapS = tex.wrapT = THREE.RepeatWrapping;
  return tex;
}

// ─── Texture Loader ───────────────────────────────────────────────────────────

const texStatusEl   = document.getElementById('tex-status');
const videoControls = document.getElementById('video-controls');

async function loadTextureFile(file) {
  if (videoElement) {
    videoElement.pause();
    URL.revokeObjectURL(videoElement.src);
    videoElement = null;
    videoControls.style.display = 'none';
  }
  if (currentTexture) { currentTexture.dispose(); currentTexture = null; }

  const ext = file.name.split('.').pop().toLowerCase();
  texStatusEl.textContent = `Loading ${file.name}…`;
  texStatusEl.style.color = '#aaa';

  try {
    if (ext === 'psd') {
      currentTexture = await loadPSD(await file.arrayBuffer());

    } else if (['mov', 'mp4', 'webm'].includes(ext)) {
      const url    = URL.createObjectURL(file);
      videoElement = document.createElement('video');
      Object.assign(videoElement, { src: url, loop: true, muted: true, playsInline: true, crossOrigin: 'anonymous' });
      await new Promise((res, rej) => {
        videoElement.onloadeddata = res;
        videoElement.onerror = () => rej(new Error('Video failed — check codec (try WebM/VP9 for alpha)'));
      });
      videoElement.play();
      const vTex = new THREE.VideoTexture(videoElement);
      vTex.colorSpace = THREE.SRGBColorSpace;
      vTex.wrapS = vTex.wrapT = THREE.RepeatWrapping;
      currentTexture = vTex;
      videoControls.style.display = 'flex';

    } else {
      currentTexture = await new Promise((res, rej) => {
        new THREE.TextureLoader().load(
          URL.createObjectURL(file),
          tex => {
            tex.colorSpace = THREE.SRGBColorSpace;
            tex.wrapS = tex.wrapT = THREE.RepeatWrapping;
            res(tex);
          },
          undefined, rej
        );
      });
    }

    texStatusEl.textContent = `${file.name} (${ext.toUpperCase()})`;
    texStatusEl.style.color = '#7fa';

    document.getElementById('tex-toggle').checked = true;
    texEnabled = true;
    // Reset animation accumulator on new texture
    animState.accX = animState.accY = 0;
    applyMaterial(currentShader, currentRoughness, currentMetalness);

  } catch (err) {
    texStatusEl.textContent = `Error: ${err.message}`;
    texStatusEl.style.color = '#f77';
    console.error(err);
  }
}

// ─── OBJ Loader ───────────────────────────────────────────────────────────────

const objLoader = new OBJLoader();
const statusEl  = document.getElementById('status');

document.getElementById('obj-input').addEventListener('change', (e) => {
  const file = e.target.files[0];
  if (!file) return;
  statusEl.textContent = `Loading ${file.name}…`;
  statusEl.style.color = '#aaa';

  const reader = new FileReader();
  reader.onload = (evt) => {
    try {
      if (currentModel) {
        scene.remove(currentModel);
        currentModel.traverse(child => {
          if (child.isMesh) {
            child.geometry.dispose();
            [child.material].flat().forEach(m => m.dispose());
          }
        });
        currentModel = null;
      }

      const obj = objLoader.parse(evt.target.result);
      centerAndFitModel(obj);
      applyMaterial(currentShader, currentRoughness, currentMetalness);
      scene.add(obj);
      currentModel = obj;

      const meshes = [];
      obj.traverse(c => { if (c.isMesh) meshes.push(c); });
      statusEl.textContent = `${file.name} — ${meshes.length} mesh(es)`;
      statusEl.style.color = '#7af';

      if (repairStatusEl) { repairStatusEl.textContent = ''; }
    } catch (err) {
      statusEl.textContent = `Error: ${err.message}`;
      statusEl.style.color = '#f77';
    }
  };
  reader.readAsText(file);
});

// ─── Texture UI ───────────────────────────────────────────────────────────────

document.getElementById('tex-input').addEventListener('change', (e) => {
  if (e.target.files[0]) loadTextureFile(e.target.files[0]);
});

document.getElementById('tex-toggle').addEventListener('change', (e) => {
  texEnabled = e.target.checked;
  applyMaterial(currentShader, currentRoughness, currentMetalness);
});

document.getElementById('projection-select').addEventListener('change', (e) => {
  texParams.projection = parseInt(e.target.value);
  applyMaterial(currentShader, currentRoughness, currentMetalness);
});

document.getElementById('blend-select').addEventListener('change', (e) => {
  texParams.blendMode = parseInt(e.target.value);
  updateProjectionUniforms();
});

document.getElementById('clear-tex').addEventListener('click', () => {
  if (videoElement) { videoElement.pause(); URL.revokeObjectURL(videoElement.src); videoElement = null; }
  if (currentTexture) { currentTexture.dispose(); currentTexture = null; }
  texEnabled = false;
  animState.accX = animState.accY = 0;
  document.getElementById('tex-toggle').checked = false;
  videoControls.style.display = 'none';
  texStatusEl.textContent = 'No texture loaded';
  texStatusEl.style.color = '#666';
  applyMaterial(currentShader, currentRoughness, currentMetalness);
});

document.getElementById('vid-play').addEventListener('click', () => {
  if (!videoElement) return;
  if (videoElement.paused) { videoElement.play(); document.getElementById('vid-play').textContent = '⏸ Pause'; }
  else { videoElement.pause(); document.getElementById('vid-play').textContent = '▶ Play'; }
});

document.getElementById('vid-loop').addEventListener('click', () => {
  if (!videoElement) return;
  videoElement.loop = !videoElement.loop;
  document.getElementById('vid-loop').textContent = `Loop ${videoElement.loop ? 'ON' : 'OFF'}`;
});

// Animation controls
document.getElementById('anim-toggle').addEventListener('change', (e) => {
  animState.enabled = e.target.checked;
  if (!animState.enabled) {
    // Reset accumulated offset so texture snaps back when re-enabled
    animState.accX = animState.accY = 0;
    updateProjectionUniforms();
  }
});

document.getElementById('anim-reset').addEventListener('click', () => {
  animState.accX = animState.accY = 0;
});

// ─── Mesh Repair UI ───────────────────────────────────────────────────────────

document.getElementById('face-cull').addEventListener('change', (e) => {
  const v = e.target.value;
  currentFaceSide = v === 'front' ? THREE.FrontSide
                  : v === 'back'  ? THREE.BackSide
                  : THREE.DoubleSide;
  applyMaterial(currentShader, currentRoughness, currentMetalness);
});

document.getElementById('zfight-toggle').addEventListener('change', (e) => {
  zFightFix = e.target.checked;
  applyMaterial(currentShader, currentRoughness, currentMetalness);
});

document.getElementById('repair-btn').addEventListener('click', repairMesh);
document.getElementById('flip-normals-btn').addEventListener('click', flipNormals);

// ─── Slider Helpers ───────────────────────────────────────────────────────────

function bindSlider(id, valId, decimals, onChange) {
  const slider  = document.getElementById(id);
  const display = document.getElementById(valId);
  slider.addEventListener('input', () => {
    const v = parseFloat(slider.value);
    display.textContent = v.toFixed(decimals);
    onChange(v);
  });
}

bindSlider('light-intensity', 'light-intensity-val', 1, v => { keyLight.intensity = v; updateProjectionUniforms(); });
bindSlider('ambient',         'ambient-val',         1, v => { ambientLight.intensity = v; updateProjectionUniforms(); });
bindSlider('roughness',       'roughness-val',       2, v => { currentRoughness = v; if (!texEnabled) applyMaterial(currentShader, v, currentMetalness); });
bindSlider('metalness',       'metalness-val',       2, v => { currentMetalness = v; if (!texEnabled) applyMaterial(currentShader, currentRoughness, v); });

bindSlider('tex-opacity',  'tex-opacity-val',  2, v => { texParams.opacity  = v; updateProjectionUniforms(); });
bindSlider('tiling-x',     'tiling-x-val',     1, v => { texParams.tilingX  = v; updateProjectionUniforms(); });
bindSlider('tiling-y',     'tiling-y-val',     1, v => { texParams.tilingY  = v; updateProjectionUniforms(); });
bindSlider('offset-x',     'offset-x-val',     2, v => { texParams.offsetX  = v; updateProjectionUniforms(); });
bindSlider('offset-y',     'offset-y-val',     2, v => { texParams.offsetY  = v; updateProjectionUniforms(); });
bindSlider('anim-speed-x', 'anim-speed-x-val', 2, v => { animState.speedX   = v; });
bindSlider('anim-speed-y', 'anim-speed-y-val', 2, v => { animState.speedY   = v; });

document.getElementById('tex-rotation').addEventListener('input', (e) => {
  const deg = parseFloat(e.target.value);
  document.getElementById('tex-rotation-val').textContent = `${deg}°`;
  texParams.rotation = deg * (Math.PI / 180);
  updateProjectionUniforms();
});

// ─── Shader / Camera UI ───────────────────────────────────────────────────────

document.getElementById('shader-select').addEventListener('change', (e) => {
  currentShader = e.target.value;
  applyMaterial(currentShader, currentRoughness, currentMetalness);
});

document.getElementById('auto-rotate').addEventListener('change', (e) => {
  const speed = parseFloat(e.target.value);
  controls.autoRotate = speed > 0;
  controls.autoRotateSpeed = speed;
});

document.getElementById('reset-camera').addEventListener('click', () => {
  if (currentModel) centerAndFitModel(currentModel);
  else { camera.position.set(0, 1, 4); controls.target.set(0, 0, 0); controls.update(); }
});

// ─── 4K PNG Export ────────────────────────────────────────────────────────────

document.getElementById('export-btn').addEventListener('click', () => {
  const resStr = document.getElementById('export-res').value;
  const [exportW, exportH] = resStr.split('x').map(Number);
  const origW = renderer.domElement.width;
  const origH = renderer.domElement.height;
  const origAspect = camera.aspect;

  renderer.setSize(exportW, exportH, false);
  camera.aspect = exportW / exportH;
  camera.updateProjectionMatrix();
  renderer.render(scene, camera);

  const link     = document.createElement('a');
  const filename = `wintermute_${resStr}_${Date.now()}.png`;
  link.download  = filename;
  link.href      = renderer.domElement.toDataURL('image/png');
  link.click();

  renderer.setSize(origW, origH, false);
  camera.aspect = origAspect;
  camera.updateProjectionMatrix();
  statusEl.textContent = `Exported ${filename}`;
  statusEl.style.color = '#af7';
});

// ─── Animate ──────────────────────────────────────────────────────────────────

const clock   = new THREE.Clock();
let prevTime  = 0;

function animate() {
  requestAnimationFrame(animate);
  const elapsed = clock.getElapsedTime();
  const delta   = elapsed - prevTime;
  prevTime       = elapsed;

  if (currentModel) {
    // Hologram time uniform
    if (currentShader === 'hologram' && !texEnabled) {
      currentModel.traverse(child => {
        if (child.isMesh && child.material.uniforms?.time)
          child.material.uniforms.time.value = elapsed;
      });
    }

    // Texture animation — scroll uAnimOffset each frame
    if (animState.enabled && texEnabled && currentTexture) {
      animState.accX += animState.speedX * delta;
      animState.accY += animState.speedY * delta;
      currentModel.traverse(child => {
        if (child.isMesh && child.material.uniforms?.uAnimOffset)
          child.material.uniforms.uAnimOffset.value.set(animState.accX, animState.accY);
      });
    }

    // Video texture sync
    if (currentTexture?.isVideoTexture) currentTexture.needsUpdate = true;
  }

  controls.update();
  renderer.render(scene, camera);
}

window.addEventListener('resize', () => {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
});

animate();
