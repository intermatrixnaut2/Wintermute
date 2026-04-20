import * as THREE from 'three';
import { OBJLoader } from 'three/addons/loaders/OBJLoader.js';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

// ─── Scene Setup ──────────────────────────────────────────────────────────────

const container = document.getElementById('canvas-container');

const renderer = new THREE.WebGLRenderer({
  antialias: true,
  preserveDrawingBuffer: true, // required for PNG export
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
keyLight.shadow.camera.near = 0.1;
keyLight.shadow.camera.far = 50;
scene.add(keyLight);

const fillLight = new THREE.DirectionalLight(0x8888ff, 0.8);
fillLight.position.set(-5, 3, -3);
scene.add(fillLight);

const rimLight = new THREE.DirectionalLight(0xffaa44, 0.6);
rimLight.position.set(0, -2, -5);
scene.add(rimLight);

// Ground plane (receives shadows)
const groundGeo = new THREE.PlaneGeometry(20, 20);
const groundMat = new THREE.ShadowMaterial({ opacity: 0.3 });
const ground = new THREE.Mesh(groundGeo, groundMat);
ground.rotation.x = -Math.PI / 2;
ground.position.y = -0.001;
ground.receiveShadow = true;
scene.add(ground);

// ─── Material Library ─────────────────────────────────────────────────────────

function buildMaterial(type, roughness = 0.5, metalness = 0.1) {
  switch (type) {
    case 'standard':
      return new THREE.MeshStandardMaterial({
        color: 0xdddddd,
        roughness,
        metalness,
        side: THREE.DoubleSide
      });

    case 'wireframe':
      return new THREE.MeshBasicMaterial({
        color: 0x44aaff,
        wireframe: true
      });

    case 'normals':
      return new THREE.MeshNormalMaterial({ side: THREE.DoubleSide });

    case 'toon': {
      const colors = new Uint8Array([64, 128, 200, 255]);
      const gradMap = new THREE.DataTexture(colors, colors.length / 4, 1);
      gradMap.needsUpdate = true;
      return new THREE.MeshToonMaterial({
        color: 0x88ccff,
        gradientMap: gradMap,
        side: THREE.DoubleSide
      });
    }

    case 'xray':
      return new THREE.MeshBasicMaterial({
        color: 0x00ffff,
        wireframe: false,
        transparent: true,
        opacity: 0.18,
        depthWrite: false,
        side: THREE.DoubleSide
      });

    case 'depth':
      return new THREE.MeshDepthMaterial({
        depthPacking: THREE.RGBADepthPacking,
        side: THREE.DoubleSide
      });

    case 'hologram':
      return new THREE.ShaderMaterial({
        uniforms: {
          time: { value: 0 },
          color: { value: new THREE.Color(0x00ffcc) }
        },
        vertexShader: `
          varying vec3 vNormal;
          varying vec3 vPosition;
          void main() {
            vNormal = normalize(normalMatrix * normal);
            vPosition = position;
            gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
          }
        `,
        fragmentShader: `
          uniform float time;
          uniform vec3 color;
          varying vec3 vNormal;
          varying vec3 vPosition;
          void main() {
            float fresnel = pow(1.0 - abs(dot(vNormal, vec3(0.0, 0.0, 1.0))), 2.5);
            float scan = step(0.5, fract(vPosition.y * 8.0 - time * 1.5));
            float alpha = fresnel * 0.9 + scan * 0.15;
            gl_FragColor = vec4(color * (fresnel + 0.3), alpha);
          }
        `,
        transparent: true,
        side: THREE.DoubleSide,
        depthWrite: false
      });

    case 'clay':
      return new THREE.MeshStandardMaterial({
        color: 0xc8a882,
        roughness: 0.95,
        metalness: 0.0,
        side: THREE.DoubleSide
      });

    default:
      return new THREE.MeshStandardMaterial({ color: 0xaaaaaa, side: THREE.DoubleSide });
  }
}

// ─── State ────────────────────────────────────────────────────────────────────

let currentModel = null;
let currentShader = 'standard';
let currentRoughness = 0.5;
let currentMetalness = 0.1;

function applyMaterial(shader, roughness, metalness) {
  if (!currentModel) return;
  const mat = buildMaterial(shader, roughness, metalness);
  currentModel.traverse(child => {
    if (child.isMesh) {
      child.material = mat;
      child.castShadow = true;
      child.receiveShadow = true;
    }
  });
}

function centerAndFitModel(model) {
  const box = new THREE.Box3().setFromObject(model);
  const center = box.getCenter(new THREE.Vector3());
  const size = box.getSize(new THREE.Vector3());
  const maxDim = Math.max(size.x, size.y, size.z);

  // Normalize scale so largest dimension = 2 units
  const scale = 2 / maxDim;
  model.scale.setScalar(scale);
  model.position.sub(center.multiplyScalar(scale));

  // Sit on ground
  const box2 = new THREE.Box3().setFromObject(model);
  model.position.y -= box2.min.y;

  // Fit camera
  const fitDist = (maxDim * scale) * 1.5 / Math.tan((camera.fov / 2) * (Math.PI / 180));
  camera.position.set(0, (maxDim * scale) * 0.5, fitDist);
  controls.target.set(0, (maxDim * scale) * 0.3, 0);
  controls.update();
}

// ─── OBJ Loader ───────────────────────────────────────────────────────────────

const loader = new OBJLoader();
const statusEl = document.getElementById('status');

document.getElementById('obj-input').addEventListener('change', (e) => {
  const file = e.target.files[0];
  if (!file) return;

  statusEl.textContent = `Loading ${file.name}...`;
  statusEl.style.color = '#aaa';

  const reader = new FileReader();
  reader.onload = (evt) => {
    try {
      if (currentModel) {
        scene.remove(currentModel);
        currentModel.traverse(child => {
          if (child.isMesh) {
            child.geometry.dispose();
            if (Array.isArray(child.material)) {
              child.material.forEach(m => m.dispose());
            } else {
              child.material.dispose();
            }
          }
        });
        currentModel = null;
      }

      const obj = loader.parse(evt.target.result);
      centerAndFitModel(obj);
      applyMaterial(currentShader, currentRoughness, currentMetalness);
      scene.add(obj);
      currentModel = obj;

      const meshCount = [];
      obj.traverse(c => { if (c.isMesh) meshCount.push(c); });
      statusEl.textContent = `${file.name} — ${meshCount.length} mesh(es)`;
      statusEl.style.color = '#7af';
    } catch (err) {
      statusEl.textContent = `Error: ${err.message}`;
      statusEl.style.color = '#f77';
      console.error(err);
    }
  };
  reader.readAsText(file);
});

// ─── UI Controls ──────────────────────────────────────────────────────────────

function bindSlider(id, valId, decimals, onChange) {
  const slider = document.getElementById(id);
  const display = document.getElementById(valId);
  slider.addEventListener('input', () => {
    const v = parseFloat(slider.value);
    display.textContent = v.toFixed(decimals);
    onChange(v);
  });
}

bindSlider('light-intensity', 'light-intensity-val', 1, v => { keyLight.intensity = v; });
bindSlider('ambient', 'ambient-val', 1, v => { ambientLight.intensity = v; });
bindSlider('roughness', 'roughness-val', 2, v => {
  currentRoughness = v;
  applyMaterial(currentShader, currentRoughness, currentMetalness);
});
bindSlider('metalness', 'metalness-val', 2, v => {
  currentMetalness = v;
  applyMaterial(currentShader, currentRoughness, currentMetalness);
});

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
  if (currentModel) {
    centerAndFitModel(currentModel);
  } else {
    camera.position.set(0, 1, 4);
    controls.target.set(0, 0, 0);
    controls.update();
  }
});

// ─── 4K PNG Export ────────────────────────────────────────────────────────────

document.getElementById('export-btn').addEventListener('click', () => {
  const resStr = document.getElementById('export-res').value;
  const [exportW, exportH] = resStr.split('x').map(Number);

  // Save current state
  const origW = renderer.domElement.width;
  const origH = renderer.domElement.height;
  const origAspect = camera.aspect;

  // Resize to export resolution
  renderer.setSize(exportW, exportH, false);
  camera.aspect = exportW / exportH;
  camera.updateProjectionMatrix();

  // Render one frame at full resolution
  renderer.render(scene, camera);

  // Export
  const dataURL = renderer.domElement.toDataURL('image/png');
  const link = document.createElement('a');
  const filename = `wintermute_${resStr}_${Date.now()}.png`;
  link.download = filename;
  link.href = dataURL;
  link.click();

  // Restore viewport
  renderer.setSize(origW, origH, false);
  camera.aspect = origAspect;
  camera.updateProjectionMatrix();

  statusEl.textContent = `Exported ${filename}`;
  statusEl.style.color = '#af7';
});

// ─── Animate ──────────────────────────────────────────────────────────────────

const clock = new THREE.Clock();

function animate() {
  requestAnimationFrame(animate);
  const elapsed = clock.getElapsedTime();

  // Update hologram time uniform if active
  if (currentModel && currentShader === 'hologram') {
    currentModel.traverse(child => {
      if (child.isMesh && child.material.uniforms?.time) {
        child.material.uniforms.time.value = elapsed;
      }
    });
  }

  controls.update();
  renderer.render(scene, camera);
}

// ─── Resize ───────────────────────────────────────────────────────────────────

window.addEventListener('resize', () => {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
});

animate();
