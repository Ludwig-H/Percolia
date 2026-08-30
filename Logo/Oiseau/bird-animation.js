/**
 * Percolia network-bird animation — framework neutral, dependency free.
 *
 * The SVG must be inline in the DOM and contain [data-percolia-bird].
 * Every animation is disabled when prefers-reduced-motion is enabled.
 */
export function initPercoliaBird(target, options = {}) {
  const svg = typeof target === "string" ? document.querySelector(target) : target;
  if (!(svg instanceof SVGElement)) {
    throw new TypeError("initPercoliaBird: target must resolve to an inline SVG element");
  }

  const root = svg.matches("[data-percolia-bird]")
    ? svg
    : svg.querySelector("[data-percolia-bird]");
  if (!root) {
    throw new Error("initPercoliaBird: [data-percolia-bird] group not found");
  }

  const settings = {
    revealDuration: 1450,
    phaseDelay: 110,
    pulseEvery: 4200,
    parallax: true,
    autoplay: true,
    ...options,
  };

  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const edges = [...root.querySelectorAll('[data-anim="edge"]')];
  const faces = [...root.querySelectorAll('[data-anim="face"]')];
  const nodes = [...root.querySelectorAll('[data-anim="node"]')];
  const scatter = root.querySelector('[data-layer="scatter"]');
  const critical = [...root.querySelectorAll('[data-kind="critical"]')];
  let pulseTimer = 0;
  let destroyed = false;

  const phase = (el) => Number(el.dataset.phase || 0);
  const maxPhase = Math.max(0, ...edges.map(phase), ...faces.map(phase));

  function prepare() {
    svg.classList.add("percolia-bird--enhanced");
    for (const edge of edges) {
      const length = Math.max(1, edge.getTotalLength());
      edge.style.setProperty("--edge-length", `${length}`);
      edge.style.strokeDasharray = `${length}`;
      edge.style.strokeDashoffset = `${length}`;
    }
    for (const face of faces) face.style.opacity = "0";
    for (const node of nodes) {
      node.style.opacity = "0";
      node.style.transformBox = "fill-box";
      node.style.transformOrigin = "center";
      node.style.transform = "scale(0.2)";
    }
  }

  function showStatic() {
    for (const edge of edges) edge.style.strokeDashoffset = "0";
    for (const face of faces) face.style.opacity = "1";
    for (const node of nodes) {
      node.style.opacity = "1";
      node.style.transform = "scale(1)";
    }
  }

  function reveal() {
    if (destroyed) return Promise.resolve();
    if (reduceMotion) {
      showStatic();
      return Promise.resolve();
    }

    const animations = [];
    for (const edge of edges) {
      const delay = phase(edge) * settings.phaseDelay;
      animations.push(edge.animate(
        [{ strokeDashoffset: edge.style.strokeDashoffset }, { strokeDashoffset: 0 }],
        { duration: settings.revealDuration * 0.58, delay, easing: "cubic-bezier(.2,.75,.25,1)", fill: "forwards" }
      ).finished.catch(() => undefined));
    }
    for (const face of faces) {
      const delay = phase(face) * settings.phaseDelay + 130;
      animations.push(face.animate(
        [{ opacity: 0 }, { opacity: 1 }],
        { duration: 520, delay, easing: "ease-out", fill: "forwards" }
      ).finished.catch(() => undefined));
    }
    nodes.forEach((node, index) => {
      const delay = 90 + (index / Math.max(1, nodes.length)) * settings.revealDuration * 0.78;
      animations.push(node.animate(
        [{ opacity: 0, transform: "scale(.2)" }, { opacity: 1, transform: "scale(1.12)" }, { opacity: 1, transform: "scale(1)" }],
        { duration: 380, delay, easing: "cubic-bezier(.2,.8,.25,1)", fill: "forwards" }
      ).finished.catch(() => undefined));
    });
    if (scatter) {
      animations.push(scatter.animate(
        [{ opacity: 0, transform: "translateX(-9px)" }, { opacity: 0.58, transform: "translateX(0)" }],
        { duration: 900, easing: "ease-out", fill: "forwards" }
      ).finished.catch(() => undefined));
    }
    return Promise.all(animations);
  }

  function pulse() {
    if (destroyed || reduceMotion) return;
    critical.forEach((element, index) => {
      const isCircle = element.tagName.toLowerCase() === "circle";
      element.animate(
        isCircle
          ? [{ transform: "scale(1)" }, { transform: "scale(1.42)" }, { transform: "scale(1)" }]
          : [{ opacity: 1 }, { opacity: 0.42 }, { opacity: 1 }],
        { duration: 720, delay: index * 34, easing: "ease-in-out" }
      );
    });
  }

  function onPointerMove(event) {
    if (!settings.parallax || reduceMotion || !scatter) return;
    const rect = svg.getBoundingClientRect();
    const dx = ((event.clientX - rect.left) / rect.width - 0.5) * 5;
    const dy = ((event.clientY - rect.top) / rect.height - 0.5) * 4;
    scatter.style.transform = `translate(${dx}px, ${dy}px)`;
  }

  function onPointerLeave() {
    if (scatter) scatter.style.transform = "translate(0, 0)";
  }

  prepare();
  if (settings.autoplay) {
    reveal().then(() => {
      if (!reduceMotion && !destroyed) {
        pulseTimer = window.setInterval(pulse, Math.max(settings.pulseEvery, 3000));
      }
    });
  } else if (reduceMotion) {
    showStatic();
  }

  svg.addEventListener("pointermove", onPointerMove, { passive: true });
  svg.addEventListener("pointerleave", onPointerLeave, { passive: true });

  return {
    reveal,
    pulse,
    destroy() {
      destroyed = true;
      window.clearInterval(pulseTimer);
      svg.removeEventListener("pointermove", onPointerMove);
      svg.removeEventListener("pointerleave", onPointerLeave);
      svg.getAnimations({ subtree: true }).forEach((animation) => animation.cancel());
    },
    maxPhase,
  };
}
