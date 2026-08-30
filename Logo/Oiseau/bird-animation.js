/**
 * Percolia directional network-bird animation.
 *
 * The visible bird is the original triangulated network silhouette. Only the
 * wings are recomputed frame by frame from a three-link chain. The outbound
 * bird always travels left-to-right and leaves the stage. A distinct inbound
 * bird then travels right-to-left and lands on the P.
 */
(function (global) {
  'use strict';

  const TAU = Math.PI * 2;
  const RAD = Math.PI / 180;
  const clamp = (value, min, max) => Math.min(max, Math.max(min, value));
  const lerp = (a, b, t) => a + (b - a) * t;
  const smoothstep = (a, b, x) => {
    const t = clamp((x - a) / (b - a), 0, 1);
    return t * t * (3 - 2 * t);
  };
  const easeInOutCubic = (t) => t < 0.5
    ? 4 * t * t * t
    : 1 - Math.pow(-2 * t + 2, 3) / 2;
  const add = (a, b) => [a[0] + b[0], a[1] + b[1]];
  const sub = (a, b) => [a[0] - b[0], a[1] - b[1]];
  const mul = (a, scalar) => [a[0] * scalar, a[1] * scalar];
  const length = (a) => Math.hypot(a[0], a[1]);
  const unit = (a) => {
    const value = length(a);
    if (value < 1e-9) throw new Error('Percolia wing: null vector');
    return [a[0] / value, a[1] / value];
  };
  const normal = (a) => {
    const [x, y] = unit(a);
    return [-y, x];
  };
  const mixPoint = (a, b, t) => [lerp(a[0], b[0], t), lerp(a[1], b[1], t)];
  const fmt = (value) => (Math.abs(value) < 5e-7 ? 0 : value)
    .toFixed(3)
    .replace(/\.0+$/, '')
    .replace(/(\.\d*?)0+$/, '$1');
  const pointsString = (points) => points.map((point) => `${fmt(point[0])},${fmt(point[1])}`).join(' ');

  function cubic(points, t) {
    const [p0, p1, p2, p3] = points;
    const u = 1 - t;
    return [
      u * u * u * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t * t * t * p3[0],
      u * u * u * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t * t * t * p3[1],
    ];
  }

  function cubicDerivative(points, t) {
    const [p0, p1, p2, p3] = points;
    const u = 1 - t;
    return [
      3 * u * u * (p1[0] - p0[0]) + 6 * u * t * (p2[0] - p1[0]) + 3 * t * t * (p3[0] - p2[0]),
      3 * u * u * (p1[1] - p0[1]) + 6 * u * t * (p2[1] - p1[1]) + 3 * t * t * (p3[1] - p2[1]),
    ];
  }

  function readModel(svg) {
    const metadata = svg.querySelector('metadata[data-network-model="true"]');
    if (!metadata) throw new Error('Percolia network model metadata not found');
    return JSON.parse(metadata.textContent);
  }

  function periodicPose(model, phase, side) {
    const wing = model.wing;
    phase = (phase + wing[`${side}_phase_offset`]) % 1;
    const theta = TAU * phase;
    const stroke = wing.stroke_center_deg
      + wing.stroke_amplitude_deg * Math.cos(theta)
      + wing.stroke_harmonic_deg * Math.cos(2 * theta + wing.stroke_harmonic_phase_deg * RAD);
    // Extended on the downstroke, folded on the recovery stroke. Unlike the
    // old prototype, the elbow and wrist do not just copy the shoulder angle.
    const upstroke = Math.pow(
      (1 - Math.sin(theta + wing.fold_phase_deg * RAD)) / 2,
      wing.fold_exponent
    );
    return {
      stroke_deg: stroke,
      elbow_deg: wing.elbow_base_deg + wing.elbow_fold_deg * upstroke,
      wrist_deg: wing.wrist_base_deg + wing.wrist_fold_deg * upstroke,
      span_scale: wing[`${side}_scale`],
      chord_scale: Math.sqrt(wing[`${side}_scale`]),
    };
  }

  function foldedPose(model, side) {
    const pose = Object.assign({}, model.wing.folded_pose);
    pose.span_scale *= model.wing[`${side}_scale`];
    pose.chord_scale *= Math.sqrt(model.wing[`${side}_scale`]);
    return pose;
  }

  function wingGeometry(model, pose, side) {
    const wing = model.wing;
    const shoulder = wing.shoulders[side];
    const lengths = wing.segment_lengths.map((value) => value * pose.span_scale);
    const a1 = pose.stroke_deg * RAD;
    const a2 = a1 + pose.elbow_deg * RAD;
    const a3 = a2 + pose.wrist_deg * RAD;
    const s = shoulder.slice();
    const e = add(s, [lengths[0] * Math.cos(a1), lengths[0] * Math.sin(a1)]);
    const w = add(e, [lengths[1] * Math.cos(a2), lengths[1] * Math.sin(a2)]);
    const tip = add(w, [lengths[2] * Math.cos(a3), lengths[2] * Math.sin(a3)]);
    const joints = [s, e, w, tip];
    const tangents = [
      sub(e, s),
      add(unit(sub(e, s)), unit(sub(w, e))),
      add(unit(sub(w, e)), unit(sub(tip, w))),
      sub(tip, w),
    ];
    const normals = tangents.map(normal);
    const widths = wing.chords.map((value) => value * pose.chord_scale);
    const leading = joints.map((point, index) => sub(point, mul(normals[index], widths[index] * wing.leading_fraction)));
    const trailing = joints.map((point, index) => add(point, mul(normals[index], widths[index] * (1 - wing.leading_fraction))));
    const boundary = [leading[0], leading[1], leading[2], tip, trailing[2], trailing[1], trailing[0]];
    const core = [
      0.18 * s[0] + 0.33 * e[0] + 0.34 * w[0] + 0.15 * tip[0],
      0.18 * s[1] + 0.33 * e[1] + 0.34 * w[1] + 0.15 * tip[1],
    ];
    return { boundary, core, joints };
  }

  function blendGeometry(a, b, t) {
    return {
      boundary: a.boundary.map((point, index) => mixPoint(point, b.boundary[index], t)),
      core: mixPoint(a.core, b.core, t),
      joints: a.joints.map((point, index) => mixPoint(point, b.joints[index], t)),
    };
  }

  function collectWing(root, side) {
    const group = root.querySelector(`[data-wing-side="${side}"]`);
    if (!group) throw new Error(`Percolia wing group missing: ${side}`);
    return {
      group,
      outline: group.querySelector('[data-wing-outline="true"]'),
      faces: [...group.querySelectorAll('[data-wing-face]')].sort((a, b) => Number(a.dataset.wingFace) - Number(b.dataset.wingFace)),
      boundary: [...group.querySelectorAll('[data-wing-boundary]')].sort((a, b) => Number(a.dataset.wingBoundary) - Number(b.dataset.wingBoundary)),
      spokes: [...group.querySelectorAll('[data-wing-spoke]')].sort((a, b) => Number(a.dataset.wingSpoke) - Number(b.dataset.wingSpoke)),
      nodes: [...group.querySelectorAll('[data-wing-node]')].sort((a, b) => Number(a.dataset.wingNode) - Number(b.dataset.wingNode)),
      core: group.querySelector('[data-wing-core="true"]'),
    };
  }

  function renderWing(elements, geometry) {
    const boundary = geometry.boundary;
    const core = geometry.core;
    elements.outline.setAttribute('points', pointsString(boundary));
    for (let index = 0; index < 7; index += 1) {
      const a = boundary[index];
      const b = boundary[(index + 1) % 7];
      elements.faces[index].setAttribute('points', pointsString([a, b, core]));
      elements.boundary[index].setAttribute('x1', fmt(a[0]));
      elements.boundary[index].setAttribute('y1', fmt(a[1]));
      elements.boundary[index].setAttribute('x2', fmt(b[0]));
      elements.boundary[index].setAttribute('y2', fmt(b[1]));
      elements.spokes[index].setAttribute('x1', fmt(a[0]));
      elements.spokes[index].setAttribute('y1', fmt(a[1]));
      elements.spokes[index].setAttribute('x2', fmt(core[0]));
      elements.spokes[index].setAttribute('y2', fmt(core[1]));
      elements.nodes[index].setAttribute('cx', fmt(a[0]));
      elements.nodes[index].setAttribute('cy', fmt(a[1]));
    }
    elements.core.setAttribute('cx', fmt(core[0]));
    elements.core.setAttribute('cy', fmt(core[1]));
  }

  function createBirdController(svg, flightGroup) {
    const model = readModel(svg);
    const root = svg.querySelector('[data-percolia-bird]');
    const wings = {
      near: collectWing(root, 'near'),
      far: collectWing(root, 'far'),
    };
    const folded = {
      near: wingGeometry(model, foldedPose(model, 'near'), 'near'),
      far: wingGeometry(model, foldedPose(model, 'far'), 'far'),
    };
    const legRefs = {};
    ['near', 'far'].forEach((side) => {
      const group = root.querySelector(`[data-leg="${side}"]`);
      legRefs[side] = {
        group,
        main: group ? group.querySelector('[data-leg-main="true"]') : null,
        toes: group ? [...group.querySelectorAll('[data-leg-toe]')] : [],
      };
    });
    const lidar = root.querySelector('[data-lidar="true"]');
    const lidarReturn = root.querySelector('[data-lidar-return="true"]');
    const beak = model.body.nodes.q1.slice(0, 2);
    const anchor = model.flight.bird_anchor;

    function setWingCycle(phase, openness) {
      ['far', 'near'].forEach((side) => {
        const flightGeometry = wingGeometry(model, periodicPose(model, phase, side), side);
        renderWing(wings[side], blendGeometry(folded[side], flightGeometry, openness));
      });
    }

    function setLegTuck(amount) {
      ['near', 'far'].forEach((side) => {
        const refs = legRefs[side];
        if (!refs.group) return;
        const leg = model.legs[side];
        const hip = leg.hip;
        const knee = mixPoint(leg.knee, hip, amount * 0.55);
        const ankle = mixPoint(leg.ankle, hip, amount * 0.72);
        refs.main.setAttribute('points', pointsString([hip, knee, ankle]));
        refs.toes.forEach((line, index) => {
          const toe = mixPoint(leg.toes[index], ankle, amount);
          line.setAttribute('x1', fmt(ankle[0]));
          line.setAttribute('y1', fmt(ankle[1]));
          line.setAttribute('x2', fmt(toe[0]));
          line.setAttribute('y2', fmt(toe[1]));
        });
        refs.group.style.opacity = String(lerp(side === 'far' ? 0.42 : 0.92, side === 'far' ? 0.16 : 0.34, amount));
      });
    }

    function setLidar(strength, sweep) {
      if (!lidar) return;
      const alpha = smoothstep(0.02, 0.38, strength);
      lidar.style.opacity = String(alpha);
      lidar.setAttribute('transform', `translate(${beak[0]} ${beak[1]}) rotate(${lerp(-14, 16, sweep).toFixed(2)})`);
      if (lidarReturn) {
        const flash = Math.exp(-Math.pow((sweep - 0.72) / 0.09, 2));
        lidarReturn.style.opacity = String(flash);
        lidarReturn.setAttribute('r', String(lerp(2.2, 5.2, flash)));
      }
    }

    function place(position, tangent, scale, mirror, opacity) {
      const angle = Math.atan2(tangent[1], tangent[0]) / RAD;
      const rotation = mirror ? angle - 180 : angle;
      const sx = mirror ? -scale : scale;
      flightGroup.setAttribute(
        'transform',
        `translate(${fmt(position[0])} ${fmt(position[1])}) rotate(${fmt(rotation)}) scale(${fmt(sx)} ${fmt(scale)}) translate(${-anchor[0]} ${-anchor[1]})`
      );
      flightGroup.style.opacity = String(opacity);
    }

    return { model, setWingCycle, setLegTuck, setLidar, place };
  }

  function initPercoliaDirectionalScene(options) {
    const stage = options.stage;
    const perched = options.perched;
    const outboundGroup = options.outboundGroup;
    const inboundGroup = options.inboundGroup;
    const outboundSvg = outboundGroup.querySelector('svg');
    const inboundSvg = inboundGroup.querySelector('svg');
    const outbound = createBirdController(outboundSvg, outboundGroup);
    const inbound = createBirdController(inboundSvg, inboundGroup);
    const model = outbound.model;
    const timeline = model.flight.timeline_ms;
    const total = Object.values(timeline).reduce((sum, value) => sum + value, 0);
    const reducedMotion = global.matchMedia && global.matchMedia('(prefers-reduced-motion: reduce)').matches;
    let start = performance.now();
    let elapsedBeforePause = 0;
    let running = false;
    let raf = 0;
    let finished = false;
    let lastState = '';

    function setState(name) {
      if (name === lastState) return;
      lastState = name;
      if (typeof options.onState === 'function') options.onState(name);
    }

    const boundaries = {};
    let cursor = 0;
    Object.entries(timeline).forEach(([name, duration]) => {
      boundaries[name] = { start: cursor, end: cursor + duration, duration };
      cursor += duration;
    });

    function phaseFor(time) {
      return (time % model.wing.period_ms) / model.wing.period_ms;
    }

    function section(name, time) {
      const part = boundaries[name];
      return clamp((time - part.start) / part.duration, 0, 1);
    }

    function showPerched(opacity) {
      perched.style.opacity = String(opacity);
    }

    function update(time) {
      const flapPhase = phaseFor(time);
      outboundGroup.style.opacity = '0';
      inboundGroup.style.opacity = '0';
      outbound.setLidar(0, 0);
      inbound.setLidar(0, 0);

      if (time < boundaries.initial_perch.end) {
        setState('perched');
        showPerched(1);
        return;
      }

      if (time < boundaries.takeoff.end) {
        setState('takeoff');
        const u = easeInOutCubic(section('takeoff', time));
        const position = cubic(model.flight.takeoff_curve, u);
        const tangent = cubicDerivative(model.flight.takeoff_curve, Math.min(0.999, u));
        showPerched(1 - smoothstep(0.08, 0.60, u));
        outbound.setWingCycle(flapPhase, smoothstep(0.02, 0.55, u));
        outbound.setLegTuck(smoothstep(0.08, 0.70, u));
        outbound.place(position, tangent, model.flight.bird_scale, false, smoothstep(0, 0.12, u));
        return;
      }

      if (time < boundaries.outbound.end) {
        setState('outbound');
        const u = section('outbound', time);
        const position = cubic(model.flight.outbound_curve, u);
        const tangent = cubicDerivative(model.flight.outbound_curve, Math.min(0.999, u));
        showPerched(0);
        outbound.setWingCycle(flapPhase, 1);
        outbound.setLegTuck(1);
        const fade = 1 - smoothstep(0.90, 1, u);
        outbound.place(position, tangent, model.flight.bird_scale, false, fade);
        const scanHalf = model.flight.scan_duration_fraction / 2;
        const scanDistance = Math.abs(u - model.flight.scan_progress);
        const scanStrength = 1 - clamp(scanDistance / scanHalf, 0, 1);
        const scanSweep = clamp((u - (model.flight.scan_progress - scanHalf)) / (2 * scanHalf), 0, 1);
        outbound.setLidar(scanStrength, scanSweep);
        return;
      }

      if (time < boundaries.empty.end) {
        setState('empty');
        showPerched(0);
        return;
      }

      if (time < boundaries.inbound.end) {
        setState('inbound');
        const u = section('inbound', time);
        const position = cubic(model.flight.inbound_curve, u);
        const tangent = cubicDerivative(model.flight.inbound_curve, Math.min(0.999, u));
        showPerched(0);
        inbound.setWingCycle((flapPhase + 0.17) % 1, 1);
        inbound.setLegTuck(1 - smoothstep(0.72, 0.98, u));
        inbound.place(position, tangent, model.flight.bird_scale, true, smoothstep(0, 0.08, u));
        return;
      }

      if (time < boundaries.landing.end) {
        setState('landing');
        const u = easeInOutCubic(section('landing', time));
        const position = cubic(model.flight.landing_curve, u);
        const tangent = cubicDerivative(model.flight.landing_curve, Math.min(0.999, u));
        const openness = 1 - smoothstep(0.45, 0.96, u);
        inbound.setWingCycle((flapPhase + 0.17) % 1, openness);
        inbound.setLegTuck(1 - smoothstep(0.02, 0.72, u));
        inbound.place(position, tangent, lerp(model.flight.bird_scale, model.flight.perched_scale, u), true, 1 - smoothstep(0.78, 1, u));
        showPerched(smoothstep(0.76, 1, u));
        return;
      }

      setState('perched');
      showPerched(1);
      if (!finished) {
        finished = true;
        running = false;
        if (typeof options.onFinish === 'function') options.onFinish();
      }
    }

    function frame(now) {
      if (!running) return;
      const time = Math.min(total, elapsedBeforePause + now - start);
      update(time);
      if (time < total) raf = requestAnimationFrame(frame);
    }

    function play() {
      if (reducedMotion || running || finished) return;
      running = true;
      start = performance.now();
      raf = requestAnimationFrame(frame);
    }

    function pause() {
      if (!running) return;
      elapsedBeforePause += performance.now() - start;
      running = false;
      cancelAnimationFrame(raf);
    }

    function restart() {
      cancelAnimationFrame(raf);
      elapsedBeforePause = 0;
      finished = false;
      start = performance.now();
      update(0);
      if (!reducedMotion) {
        running = true;
        raf = requestAnimationFrame(frame);
      }
    }

    function seek(milliseconds) {
      pause();
      elapsedBeforePause = clamp(milliseconds, 0, total);
      update(elapsedBeforePause);
    }

    update(0);
    if (!reducedMotion && options.autoplay !== false) play();

    return { play, pause, restart, seek, duration: total, isRunning: () => running };
  }

  global.initPercoliaDirectionalScene = initPercoliaDirectionalScene;
})(window);
