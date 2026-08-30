/**
 * Percolia parametric network bird.
 *
 * The wing outline and internal triangulation are recomputed at every frame
 * from a continuous 3-D kinematic model, then projected into the SVG plane.
 */
(function (global) {
  'use strict';

  const TAU = Math.PI * 2;
  const clamp = (x, a, b) => Math.min(b, Math.max(a, x));
  const lerp = (a, b, t) => a + (b - a) * t;
  const rad = (degrees) => degrees * Math.PI / 180;
  const smoothstep = (a, b, x) => {
    const t = clamp((x - a) / (b - a), 0, 1);
    return t * t * (3 - 2 * t);
  };
  const mod1 = (x) => ((x % 1) + 1) % 1;

  function parseModel(root) {
    const metadata = root.querySelector('#percolia-bird-model');
    if (!metadata) throw new Error('Percolia bird model metadata is missing');
    return JSON.parse(metadata.textContent);
  }

  function catmull(points, t) {
    const n = points.length;
    const scaled = clamp(t, 0, 0.999999999) * (n - 1);
    const i = Math.min(n - 2, Math.floor(scaled));
    const u = scaled - i;
    const p0 = points[Math.max(0, i - 1)];
    const p1 = points[i];
    const p2 = points[i + 1];
    const p3 = points[Math.min(n - 1, i + 2)];
    const component = (k) => 0.5 * (
      2 * p1[k]
      + (-p0[k] + p2[k]) * u
      + (2 * p0[k] - 5 * p1[k] + 4 * p2[k] - p3[k]) * u * u
      + (-p0[k] + 3 * p1[k] - 3 * p2[k] + p3[k]) * u * u * u
    );
    return [component(0), component(1)];
  }

  function localWingFrame(model, phase, openness) {
    const flight = model.wing.flight;
    const perched = model.wing.perched;
    const theta = TAU * phase;
    const foldRaw = 0.5 * (1 + Math.sin(theta + rad(flight.fold_phase_deg)));
    const fold = Math.pow(foldRaw, flight.fold_exponent);
    const strokeFlight = flight.stroke_center_deg
      + flight.stroke_h1_deg * Math.cos(theta)
      + flight.stroke_h2_deg * Math.cos(2 * theta + rad(flight.stroke_h2_phase_deg));
    const sweepFlight = flight.sweep_center_deg
      + flight.sweep_amp_deg * Math.sin(theta + rad(flight.sweep_phase_deg));
    const elbowFlight = flight.elbow_base_deg + flight.elbow_fold_deg * fold;
    const wristFlight = flight.wrist_base_deg + flight.wrist_fold_deg * fold;
    const pronationFlight = flight.pronation_deg
      * Math.sin(theta + rad(flight.pronation_phase_deg));
    return {
      stroke: lerp(perched.stroke_deg, strokeFlight, openness),
      sweep: lerp(perched.sweep_deg, sweepFlight, openness),
      elbow: lerp(perched.elbow_deg, elbowFlight, openness),
      wrist: lerp(perched.wrist_deg, wristFlight, openness),
      pronation: lerp(perched.pronation_deg, pronationFlight, openness),
      spanScale: lerp(perched.span_scale, 1, openness),
      chordScale: lerp(perched.chord_scale, 1, openness),
    };
  }

  function localSkeleton(model, frame) {
    const [base1, base2, base3] = model.wing.segment_lengths;
    const l1 = base1 * frame.spanScale;
    const l2 = base2 * frame.spanScale;
    const l3 = base3 * frame.spanScale;
    const a0 = rad(frame.sweep);
    const a1 = a0 + rad(frame.elbow);
    const a2 = a1 + rad(frame.wrist);
    const shoulder = [0, 0];
    const elbow = [l1 * Math.cos(a0), l1 * Math.sin(a0)];
    const wrist = [elbow[0] + l2 * Math.cos(a1), elbow[1] + l2 * Math.sin(a1)];
    const tip = [wrist[0] + l3 * Math.cos(a2), wrist[1] + l3 * Math.sin(a2)];
    return [shoulder, elbow, wrist, tip];
  }

  function chord(model, station, scale) {
    const wing = model.wing;
    const base = wing.root_chord * Math.pow(1 - station, wing.chord_exponent);
    const bulge = 1 + wing.chord_bulge * Math.sin(Math.PI * station);
    return (base * bulge + wing.tip_chord * (1 - station)) * scale;
  }

  function projectPoint(model, side, local, zTwist, strokeDegrees) {
    const sign = side === 'near' ? -1 : 1;
    const shoulder = model.wing.shoulders[side];
    const [u, v] = local;
    const phi = rad(strokeDegrees * sign);
    const bodyX = shoulder[0] - v;
    const lateral = shoulder[1] + sign * u;
    const vertical = shoulder[2] + zTwist;
    const relY = lateral - shoulder[1];
    const relZ = vertical - shoulder[2];
    const y3 = shoulder[1] + relY * Math.cos(phi) - relZ * Math.sin(phi);
    const z3 = shoulder[2] + relY * Math.sin(phi) + relZ * Math.cos(phi);
    const camera = model.wing.camera;
    return [
      bodyX + (camera.x_from_y || 0) * y3 + camera.x_from_z * z3,
      camera.y_from_y * y3 + camera.y_from_z * z3,
    ];
  }

  function wingGeometry(model, side, phase, openness) {
    const frame = localWingFrame(model, phase, openness);
    const skeleton = localSkeleton(model, frame);
    const stations = model.wing.stations;
    const leadingLocal = [];
    const trailingLocal = [];

    stations.forEach((station) => {
      const lead = catmull(skeleton, station);
      const eps = 1e-3;
      const before = catmull(skeleton, Math.max(0, station - eps));
      const after = catmull(skeleton, Math.min(1, station + eps));
      const tangent = [after[0] - before[0], after[1] - before[1]];
      const length = Math.hypot(tangent[0], tangent[1]) || 1;
      const normalRaw = [-0.35 * tangent[1] / length, 1];
      const normalLength = Math.hypot(normalRaw[0], normalRaw[1]) || 1;
      const normal = [normalRaw[0] / normalLength, normalRaw[1] / normalLength];
      const c = chord(model, station, frame.chordScale);
      leadingLocal.push([lead[0] - normal[0] * c * 0.16, lead[1] - normal[1] * c * 0.16]);
      trailingLocal.push([lead[0] + normal[0] * c * 0.84, lead[1] + normal[1] * c * 0.84]);
    });

    const pronation = rad(frame.pronation);
    const leading = [];
    const trailing = [];
    stations.forEach((station, index) => {
      const c = chord(model, station, frame.chordScale);
      const twist = Math.sin(pronation) * c * (0.12 + 0.26 * station);
      leading.push(projectPoint(model, side, leadingLocal[index], -twist * 0.12, frame.stroke));
      trailing.push(projectPoint(model, side, trailingLocal[index], twist, frame.stroke));
    });

    const names = ['shoulder', 'elbow', 'wrist', 'tip'];
    const joints = {};
    skeleton.forEach((point, index) => {
      joints[names[index]] = projectPoint(model, side, point, 0, frame.stroke);
    });
    return { leading, trailing, joints, frame };
  }

  function smoothOpenPath(points) {
    if (points.length < 2) return '';
    const commands = [`M ${points[0][0].toFixed(3)} ${points[0][1].toFixed(3)}`];
    for (let i = 0; i < points.length - 1; i += 1) {
      const p0 = points[Math.max(0, i - 1)];
      const p1 = points[i];
      const p2 = points[i + 1];
      const p3 = points[Math.min(points.length - 1, i + 2)];
      const c1 = [p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6];
      const c2 = [p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6];
      commands.push(`C ${c1[0].toFixed(3)} ${c1[1].toFixed(3)} ${c2[0].toFixed(3)} ${c2[1].toFixed(3)} ${p2[0].toFixed(3)} ${p2[1].toFixed(3)}`);
    }
    return commands.join(' ');
  }

  function wingOutline(geometry) {
    const trailing = [...geometry.trailing].reverse();
    const leadingPath = smoothOpenPath(geometry.leading);
    const trailingPath = smoothOpenPath(trailing);
    return `${leadingPath} L ${trailing[0][0].toFixed(3)} ${trailing[0][1].toFixed(3)} ${trailingPath.split(' ').slice(3).join(' ')} Z`;
  }

  function cubic(a, b, c, d, t) {
    const u = 1 - t;
    return {
      x: u * u * u * a.x + 3 * u * u * t * b.x + 3 * u * t * t * c.x + t * t * t * d.x,
      y: u * u * u * a.y + 3 * u * u * t * b.y + 3 * u * t * t * c.y + t * t * t * d.y,
    };
  }

  function cubicDerivative(a, b, c, d, t) {
    const u = 1 - t;
    return {
      x: 3 * u * u * (b.x - a.x) + 6 * u * t * (c.x - b.x) + 3 * t * t * (d.x - c.x),
      y: 3 * u * u * (b.y - a.y) + 6 * u * t * (c.y - b.y) + 3 * t * t * (d.y - c.y),
    };
  }

  function initPercoliaBird(svg, options = {}) {
    if (!(svg instanceof SVGElement)) throw new TypeError('initPercoliaBird requires an inline SVG');
    const root = svg.matches('[data-percolia-bird]') ? svg : svg.querySelector('[data-percolia-bird]');
    if (!root) throw new Error('[data-percolia-bird] not found');
    const model = parseModel(root);
    const settings = Object.assign({
      autoplay: true,
      loop: true,
      birdElement: svg.closest('[data-flight-bird]'),
      stageElement: svg.closest('[data-flight-stage]'),
      perchElement: null,
      onState: null,
    }, options);
    const reducedMotion = global.matchMedia && global.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const q = (selector) => root.querySelector(selector);
    const qa = (selector) => [...root.querySelectorAll(selector)];
    const rig = q('#bird-rig');
    const foldedWing = q('[data-folded-wing]');
    const nearWingGroup = q('[data-wing="near"]');
    const farWingGroup = q('[data-wing="far"]');
    const legs = { near: q('[data-leg="near"]'), far: q('[data-leg="far"]') };
    const lidar = q('#lidar-scan');
    const lidarSweep = q('[data-lidar-sweep]');
    const lidarReturn = q('#lidar-return');
    const lidarRing = q('#lidar-ring');
    const critical = qa('[data-kind="critical"]');
    const edges = qa('[data-anim="edge"]');
    const faces = qa('[data-anim="face"]');
    const nodes = qa('[data-anim="node"]');

    let raf = 0;
    let startTime = 0;
    let pausedAt = 0;
    let running = false;
    let destroyed = false;
    let manualScanStart = -Infinity;
    let lastState = '';

    function setState(state) {
      if (state === lastState) return;
      lastState = state;
      root.dataset.flightState = state;
      if (settings.birdElement) settings.birdElement.dataset.flightState = state;
      if (typeof settings.onState === 'function') settings.onState(state);
    }

    function updateWing(side, geometry) {
      const outline = q(`[data-wing-outline="${side}"]`);
      if (outline) outline.setAttribute('d', wingOutline(geometry));
      for (let i = 0; i < geometry.leading.length - 1; i += 1) {
        const a = geometry.leading[i];
        const b = geometry.leading[i + 1];
        const c = geometry.trailing[i + 1];
        const d = geometry.trailing[i];
        const faceA = q(`[data-wing-face="${side}:${i}:a"]`);
        const faceB = q(`[data-wing-face="${side}:${i}:b"]`);
        if (faceA) faceA.setAttribute('points', `${a[0]},${a[1]} ${b[0]},${b[1]} ${d[0]},${d[1]}`);
        if (faceB) faceB.setAttribute('points', `${b[0]},${b[1]} ${c[0]},${c[1]} ${d[0]},${d[1]}`);
      }
      geometry.leading.forEach((lead, i) => {
        const trail = geometry.trailing[i];
        const spar = q(`[data-wing-spar="${side}:${i}"]`);
        if (spar) {
          spar.setAttribute('x1', lead[0]); spar.setAttribute('y1', lead[1]);
          spar.setAttribute('x2', trail[0]); spar.setAttribute('y2', trail[1]);
        }
      });
      for (let i = 0; i < geometry.leading.length - 1; i += 1) {
        const a = i % 2 === 0 ? geometry.trailing[i] : geometry.leading[i];
        const b = i % 2 === 0 ? geometry.leading[i + 1] : geometry.trailing[i + 1];
        const diagonal = q(`[data-wing-diagonal="${side}:${i}"]`);
        if (diagonal) {
          diagonal.setAttribute('x1', a[0]); diagonal.setAttribute('y1', a[1]);
          diagonal.setAttribute('x2', b[0]); diagonal.setAttribute('y2', b[1]);
        }
      }
      Object.entries(geometry.joints).forEach(([name, point]) => {
        const joint = q(`[data-wing-joint="${side}:${name}"]`);
        if (joint) { joint.setAttribute('cx', point[0]); joint.setAttribute('cy', point[1]); }
      });
    }

    function updateWings(phase, openness) {
      updateWing('far', wingGeometry(model, 'far', phase, openness));
      updateWing('near', wingGeometry(model, 'near', phase, openness));
      const open = clamp(openness, 0, 1);
      if (foldedWing) foldedWing.style.opacity = String(1 - smoothstep(0.05, 0.62, open));
      if (nearWingGroup) nearWingGroup.style.opacity = String(0.90 * smoothstep(0.20, 0.88, open));
      if (farWingGroup) farWingGroup.style.opacity = String(0.24 * smoothstep(0.28, 0.92, open));
    }

    function updateLegs(retraction) {
      const near = model.legs.near;
      const far = model.legs.far;
      const angleNear = lerp(0, -54, retraction);
      const angleFar = lerp(0, -48, retraction);
      if (legs.near) {
        legs.near.setAttribute('transform', `rotate(${angleNear.toFixed(2)} ${near.hip[0]} ${near.hip[1]})`);
        legs.near.style.opacity = String(lerp(0.82, 0.12, retraction));
      }
      if (legs.far) {
        legs.far.setAttribute('transform', `rotate(${angleFar.toFixed(2)} ${far.hip[0]} ${far.hip[1]})`);
        legs.far.style.opacity = String(lerp(0.42, 0.06, retraction));
      }
    }

    function pathGeometry() {
      const stage = settings.stageElement;
      const perch = settings.perchElement;
      if (!stage || !perch) return null;
      const stageRect = stage.getBoundingClientRect();
      const perchRect = perch.getBoundingClientRect();
      const start = {
        x: perchRect.left - stageRect.left + perchRect.width / 2,
        y: perchRect.top - stageRect.top + perchRect.height / 2,
      };
      const w = stageRect.width;
      const h = stageRect.height;
      return {
        start,
        segments: [
          [start, { x: start.x + w * 0.02, y: start.y - h * 0.30 }, { x: w * 0.22, y: h * 0.18 }, { x: w * 0.39, y: h * 0.22 }],
          [{ x: w * 0.39, y: h * 0.22 }, { x: w * 0.56, y: h * 0.06 }, { x: w * 0.80, y: h * 0.12 }, { x: w * 0.86, y: h * 0.34 }],
          [{ x: w * 0.86, y: h * 0.34 }, { x: w * 0.89, y: h * 0.59 }, { x: w * 0.61, y: h * 0.61 }, { x: w * 0.41, y: h * 0.37 }],
          [{ x: w * 0.41, y: h * 0.37 }, { x: w * 0.25, y: h * 0.16 }, { x: start.x + w * 0.10, y: start.y - h * 0.22 }, start],
        ],
      };
    }

    function pathPoint(progress) {
      const geometry = pathGeometry();
      if (!geometry) return null;
      const scaled = clamp(progress, 0, 0.999999) * geometry.segments.length;
      const index = Math.min(geometry.segments.length - 1, Math.floor(scaled));
      const local = scaled - index;
      const [a, b, c, d] = geometry.segments[index];
      return {
        point: cubic(a, b, c, d, local),
        derivative: cubicDerivative(a, b, c, d, local),
        start: geometry.start,
      };
    }

    function updatePosition(progress, heave, pitchHint) {
      if (!settings.birdElement) return;
      const sample = pathPoint(progress);
      if (!sample) return;
      const angle = Math.atan2(sample.derivative.y, sample.derivative.x) * 180 / Math.PI;
      const dx = sample.point.x - sample.start.x;
      const dy = sample.point.y - sample.start.y + heave;
      const pitch = clamp(angle * 0.22 + pitchHint, -10, 10);
      settings.birdElement.style.transform = `translate(${dx.toFixed(2)}px, ${dy.toFixed(2)}px) translate(-50%, -100%) rotate(${pitch.toFixed(2)}deg)`;
    }

    function updateScan(progress, now) {
      if (!lidar) return;
      const target = model.flight_path.scan_progress;
      const automatic = 1 - Math.min(1, Math.abs(progress - target) / 0.045);
      const manualElapsed = now - manualScanStart;
      const manual = manualElapsed >= 0 && manualElapsed < 1200
        ? Math.sin(Math.PI * manualElapsed / 1200)
        : 0;
      const strength = clamp(Math.max(automatic, manual), 0, 1);
      lidar.style.opacity = String(smoothstep(0.08, 0.55, strength));
      if (strength <= 0) return;
      const sweep = manual > automatic
        ? manualElapsed / 1200
        : clamp((progress - (target - 0.045)) / 0.09, 0, 1);
      if (lidarSweep) lidarSweep.setAttribute('transform', `rotate(${lerp(-14, 16, sweep).toFixed(2)})`);
      const flash = Math.exp(-Math.pow((sweep - 0.72) / 0.075, 2));
      if (lidarReturn) {
        lidarReturn.style.opacity = String(flash);
        lidarReturn.setAttribute('r', String(lerp(1.3, 3.8, flash)));
      }
      if (lidarRing) {
        const ring = clamp((sweep - 0.70) / 0.30, 0, 1);
        lidarRing.style.opacity = String((1 - ring) * (ring > 0 ? 0.8 : 0));
        lidarRing.setAttribute('r', String(lerp(2.5, 9.5, ring)));
      }
    }

    function reveal() {
      if (reducedMotion) return Promise.resolve();
      const promises = [];
      edges.forEach((edge) => {
        const length = Math.max(1, edge.getTotalLength());
        edge.style.strokeDasharray = String(length);
        edge.style.strokeDashoffset = String(length);
        promises.push(edge.animate(
          [{ strokeDashoffset: length }, { strokeDashoffset: 0 }],
          { duration: 700, delay: Number(edge.dataset.phase || 0) * 45, easing: 'cubic-bezier(.2,.75,.25,1)', fill: 'forwards' }
        ).finished.catch(() => undefined));
      });
      faces.forEach((face) => {
        const opacity = getComputedStyle(face).opacity;
        promises.push(face.animate(
          [{ opacity: 0 }, { opacity }],
          { duration: 430, delay: Number(face.dataset.phase || 0) * 45 + 80, easing: 'ease-out', fill: 'forwards' }
        ).finished.catch(() => undefined));
      });
      nodes.forEach((node, index) => {
        node.style.transformBox = 'fill-box';
        node.style.transformOrigin = 'center';
        promises.push(node.animate(
          [{ opacity: 0, transform: 'scale(.35)' }, { opacity: 1, transform: 'scale(1)' }],
          { duration: 280, delay: 40 + index * 12, easing: 'ease-out', fill: 'forwards' }
        ).finished.catch(() => undefined));
      });
      return Promise.all(promises);
    }

    function pulse() {
      if (reducedMotion || destroyed) return;
      critical.forEach((element, index) => {
        const isCircle = element.tagName.toLowerCase() === 'circle';
        element.animate(
          isCircle
            ? [{ transform: 'scale(1)' }, { transform: 'scale(1.28)' }, { transform: 'scale(1)' }]
            : [{ opacity: 1 }, { opacity: 0.4 }, { opacity: 1 }],
          { duration: 760, delay: index * 34, easing: 'ease-in-out' }
        );
      });
    }

    function timeline(now) {
      if (destroyed || !running) return;
      const path = model.flight_path;
      const elapsed = now - startTime;
      const cycle = path.cycle_ms;
      const local = settings.loop ? elapsed % cycle : Math.min(elapsed, cycle);
      const perchEnd = path.perch_ms;
      const takeoffEnd = perchEnd + path.takeoff_ms;
      const flightEnd = takeoffEnd + path.flight_ms;
      const landingEnd = flightEnd + path.landing_ms;

      let state = 'perched';
      let openness = 0;
      let progress = 0;
      let retraction = 0;

      if (local < perchEnd) {
        state = 'perched';
      } else if (local < takeoffEnd) {
        state = 'takeoff';
        const t = smoothstep(perchEnd, takeoffEnd, local);
        openness = t;
        progress = 0.08 * t;
        retraction = t;
      } else if (local < flightEnd) {
        state = 'flight';
        const t = (local - takeoffEnd) / path.flight_ms;
        openness = 1;
        progress = lerp(0.08, 0.92, t);
        retraction = 1;
      } else if (local < landingEnd) {
        state = 'landing';
        const t = smoothstep(flightEnd, landingEnd, local);
        openness = 1 - t;
        progress = lerp(0.92, 0.999999, t);
        retraction = 1 - t;
      }

      setState(state);
      const wingTime = Math.max(0, local - perchEnd);
      const phase = mod1(wingTime / model.wing.flight.period_ms);
      updateWings(phase, openness);
      updateLegs(retraction);
      const theta = TAU * phase;
      const heave = openness * model.wing.flight.heave * Math.cos(theta);
      const pitch = openness * model.wing.flight.pitch_deg * Math.sin(theta);
      if (rig) rig.setAttribute('transform', `translate(0 ${heave.toFixed(3)}) rotate(${pitch.toFixed(3)} 0 0)`);
      updatePosition(progress, heave, pitch);
      updateScan(progress, now);

      if (!settings.loop && local >= landingEnd) {
        running = false;
        return;
      }
      raf = global.requestAnimationFrame(timeline);
    }

    function play() {
      if (destroyed || running) return;
      running = true;
      const now = performance.now();
      if (!startTime) startTime = now;
      if (pausedAt) {
        startTime += now - pausedAt;
        pausedAt = 0;
      }
      raf = global.requestAnimationFrame(timeline);
    }

    function pause() {
      if (!running) return;
      running = false;
      pausedAt = performance.now();
      global.cancelAnimationFrame(raf);
    }

    function restart() {
      startTime = performance.now();
      pausedAt = 0;
      running = true;
      global.cancelAnimationFrame(raf);
      raf = global.requestAnimationFrame(timeline);
    }

    function scan() {
      manualScanStart = performance.now();
    }

    updateWings(0.12, 0);
    updateLegs(0);
    reveal().then(() => {
      if (settings.autoplay && !reducedMotion) play();
    });

    return {
      play,
      pause,
      restart,
      scan,
      pulse,
      model,
      get state() { return lastState; },
      destroy() {
        destroyed = true;
        running = false;
        global.cancelAnimationFrame(raf);
        if (svg.getAnimations) svg.getAnimations({ subtree: true }).forEach((animation) => animation.cancel());
      },
    };
  }

  global.initPercoliaBird = initPercoliaBird;
})(window);
