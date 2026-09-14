import React, { useEffect, useRef } from 'react';
import * as THREE from 'three';

interface MachineCanvasProps {
  machineId: string;
  status: 'RUNNING' | 'STOPPED' | 'THROTTLED' | string;
  rpm: number;
  height?: number;
}

export const ThreeMachineCanvas: React.FC<MachineCanvasProps> = ({ machineId, status, rpm, height: propHeight }) => {
  const mountRef = useRef<HTMLDivElement>(null);
  const isRunning = status === 'RUNNING';
  const isThrottled = status === 'THROTTLED';

  useEffect(() => {
    const container = mountRef.current;
    if (!container) return;

    const width = container.clientWidth || 360;
    const height = propHeight || container.clientHeight || 240;

    // ═════════════════════════════════════════════════════════════════
    // 1. SCENE & DRAMATIC INDUSTRIAL FOUNDRY ATMOSPHERE
    // ═════════════════════════════════════════════════════════════════
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x060911);
    scene.fog = new THREE.FogExp2(0x060911, 0.045);

    const camera = new THREE.PerspectiveCamera(42, width / height, 0.1, 100);
    camera.position.set(4.6, 3.2, 5.2);
    camera.lookAt(0, 0.25, 0);

    let renderer: THREE.WebGLRenderer;
    try {
      renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: 'high-performance' });
      renderer.setSize(width, height);
      renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
      renderer.toneMapping = THREE.ACESFilmicToneMapping;
      renderer.toneMappingExposure = 1.4;
      renderer.shadowMap.enabled = true;
      renderer.shadowMap.type = THREE.PCFSoftShadowMap;
      container.innerHTML = '';
      container.appendChild(renderer.domElement);
    } catch (e) {
      console.warn('WebGL initialization fallback for:', machineId, e);
      return;
    }

    // ═════════════════════════════════════════════════════════════════
    // 2. PROCEDURAL TEXTURES (Brushed Steel, Carbon Grate, Warning Stripes)
    // ═════════════════════════════════════════════════════════════════
    const createBrushedSteelCanvas = () => {
      const cv = document.createElement('canvas');
      cv.width = 256;
      cv.height = 256;
      const ctx = cv.getContext('2d');
      if (ctx) {
        ctx.fillStyle = '#b8c2cc';
        ctx.fillRect(0, 0, 256, 256);
        for (let i = 0; i < 600; i++) {
          const y = Math.random() * 256;
          const alpha = 0.05 + Math.random() * 0.12;
          ctx.strokeStyle = Math.random() > 0.5 ? `rgba(255,255,255,${alpha})` : `rgba(30,41,59,${alpha})`;
          ctx.lineWidth = 1 + Math.random() * 2;
          ctx.beginPath();
          ctx.moveTo(0, y);
          ctx.lineTo(256, y);
          ctx.stroke();
        }
      }
      const tex = new THREE.CanvasTexture(cv);
      tex.wrapS = THREE.RepeatWrapping;
      tex.wrapT = THREE.RepeatWrapping;
      return tex;
    };

    const createGrateTexture = () => {
      const cv = document.createElement('canvas');
      cv.width = 64;
      cv.height = 64;
      const ctx = cv.getContext('2d');
      if (ctx) {
        ctx.fillStyle = '#0f172a';
        ctx.fillRect(0, 0, 64, 64);
        ctx.strokeStyle = '#334155';
        ctx.lineWidth = 3;
        ctx.strokeRect(4, 4, 56, 56);
        ctx.fillStyle = '#00f0ff';
        ctx.fillRect(28, 28, 8, 8);
      }
      const tex = new THREE.CanvasTexture(cv);
      tex.wrapS = THREE.RepeatWrapping;
      tex.wrapT = THREE.RepeatWrapping;
      tex.repeat.set(12, 12);
      return tex;
    };

    const brushedTexture = createBrushedSteelCanvas();
    const floorTexture = createGrateTexture();

    // ═════════════════════════════════════════════════════════════════
    // 3. REFINED INDUSTRIAL STEEL & HIGH-HEAT MATERIALS
    // ═════════════════════════════════════════════════════════════════
    // Stainless Mirror Chrome Steel (High shine, sharp highlights)
    const chromeSteelMat = new THREE.MeshStandardMaterial({
      color: 0xecf0f1,
      metalness: 0.98,
      roughness: 0.12,
      map: brushedTexture,
    });

    // Heavy Gunmetal Cast Carbon Steel Casing
    const gunmetalSteelMat = new THREE.MeshStandardMaterial({
      color: 0x222a35,
      metalness: 0.88,
      roughness: 0.28,
    });

    // Dark Motor Stator Housing
    const motorStatorMat = new THREE.MeshStandardMaterial({
      color: 0x111827,
      metalness: 0.92,
      roughness: 0.24,
    });

    // High-Precision Titanium Alloy Rotor Blades (with Speed Glow)
    const titaniumRotorMat = new THREE.MeshStandardMaterial({
      color: isRunning ? 0x00f0ff : isThrottled ? 0xffb703 : 0x64748b,
      metalness: 0.96,
      roughness: 0.08,
      emissive: isRunning ? 0x0088cc : isThrottled ? 0xcc6600 : 0x1e293b,
      emissiveIntensity: isRunning ? 0.65 : isThrottled ? 0.35 : 0.08,
    });

    // Machined Industrial Brass & Copper Fittings
    const brassFittingMat = new THREE.MeshStandardMaterial({
      color: 0xf59e0b,
      metalness: 0.94,
      roughness: 0.2,
    });

    // Glowing Superheated Induction Heater Coils (Orange/Red Fire)
    const glowingHeatMat = new THREE.MeshStandardMaterial({
      color: 0xff4500,
      emissive: 0xff3300,
      emissiveIntensity: isRunning ? 2.8 : isThrottled ? 1.2 : 0.2,
      roughness: 0.3,
      metalness: 0.5,
    });

    // High-Pressure Steam & Hydrocarbon Steel Piping
    const steelPipingMat = new THREE.MeshStandardMaterial({
      color: 0x718096,
      metalness: 0.92,
      roughness: 0.18,
    });

    // Toughened Borosilicate Sight Glass
    const borosilicateGlassMat = new THREE.MeshPhysicalMaterial({
      color: 0xffffff,
      transmission: 0.92,
      opacity: 1,
      transparent: true,
      roughness: 0.05,
      ior: 1.52,
    });

    // ═════════════════════════════════════════════════════════════════
    // 4. DYNAMIC FOUNDRY & VOLUMETRIC LIGHTING
    // ═════════════════════════════════════════════════════════════════
    const ambientLight = new THREE.AmbientLight(0x1e293b, 1.8);
    scene.add(ambientLight);

    // High-Bay Top Down Industrial Spotlight
    const topKeySpot = new THREE.SpotLight(0xffffff, 6.5);
    topKeySpot.position.set(0, 7.5, 0);
    topKeySpot.target.position.set(0, 0, 0);
    topKeySpot.angle = Math.PI / 3.4;
    topKeySpot.penumbra = 0.45;
    scene.add(topKeySpot);
    scene.add(topKeySpot.target);

    // Dramatic Cyan Electric Key Light
    const cyanKeyLight = new THREE.DirectionalLight(0x00f0ff, 3.2);
    cyanKeyLight.position.set(5, 5, 4);
    scene.add(cyanKeyLight);

    // Molten Orange Furnace Rim Light (Opposite side)
    const orangeRimLight = new THREE.DirectionalLight(0xff5500, 3.8);
    orangeRimLight.position.set(-5, 4, -4);
    scene.add(orangeRimLight);

    // Cold Blue Underside Fill Light
    const coldUnderFill = new THREE.PointLight(0x0284c7, 2.5, 9);
    coldUnderFill.position.set(0, -0.6, 2.5);
    scene.add(coldUnderFill);

    // Status Telemetry Beacon Light
    const statusColor = isRunning ? 0x00e676 : isThrottled ? 0xffb703 : 0xff3366;
    const statusBeaconLight = new THREE.PointLight(statusColor, isRunning ? 4.0 : 2.5, 8);
    statusBeaconLight.position.set(0, 1.8, 0.8);
    scene.add(statusBeaconLight);

    // High-Tech Industrial Steel Catwalk Grid Floor
    const floorGeo = new THREE.PlaneGeometry(12, 12);
    const floorMat = new THREE.MeshStandardMaterial({
      map: floorTexture,
      roughness: 0.7,
      metalness: 0.6,
    });
    const floorMesh = new THREE.Mesh(floorGeo, floorMat);
    floorMesh.rotation.x = -Math.PI / 2;
    floorMesh.position.y = -0.78;
    scene.add(floorMesh);

    const groundGrid = new THREE.GridHelper(12, 24, 0x00f0ff, 0x1e293b);
    groundGrid.position.y = -0.77;
    scene.add(groundGrid);

    // ═════════════════════════════════════════════════════════════════
    // 5. ROOT RIG & FOUNDATION BEDPLATE
    // ═════════════════════════════════════════════════════════════════
    const rootGroup = new THREE.Group();
    scene.add(rootGroup);

    // Cast Steel Foundation Bedplate Skid with Machine Mounting Rails
    const baseBedGeo = new THREE.BoxGeometry(3.4, 0.24, 2.3);
    const baseBed = new THREE.Mesh(baseBedGeo, gunmetalSteelMat);
    baseBed.position.y = -0.65;
    rootGroup.add(baseBed);

    // Dual Chromed Precision Guide Runners
    for (const bz of [-0.9, 0.9]) {
      const railGeo = new THREE.BoxGeometry(3.5, 0.12, 0.18);
      const rail = new THREE.Mesh(railGeo, chromeSteelMat);
      rail.position.set(0, -0.73, bz);
      rootGroup.add(rail);
    }

    // 4 Heavy Anti-Vibration Heavy Spring Damper Mounts
    const mountCoords: [number, number][] = [
      [-1.45, -0.9], [1.45, -0.9],
      [-1.45, 0.9], [1.45, 0.9]
    ];
    mountCoords.forEach(([bx, bz]) => {
      const padGeo = new THREE.CylinderGeometry(0.14, 0.16, 0.12, 16);
      const pad = new THREE.Mesh(padGeo, gunmetalSteelMat);
      pad.position.set(bx, -0.5, bz);
      rootGroup.add(pad);

      // Chromed Damper Spring
      const springGeo = new THREE.TorusGeometry(0.09, 0.024, 8, 20);
      springGeo.rotateX(Math.PI / 2);
      const spring = new THREE.Mesh(springGeo, chromeSteelMat);
      spring.position.set(bx, -0.42, bz);
      rootGroup.add(spring);

      // Gold-plated Hex Anchor Nut
      const nutGeo = new THREE.CylinderGeometry(0.06, 0.06, 0.08, 6);
      const nut = new THREE.Mesh(nutGeo, brassFittingMat);
      nut.position.set(bx, -0.36, bz);
      rootGroup.add(nut);
    });

    // SCADA LED Beacon Telemetry Mast
    const mastPole = new THREE.Mesh(new THREE.CylinderGeometry(0.025, 0.025, 0.8, 12), chromeSteelMat);
    mastPole.position.set(1.4, 0.3, -0.9);
    rootGroup.add(mastPole);

    const mastDome = new THREE.Mesh(new THREE.SphereGeometry(0.09, 16, 16), new THREE.MeshStandardMaterial({
      color: statusColor,
      emissive: statusColor,
      emissiveIntensity: 1.8,
      roughness: 0.1,
    }));
    mastDome.position.set(1.4, 0.72, -0.9);
    rootGroup.add(mastDome);

    // Analog Dial Pressure/Temp Gauge Component
    const createAnalogGauge = (gx: number, gy: number, gz: number, rotY = 0) => {
      const gGroup = new THREE.Group();
      gGroup.position.set(gx, gy, gz);
      gGroup.rotation.y = rotY;

      const stem = new THREE.Mesh(new THREE.CylinderGeometry(0.02, 0.02, 0.16, 8), brassFittingMat);
      stem.position.y = 0.08;
      gGroup.add(stem);

      const dialBodyGeo = new THREE.CylinderGeometry(0.14, 0.14, 0.06, 24);
      dialBodyGeo.rotateX(Math.PI / 2);
      const dialBody = new THREE.Mesh(dialBodyGeo, chromeSteelMat);
      dialBody.position.y = 0.22;
      gGroup.add(dialBody);

      const face = new THREE.Mesh(new THREE.CircleGeometry(0.12, 24), new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.2 }));
      face.position.set(0, 0.22, 0.032);
      gGroup.add(face);

      const needle = new THREE.Mesh(new THREE.BoxGeometry(0.015, 0.09, 0.005), new THREE.MeshBasicMaterial({ color: isRunning ? 0xef4444 : 0x64748b }));
      needle.position.set(0.02, 0.24, 0.035);
      needle.rotation.z = isRunning ? -Math.PI / 3.8 : Math.PI / 3;
      gGroup.add(needle);

      return gGroup;
    };

    // ═════════════════════════════════════════════════════════════════
    // 6. SPECIALIZED MACHINE MODELS WITH MOVING PARTS
    // ═════════════════════════════════════════════════════════════════
    const rotorGroup = new THREE.Group();
    const secondaryMovingParts: THREE.Object3D[] = [];

    // Fire / Plasma / Electricity Dynamic Objects
    let fireLight: THREE.PointLight | null = null;
    let electricArcLight: THREE.PointLight | null = null;
    const flameCones: THREE.Mesh[] = [];
    const sparkParticles: THREE.Points[] = [];
    const arcLines: THREE.Line[] = [];

    // ─────────────────────────────────────────────────────────────
    // TYPE 1: HIGH-PERFORMANCE CRUDE CHARGE PUMP (PUMP_301A / B)
    // ─────────────────────────────────────────────────────────────
    if (machineId.includes('PUMP')) {
      // 1. Heavy Electric Motor (Dark Gunmetal with Chromed Longitudinal Stator Ribs)
      const motorCoreGeo = new THREE.CylinderGeometry(0.58, 0.58, 1.45, 32);
      motorCoreGeo.rotateZ(Math.PI / 2);
      const motorCore = new THREE.Mesh(motorCoreGeo, motorStatorMat);
      motorCore.position.set(-0.75, 0.1, 0);
      rootGroup.add(motorCore);

      // Motor Rear Cooling Shroud with Exhaust Air Grill
      const cowlGeo = new THREE.CylinderGeometry(0.62, 0.56, 0.3, 32);
      cowlGeo.rotateZ(Math.PI / 2);
      const cowl = new THREE.Mesh(cowlGeo, chromeSteelMat);
      cowl.position.set(-1.55, 0.1, 0);
      rootGroup.add(cowl);

      // High-efficiency Radiating Cooling Fins
      for (let fx = -1.35; fx <= -0.2; fx += 0.11) {
        const ribGeo = new THREE.TorusGeometry(0.62, 0.02, 8, 32);
        ribGeo.rotateY(Math.PI / 2);
        const rib = new THREE.Mesh(ribGeo, brassFittingMat);
        rib.position.set(fx, 0.1, 0);
        rootGroup.add(rib);
      }

      // Explosion-Proof Electrical Terminal Box with High-Voltage Conduit
      const jBox = new THREE.Mesh(new THREE.BoxGeometry(0.4, 0.32, 0.4), chromeSteelMat);
      jBox.position.set(-0.75, 0.8, 0.18);
      rootGroup.add(jBox);

      // High Voltage Cable Conduit
      const conduitGeo = new THREE.TorusGeometry(0.35, 0.04, 12, 24, Math.PI / 2);
      const conduit = new THREE.Mesh(conduitGeo, brassFittingMat);
      conduit.position.set(-0.55, 0.8, 0.38);
      rootGroup.add(conduit);

      // Flexible Shaft Coupling Inspection Guard (Slotted Steel Cage)
      const coupShieldGeo = new THREE.CylinderGeometry(0.34, 0.34, 0.44, 20);
      coupShieldGeo.rotateZ(Math.PI / 2);
      const coupShield = new THREE.Mesh(coupShieldGeo, chromeSteelMat);
      coupShield.position.set(0.12, 0.1, 0);
      rootGroup.add(coupShield);

      // 2. Heavy Volute Spiral Pump Casing (Gunmetal with Chromed Reinforcement Ribs)
      const voluteOuterGeo = new THREE.CylinderGeometry(0.95, 0.95, 0.58, 36);
      voluteOuterGeo.rotateZ(Math.PI / 2);
      const voluteOuter = new THREE.Mesh(voluteOuterGeo, gunmetalSteelMat);
      voluteOuter.position.set(0.64, 0.14, 0);
      rootGroup.add(voluteOuter);

      // Front Face Cover Plate with Heavy Rim Bolting
      const coverGeo = new THREE.CylinderGeometry(0.88, 0.88, 0.09, 32);
      coverGeo.rotateZ(Math.PI / 2);
      const cover = new THREE.Mesh(coverGeo, chromeSteelMat);
      cover.position.set(0.96, 0.14, 0);
      rootGroup.add(cover);

      // 12 High-Tensile Stud Bolts along Volute Rim
      for (let cb = 0; cb < 12; cb++) {
        const cAngle = (cb * Math.PI) / 6;
        const cBoltGeo = new THREE.CylinderGeometry(0.03, 0.03, 0.07, 6);
        cBoltGeo.rotateZ(Math.PI / 2);
        const cBolt = new THREE.Mesh(cBoltGeo, brassFittingMat);
        cBolt.position.set(1.01, 0.14 + Math.sin(cAngle) * 0.76, Math.cos(cAngle) * 0.76);
        rootGroup.add(cBolt);
      }

      // Suction Axial Inflow Flanged Pipe
      const suctionPipeGeo = new THREE.CylinderGeometry(0.34, 0.34, 0.6, 24);
      suctionPipeGeo.rotateX(Math.PI / 2);
      const suctionPipe = new THREE.Mesh(suctionPipeGeo, steelPipingMat);
      suctionPipe.position.set(0.64, 0.14, 0.58);
      rootGroup.add(suctionPipe);

      // Suction Flange Ring with Bolt Circle
      const sFlange = new THREE.Mesh(new THREE.TorusGeometry(0.4, 0.065, 8, 24), chromeSteelMat);
      sFlange.position.set(0.64, 0.14, 0.88);
      rootGroup.add(sFlange);

      // Vertical High-Pressure Discharge Pipe & Reducer
      const dischargePipe = new THREE.Mesh(new THREE.CylinderGeometry(0.28, 0.36, 0.88, 24), steelPipingMat);
      dischargePipe.position.set(0.64, 0.9, 0);
      rootGroup.add(dischargePipe);

      // Top Discharge Flange
      const dFlange = new THREE.Mesh(new THREE.TorusGeometry(0.38, 0.065, 8, 24), brassFittingMat);
      dFlange.rotation.x = Math.PI / 2;
      dFlange.position.set(0.64, 1.34, 0);
      rootGroup.add(dFlange);

      // Dual Analog Gauges (Discharge Pressure & Seal Flush Pressure)
      rootGroup.add(createAnalogGauge(0.64, 1.34, 0.34, 0));
      rootGroup.add(createAnalogGauge(0.12, 0.44, 0.34, 0));

      // Stainless Steel Seal Flush Circulation Tubing
      const sealTube = new THREE.Mesh(new THREE.TorusGeometry(0.26, 0.022, 8, 24, Math.PI), chromeSteelMat);
      sealTube.position.set(0.36, 0.44, 0.3);
      sealTube.rotation.z = -Math.PI / 3;
      rootGroup.add(sealTube);

      // 3. Rotating Centrifugal Impeller Rotor (Inside Casing)
      const hubGeo = new THREE.CylinderGeometry(0.22, 0.22, 0.48, 24);
      hubGeo.rotateZ(Math.PI / 2);
      rotorGroup.add(new THREE.Mesh(hubGeo, brassFittingMat));

      // 8 Titanium Alloy Backward-Swept Centrifugal Vanes
      for (let b = 0; b < 8; b++) {
        const bladeGeo = new THREE.BoxGeometry(0.05, 0.74, 0.24);
        const blade = new THREE.Mesh(bladeGeo, titaniumRotorMat);
        blade.rotation.x = (b * Math.PI) / 4;
        rotorGroup.add(blade);
      }
      rotorGroup.position.set(0.64, 0.14, 0);
      rootGroup.add(rotorGroup);

      // 4. ELECTRIC PLASMA DISCHARGE ARCS ON HIGH VOLTAGE MOTOR TERMINALS
      electricArcLight = new THREE.PointLight(0x00f0ff, isRunning ? 4.5 : isThrottled ? 2.0 : 0.2, 5);
      electricArcLight.position.set(-0.75, 1.1, 0.18);
      rootGroup.add(electricArcLight);

      // High voltage plasma discharge sparks
      const sparkCount = 120;
      const sparkGeo = new THREE.BufferGeometry();
      const sparkPositions = new Float32Array(sparkCount * 3);
      for (let i = 0; i < sparkCount * 3; i += 3) {
        sparkPositions[i] = -0.75 + (Math.random() - 0.5) * 0.4;
        sparkPositions[i + 1] = 0.95 + Math.random() * 0.4;
        sparkPositions[i + 2] = 0.18 + (Math.random() - 0.5) * 0.4;
      }
      sparkGeo.setAttribute('position', new THREE.BufferAttribute(sparkPositions, 3));
      const sparkMat = new THREE.PointsMaterial({
        color: 0x00f0ff,
        size: 0.05,
        transparent: true,
        opacity: 0.9,
        blending: THREE.AdditiveBlending,
      });
      const sparkSystem = new THREE.Points(sparkGeo, sparkMat);
      rootGroup.add(sparkSystem);
      sparkParticles.push(sparkSystem);

      // Jagged Electric Arc Lines
      for (let al = 0; al < 3; al++) {
        const arcPoints: THREE.Vector3[] = [];
        let cur = new THREE.Vector3(-0.75, 0.96, 0.18);
        arcPoints.push(cur.clone());
        for (let seg = 0; seg < 6; seg++) {
          cur = new THREE.Vector3(
            cur.x + (Math.random() - 0.5) * 0.15,
            cur.y + 0.05 + Math.random() * 0.04,
            cur.z + (Math.random() - 0.5) * 0.15
          );
          arcPoints.push(cur.clone());
        }
        const arcGeo = new THREE.BufferGeometry().setFromPoints(arcPoints);
        const arcMat = new THREE.LineBasicMaterial({
          color: 0x00ffff,
          linewidth: 2,
          transparent: true,
          opacity: 0.85,
        });
        const arcLine = new THREE.Line(arcGeo, arcMat);
        rootGroup.add(arcLine);
        arcLines.push(arcLine);
      }

    // ─────────────────────────────────────────────────────────────
    // TYPE 2: MULTI-STAGE RECYCLE COMPRESSOR (COMPRESSOR_301)
    // ─────────────────────────────────────────────────────────────
    } else if (machineId.includes('COMPRESSOR')) {
      // High-Pressure Forged Steel Barrel Casing with Horizontally Split Flange
      const barrelGeo = new THREE.CylinderGeometry(0.85, 0.85, 2.5, 36);
      barrelGeo.rotateZ(Math.PI / 2);
      const barrel = new THREE.Mesh(barrelGeo, gunmetalSteelMat);
      rootGroup.add(barrel);

      // Outer Inspection Sight Windows (Viewing Rotating Impellers)
      const windowCutout = new THREE.Mesh(new THREE.BoxGeometry(1.6, 0.5, 0.88), borosilicateGlassMat);
      windowCutout.position.set(0, 0.1, 0.45);
      rootGroup.add(windowCutout);

      // Heavy Chromed End Heads (Cast Flanged Closures)
      for (const px of [-1.3, 1.3]) {
        const flangeHead = new THREE.Mesh(new THREE.CylinderGeometry(0.98, 0.98, 0.2, 36), chromeSteelMat);
        flangeHead.rotation.z = Math.PI / 2;
        flangeHead.position.x = px;
        rootGroup.add(flangeHead);

        // Journal & Thrust Bearing Pedestals
        const bearing = new THREE.Mesh(new THREE.BoxGeometry(0.34, 0.68, 0.72), motorStatorMat);
        bearing.position.set(px > 0 ? 1.48 : -1.48, -0.15, 0);
        rootGroup.add(bearing);
      }

      // 8 High-Tensile Chrome Tie-Rods with Hex Tensioning Nuts
      for (let tr = 0; tr < 8; tr++) {
        const angle = (tr * Math.PI) / 4;
        const rodGeo = new THREE.CylinderGeometry(0.038, 0.038, 2.75, 12);
        rodGeo.rotateZ(Math.PI / 2);
        const rod = new THREE.Mesh(rodGeo, chromeSteelMat);
        rod.position.set(0, 0.9 * Math.sin(angle), 0.9 * Math.cos(angle));
        rootGroup.add(rod);

        [-1.4, 1.4].forEach(nx => {
          const nutGeo = new THREE.CylinderGeometry(0.055, 0.055, 0.07, 6);
          nutGeo.rotateZ(Math.PI / 2);
          const nut = new THREE.Mesh(nutGeo, brassFittingMat);
          nut.position.set(nx, 0.9 * Math.sin(angle), 0.9 * Math.cos(angle));
          rootGroup.add(nut);
        });
      }

      // Multi-Nozzle Process Manifolds (Dual Suction & High-Pressure Discharge)
      const nozzles = [
        { x: -0.75, r: 0.25 },
        { x: -0.22, r: 0.22 },
        { x: 0.32, r: 0.2 },
        { x: 0.85, r: 0.18 }
      ];
      nozzles.forEach(noz => {
        const nPipe = new THREE.Mesh(new THREE.CylinderGeometry(noz.r, noz.r, 0.6, 20), steelPipingMat);
        nPipe.position.set(noz.x, 0.88, 0);
        rootGroup.add(nPipe);

        const nFlange = new THREE.Mesh(new THREE.TorusGeometry(noz.r + 0.08, 0.045, 8, 20), chromeSteelMat);
        nFlange.rotation.x = Math.PI / 2;
        nFlange.position.set(noz.x, 1.18, 0);
        rootGroup.add(nFlange);
      });

      // Analog Pressure Gauges
      rootGroup.add(createAnalogGauge(-0.75, 1.18, 0.3, 0));
      rootGroup.add(createAnalogGauge(0.85, 1.18, 0.3, 0));

      // Central High-Tensile Forged Steel Rotor Shaft
      const shaftGeo = new THREE.CylinderGeometry(0.15, 0.15, 2.65, 24);
      shaftGeo.rotateZ(Math.PI / 2);
      rotorGroup.add(new THREE.Mesh(shaftGeo, chromeSteelMat));

      // 5 Progressive Aerodynamic Compression Impeller Discs
      const compStages = [-0.85, -0.42, 0.0, 0.42, 0.85];
      compStages.forEach((posX, idx) => {
        const discR = 0.7 - idx * 0.06;
        const discGeo = new THREE.CylinderGeometry(discR, discR, 0.13, 28);
        discGeo.rotateZ(Math.PI / 2);
        const disc = new THREE.Mesh(discGeo, titaniumRotorMat);
        disc.position.x = posX;
        rotorGroup.add(disc);

        // 12 Titanium Aerofoil Vanes per Compression Stage
        for (let v = 0; v < 12; v++) {
          const vane = new THREE.Mesh(new THREE.BoxGeometry(0.11, discR * 1.9, 0.025), chromeSteelMat);
          vane.position.x = posX;
          vane.rotation.x = (v * Math.PI) / 6;
          rotorGroup.add(vane);
        }
      });
      rootGroup.add(rotorGroup);

      // Glowing Induction Heating Jacket (Pre-heating Gas)
      for (let hc = -0.7; hc <= 0.7; hc += 0.35) {
        const coilGeo = new THREE.TorusGeometry(0.92, 0.035, 8, 32);
        coilGeo.rotateY(Math.PI / 2);
        const coil = new THREE.Mesh(coilGeo, glowingHeatMat);
        coil.position.x = hc;
        rootGroup.add(coil);
      }

    // ─────────────────────────────────────────────────────────────
    // TYPE 3: COMBUSTION FURNACE BLOWER (BLOWER_301 - FIRE / FLAME)
    // ─────────────────────────────────────────────────────────────
    } else if (machineId.includes('BLOWER')) {
      // Heavy Spiral Blower Snail Volute (Brushed Chrome & Gunmetal)
      const snailVoluteGeo = new THREE.TorusGeometry(0.92, 0.36, 20, 44);
      const snailVolute = new THREE.Mesh(snailVoluteGeo, chromeSteelMat);
      snailVolute.position.set(0.48, 0.16, 0);
      rootGroup.add(snailVolute);

      // Centrifugal Air Bellmouth Suction Intake with Protective Mesh
      const intakeHornGeo = new THREE.CylinderGeometry(0.68, 0.5, 0.48, 28);
      intakeHornGeo.rotateX(Math.PI / 2);
      const intakeHorn = new THREE.Mesh(intakeHornGeo, steelPipingMat);
      intakeHorn.position.set(0.48, 0.16, 0.45);
      rootGroup.add(intakeHorn);

      const intakeScreen = new THREE.Mesh(new THREE.TorusGeometry(0.68, 0.05, 8, 28), brassFittingMat);
      intakeScreen.position.set(0.48, 0.16, 0.7);
      rootGroup.add(intakeScreen);

      // Upward Exhaust Duct Stack with Pneumatic Actuator
      const airDuct = new THREE.Mesh(new THREE.BoxGeometry(0.68, 1.3, 0.58), gunmetalSteelMat);
      airDuct.position.set(1.2, 0.75, 0);
      rootGroup.add(airDuct);

      const exhaustRim = new THREE.Mesh(new THREE.BoxGeometry(0.8, 0.09, 0.7), chromeSteelMat);
      exhaustRim.position.set(1.2, 1.4, 0);
      rootGroup.add(exhaustRim);

      // Pneumatic Damper Actuator Cylinder with Brass Rod
      const damperAct = new THREE.Mesh(new THREE.CylinderGeometry(0.085, 0.085, 0.4, 16), brassFittingMat);
      damperAct.position.set(1.6, 0.75, 0.22);
      rootGroup.add(damperAct);

      // Squirrel-Cage Rotating Impeller
      const cageHub = new THREE.Mesh(new THREE.CylinderGeometry(0.22, 0.22, 0.44, 20), brassFittingMat);
      cageHub.rotation.z = Math.PI / 2;
      rotorGroup.add(cageHub);

      const outerRing = new THREE.Mesh(new THREE.TorusGeometry(0.74, 0.04, 8, 28), chromeSteelMat);
      rotorGroup.add(outerRing);

      for (let f = 0; f < 24; f++) {
        const blade = new THREE.Mesh(new THREE.BoxGeometry(0.05, 1.15, 0.3), titaniumRotorMat);
        blade.rotation.z = (f * Math.PI) / 12;
        rotorGroup.add(blade);
      }
      rotorGroup.position.set(0.48, 0.16, 0);
      rootGroup.add(rotorGroup);

      // ─── INDUSTRIAL FIREBOX COMBUSTION FURNACE (Left Side) ───
      const furnaceBoxGeo = new THREE.BoxGeometry(1.3, 1.6, 1.35);
      const furnaceMat = new THREE.MeshStandardMaterial({
        color: 0x1f242d,
        roughness: 0.8,
        metalness: 0.45,
      });
      const furnaceBox = new THREE.Mesh(furnaceBoxGeo, furnaceMat);
      furnaceBox.position.set(-1.0, 0.35, 0);
      rootGroup.add(furnaceBox);

      // Quartz Glass Sight Observation Window Port
      const windowPortGeo = new THREE.CylinderGeometry(0.38, 0.38, 0.2, 24);
      windowPortGeo.rotateX(Math.PI / 2);
      const windowPort = new THREE.Mesh(windowPortGeo, chromeSteelMat);
      windowPort.position.set(-1.0, 0.35, 0.68);
      rootGroup.add(windowPort);

      const quartzGlass = new THREE.Mesh(new THREE.CylinderGeometry(0.3, 0.3, 0.06, 24), borosilicateGlassMat);
      quartzGlass.rotation.x = Math.PI / 2;
      quartzGlass.position.set(-1.0, 0.35, 0.78);
      rootGroup.add(quartzGlass);

      // Chimney Flue with Chrome Reinforcement Ring
      const chimney = new THREE.Mesh(new THREE.CylinderGeometry(0.3, 0.34, 0.65, 20), steelPipingMat);
      chimney.position.set(-1.0, 1.3, 0);
      rootGroup.add(chimney);

      rootGroup.add(createAnalogGauge(-1.48, 0.75, 0.68, -Math.PI / 6));

      // DYNAMIC INTERNAL FURNACE FIRE FLAMES & GLOWING EMBER SPARKS
      const fireGroup = new THREE.Group();
      fireGroup.position.set(-1.0, 0.12, 0.44);

      fireLight = new THREE.PointLight(0xff4500, isRunning ? 7.5 : isThrottled ? 3.5 : 0.5, 5.0);
      fireGroup.add(fireLight);

      const flameColors = [0xff0000, 0xff3b00, 0xff6a00, 0xffa500, 0xffd700, 0xffe600];
      for (let fi = 0; fi < 12; fi++) {
        const fH = 0.42 + (fi % 4) * 0.12;
        const fR = 0.09 + (fi % 3) * 0.035;
        const flGeo = new THREE.ConeGeometry(fR, fH, 12);
        const flMat = new THREE.MeshStandardMaterial({
          color: flameColors[fi % flameColors.length],
          emissive: flameColors[fi % flameColors.length],
          emissiveIntensity: isRunning ? 3.2 : isThrottled ? 1.5 : 0.2,
          roughness: 0.1,
          transparent: true,
          opacity: 0.92,
        });
        const flMesh = new THREE.Mesh(flGeo, flMat);
        flMesh.position.set((fi - 6) * 0.06, 0.06, (Math.random() - 0.5) * 0.12);
        fireGroup.add(flMesh);
        flameCones.push(flMesh);
      }
      rootGroup.add(fireGroup);

      // Embers / Fire Sparks Particles Erupting from Chimney
      const emberCount = 80;
      const emberGeo = new THREE.BufferGeometry();
      const emberPos = new Float32Array(emberCount * 3);
      for (let e = 0; e < emberCount * 3; e += 3) {
        emberPos[e] = -1.0 + (Math.random() - 0.5) * 0.25;
        emberPos[e + 1] = 1.35 + Math.random() * 0.7;
        emberPos[e + 2] = (Math.random() - 0.5) * 0.25;
      }
      emberGeo.setAttribute('position', new THREE.BufferAttribute(emberPos, 3));
      const emberMat = new THREE.PointsMaterial({
        color: 0xff6600,
        size: 0.045,
        transparent: true,
        opacity: 0.85,
        blending: THREE.AdditiveBlending,
      });
      const emberSystem = new THREE.Points(emberGeo, emberMat);
      rootGroup.add(emberSystem);
      sparkParticles.push(emberSystem);

    // ─────────────────────────────────────────────────────────────
    // TYPE 4: POWER RECOVERY FLUE GAS TURBINE (TURBINE_301 - ELECTRICITY)
    // ─────────────────────────────────────────────────────────────
    } else {
      // Precision Aerodynamic Conical Expansion Stator Housing
      const coneHousingGeo = new THREE.ConeGeometry(1.08, 2.3, 36);
      coneHousingGeo.rotateZ(-Math.PI / 2);
      const coneHousing = new THREE.Mesh(coneHousingGeo, gunmetalSteelMat);
      rootGroup.add(coneHousing);

      // Flue Gas Exhaust Diffuser (Large Venturi Duct)
      const diffuserGeo = new THREE.CylinderGeometry(1.08, 0.74, 0.75, 28);
      diffuserGeo.rotateZ(-Math.PI / 2);
      const diffuser = new THREE.Mesh(diffuserGeo, steelPipingMat);
      diffuser.position.x = -1.18;
      rootGroup.add(diffuser);

      // Heavy Chromed Flue Exhaust Flange Ring
      const exhFlange = new THREE.Mesh(new THREE.TorusGeometry(1.1, 0.075, 8, 32), chromeSteelMat);
      exhFlange.rotation.y = Math.PI / 2;
      exhFlange.position.x = -1.55;
      rootGroup.add(exhFlange);

      // Hot Gas Inlet Manifold Scroll
      const inletScroll = new THREE.Mesh(new THREE.TorusGeometry(0.88, 0.24, 16, 32), chromeSteelMat);
      inletScroll.rotation.y = Math.PI / 2;
      inletScroll.position.x = 0.58;
      rootGroup.add(inletScroll);

      const hotInletPipe = new THREE.Mesh(new THREE.CylinderGeometry(0.32, 0.32, 0.68, 20), steelPipingMat);
      hotInletPipe.position.set(0.58, 1.05, 0);
      rootGroup.add(hotInletPipe);

      const hFlange = new THREE.Mesh(new THREE.TorusGeometry(0.4, 0.065, 8, 24), brassFittingMat);
      hFlange.rotation.x = Math.PI / 2;
      hFlange.position.set(0.58, 1.38, 0);
      rootGroup.add(hFlange);

      rootGroup.add(createAnalogGauge(0.58, 1.38, 0.34, 0));

      // Precision Turbine Rotor Shaft & Aerodynamic Bullet Nose Cone
      const shaft = new THREE.Mesh(new THREE.CylinderGeometry(0.25, 0.25, 2.35, 24), chromeSteelMat);
      shaft.rotation.z = Math.PI / 2;
      rotorGroup.add(shaft);

      const noseCone = new THREE.Mesh(new THREE.ConeGeometry(0.34, 0.55, 24), titaniumRotorMat);
      noseCone.rotation.z = -Math.PI / 2;
      noseCone.position.x = 1.3;
      rotorGroup.add(noseCone);

      // 18 Precision Aerofoil Titanium Blades on Expander Wheel
      for (let r = 0; r < 18; r++) {
        const blade = new THREE.Mesh(new THREE.BoxGeometry(0.065, 1.3, 0.25), titaniumRotorMat);
        blade.rotation.x = (r * Math.PI) / 9;
        rotorGroup.add(blade);
      }
      rootGroup.add(rotorGroup);

      // Superheated Induction Heat Exchanger Coils (Glowing Copper)
      for (let c = -0.6; c <= 0.6; c += 0.3) {
        const coil = new THREE.Mesh(new THREE.TorusGeometry(0.94, 0.038, 8, 32), glowingHeatMat);
        coil.rotation.y = Math.PI / 2;
        coil.position.x = c;
        rootGroup.add(coil);
      }

      // HIGH-VOLTAGE GENERATOR & ELECTRIC DISCHARGE LIGHTNING
      electricArcLight = new THREE.PointLight(0x00f0ff, isRunning ? 5.5 : isThrottled ? 2.5 : 0.3, 6);
      electricArcLight.position.set(1.4, 0.8, 0);
      rootGroup.add(electricArcLight);

      // Multi-Branch Electric Blue Corona Discharge Sparks
      const turbineSparkCount = 140;
      const turbineSparkGeo = new THREE.BufferGeometry();
      const turbineSparkPos = new Float32Array(turbineSparkCount * 3);
      for (let i = 0; i < turbineSparkCount * 3; i += 3) {
        turbineSparkPos[i] = 1.3 + (Math.random() - 0.5) * 0.5;
        turbineSparkPos[i + 1] = 0.2 + (Math.random() - 0.5) * 0.7;
        turbineSparkPos[i + 2] = (Math.random() - 0.5) * 0.7;
      }
      turbineSparkGeo.setAttribute('position', new THREE.BufferAttribute(turbineSparkPos, 3));
      const turbineSparkMat = new THREE.PointsMaterial({
        color: 0x00f0ff,
        size: 0.05,
        transparent: true,
        opacity: 0.9,
        blending: THREE.AdditiveBlending,
      });
      const turbineSparkSystem = new THREE.Points(turbineSparkGeo, turbineSparkMat);
      rootGroup.add(turbineSparkSystem);
      sparkParticles.push(turbineSparkSystem);

      // Lightning Arcs Across Generator Bushing
      for (let al = 0; al < 3; al++) {
        const arcPoints: THREE.Vector3[] = [];
        let cur = new THREE.Vector3(1.2, 0.4, 0);
        arcPoints.push(cur.clone());
        for (let seg = 0; seg < 6; seg++) {
          cur = new THREE.Vector3(
            cur.x + (Math.random() - 0.5) * 0.18,
            cur.y + (Math.random() - 0.5) * 0.18,
            cur.z + (Math.random() - 0.5) * 0.18
          );
          arcPoints.push(cur.clone());
        }
        const arcGeo = new THREE.BufferGeometry().setFromPoints(arcPoints);
        const arcMat = new THREE.LineBasicMaterial({
          color: 0x67e8f9,
          linewidth: 2,
          transparent: true,
          opacity: 0.85,
        });
        const arcLine = new THREE.Line(arcGeo, arcMat);
        rootGroup.add(arcLine);
        arcLines.push(arcLine);
      }
    }

    // ═════════════════════════════════════════════════════════════════
    // 7. INTERACTIVE MOUSE ROTATION / ORBIT DAMPING
    // ═════════════════════════════════════════════════════════════════
    let isDragging = false;
    let prevMouseX = 0;
    let prevMouseY = 0;
    let targetRotY = 0;
    let targetRotX = 0;

    const onMouseDown = (e: MouseEvent) => {
      isDragging = true;
      prevMouseX = e.clientX;
      prevMouseY = e.clientY;
    };

    const onMouseMove = (e: MouseEvent) => {
      if (!isDragging) return;
      const deltaX = e.clientX - prevMouseX;
      const deltaY = e.clientY - prevMouseY;
      prevMouseX = e.clientX;
      prevMouseY = e.clientY;

      targetRotY += deltaX * 0.012;
      targetRotX += deltaY * 0.008;
      targetRotX = Math.max(-0.65, Math.min(0.85, targetRotX));
    };

    const onMouseUp = () => {
      isDragging = false;
    };

    const dom = renderer.domElement;
    dom.addEventListener('mousedown', onMouseDown);
    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('mouseup', onMouseUp);

    // ═════════════════════════════════════════════════════════════════
    // 8. HIGH-PERFORMANCE REAL-TIME ANIMATION LOOP
    // ═════════════════════════════════════════════════════════════════
    let currentSpeed = isRunning ? (rpm / 2980) * 0.16 : 0;
    const targetSpeed = isRunning ? (rpm / 2980) * 0.19 : isThrottled ? 0.05 : 0;
    let time = 0;
    let animId = 0;

    const animate = () => {
      animId = requestAnimationFrame(animate);
      time += 0.035;

      // Mouse-orbit rotation easing
      rootGroup.rotation.y += (targetRotY - rootGroup.rotation.y) * 0.1;
      rootGroup.rotation.x += (targetRotX - rootGroup.rotation.x) * 0.1;

      // Telemetric Status Beacon Pulse
      if (isRunning) {
        statusBeaconLight.intensity = 3.8 + Math.sin(time * 6) * 1.4;
      } else if (isThrottled) {
        statusBeaconLight.intensity = 2.2 + Math.sin(time * 3) * 0.9;
      } else {
        statusBeaconLight.intensity = 3.0 + Math.sin(time * 2) * 1.8;
      }

      // Overhead moving industrial spotlight
      topKeySpot.position.x = 2.2 * Math.cos(time * 0.5);
      topKeySpot.position.z = 2.2 * Math.sin(time * 0.5);
      topKeySpot.intensity = 5.5 + Math.sin(time * 2) * 0.9;

      // ─── 1. ANIMATED REALISTIC FIRE & COMBUSTION FLICKER ───
      if (machineId.includes('BLOWER')) {
        const fireFlicker = isRunning
          ? 1.0 + Math.sin(time * 15) * 0.35 + Math.cos(time * 23) * 0.22
          : isThrottled
          ? 0.5 + Math.sin(time * 8) * 0.15
          : 0.05;

        flameCones.forEach((flame, idx) => {
          const individualWave = Math.sin(time * 18 + idx * 1.6) * 0.32 + Math.cos(time * 26 + idx) * 0.18;
          const currentScaleY = Math.max(0.2, (isRunning ? 1.0 : 0.3) + individualWave);
          flame.scale.set(1.0 + Math.sin(time * 10 + idx) * 0.2, currentScaleY, 1.0);
          flame.rotation.z = Math.sin(time * 14 + idx) * 0.18;
        });

        if (fireLight) {
          fireLight.intensity = isRunning ? 5.0 + fireFlicker * 3.0 : isThrottled ? 2.2 : 0.3;
        }
      }

      // ─── 2. HIGH-VOLTAGE ELECTRICITY & ARC DISCHARGE ANIMATION ───
      if (electricArcLight) {
        const electricFlicker = isRunning
          ? (Math.random() > 0.3 ? 1.0 : 0.4) * (4.5 + Math.random() * 3.5)
          : isThrottled
          ? 2.0 + Math.sin(time * 10) * 1.0
          : 0.2;
        electricArcLight.intensity = electricFlicker;
      }

      // Regenerate Jagged Lightning Arcs randomly on high speed
      if (isRunning && arcLines.length > 0 && Math.random() > 0.4) {
        arcLines.forEach((arc) => {
          const posAttr = arc.geometry.getAttribute('position') as THREE.BufferAttribute;
          if (posAttr) {
            for (let p = 1; p < posAttr.count - 1; p++) {
              posAttr.setXYZ(
                p,
                posAttr.getX(p) + (Math.random() - 0.5) * 0.04,
                posAttr.getY(p) + (Math.random() - 0.5) * 0.04,
                posAttr.getZ(p) + (Math.random() - 0.5) * 0.04
              );
            }
            posAttr.needsUpdate = true;
          }
        });
      }

      // Spark Particles Motion (floating upward like real sparks)
      sparkParticles.forEach((sys) => {
        const pAttr = sys.geometry.getAttribute('position') as THREE.BufferAttribute;
        if (pAttr && isRunning) {
          for (let sp = 1; sp < pAttr.count * 3; sp += 3) {
            let y = pAttr.array[sp];
            y += 0.015 + Math.random() * 0.02;
            if (y > 2.2) y = 0.8;
            pAttr.array[sp] = y;
          }
          pAttr.needsUpdate = true;
        }
      });

      // ─── 3. SMOOTH INERTIA SHAFT & IMPELLER ROTATION ───
      currentSpeed += (targetSpeed - currentSpeed) * 0.05;

      if (machineId.includes('BLOWER')) {
        rotorGroup.rotation.z -= currentSpeed;
      } else {
        rotorGroup.rotation.x += currentSpeed;
      }

      // High-RPM Mechanical Vibration
      if (currentSpeed > 0.08) {
        rootGroup.position.x = (Math.random() - 0.5) * 0.018;
        rootGroup.position.y = (Math.random() - 0.5) * 0.018;
      } else {
        rootGroup.position.set(0, 0, 0);
      }

      renderer.render(scene, camera);
    };

    animate();

    // ═════════════════════════════════════════════════════════════════
    // 9. RESOURCE CLEANUP
    // ═════════════════════════════════════════════════════════════════
    return () => {
      cancelAnimationFrame(animId);
      dom.removeEventListener('mousedown', onMouseDown);
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('mouseup', onMouseUp);

      scene.traverse((obj) => {
        if ((obj as THREE.Mesh).geometry) {
          (obj as THREE.Mesh).geometry.dispose();
        }
        if ((obj as THREE.Mesh).material) {
          const mat = (obj as THREE.Mesh).material;
          if (Array.isArray(mat)) {
            mat.forEach((m) => m.dispose());
          } else {
            mat.dispose();
          }
        }
      });

      brushedTexture.dispose();
      floorTexture.dispose();

      renderer.forceContextLoss();
      renderer.dispose();
      if (container.contains(renderer.domElement)) {
        container.removeChild(renderer.domElement);
      }
    };
  }, [machineId, status, rpm]);

  return (
    <div
      ref={mountRef}
      style={propHeight ? { height: `${propHeight}px` } : undefined}
      className={`w-full ${propHeight ? '' : 'h-[240px]'} flex items-center justify-center relative cursor-grab active:cursor-grabbing`}
      title={`3D Three.js Digital Twin: ${machineId} (${status}) - Click & Drag to Orbit`}
    />
  );
};
