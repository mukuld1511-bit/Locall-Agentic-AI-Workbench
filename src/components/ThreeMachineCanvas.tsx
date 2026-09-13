import React, { useEffect, useRef } from 'react';
import * as THREE from 'three';

interface MachineCanvasProps {
  machineId: string;
  status: 'RUNNING' | 'STOPPED' | 'THROTTLED' | string;
  rpm: number;
}

export const ThreeMachineCanvas: React.FC<MachineCanvasProps> = ({ machineId, status, rpm }) => {
  const mountRef = useRef<HTMLDivElement>(null);
  const isRunning = status === 'RUNNING';
  const isThrottled = status === 'THROTTLED';

  useEffect(() => {
    const container = mountRef.current;
    if (!container) return;

    const width = container.clientWidth || 360;
    const height = 240;

    // 1. Scene & Light Industrial Studio Skybox
    const scene = new THREE.Scene();
    // Light skybox backdrop with subtle gradient fog
    scene.background = new THREE.Color(0x0a0f1d);
    scene.fog = new THREE.FogExp2(0x0a0f1d, 0.04);

    const camera = new THREE.PerspectiveCamera(40, width / height, 0.1, 100);
    camera.position.set(4.2, 3.4, 5.2);
    camera.lookAt(0, 0.2, 0);

    // 2. Renderer with Error Fallback for Electron WebGL
    let renderer: THREE.WebGLRenderer;
    try {
      renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false, powerPreference: 'high-performance' });
      renderer.setSize(width, height);
      renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
      renderer.toneMapping = THREE.ACESFilmicToneMapping;
      renderer.toneMappingExposure = 1.45;
      container.innerHTML = '';
      container.appendChild(renderer.domElement);
    } catch (e) {
      console.warn('WebGL initialization fallback for:', machineId, e);
      return;
    }

    // 3. Dynamic Studio & Machine Top Lighting
    // Ambient light
    const ambientLight = new THREE.AmbientLight(0xffffff, 1.2);
    scene.add(ambientLight);

    // Top Key Spot Light (Dramatic Industrial Stage Beam pointing directly down on the machine)
    const topSpot = new THREE.SpotLight(0xffffff, 6.0);
    topSpot.position.set(0, 6.5, 0);
    topSpot.target.position.set(0, 0, 0);
    topSpot.angle = Math.PI / 3.5;
    topSpot.penumbra = 0.5;
    scene.add(topSpot);
    scene.add(topSpot.target);

    // Cyan/Blue Edge Rim Light
    const cyanRim = new THREE.DirectionalLight(0x38bdf8, 3.8);
    cyanRim.position.set(-4, 4, -3);
    scene.add(cyanRim);

    // Warm Industrial Fill Light
    const warmFill = new THREE.DirectionalLight(0xf59e0b, 2.5);
    warmFill.position.set(4, -1, 3);
    scene.add(warmFill);

    // Status Color
    const statusColor = isRunning ? 0x10b981 : isThrottled ? 0xf59e0b : 0xef4444;
    const beaconLight = new THREE.PointLight(statusColor, isRunning ? 4.5 : isThrottled ? 2.8 : 3.8, 8);
    beaconLight.position.set(0, 1.8, 0.8);
    scene.add(beaconLight);

    // Dynamic Chassis Underglow / Neon Ground Reflection
    const underglowLight = new THREE.PointLight(statusColor, isRunning ? 3.2 : 1.5, 6);
    underglowLight.position.set(0, -0.6, 0);
    scene.add(underglowLight);

    // 4. Materials (High Metallic sheen with specular highlights)
    const metalMat = new THREE.MeshStandardMaterial({
      color: 0x334155,
      metalness: 0.88,
      roughness: 0.22,
    });

    const rotorMat = new THREE.MeshStandardMaterial({
      color: isRunning ? 0x38bdf8 : isThrottled ? 0xfbbf24 : 0x64748b,
      metalness: 0.95,
      roughness: 0.12,
      emissive: isRunning ? 0x0284c7 : isThrottled ? 0xb45309 : 0x450a0a,
      emissiveIntensity: isRunning ? 0.65 : isThrottled ? 0.35 : 0.15,
    });

    const brassMat = new THREE.MeshStandardMaterial({
      color: 0xf59e0b,
      metalness: 0.85,
      roughness: 0.25,
    });

    const housingMat = new THREE.MeshStandardMaterial({
      color: 0x1e293b,
      metalness: 0.7,
      roughness: 0.35,
      transparent: true,
      opacity: 0.88,
    });

    const steelPipeMat = new THREE.MeshStandardMaterial({
      color: 0x64748b,
      metalness: 0.9,
      roughness: 0.2,
    });

    // 5. Build Model based on Machine ID
    const rootGroup = new THREE.Group();
    scene.add(rootGroup);

    let fireLight: THREE.PointLight | null = null;
    const flameMeshes: THREE.Mesh[] = [];

    // Indicator Tower Beacon Mesh
    const beaconPoleGeo = new THREE.CylinderGeometry(0.03, 0.03, 0.6, 12);
    const beaconPole = new THREE.Mesh(beaconPoleGeo, metalMat);
    beaconPole.position.set(1.1, 0.45, -0.7);
    rootGroup.add(beaconPole);

    const beaconDomeGeo = new THREE.SphereGeometry(0.09, 16, 16);
    const beaconMat = new THREE.MeshStandardMaterial({
      color: statusColor,
      emissive: statusColor,
      emissiveIntensity: isRunning ? 1.0 : 0.7,
      roughness: 0.1,
    });
    const beaconDome = new THREE.Mesh(beaconDomeGeo, beaconMat);
    beaconDome.position.set(1.1, 0.75, -0.7);
    rootGroup.add(beaconDome);

    // Common Base Plinth with bolted corners
    const plinthGeo = new THREE.BoxGeometry(2.8, 0.24, 2.0);
    const plinth = new THREE.Mesh(plinthGeo, metalMat);
    plinth.position.y = -0.65;
    rootGroup.add(plinth);

    // Plinth Corner Bolt Details
    const boltGeo = new THREE.CylinderGeometry(0.06, 0.06, 0.08, 6);
    [[-1.2, -0.8], [1.2, -0.8], [-1.2, 0.8], [1.2, 0.8]].forEach(([bx, bz]) => {
      const bolt = new THREE.Mesh(boltGeo, brassMat);
      bolt.position.set(bx, -0.5, bz);
      rootGroup.add(bolt);
    });

    const rotorGroup = new THREE.Group();

    if (machineId.includes('PUMP')) {
      // ═════════════════════════════════════════════════════════════
      // ─── TYPE 1: Centrifugal Crude Charge Volute Pump ───────────
      // ═════════════════════════════════════════════════════════════
      // Heavy Industrial Electric Motor Drive
      const motorGeo = new THREE.CylinderGeometry(0.65, 0.65, 1.4, 32);
      motorGeo.rotateZ(Math.PI / 2);
      const motor = new THREE.Mesh(motorGeo, metalMat);
      motor.position.set(-0.7, 0.1, 0);
      rootGroup.add(motor);

      // Terminal Junction Box on Motor
      const jBoxGeo = new THREE.BoxGeometry(0.35, 0.25, 0.35);
      const jBox = new THREE.Mesh(jBoxGeo, brassMat);
      jBox.position.set(-0.7, 0.8, 0.2);
      rootGroup.add(jBox);

      // Motor Cooling Ribs / Heat Sink Fins
      for (let i = -1.15; i <= -0.25; i += 0.14) {
        const finGeo = new THREE.TorusGeometry(0.68, 0.02, 8, 32);
        finGeo.rotateY(Math.PI / 2);
        const fin = new THREE.Mesh(finGeo, brassMat);
        fin.position.set(i, 0.1, 0);
        rootGroup.add(fin);
      }

      // Coupling Guard
      const coupGeo = new THREE.CylinderGeometry(0.3, 0.3, 0.35, 16);
      coupGeo.rotateZ(Math.PI / 2);
      const coupling = new THREE.Mesh(coupGeo, steelPipeMat);
      coupling.position.set(0.15, 0.1, 0);
      rootGroup.add(coupling);

      // Large Volute Spiral Pump Casing
      const voluteGeo = new THREE.CylinderGeometry(0.85, 0.85, 0.5, 32);
      voluteGeo.rotateZ(Math.PI / 2);
      const volute = new THREE.Mesh(voluteGeo, housingMat);
      volute.position.set(0.6, 0.1, 0);
      rootGroup.add(volute);

      // Suction Nozzle (Front Flanged Inlet)
      const suctionGeo = new THREE.CylinderGeometry(0.28, 0.28, 0.5, 20);
      suctionGeo.rotateX(Math.PI / 2);
      const suction = new THREE.Mesh(suctionGeo, steelPipeMat);
      suction.position.set(0.6, 0.1, 0.45);
      rootGroup.add(suction);

      // Discharge Nozzle (Vertical Flanged Outlet)
      const dischargeGeo = new THREE.CylinderGeometry(0.25, 0.25, 0.9, 20);
      const discharge = new THREE.Mesh(dischargeGeo, steelPipeMat);
      discharge.position.set(0.6, 0.8, 0);
      rootGroup.add(discharge);

      // Flange Rings
      const flangeGeo = new THREE.TorusGeometry(0.32, 0.05, 8, 20);
      const dFlange = new THREE.Mesh(flangeGeo, brassMat);
      dFlange.rotation.x = Math.PI / 2;
      dFlange.position.set(0.6, 1.25, 0);
      rootGroup.add(dFlange);

      // Impeller Rotor (Inside Volute)
      const hubGeo = new THREE.CylinderGeometry(0.16, 0.16, 0.42, 16);
      hubGeo.rotateZ(Math.PI / 2);
      rotorGroup.add(new THREE.Mesh(hubGeo, brassMat));

      // 6 Curved Centrifugal Impeller Blades
      for (let b = 0; b < 6; b++) {
        const bladeGeo = new THREE.BoxGeometry(0.04, 0.68, 0.2);
        const blade = new THREE.Mesh(bladeGeo, rotorMat);
        blade.rotation.x = (b * Math.PI) / 3;
        rotorGroup.add(blade);
      }
      rotorGroup.position.set(0.6, 0.1, 0);
      rootGroup.add(rotorGroup);

    } else if (machineId.includes('COMPRESSOR')) {
      // ═════════════════════════════════════════════════════════════
      // ─── TYPE 2: Multi-Stage High-Pressure H2 Compressor ────────
      // ═════════════════════════════════════════════════════════════
      // Heavy Reinforced Barrel Cylinder
      const barrelGeo = new THREE.CylinderGeometry(0.78, 0.78, 2.3, 36);
      barrelGeo.rotateZ(Math.PI / 2);
      const barrel = new THREE.Mesh(barrelGeo, housingMat);
      rootGroup.add(barrel);

      // Heavy End Flanges & High-Tensile Tie-Rods
      for (const px of [-1.15, 1.15]) {
        const flangeGeo = new THREE.CylinderGeometry(0.92, 0.92, 0.15, 32);
        flangeGeo.rotateZ(Math.PI / 2);
        const fl = new THREE.Mesh(flangeGeo, metalMat);
        fl.position.x = px;
        rootGroup.add(fl);
      }

      // Tie-Rods holding the compressor barrel
      for (let tr = 0; tr < 6; tr++) {
        const rodGeo = new THREE.CylinderGeometry(0.03, 0.03, 2.5, 8);
        rodGeo.rotateZ(Math.PI / 2);
        const rod = new THREE.Mesh(rodGeo, brassMat);
        rod.position.set(0, 0.82 * Math.cos((tr * Math.PI) / 3), 0.82 * Math.sin((tr * Math.PI) / 3));
        rootGroup.add(rod);
      }

      // Interstage Suction & Discharge Manifolds
      const pipeInGeo = new THREE.CylinderGeometry(0.2, 0.2, 0.7, 16);
      const pipeIn = new THREE.Mesh(pipeInGeo, steelPipeMat);
      pipeIn.position.set(-0.6, 0.9, 0);
      rootGroup.add(pipeIn);

      const pipeOutGeo = new THREE.CylinderGeometry(0.18, 0.18, 0.7, 16);
      const pipeOut = new THREE.Mesh(pipeOutGeo, steelPipeMat);
      pipeOut.position.set(0.6, 0.9, 0);
      rootGroup.add(pipeOut);

      // Multi-Stage Impeller Discs on Central Rotor Shaft
      const shaftGeo = new THREE.CylinderGeometry(0.12, 0.12, 2.4, 16);
      shaftGeo.rotateZ(Math.PI / 2);
      rotorGroup.add(new THREE.Mesh(shaftGeo, brassMat));

      const discPositions = [-0.75, -0.25, 0.25, 0.75];
      discPositions.forEach((pos, idx) => {
        const discRadius = 0.62 - idx * 0.06; // Graduated compression stages
        const discGeo = new THREE.CylinderGeometry(discRadius, discRadius, 0.1, 24);
        discGeo.rotateZ(Math.PI / 2);
        const disc = new THREE.Mesh(discGeo, rotorMat);
        disc.position.x = pos;
        rotorGroup.add(disc);

        // 8 Radial Vanes per disc
        for (let v = 0; v < 8; v++) {
          const vaneGeo = new THREE.BoxGeometry(0.09, discRadius * 1.85, 0.03);
          const vane = new THREE.Mesh(vaneGeo, metalMat);
          vane.position.x = pos;
          vane.rotation.x = (v * Math.PI) / 4;
          rotorGroup.add(vane);
        }
      });
      rootGroup.add(rotorGroup);

    } else if (machineId.includes('BLOWER')) {
      // ═════════════════════════════════════════════════════════════
      // ─── TYPE 3: Furnace Draft Blower & Air Forced Fan ───────────
      // ═════════════════════════════════════════════════════════════
      // Heavy Spiral Snail Duct Housing
      const scrollGeo = new THREE.TorusGeometry(0.85, 0.3, 16, 36);
      const scroll = new THREE.Mesh(scrollGeo, metalMat);
      rootGroup.add(scroll);

      // Tangential Air Exhaust Stack Duct
      const exhaustGeo = new THREE.BoxGeometry(0.55, 1.2, 0.45);
      const exhaust = new THREE.Mesh(exhaustGeo, housingMat);
      exhaust.position.set(0.85, 0.6, 0);
      rootGroup.add(exhaust);

      // Intake Bell-Mouth Duct (Center Flange)
      const ductGeo = new THREE.CylinderGeometry(0.55, 0.4, 0.7, 24);
      ductGeo.rotateX(Math.PI / 2);
      const duct = new THREE.Mesh(ductGeo, steelPipeMat);
      duct.position.z = 0.4;
      rootGroup.add(duct);

      // Squirrel-Cage Outer Rim Wheel
      const rimGeo = new THREE.TorusGeometry(0.65, 0.04, 8, 24);
      const rimMesh = new THREE.Mesh(rimGeo, brassMat);
      rotorGroup.add(rimMesh);

      // Large 16-Blade Industrial Squirrel-Cage Rotor Fan
      for (let f = 0; f < 16; f++) {
        const fGeo = new THREE.BoxGeometry(0.06, 0.9, 0.24);
        const fanBlade = new THREE.Mesh(fGeo, rotorMat);
        fanBlade.rotation.z = (f * Math.PI) / 8;
        rotorGroup.add(fanBlade);
      }
      rootGroup.add(rotorGroup);

      // ─── ATMOSPHERIC FURNACE COMBUSTION CHAMBER & ANIMATED FIRE FLAMES ───
      const furnaceBoxGeo = new THREE.BoxGeometry(1.0, 1.4, 1.1);
      const furnaceFireMat = new THREE.MeshStandardMaterial({
        color: 0x1e1e24,
        roughness: 0.6,
        metalness: 0.7,
      });
      const furnaceBox = new THREE.Mesh(furnaceBoxGeo, furnaceFireMat);
      furnaceBox.position.set(-0.9, 0.35, 0);
      rootGroup.add(furnaceBox);

      // Furnace Burner Observation Window (Sight Glass)
      const windowFrameGeo = new THREE.CylinderGeometry(0.32, 0.32, 0.15, 20);
      windowFrameGeo.rotateX(Math.PI / 2);
      const windowFrame = new THREE.Mesh(windowFrameGeo, brassMat);
      windowFrame.position.set(-0.9, 0.35, 0.52);
      rootGroup.add(windowFrame);

      // Animated Fire Flame Group inside combustion chamber
      const fireGroup = new THREE.Group();
      fireGroup.position.set(-0.9, 0.15, 0.35);

      // Internal Fire Point Light (Flickering Flame Illumination)
      fireLight = new THREE.PointLight(0xff4500, isRunning ? 5.5 : isThrottled ? 2.5 : 0.4, 4);
      fireGroup.add(fireLight);

      // 7 Procedural Fire Cones / Flames with gradient emissive glow
      const fireColors = [0xff1100, 0xff4500, 0xff8800, 0xffbb00, 0xffdd44];
      for (let fi = 0; fi < 7; fi++) {
        const fHeight = 0.35 + (fi % 3) * 0.12;
        const flameGeo = new THREE.ConeGeometry(0.12, fHeight, 8);
        const flameMat = new THREE.MeshStandardMaterial({
          color: fireColors[fi % fireColors.length],
          emissive: fireColors[fi % fireColors.length],
          emissiveIntensity: isRunning ? 2.2 : isThrottled ? 1.0 : 0.1,
          roughness: 0.2,
          transparent: true,
          opacity: 0.9,
        });
        const flameMesh = new THREE.Mesh(flameGeo, flameMat);
        flameMesh.position.set((fi - 3) * 0.08, 0, (Math.random() - 0.5) * 0.1);
        fireGroup.add(flameMesh);
        flameMeshes.push(flameMesh);
      }
      rootGroup.add(fireGroup);

    } else {
      // ═════════════════════════════════════════════════════════════
      // ─── TYPE 4: Power Recovery Expander Flue Gas Turbine ────────
      // ═════════════════════════════════════════════════════════════
      // Heavy Conical Shroud Casting Shell
      const shellGeo = new THREE.ConeGeometry(0.95, 2.1, 32);
      shellGeo.rotateZ(-Math.PI / 2);
      const shell = new THREE.Mesh(shellGeo, housingMat);
      rootGroup.add(shell);

      // Flue Gas Exhaust Diffuser Duct
      const diffuserGeo = new THREE.CylinderGeometry(0.95, 0.7, 0.6, 24);
      diffuserGeo.rotateZ(-Math.PI / 2);
      const diffuser = new THREE.Mesh(diffuserGeo, steelPipeMat);
      diffuser.position.x = -1.1;
      rootGroup.add(diffuser);

      // Stator Nozzle Guide Vane Ring
      const statorRing = new THREE.TorusGeometry(0.8, 0.06, 8, 24);
      statorRing.rotateY(Math.PI / 2);
      const statorMesh = new THREE.Mesh(statorRing, brassMat);
      statorMesh.position.x = 0.4;
      rootGroup.add(statorMesh);

      // High-Velocity Turbine Central Drive Shaft
      const wheelGeo = new THREE.CylinderGeometry(0.22, 0.22, 2.2, 20);
      wheelGeo.rotateZ(Math.PI / 2);
      rotorGroup.add(new THREE.Mesh(wheelGeo, brassMat));

      // 16 Aerofoil Turbine Rotor Blades
      for (let r = 0; r < 16; r++) {
        const tGeo = new THREE.BoxGeometry(0.05, 1.15, 0.22);
        const tBlade = new THREE.Mesh(tGeo, rotorMat);
        tBlade.rotation.x = (r * Math.PI) / 8;
        rotorGroup.add(tBlade);
      }
      rootGroup.add(rotorGroup);
    }

    // ─── 6. INTERACTIVE MOUSE ROTATION / ORBIT CONTROLS ───
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
      // Clamp vertical pitch to prevent flipping upside down
      targetRotX = Math.max(-0.6, Math.min(0.8, targetRotX));
    };

    const onMouseUp = () => {
      isDragging = false;
    };

    const dom = renderer.domElement;
    dom.addEventListener('mousedown', onMouseDown);
    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('mouseup', onMouseUp);

    // 7. Animation Loop (Smooth physics acceleration / deceleration & fire flicker)
    let currentSpeed = isRunning ? (rpm / 2980) * 0.15 : 0;
    const targetSpeed = isRunning ? (rpm / 2980) * 0.18 : isThrottled ? 0.05 : 0;
    let time = 0;
    let animId = 0;

    const animate = () => {
      animId = requestAnimationFrame(animate);
      time += 0.035;

      // Smooth mouse-orbit rotation damping
      rootGroup.rotation.y += (targetRotY - rootGroup.rotation.y) * 0.1;
      rootGroup.rotation.x += (targetRotX - rootGroup.rotation.x) * 0.1;

      // Dynamic beacon light pulse
      if (isRunning) {
        beaconLight.intensity = 3.5 + Math.sin(time * 6) * 1.2;
      } else if (isThrottled) {
        beaconLight.intensity = 2.0 + Math.sin(time * 3) * 0.8;
      } else {
        beaconLight.intensity = 2.8 + Math.sin(time * 2) * 1.5; // Red warning pulse
      }

      // Smooth overhead top spotlight movement illuminating machine features
      topSpot.position.x = 2.0 * Math.cos(time * 0.6);
      topSpot.position.z = 2.0 * Math.sin(time * 0.6);
      topSpot.intensity = 5.0 + Math.sin(time * 2) * 0.8;

      // ─── REALISTIC FURNACE FIRE FLICKER ANIMATION ───
      if (machineId.includes('BLOWER')) {
        // Fire flames flicker height & scale
        const fireFlicker = isRunning
          ? 1.0 + Math.sin(time * 14) * 0.35 + Math.cos(time * 22) * 0.2
          : isThrottled
          ? 0.5 + Math.sin(time * 8) * 0.15
          : 0.05;

        // Dynamic scale & wobble on individual flame cones
        flameMeshes.forEach((flame, idx) => {
          const individualWave = Math.sin(time * 16 + idx * 1.5) * 0.3 + Math.cos(time * 24 + idx) * 0.15;
          const currentScaleY = Math.max(0.2, (isRunning ? 1.0 : 0.3) + individualWave);
          flame.scale.set(1.0 + Math.sin(time * 10 + idx) * 0.2, currentScaleY, 1.0);
          flame.rotation.z = Math.sin(time * 12 + idx) * 0.15;
        });

        // Dynamic internal fire light flicker
        if (fireLight) {
          fireLight.intensity = isRunning ? 4.5 + fireFlicker * 2.5 : isThrottled ? 2.0 : 0.2;
        }
      }

      // Smooth inertia rotation transition (spinning up on start, slowing down to 0 on stop)
      currentSpeed += (targetSpeed - currentSpeed) * 0.05;

      if (machineId.includes('BLOWER')) {
        rotorGroup.rotation.z -= currentSpeed;
      } else {
        rotorGroup.rotation.x += currentSpeed;
      }

      // Subtle vibration effect on high speed
      if (currentSpeed > 0.08) {
        rootGroup.position.x = (Math.random() - 0.5) * 0.015;
        rootGroup.position.y = (Math.random() - 0.5) * 0.015;
      } else {
        rootGroup.position.set(0, 0, 0);
      }

      renderer.render(scene, camera);
    };

    animate();

    // 8. Cleanup
    return () => {
      cancelAnimationFrame(animId);
      dom.removeEventListener('mousedown', onMouseDown);
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('mouseup', onMouseUp);
      renderer.dispose();
      if (container.contains(renderer.domElement)) {
        container.removeChild(renderer.domElement);
      }
    };
  }, [machineId, status, rpm]);

  return (
    <div
      ref={mountRef}
      className="w-full h-[240px] flex items-center justify-center relative cursor-grab active:cursor-grabbing"
      title={`3D Three.js Digital Twin: ${machineId} (${status})`}
    />
  );
};
