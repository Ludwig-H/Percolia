/**
 * Percolia network-bird animation controller.
 *
 * The controller follows a game-animation pipeline rather than deriving the
 * whole performance from one periodic formula:
 *   - authored animation clips with explicit keyframes;
 *   - a deterministic state machine;
 *   - root motion for take-off, approach and landing;
 *   - motion warping at the P;
 *   - two-bone leg IK and explicit toe-off / touchdown events;
 *   - a separate looping cruise clip for each flying actor.
 *
 * The graphic language remains the original Percolia triangulated network.
 */
(function (global) {
  'use strict';

  const TAU = Math.PI * 2;
  const RAD = Math.PI / 180;
  const clamp = (value, min, max) => Math.min(max, Math.max(min, value));
  const lerp = (a, b, t) => a + (b - a) * t;
  const add = (a, b) => [a[0] + b[0], a[1] + b[1]];
  const sub = (a, b) => [a[0] - b[0], a[1] - b[1]];
  const mul = (a, scalar) => [a[0] * scalar, a[1] * scalar];
  const length = (a) => Math.hypot(a[0], a[1]);
  const mixPoint = (a, b, t) => [lerp(a[0], b[0], t), lerp(a[1], b[1], t)];
  const smoothstep = (a, b, x) => {
    if (Math.abs(b - a) < 1e-9) return x >= b ? 1 : 0;
    const t = clamp((x - a) / (b - a), 0, 1);
    return t * t * (3 - 2 * t);
  };
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

  function readClipLibrary(options, stage) {
    if (options.clips && options.clips.clips && options.clips.timeline) return options.clips;
    const node = stage.querySelector('[data-animation-clips="true"]');
    if (!node) throw new Error('Percolia animation clip library not found');
    return JSON.parse(node.textContent);
  }

  function unit(vector) {
    const value = length(vector);
    if (value < 1e-9) return [1, 0];
    return [vector[0] / value, vector[1] / value];
  }

  function normal(vector) {
    const [x, y] = unit(vector);
    return [-y, x];
  }

  function hermiteValue(p0, p1, p2, p3, t0, t1, t2, t3, t) {
    const duration = Math.max(1e-9, t2 - t1);
    const u = clamp((t - t1) / duration, 0, 1);
    const u2 = u * u;
    const u3 = u2 * u;
    const h00 = 2 * u3 - 3 * u2 + 1;
    const h10 = u3 - 2 * u2 + u;
    const h01 = -2 * u3 + 3 * u2;
    const h11 = u3 - u2;
    const m1 = (p2 - p0) / Math.max(1e-9, t2 - t0);
    const m2 = (p3 - p1) / Math.max(1e-9, t3 - t1);
    return h00 * p1 + h10 * duration * m1 + h01 * p2 + h11 * duration * m2;
  }

  function sampleTrack(frames, key, progress) {
    if (frames.length === 1) return frames[0][key].slice();
    const t = clamp(progress, 0, 1);
    let index = frames.length - 2;
    for (let i = 0; i < frames.length - 1; i += 1) {
      if (t <= frames[i + 1].t) {
        index = i;
        break;
      }
    }
    const f0 = frames[Math.max(0, index - 1)];
    const f1 = frames[index];
    const f2 = frames[index + 1];
    const f3 = frames[Math.min(frames.length - 1, index + 2)];
    const output = [];
    for (let component = 0; component < f1[key].length; component += 1) {
      let value = hermiteValue(
        f0[key][component],
        f1[key][component],
        f2[key][component],
        f3[key][component],
        f0.t,
        f1.t,
        f2.t,
        f3.t,
        t
      );
      // Root x/y and all scalar rig controls are clamped to the neighbouring
      // authored values. This keeps Hermite continuity without overshoot.
      const low = Math.min(f1[key][component], f2[key][component]);
      const high = Math.max(f1[key][component], f2[key][component]);
      value = clamp(value, low, high);
      output.push(value);
    }
    return output;
  }

  function sampleClip(library, name, progress) {
    const clip = library.clips[name];
    if (!clip) throw new Error(`Percolia clip not found: ${name}`);
    let t = progress;
    if (clip.loop) t = ((t % 1) + 1) % 1;
    else t = clamp(t, 0, 1);
    return {
      root: sampleTrack(clip.keyframes, 'root', t),
      wing: sampleTrack(clip.keyframes, 'wing', t),
      legs: sampleTrack(clip.keyframes, 'legs', t),
    };
  }

  function eventTime(library, clipName, eventName) {
    const clip = library.clips[clipName];
    const event = (clip.events || []).find((item) => item.name === eventName);
    if (!event) throw new Error(`Percolia event ${eventName} missing in ${clipName}`);
    return event.t;
  }

  function poseForSide(model, wingTrack, side) {
    const [stroke, elbow, wrist, span, chord] = wingTrack;
    const sideScale = model.wing[`${side}_scale`];
    return {
      stroke_deg: stroke + (side === 'far' ? -5.5 : 0),
      elbow_deg: elbow + (side === 'far' ? 2 : 0),
      wrist_deg: wrist + (side === 'far' ? 3 : 0),
      span_scale: span * sideScale,
      chord_scale: chord * Math.sqrt(sideScale),
    };
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

  function solveTwoBone(hip, originalKnee, originalAnkle, target) {
    const upperLength = length(sub(originalKnee, hip));
    const lowerLength = length(sub(originalAnkle, originalKnee));
    const delta = sub(target, hip);
    const direction = unit(delta);
    const distance = clamp(length(delta), Math.abs(upperLength - lowerLength) + 1e-4, upperLength + lowerLength - 1e-4);
    const base = Math.atan2(direction[1], direction[0]);
    const cosine = clamp(
      (upperLength * upperLength + distance * distance - lowerLength * lowerLength) / (2 * upperLength * distance),
      -1,
      1
    );
    const bend = Math.acos(cosine);
    const originalA = sub(originalKnee, hip);
    const originalB = sub(originalAnkle, originalKnee);
    const cross = originalA[0] * originalB[1] - originalA[1] * originalB[0];
    const sign = cross >= 0 ? 1 : -1;
    const angle = base + sign * bend;
    const knee = add(hip, [upperLength * Math.cos(angle), upperLength * Math.sin(angle)]);
    return { knee, ankle: target };
  }

  function createBirdController(svg, flightGroup) {
    const model = readModel(svg);
    const root = svg.querySelector('[data-percolia-bird]');
    const wings = {
      near: collectWing(root, 'near'),
      far: collectWing(root, 'far'),
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
    const lidarPulse = root.querySelector('[data-lidar-pulse="true"]');
    const lidarRays = root.querySelector('[data-lidar-rays="true"]');
    const lidarReturn = root.querySelector('[data-lidar-return="true"]');
    // The scan is mounted on the central head node.
    const sensor = model.body.nodes.h5.slice(0, 2);
    const anchor = model.flight.flight_anchor || model.flight.bird_anchor;
    const defaultContact = model.flight.perched_anchor || [306, 285];

    // Compact head-mounted pulse and short rotating scan tick.
    if (lidarPulse) {
      lidarPulse.setAttribute('fill', 'none');
      lidarPulse.setAttribute('stroke', model.palette.cyan);
      lidarPulse.setAttribute('stroke-width', '1.45');
      lidarPulse.setAttribute('vector-effect', 'non-scaling-stroke');
    }
    if (lidarRays) {
      lidarRays.setAttribute('x1', '0');
      lidarRays.setAttribute('y1', '-4');
      lidarRays.setAttribute('x2', '0');
      lidarRays.setAttribute('y2', '-18');
      lidarRays.setAttribute('stroke', model.palette.blue);
      lidarRays.setAttribute('stroke-width', '1.35');
    }
    if (lidarReturn) {
      lidarReturn.setAttribute('cx', '0');
      lidarReturn.setAttribute('cy', '0');
    }

    function setWingPose(wingTrack) {
      ['far', 'near'].forEach((side) => {
        renderWing(wings[side], wingGeometry(model, poseForSide(model, wingTrack, side), side));
      });
    }

    function setLegPose(legTrack) {
      const tuck = clamp(legTrack[0], 0, 1);
      const compression = clamp(legTrack[1], 0, 1);
      const contact = clamp(legTrack[2], 0, 1);
      let nearTarget = null;

      ['near', 'far'].forEach((side) => {
        const refs = legRefs[side];
        if (!refs.group) return;
        const leg = model.legs[side];
        const hip = leg.hip;
        const originalKnee = leg.knee;
        const originalAnkle = leg.ankle;
        const compressed = mixPoint(originalAnkle, hip, compression * 0.18);
        const tucked = [hip[0] + (side === 'near' ? -4 : 5), hip[1] + 11];
        const target = mixPoint(compressed, tucked, tuck);
        const solved = solveTwoBone(hip, originalKnee, originalAnkle, target);
        refs.main.setAttribute('points', pointsString([hip, solved.knee, solved.ankle]));

        const toeSpread = clamp((1 - tuck) * lerp(0.68, 1, contact), 0, 1);
        refs.toes.forEach((line, index) => {
          const toeVector = sub(leg.toes[index], originalAnkle);
          const toe = add(solved.ankle, mul(toeVector, toeSpread));
          line.setAttribute('x1', fmt(solved.ankle[0]));
          line.setAttribute('y1', fmt(solved.ankle[1]));
          line.setAttribute('x2', fmt(toe[0]));
          line.setAttribute('y2', fmt(toe[1]));
        });
        refs.group.style.opacity = String(lerp(side === 'far' ? 0.18 : 0.38, side === 'far' ? 0.42 : 0.92, 1 - tuck));
        if (side === 'near') nearTarget = target;
      });

      const baseNearAnkle = model.legs.near.ankle;
      const anchorShift = nearTarget ? sub(nearTarget, baseNearAnkle) : [0, 0];
      return { contactLocal: add(defaultContact, anchorShift) };
    }

    function setLidar(strength, sweep) {
      if (!lidar) return;
      const alpha = smoothstep(0.02, 0.32, strength);
      lidar.style.opacity = String(alpha);
      lidar.setAttribute('transform', `translate(${fmt(sensor[0])} ${fmt(sensor[1])})`);
      if (lidarPulse) {
        const radius = lerp(3.5, 27, sweep);
        lidarPulse.setAttribute('d', `M 0 ${fmt(-radius)} A ${fmt(radius)} ${fmt(radius)} 0 1 1 0 ${fmt(radius)} A ${fmt(radius)} ${fmt(radius)} 0 1 1 0 ${fmt(-radius)}`);
        lidarPulse.style.opacity = String(alpha * (1 - 0.72 * sweep));
      }
      if (lidarRays) {
        lidarRays.setAttribute('transform', `rotate(${fmt(lerp(-35, 55, sweep))})`);
        lidarRays.style.opacity = String(alpha * 0.82);
      }
      if (lidarReturn) {
        const flash = Math.exp(-Math.pow((sweep - 0.72) / 0.085, 2));
        lidarReturn.style.opacity = String(flash);
        lidarReturn.setAttribute('r', fmt(lerp(2.0, 5.0, flash)));
      }
    }

    function contactPosition(perch, scale, mirror, rotationDeg, localContact, offset = [0, 0]) {
      const sx = mirror ? -scale : scale;
      const local = [
        (localContact[0] - anchor[0]) * sx,
        (localContact[1] - anchor[1]) * scale,
      ];
      const angle = rotationDeg * RAD;
      const rotated = [
        local[0] * Math.cos(angle) - local[1] * Math.sin(angle),
        local[0] * Math.sin(angle) + local[1] * Math.cos(angle),
      ];
      return [perch[0] + offset[0] - rotated[0], perch[1] + offset[1] - rotated[1]];
    }

    function place(position, tangent, scale, mirror, opacity, rotationOverride = null) {
      const angle = Math.atan2(tangent[1], tangent[0]) / RAD;
      const pathRotation = mirror ? angle - 180 : angle;
      const rotation = Number.isFinite(rotationOverride) ? rotationOverride : pathRotation;
      const sx = mirror ? -scale : scale;
      flightGroup.setAttribute(
        'transform',
        `translate(${fmt(position[0])} ${fmt(position[1])}) rotate(${fmt(rotation)}) scale(${fmt(sx)} ${fmt(scale)}) translate(${-anchor[0]} ${-anchor[1]})`
      );
      flightGroup.style.opacity = String(opacity);
    }

    return { model, setWingPose, setLegPose, setLidar, contactPosition, place };
  }

  function initPercoliaDirectionalScene(options) {
    const stage = options.stage;
    const perched = options.perched;
    const outboundGroup = options.outboundGroup;
    const inboundGroup = options.inboundGroup;
    const library = readClipLibrary(options, stage);
    const outbound = createBirdController(outboundGroup.querySelector('svg'), outboundGroup);
    const inbound = createBirdController(inboundGroup.querySelector('svg'), inboundGroup);
    const model = outbound.model;
    const flight = model.flight;
    const perch = flight.perch;
    const reducedMotion = global.matchMedia && global.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const timeline = library.timeline;
    const boundaries = [];
    let total = 0;
    timeline.forEach((entry) => {
      boundaries.push(Object.assign({}, entry, { start: total, end: total + entry.duration_ms }));
      total += entry.duration_ms;
    });

    let start = performance.now();
    let elapsedBeforePause = 0;
    let running = false;
    let raf = 0;
    let finished = false;
    let lastState = '';
    let previousTime = 0;

    function setState(name) {
      if (name === lastState) return;
      lastState = name;
      if (typeof options.onState === 'function') options.onState(name);
    }

    function segmentAt(time) {
      return boundaries.find((entry) => time < entry.end) || boundaries[boundaries.length - 1];
    }

    function progressIn(entry, time) {
      return clamp((time - entry.start) / entry.duration_ms, 0, 1);
    }

    function clipProgress(entry, time) {
      if (!entry.clip) return 0;
      if (entry.loop) {
        const clipPeriod = entry.state === 'perched' || entry.state === 'perched_final'
          ? entry.duration_ms
          : model.wing.period_ms;
        return ((time - entry.start) / clipPeriod) % 1;
      }
      return progressIn(entry, time);
    }

    function emitEvents(from, to) {
      if (to < from) return;
      boundaries.forEach((entry) => {
        if (!entry.clip) return;
        const clip = library.clips[entry.clip];
        (clip.events || []).forEach((event) => {
          const eventTimeMs = entry.start + event.t * entry.duration_ms;
          if (eventTimeMs > from && eventTimeMs <= to && typeof options.onEvent === 'function') {
            options.onEvent(event.name, entry.state);
          }
        });
      });
    }

    function visualRotation(tangent, mirror, minimum, maximum) {
      const angle = Math.atan2(tangent[1], tangent[0]) / RAD;
      const rotation = mirror ? angle - 180 : angle;
      return clamp(rotation, minimum, maximum);
    }

    function applyContactPose(controller, sample, baseScale, mirror, opacity = 1, rotationOverride = null) {
      controller.setWingPose(sample.wing);
      const legState = controller.setLegPose(sample.legs);
      const scale = baseScale * sample.root[3];
      const rotation = Number.isFinite(rotationOverride) ? rotationOverride : sample.root[2];
      const position = controller.contactPosition(perch, scale, mirror, rotation, legState.contactLocal);
      controller.place(position, mirror ? [-1, 0] : [1, 0], scale, mirror, opacity, rotation);
      return { position, scale, rotation, legState };
    }

    function pushReleasePose() {
      const toe = eventTime(library, 'push_off', 'toe_off');
      const sample = sampleClip(library, 'push_off', toe);
      outbound.setWingPose(sample.wing);
      const legState = outbound.setLegPose(sample.legs);
      const scale = flight.perched_scale * sample.root[3];
      const rotation = sample.root[2];
      const position = outbound.contactPosition(perch, scale, false, rotation, legState.contactLocal);
      return { sample, position, scale, rotation };
    }

    function pushEndPose() {
      const release = pushReleasePose();
      const end = sampleClip(library, 'push_off', 1);
      return {
        position: add(release.position, [end.root[0] - release.sample.root[0], end.root[1] - release.sample.root[1]]),
        rotation: end.root[2],
        scale: flight.perched_scale * end.root[3],
      };
    }

    function renderPerchedActor(controller, sample, mirror) {
      applyContactPose(controller, sample, flight.perched_scale, mirror, 1);
    }

    function update(time) {
      const boundedTime = clamp(time, 0, total);
      const entry = segmentAt(boundedTime);
      const p = progressIn(entry, boundedTime);
      const cp = clipProgress(entry, boundedTime);
      const sample = entry.clip ? sampleClip(library, entry.clip, cp) : null;

      outboundGroup.style.opacity = '0';
      inboundGroup.style.opacity = '0';
      perched.style.opacity = reducedMotion ? '1' : '0';
      outbound.setLidar(0, 0);
      inbound.setLidar(0, 0);
      setState(entry.state);

      if (reducedMotion) {
        perched.style.opacity = '1';
        return;
      }

      switch (entry.state) {
        case 'perched':
          renderPerchedActor(outbound, sample, false);
          break;

        case 'anticipation':
          applyContactPose(outbound, sample, flight.perched_scale, false, 1);
          break;

        case 'push_off': {
          outbound.setWingPose(sample.wing);
          const legState = outbound.setLegPose(sample.legs);
          const scale = flight.perched_scale * sample.root[3];
          const rotation = sample.root[2];
          const toe = eventTime(library, 'push_off', 'toe_off');
          let position;
          if (p <= toe) {
            position = outbound.contactPosition(perch, scale, false, rotation, legState.contactLocal);
          } else {
            const release = pushReleasePose();
            position = add(release.position, [sample.root[0] - release.sample.root[0], sample.root[1] - release.sample.root[1]]);
          }
          outbound.place(position, [1, -0.25], scale, false, 1, rotation);
          break;
        }

        case 'takeoff': {
          const origin = pushEndPose();
          const first = library.clips.takeoff.keyframes[0].root;
          let position = add(origin.position, [sample.root[0] - first[0], sample.root[1] - first[1]]);
          const target = library.world.outbound_curve[0];
          const endSample = sampleClip(library, 'takeoff', 1);
          const authoredEnd = add(origin.position, [endSample.root[0] - first[0], endSample.root[1] - first[1]]);
          const warp = sub(target, authoredEnd);
          position = add(position, mul(warp, smoothstep(0.55, 1, p)));
          outbound.setWingPose(sample.wing);
          outbound.setLegPose(sample.legs);
          const scale = lerp(flight.perched_scale, flight.bird_scale, smoothstep(0, 0.55, p)) * sample.root[3];
          outbound.place(position, [1, -0.35], scale, false, 1, sample.root[2]);
          break;
        }

        case 'outbound': {
          const positionBase = cubic(library.world.outbound_curve, p);
          const tangent = cubicDerivative(library.world.outbound_curve, Math.min(0.999, p));
          const position = add(positionBase, [sample.root[0], sample.root[1]]);
          outbound.setWingPose(sample.wing);
          outbound.setLegPose(sample.legs);
          const fade = 1 - smoothstep(0.93, 1, p);
          const rotation = visualRotation(tangent, false, -22, 7) + sample.root[2] * 0.28;
          outbound.place(position, tangent, flight.bird_scale * sample.root[3], false, fade, rotation);
          const scanHalf = library.world.scan_duration_fraction / 2;
          const scanDistance = Math.abs(p - library.world.scan_progress);
          const scanStrength = 1 - clamp(scanDistance / scanHalf, 0, 1);
          const scanSweep = clamp((p - (library.world.scan_progress - scanHalf)) / (2 * scanHalf), 0, 1);
          outbound.setLidar(scanStrength, scanSweep);
          break;
        }

        case 'empty':
          break;

        case 'inbound': {
          const positionBase = cubic(library.world.inbound_curve, p);
          const tangent = cubicDerivative(library.world.inbound_curve, Math.min(0.999, p));
          const position = add(positionBase, [-sample.root[0], sample.root[1]]);
          inbound.setWingPose(sample.wing);
          inbound.setLegPose(sample.legs);
          const rotation = visualRotation(tangent, true, -12, 5) - sample.root[2] * 0.22;
          inbound.place(position, tangent, flight.bird_scale * sample.root[3], true, smoothstep(0, 0.08, p), rotation);
          break;
        }

        case 'approach':
        case 'flare': {
          const world = add(perch, [sample.root[0], sample.root[1]]);
          inbound.setWingPose(sample.wing);
          inbound.setLegPose(sample.legs);
          inbound.place(world, [-1, 0.22], flight.bird_scale * sample.root[3], true, 1, sample.root[2]);
          break;
        }

        case 'touchdown': {
          inbound.setWingPose(sample.wing);
          const legState = inbound.setLegPose(sample.legs);
          const scale = flight.bird_scale * sample.root[3];
          const rotation = sample.root[2];
          const touchdown = eventTime(library, 'touchdown', 'touchdown');
          const authored = add(perch, [sample.root[0], sample.root[1]]);

          if (p < touchdown) {
            const eventSample = sampleClip(library, 'touchdown', touchdown);
            inbound.setWingPose(eventSample.wing);
            const eventLeg = inbound.setLegPose(eventSample.legs);
            const eventScale = flight.bird_scale * eventSample.root[3];
            const target = inbound.contactPosition(perch, eventScale, true, eventSample.root[2], eventLeg.contactLocal);
            const authoredAtEvent = add(perch, [eventSample.root[0], eventSample.root[1]]);
            const warp = sub(target, authoredAtEvent);
            const position = add(authored, mul(warp, smoothstep(0.10, touchdown, p)));
            // Restore the actual frame after computing the target pose.
            inbound.setWingPose(sample.wing);
            inbound.setLegPose(sample.legs);
            inbound.place(position, [-1, 0.30], scale, true, 1, rotation);
          } else {
            const position = inbound.contactPosition(perch, scale, true, rotation, legState.contactLocal);
            inbound.place(position, [-1, 0], scale, true, 1, rotation);
          }
          break;
        }

        case 'settle':
          applyContactPose(inbound, sample, flight.bird_scale, true, 1);
          break;

        case 'perched_final':
          applyContactPose(inbound, sample, flight.perched_scale, true, 1);
          break;

        default:
          throw new Error(`Unknown Percolia animation state: ${entry.state}`);
      }

      emitEvents(previousTime, boundedTime);
      previousTime = boundedTime;
      if (boundedTime >= total && !finished) {
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
      previousTime = 0;
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
      previousTime = elapsedBeforePause;
      update(elapsedBeforePause);
    }

    update(0);
    if (!reducedMotion && options.autoplay !== false) play();

    return {
      play,
      pause,
      restart,
      seek,
      duration: total,
      isRunning: () => running,
      state: () => lastState,
    };
  }

  global.initPercoliaDirectionalScene = initPercoliaDirectionalScene;
})(window);
