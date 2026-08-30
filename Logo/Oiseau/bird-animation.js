/**
 * Articulated Percolia network bird.
 *
 * No framework and no external dependency. The bird is a real 2-D rig:
 * shoulder -> elbow -> wrist for each wing, plus independent head, tail and
 * legs. The flight follows a closed Bézier trajectory, takes off from the P,
 * scans once, then lands on the same perch.
 */
(function (global) {
  'use strict';

  const TAU = Math.PI * 2;
  const clamp = (value, min, max) => Math.min(max, Math.max(min, value));
  const lerp = (a, b, t) => a + (b - a) * t;
  const smoothstep = (a, b, x) => {
    const t = clamp((x - a) / (b - a), 0, 1);
    return t * t * (3 - 2 * t);
  };
  const easeOutCubic = (t) => 1 - Math.pow(1 - t, 3);
  const easeInOutSine = (t) => -(Math.cos(Math.PI * t) - 1) / 2;

  function parsePair(value, fallback) {
    if (!value) return fallback;
    const parts = value.split(',').map(Number);
    return parts.length === 2 && parts.every(Number.isFinite) ? parts : fallback;
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
    if (!(svg instanceof SVGElement)) {
      throw new TypeError('initPercoliaBird: an inline SVG element is required');
    }

    const root = svg.matches('[data-percolia-bird]') ? svg : svg.querySelector('[data-percolia-bird]');
    if (!root) throw new Error('initPercoliaBird: [data-percolia-bird] not found');

    const settings = Object.assign({
      autoplay: true,
      loop: true,
      flightDuration: 7600,
      perchDuration: 2100,
      revealDuration: 1250,
      birdElement: svg.closest('[data-flight-bird]'),
      stageElement: svg.closest('[data-flight-stage]'),
      perchElement: null,
      onState: null,
    }, options);

    const reducedMotion = global.matchMedia && global.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const q = (selector) => root.querySelector(selector);
    const qa = (selector) => [...root.querySelectorAll(selector)];

    const bones = {
      nearUpper: q('[data-bone="wing-near-upper"]'),
      nearForearm: q('[data-bone="wing-near-forearm"]'),
      nearHand: q('[data-bone="wing-near-hand"]'),
      farUpper: q('[data-bone="wing-far-upper"]'),
      farForearm: q('[data-bone="wing-far-forearm"]'),
      farHand: q('[data-bone="wing-far-hand"]'),
      nearWing: q('#wing-near'),
      farWing: q('#wing-far'),
      foldedWing: q('[data-bone="folded-wing"]'),
      body: q('[data-bone="body"]'),
      head: q('[data-bone="head"]'),
      tail: q('[data-bone="tail"]'),
      nearLeg: q('[data-bone="leg-near"]'),
      farLeg: q('[data-bone="leg-far"]'),
      lidar: q('#lidar-scan'),
      lidarSweep: q('[data-bone="lidar-sweep"]'),
      lidarReturn: q('#lidar-return'),
      lidarRing: q('#lidar-ring'),
    };

    const edges = qa('[data-anim="edge"]');
    const faces = qa('[data-anim="face"]');
    const nodes = qa('[data-anim="node"]');
    const critical = qa('[data-kind="critical"]');
    const scatter = q('[data-layer="scatter"]');

    const elbow = parsePair(root.dataset.elbow, [-35, -16]);
    const wrist = parsePair(root.dataset.wrist, [-34, 7]);
    const hipNear = parsePair(root.dataset.hipNear, [-13, 18]);
    const hipFar = parsePair(root.dataset.hipFar, [-1, 18]);

    let raf = 0;
    let pulseTimer = 0;
    let startTime = 0;
    let pausedAt = 0;
    let destroyed = false;
    let running = false;
    let manualScanStart = -Infinity;
    let lastState = '';

    function setState(state) {
      if (state === lastState) return;
      lastState = state;
      root.dataset.flightState = state;
      if (settings.birdElement) settings.birdElement.dataset.flightState = state;
      if (typeof settings.onState === 'function') settings.onState(state);
    }

    function wingAngles(phase) {
      // Downstroke is deliberately shorter and stronger than the recovery
      // stroke. Folding the wrist during the upstroke avoids the mechanical
      // windscreen-wiper look of the old prototype.
      if (phase < 0.43) {
        const t = easeOutCubic(phase / 0.43);
        return {
          upper: lerp(-53, 36, t),
          forearm: lerp(-22, 15, t),
          hand: lerp(20, -8, t),
        };
      }
      const t = easeInOutSine((phase - 0.43) / 0.57);
      return {
        upper: lerp(36, -53, t),
        forearm: lerp(15, -34, t),
        hand: lerp(-8, 24, t),
      };
    }

    function setWing(side, angles) {
      const upper = side === 'near' ? bones.nearUpper : bones.farUpper;
      const forearm = side === 'near' ? bones.nearForearm : bones.farForearm;
      const hand = side === 'near' ? bones.nearHand : bones.farHand;
      if (upper) upper.setAttribute('transform', `rotate(${angles.upper.toFixed(3)})`);
      if (forearm) forearm.setAttribute('transform', `translate(${elbow[0]} ${elbow[1]}) rotate(${angles.forearm.toFixed(3)})`);
      if (hand) hand.setAttribute('transform', `translate(${wrist[0]} ${wrist[1]}) rotate(${angles.hand.toFixed(3)})`);
    }

    function foldedPose() {
      return { upper: -54, forearm: 188, hand: -144 };
    }

    function blendPose(a, b, t) {
      return {
        upper: lerp(a.upper, b.upper, t),
        forearm: lerp(a.forearm, b.forearm, t),
        hand: lerp(a.hand, b.hand, t),
      };
    }

    function setWingVisibility(open) {
      const t = clamp(open, 0, 1);
      if (bones.foldedWing) bones.foldedWing.style.opacity = String(1 - t);
      if (bones.nearWing) bones.nearWing.style.opacity = String(0.92 * t);
      if (bones.farWing) bones.farWing.style.opacity = String(0.38 * t);
    }

    function setLegs(retraction) {
      const t = clamp(retraction, 0, 1);
      const nearAngle = lerp(0, -58, t);
      const farAngle = lerp(0, -52, t);
      if (bones.nearLeg) {
        bones.nearLeg.setAttribute('transform', `rotate(${nearAngle.toFixed(2)} ${hipNear[0]} ${hipNear[1]})`);
        bones.nearLeg.style.opacity = String(lerp(0.88, 0.38, t));
      }
      if (bones.farLeg) {
        bones.farLeg.setAttribute('transform', `rotate(${farAngle.toFixed(2)} ${hipFar[0]} ${hipFar[1]})`);
        bones.farLeg.style.opacity = String(lerp(0.46, 0.18, t));
      }
    }

    function setBodyPose(pitch, flapPhase, turn) {
      const bob = Math.sin(TAU * flapPhase) * 1.3;
      if (bones.body) bones.body.setAttribute('transform', `translate(0 ${bob.toFixed(2)}) rotate(${pitch.toFixed(2)} -5 2)`);
      if (bones.head) bones.head.setAttribute('transform', `rotate(${(-pitch * 0.42 + turn * 2.2).toFixed(2)} 35 -8)`);
      if (bones.tail) bones.tail.setAttribute('transform', `rotate(${(-pitch * 0.35 - turn * 7).toFixed(2)} -44 6)`);
    }

    function reveal() {
      if (reducedMotion) {
        edges.forEach((edge) => { edge.style.strokeDasharray = ''; edge.style.strokeDashoffset = '0'; });
        faces.forEach((face) => { face.style.opacity = ''; });
        nodes.forEach((node) => { node.style.opacity = ''; node.style.transform = ''; });
        if (scatter) scatter.style.opacity = '';
        return Promise.resolve();
      }
      const promises = [];
      edges.forEach((edge) => {
        const length = Math.max(1, edge.getTotalLength());
        edge.style.strokeDasharray = `${length}`;
        edge.style.strokeDashoffset = `${length}`;
        const delay = Number(edge.dataset.phase || 0) * 65;
        promises.push(edge.animate(
          [{ strokeDashoffset: length }, { strokeDashoffset: 0 }],
          { duration: settings.revealDuration * 0.62, delay, easing: 'cubic-bezier(.2,.75,.25,1)', fill: 'forwards' }
        ).finished.catch(() => undefined));
      });
      faces.forEach((face) => {
        const finalOpacity = getComputedStyle(face).opacity;
        const delay = Number(face.dataset.phase || 0) * 65 + 110;
        promises.push(face.animate(
          [{ opacity: 0 }, { opacity: finalOpacity }],
          { duration: 480, delay, easing: 'ease-out', fill: 'forwards' }
        ).finished.catch(() => undefined));
      });
      nodes.forEach((node, index) => {
        node.style.transformBox = 'fill-box';
        node.style.transformOrigin = 'center';
        promises.push(node.animate(
          [{ opacity: 0, transform: 'scale(.25)' }, { opacity: 1, transform: 'scale(1.12)' }, { opacity: 1, transform: 'scale(1)' }],
          { duration: 320, delay: 60 + index * 10, easing: 'cubic-bezier(.2,.8,.25,1)', fill: 'forwards' }
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
            ? [{ transform: 'scale(1)' }, { transform: 'scale(1.34)' }, { transform: 'scale(1)' }]
            : [{ opacity: 1 }, { opacity: 0.35 }, { opacity: 1 }],
          { duration: 650, delay: index * 28, easing: 'ease-in-out' }
        );
      });
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
        stageRect,
        start,
        segments: [
          [start, { x: start.x + w * .02, y: start.y - h * .28 }, { x: w * .20, y: h * .20 }, { x: w * .36, y: h * .24 }],
          [{ x: w * .36, y: h * .24 }, { x: w * .52, y: h * .05 }, { x: w * .77, y: h * .10 }, { x: w * .84, y: h * .32 }],
          [{ x: w * .84, y: h * .32 }, { x: w * .89, y: h * .56 }, { x: w * .58, y: h * .59 }, { x: w * .39, y: h * .34 }],
          [{ x: w * .39, y: h * .34 }, { x: w * .24, y: h * .15 }, { x: start.x + w * .10, y: start.y - h * .22 }, start],
        ],
      };
    }

    function pathPoint(progress) {
      const geo = pathGeometry();
      if (!geo) return null;
      const scaled = clamp(progress, 0, 0.999999) * geo.segments.length;
      const index = Math.min(geo.segments.length - 1, Math.floor(scaled));
      const local = scaled - index;
      const [a, b, c, d] = geo.segments[index];
      const point = cubic(a, b, c, d, local);
      const derivative = cubicDerivative(a, b, c, d, local);
      return { point, derivative, start: geo.start };
    }

    function updateScan(flightProgress, now) {
      if (!bones.lidar) return;
      const auto = 1 - Math.min(1, Math.abs(flightProgress - 0.47) / 0.055);
      const manualElapsed = now - manualScanStart;
      const manual = manualElapsed >= 0 && manualElapsed < 1000
        ? Math.sin(Math.PI * manualElapsed / 1000)
        : 0;
      const strength = clamp(Math.max(auto, manual), 0, 1);
      bones.lidar.style.opacity = String(smoothstep(0.06, 0.5, strength));
      if (strength <= 0) return;
      const sweepPhase = manual > auto ? manualElapsed / 1000 : clamp((flightProgress - 0.415) / 0.11, 0, 1);
      if (bones.lidarSweep) bones.lidarSweep.setAttribute('transform', `rotate(${lerp(-16, 18, sweepPhase).toFixed(2)})`);
      const flash = Math.exp(-Math.pow((sweepPhase - 0.72) / 0.08, 2));
      if (bones.lidarReturn) {
        bones.lidarReturn.style.opacity = String(flash);
        bones.lidarReturn.setAttribute('r', String(lerp(1.5, 4.2, flash)));
      }
      if (bones.lidarRing) {
        const ringPhase = clamp((sweepPhase - 0.70) / 0.30, 0, 1);
        bones.lidarRing.style.opacity = String((1 - ringPhase) * (ringPhase > 0 ? 0.8 : 0));
        bones.lidarRing.setAttribute('r', String(3 + ringPhase * 14));
      }
    }

    function setPerched(now) {
      setState('perched');
      setWingVisibility(0);
      setWing('near', foldedPose());
      setWing('far', foldedPose());
      setLegs(0);
      const breathe = Math.sin(now / 700) * 0.45;
      if (bones.body) bones.body.setAttribute('transform', `translate(0 ${breathe.toFixed(2)})`);
      if (bones.head) bones.head.setAttribute('transform', `rotate(${(Math.sin(now / 1200) * 1.4).toFixed(2)} 35 -8)`);
      if (bones.tail) bones.tail.setAttribute('transform', `rotate(${(Math.sin(now / 900) * 1.1).toFixed(2)} -44 6)`);
      if (settings.birdElement && settings.perchElement && settings.stageElement) {
        const geo = pathGeometry();
        if (geo) {
          settings.birdElement.style.transform = `translate3d(${geo.start.x}px, ${geo.start.y}px, 0) translate(-43%, -82%) rotate(0deg)`;
        }
      }
      updateScan(-10, now);
    }

    function setFlight(progress, now) {
      const sample = pathPoint(progress);
      if (!sample) return;
      const { point, derivative } = sample;
      const pathAngle = Math.atan2(derivative.y, derivative.x) * 180 / Math.PI;
      const angle = clamp(pathAngle, -24, 24);
      const lift = smoothstep(0, 0.09, progress);
      const landing = smoothstep(0.88, 1, progress);
      const open = lift * (1 - landing);
      const retraction = smoothstep(0.035, 0.14, progress) * (1 - smoothstep(0.82, 0.97, progress));
      const flapHz = lerp(5.0, 4.15, smoothstep(0.12, 0.35, progress));
      const flapPhase = ((now / 1000) * flapHz) % 1;
      const active = wingAngles(flapPhase);
      const folded = foldedPose();
      setWingVisibility(open);
      setWing('near', blendPose(folded, active, open));
      const farActive = wingAngles((flapPhase + 0.025) % 1);
      setWing('far', blendPose(folded, farActive, open));
      setLegs(retraction);
      const turn = clamp(derivative.y / Math.max(40, Math.abs(derivative.x)), -1, 1);
      setBodyPose(angle * 0.22, flapPhase, turn);

      if (settings.birdElement) {
        const anchorY = lerp(82, 52, smoothstep(0.01, 0.12, progress) * (1 - smoothstep(0.86, 0.99, progress)));
        const landingScale = 1 - Math.sin(Math.PI * clamp((progress - 0.86) / 0.14, 0, 1)) * 0.035;
        settings.birdElement.style.transform = `translate3d(${point.x}px, ${point.y}px, 0) translate(-43%, -${anchorY}%) rotate(${angle.toFixed(2)}deg) scale(${landingScale.toFixed(3)})`;
      }
      updateScan(progress, now);
      if (progress < 0.10) setState('takeoff');
      else if (progress > 0.88) setState('landing');
      else setState('flight');
    }

    function frame(now) {
      if (!running || destroyed) return;
      if (!startTime) startTime = now;
      const travel = settings.flightDuration;
      const cycle = settings.perchDuration + travel;
      const elapsed = now - startTime;
      const local = settings.loop ? elapsed % cycle : Math.min(elapsed, cycle);
      if (local < settings.perchDuration || reducedMotion) {
        setPerched(now);
      } else {
        const progress = clamp((local - settings.perchDuration) / travel, 0, 1);
        setFlight(progress, now);
      }
      if (!settings.loop && local >= cycle) {
        pause();
        setPerched(now);
        return;
      }
      raf = global.requestAnimationFrame(frame);
    }

    function play() {
      if (destroyed || running) return;
      running = true;
      if (pausedAt) {
        startTime += performance.now() - pausedAt;
        pausedAt = 0;
      }
      raf = global.requestAnimationFrame(frame);
    }

    function pause() {
      if (!running) return;
      running = false;
      pausedAt = performance.now();
      global.cancelAnimationFrame(raf);
    }

    function replay() {
      startTime = performance.now() - settings.perchDuration + 30;
      pausedAt = 0;
      if (!running) play();
    }

    function scan() {
      manualScanStart = performance.now();
    }

    function destroy() {
      destroyed = true;
      pause();
      global.clearInterval(pulseTimer);
      if (svg.getAnimations) svg.getAnimations({ subtree: true }).forEach((animation) => animation.cancel());
    }

    setWingVisibility(0);
    setWing('near', foldedPose());
    setWing('far', foldedPose());
    setLegs(0);
    reveal().then(() => {
      if (!destroyed) {
        pulseTimer = global.setInterval(pulse, 5200);
        if (settings.autoplay) play();
        else setPerched(performance.now());
      }
    });

    return { play, pause, replay, scan, pulse, destroy, reveal };
  }

  global.PercoliaBird = Object.freeze({ init: initPercoliaBird });
})(window);
