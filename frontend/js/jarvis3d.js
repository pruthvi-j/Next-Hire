/**
 * NEXT HIRE - 3D JARVIS Character Controller
 * Replaces the Siri orb with a futuristic humanoid armored AI using Three.js
 */

(function () {
  const JARVIS_STATES = {
    IDLE: 'idle',
    LISTENING: 'listening',
    THINKING: 'thinking',
    SPEAKING: 'speaking'
  };

  let scene, camera, renderer, clock;
  let characterGroup, modelMesh;
  let holoRings = [];
  let particles;
  
  let currentState = JARVIS_STATES.IDLE;
  let currentVol = 0; // Audio volume from microphone
  
  // State target values for smooth interpolation
  let targets = {
    glowIntensity: 1.0,
    particleSpeed: 0.001,
    ringSpeed: 0.01,
    ringOpacity: 0.1,
    breathingSpeed: 1.0,
    breathingAmp: 0.02
  };
  
  // Current values
  let current = {
    glowIntensity: 1.0,
    particleSpeed: 0.001,
    ringSpeed: 0.01,
    ringOpacity: 0.1,
    breathingSpeed: 1.0,
    breathingAmp: 0.02
  };
  
  // Materials that need to be updated (emissive parts)
  let emissiveMaterials = [];
  
  function init() {
    const container = document.getElementById('jarvis-3d-container');
    if (!container) return;

    // SCENE
    scene = new THREE.Scene();
    
    // CAMERA
    camera = new THREE.PerspectiveCamera(45, container.clientWidth / container.clientHeight, 0.1, 100);
    camera.position.set(0, 1.2, 3.5);
    
    // RENDERER
    renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
    renderer.setSize(container.clientWidth, container.clientHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setClearColor(0x000000, 0); // Transparent
    // Support newer three.js format depending on version
    if(THREE.sRGBEncoding) renderer.outputEncoding = THREE.sRGBEncoding;
    if(THREE.ACESFilmicToneMapping) renderer.toneMapping = THREE.ACESFilmicToneMapping;
    container.appendChild(renderer.domElement);
    
    clock = new THREE.Clock();
    
    // LIGHTING
    const ambientLight = new THREE.AmbientLight(0x1a2b4c, 1.5);
    scene.add(ambientLight);
    
    const rimLight = new THREE.DirectionalLight(0x00d2ff, 3);
    rimLight.position.set(-1, 2, -2);
    scene.add(rimLight);
    
    const rimLight2 = new THREE.DirectionalLight(0xff0044, 2);
    rimLight2.position.set(2, -1, -2);
    scene.add(rimLight2);
    
    const fillLight = new THREE.DirectionalLight(0x38bdf8, 1);
    fillLight.position.set(0, 0, 2);
    scene.add(fillLight);
    
    // CHARACTER GROUP
    characterGroup = new THREE.Group();
    scene.add(characterGroup);
    
    // LOAD MODEL
    loadModel();
    
    // ADD EFFECTS
    createHoloRings();
    createParticles();
    createBasePlatform();
    
    // EVENTS
    window.addEventListener('resize', onWindowResize, false);
    
    // ANIMATION LOOP
    renderer.setAnimationLoop(renderLoop);
  }
  
  function loadModel() {
    const loader = new THREE.GLTFLoader();
    // Using a standard Khronos rigged figure and reskinning it as an armored AI
    const url = 'https://raw.githubusercontent.com/KhronosGroup/glTF-Sample-Models/master/2.0/RiggedFigure/glTF-Binary/RiggedFigure.glb';
    
    loader.load(url, function (gltf) {
      const model = gltf.scene;
      
      // Reskin materials to look like futuristic armor (Red/Gold/Gunmetal)
      const armorMaterial = new THREE.MeshStandardMaterial({
        color: 0x8a0303, // Deep Red
        metalness: 0.9,
        roughness: 0.2,
      });
      
      const jointMaterial = new THREE.MeshStandardMaterial({
        color: 0x111111, // Dark Gunmetal
        metalness: 0.8,
        roughness: 0.5,
      });
      
      const goldMaterial = new THREE.MeshStandardMaterial({
        color: 0xd4af37, // Gold accent
        metalness: 1.0,
        roughness: 0.1,
      });
      
      const coreEmissive = new THREE.MeshStandardMaterial({
        color: 0x00ffff,
        emissive: 0x00ffff,
        emissiveIntensity: 2.0,
        metalness: 0.1,
        roughness: 0.1
      });
      emissiveMaterials.push(coreEmissive);

      model.traverse((child) => {
        if (child.isMesh) {
          child.material = armorMaterial;
          
          // Add some glowing parts artificially if we can't target eyes/chest directly
          if (Math.random() > 0.8) {
             child.material = coreEmissive;
          } else if (Math.random() > 0.6) {
             child.material = goldMaterial;
          }
        }
      });
      
      // Scale and position
      model.scale.set(1.2, 1.2, 1.2);
      model.position.y = -0.5;
      
      // We manually create a glowing chest core
      const coreGeo = new THREE.SphereGeometry(0.1, 16, 16);
      const coreMesh = new THREE.Mesh(coreGeo, coreEmissive);
      coreMesh.position.set(0, 0.7, 0.15); // Approximate chest area
      coreMesh.scale.z = 0.5;
      model.add(coreMesh);
      
      characterGroup.add(model);
      modelMesh = model;
      
    }, undefined, function (error) {
      console.error('ThreeJS JARVIS Model loading error:', error);
      createFallbackRobot();
    });
  }
  
  function createFallbackRobot() {
    const coreEmissive = new THREE.MeshStandardMaterial({
        color: 0x00ffff,
        emissive: 0x00ffff,
        emissiveIntensity: 2.0,
    });
    emissiveMaterials.push(coreEmissive);
      
    const armorMat = new THREE.MeshStandardMaterial({
        color: 0x8a0303, metalness: 0.9, roughness: 0.2,
    });
    
    // Head
    const head = new THREE.Mesh(new THREE.BoxGeometry(0.3, 0.3, 0.3), armorMat);
    head.position.y = 1.2;
    characterGroup.add(head);
    
    // Eye
    const eye = new THREE.Mesh(new THREE.PlaneGeometry(0.2, 0.05), coreEmissive);
    eye.position.set(0, 1.25, 0.16);
    characterGroup.add(eye);
    
    // Torso
    const torso = new THREE.Mesh(new THREE.CylinderGeometry(0.3, 0.2, 0.8, 8), armorMat);
    torso.position.y = 0.6;
    characterGroup.add(torso);
    
    // Core
    const core = new THREE.Mesh(new THREE.SphereGeometry(0.1), coreEmissive);
    core.position.set(0, 0.6, 0.2);
    characterGroup.add(core);
    
    modelMesh = characterGroup;
  }
  
  function createHoloRings() {
    const ringMat = new THREE.MeshBasicMaterial({
      color: 0x00d2ff,
      transparent: true,
      opacity: 0.1,
      side: THREE.DoubleSide,
      wireframe: true
    });
    
    for (let i=0; i<3; i++) {
      const geo = new THREE.TorusGeometry(0.8 + i*0.2, 0.01, 3, 30);
      const ring = new THREE.Mesh(geo, ringMat);
      ring.rotation.x = Math.PI / 2;
      ring.position.y = 0.5;
      holoRings.push(ring);
      scene.add(ring);
    }
  }
  
  function createBasePlatform() {
    const geo = new THREE.CylinderGeometry(1.2, 1.5, 0.1, 32);
    const mat = new THREE.MeshStandardMaterial({
      color: 0x0f172a,
      metalness: 0.8,
      roughness: 0.2
    });
    const platform = new THREE.Mesh(geo, mat);
    platform.position.y = -0.55;
    scene.add(platform);
    
    // Inner glowing ring
    const glowGeo = new THREE.RingGeometry(0.8, 0.9, 32);
    const glowMat = new THREE.MeshBasicMaterial({ color: 0x00d2ff, transparent: true, opacity: 0.5 });
    const glowRing = new THREE.Mesh(glowGeo, glowMat);
    glowRing.rotation.x = -Math.PI / 2;
    glowRing.position.y = -0.49;
    scene.add(glowRing);
  }
  
  function createParticles() {
    const particleCount = 200;
    const geo = new THREE.BufferGeometry();
    const positions = new Float32Array(particleCount * 3);
    
    for(let i=0; i < particleCount * 3; i++) {
      positions[i] = (Math.random() - 0.5) * 4;
    }
    
    geo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    
    const mat = new THREE.PointsMaterial({
      color: 0x38bdf8,
      size: 0.02,
      transparent: true,
      opacity: 0.6,
      blending: THREE.AdditiveBlending
    });
    
    particles = new THREE.Points(geo, mat);
    scene.add(particles);
  }
  
  function onWindowResize() {
    const container = document.getElementById('jarvis-3d-container');
    if (!container || !camera || !renderer) return;
    
    camera.aspect = container.clientWidth / container.clientHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(container.clientWidth, container.clientHeight);
  }
  
  function renderLoop() {
    const elapsedTime = clock.getElapsedTime();
    
    // Smooth interpolate state targets
    current.glowIntensity += (targets.glowIntensity - current.glowIntensity) * 0.1;
    current.particleSpeed += (targets.particleSpeed - current.particleSpeed) * 0.1;
    current.ringSpeed += (targets.ringSpeed - current.ringSpeed) * 0.05;
    current.ringOpacity += (targets.ringOpacity - current.ringOpacity) * 0.1;
    current.breathingSpeed += (targets.breathingSpeed - current.breathingSpeed) * 0.05;
    current.breathingAmp += (targets.breathingAmp - current.breathingAmp) * 0.1;
    
    // Apply Audio Reactive Glow
    let finalGlow = current.glowIntensity;
    if (currentState === JARVIS_STATES.LISTENING && currentVol > 0.01) {
      finalGlow += currentVol * 5.0; // React to real mic volume
    } else if (currentState === JARVIS_STATES.SPEAKING) {
      // Simulate speaking volume with a sine wave since TTS doesn't give audio stream
      finalGlow += (Math.sin(elapsedTime * 15) * 0.5 + 0.5) * 1.5;
    }
    
    emissiveMaterials.forEach(mat => {
      mat.emissiveIntensity = finalGlow;
    });
    
    // Character Breathing Animation
    if (characterGroup) {
      characterGroup.position.y = Math.sin(elapsedTime * current.breathingSpeed) * current.breathingAmp;
      
      // Subtle head/body looking around
      if (currentState !== JARVIS_STATES.THINKING) {
        characterGroup.rotation.y = Math.sin(elapsedTime * 0.5) * 0.1;
      } else {
        characterGroup.rotation.y = 0; // Stiff when thinking
      }
    }
    
    // Holographic Rings
    holoRings.forEach((ring, idx) => {
      ring.rotation.z = elapsedTime * current.ringSpeed * (idx % 2 === 0 ? 1 : -1);
      ring.material.opacity = current.ringOpacity;
      
      if (currentState === JARVIS_STATES.THINKING) {
        ring.position.y = 0.5 + Math.sin(elapsedTime * 2 + idx) * 0.4;
      } else {
        ring.position.y += (0.5 - ring.position.y) * 0.1;
      }
    });
    
    // Particles
    if (particles) {
      particles.rotation.y = elapsedTime * current.particleSpeed;
      const positions = particles.geometry.attributes.position.array;
      for(let i=1; i < positions.length; i+=3) {
        positions[i] += current.particleSpeed;
        if (positions[i] > 2) positions[i] = -2;
      }
      particles.geometry.attributes.position.needsUpdate = true;
    }
    
    renderer.render(scene, camera);
  }
  
  // PUBLIC API
  window.Jarvis3D = {
    setState: function(state) {
      currentState = state;
      
      switch(state) {
        case JARVIS_STATES.IDLE:
          targets = { glowIntensity: 1.5, particleSpeed: 0.05, ringSpeed: 0.5, ringOpacity: 0.05, breathingSpeed: 1.5, breathingAmp: 0.02 };
          break;
        case JARVIS_STATES.LISTENING:
          targets = { glowIntensity: 2.5, particleSpeed: 0.2, ringSpeed: 1.0, ringOpacity: 0.2, breathingSpeed: 2.5, breathingAmp: 0.04 };
          break;
        case JARVIS_STATES.THINKING:
          targets = { glowIntensity: 1.0, particleSpeed: 0.05, ringSpeed: 3.0, ringOpacity: 0.5, breathingSpeed: 0.5, breathingAmp: 0.01 };
          break;
        case JARVIS_STATES.SPEAKING:
          targets = { glowIntensity: 3.0, particleSpeed: 0.1, ringSpeed: 1.5, ringOpacity: 0.3, breathingSpeed: 3.0, breathingAmp: 0.05 };
          break;
      }
    },
    
    updateVolume: function(vol) {
      currentVol = vol;
    }
  };

  // Initialize on load
  window.addEventListener('load', init);

})();
