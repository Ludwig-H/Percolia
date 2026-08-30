#!/usr/bin/env python3
"""Build the self-contained directional flight demonstration."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LOGO_ROOT = ROOT.parent


def inline_svg(path: Path, width: int, height: int, extra_class: str = "") -> str:
    text = path.read_text(encoding="utf-8")
    text = re.sub(r'<\?xml[^>]*>\s*', '', text)
    return text.replace(
        '<svg ',
        f'<svg width="{width}" height="{height}" overflow="visible" class="{extra_class}" ',
        1,
    )


def extract_group(path: Path, group_id: str) -> tuple[str, str]:
    text = path.read_text(encoding="utf-8")
    styles = "\n".join(re.findall(r'<style>(.*?)</style>', text, flags=re.S))
    match = re.search(rf'(<g id="{re.escape(group_id)}".*?</g>)\s*</svg>', text, flags=re.S)
    if not match:
        raise ValueError(f"{group_id!r} not found in {path}")
    return styles, match.group(1)


def main() -> None:
    model = json.loads((ROOT / "source" / "bird_model.json").read_text(encoding="utf-8"))
    js = (ROOT / "bird-animation.js").read_text(encoding="utf-8")
    component_css = (ROOT / "bird-animation.css").read_text(encoding="utf-8")
    primary = inline_svg(ROOT / "percolia-bird-primary.svg", 640, 360, "network-bird-svg")
    compact = inline_svg(
        ROOT / "percolia-bird-compact.svg",
        520,
        292,
        "network-bird-svg network-bird-svg--compact",
    )
    word_style, wordmark = extract_group(
        LOGO_ROOT / "Police" / "percolia-wordmark-primary.svg",
        "percolia-wordmark",
    )
    perch_x, perch_y = model["flight"]["perch"]
    local_perch = tuple(model["flight"]["perched_anchor"])
    perched_scale = model["flight"]["perched_scale"]

    html = f'''<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Percolia — envol et atterrissage de l’oiseau-réseau</title>
<style>
:root {{ --ink:#082C4C; --blue:#1C83D4; --cyan:#20C9C4; --mist:#EAF5F7; --slate:#5D7385; --white:#FFFFFF; }}
* {{ box-sizing:border-box; }}
html,body {{ margin:0; min-height:100%; background:#F7FBFC; color:var(--ink); font-family:Inter,ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif; }}
body {{ background:radial-gradient(circle at 18% 15%,rgba(32,201,196,.07),transparent 28%),linear-gradient(180deg,#FBFDFE,#F2F8FA); }}
main {{ width:min(96vw,1440px); margin:0 auto; padding:28px 0 40px; }}
header {{ display:flex; align-items:flex-end; justify-content:space-between; gap:22px; flex-wrap:wrap; margin-bottom:18px; }}
.kicker {{ margin:0 0 7px; color:var(--slate); font-size:12px; font-weight:750; letter-spacing:.18em; text-transform:uppercase; }}
h1 {{ margin:0; font-size:clamp(2rem,4vw,4rem); line-height:1.02; letter-spacing:-.035em; }}
.lead {{ margin:10px 0 0; color:#355874; max-width:78ch; font-size:clamp(1rem,1.5vw,1.22rem); line-height:1.58; }}
.controls {{ display:flex; align-items:center; gap:10px; flex-wrap:wrap; }}
button {{ appearance:none; border:1px solid #C9D9E3; background:#fff; color:var(--ink); border-radius:999px; padding:.72rem 1rem; font:650 .92rem/1 Inter,ui-sans-serif,system-ui,sans-serif; cursor:pointer; }}
button:hover {{ border-color:var(--blue); }}
button.primary {{ background:var(--ink); color:#fff; border-color:var(--ink); }}
.status {{ min-width:116px; text-align:right; color:var(--slate); font-size:.8rem; letter-spacing:.12em; text-transform:uppercase; }}
.stage-shell {{ background:rgba(255,255,255,.94); border:1px solid #D9E7ED; border-radius:28px; box-shadow:0 20px 55px rgba(8,44,76,.08); overflow:hidden; }}
#flight-stage {{ display:block; width:100%; height:auto; }}
.info {{ display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:14px; margin-top:16px; }}
.card {{ background:rgba(255,255,255,.82); border:1px solid #DCE9EE; border-radius:18px; padding:18px 20px; }}
.card h2 {{ margin:0 0 7px; font-size:1rem; }}
.card p {{ margin:0; color:#49677D; line-height:1.55; font-size:.94rem; }}
code {{ font-family:ui-monospace,SFMono-Regular,Menlo,monospace; font-size:.9em; }}
footer {{ margin-top:16px; color:var(--slate); font-size:.83rem; text-align:right; }}
{component_css}
@media(max-width:860px) {{ .info {{ grid-template-columns:1fr; }} .status {{ text-align:left; }} }}
@media(prefers-reduced-motion:reduce) {{ .controls {{ display:none; }} }}
</style>
</head>
<body>
<main>
<header>
  <div>
    <p class="kicker">Percolia · direction 03 · cinématique v0.9</p>
    <h1>Un envol préparé, un posé amorti</h1>
    <p class="lead">Le premier oiseau se tasse, ouvre ses ailes, pousse sur le <strong>P</strong> puis part vers la droite. Il disparaît. Après un court silence, un autre arrive depuis la direction opposée, ralentit en arrondi, sort ses pattes, touche le perchoir et stabilise sa pose.</p>
  </div>
  <div class="controls" aria-label="Commandes de l’animation">
    <span id="status" class="status">PERCHÉ</span>
    <button id="pause" type="button">Pause</button>
    <button id="replay" class="primary" type="button">Rejouer</button>
  </div>
</header>

<section class="stage-shell">
<svg id="flight-stage" class="percolia-flight-stage" data-flight-stage="true" viewBox="0 0 1360 760" role="img" aria-labelledby="scene-title scene-desc">
  <title id="scene-title">Vol directionnel de deux oiseaux-réseaux Percolia</title>
  <desc id="scene-desc">Un oiseau se prépare, décolle vers la droite et quitte la scène. Un autre arrive de droite, effectue un arrondi et se pose sur le P.</desc>
  <defs>
    <linearGradient id="stage-wash" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#FFFFFF"/><stop offset="1" stop-color="#F4FAFC"/></linearGradient>
    <filter id="soft-shadow" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="5"/></filter>
  </defs>
  <rect width="1360" height="760" fill="url(#stage-wash)"/>
  <g opacity=".48" stroke="#E5EEF2" stroke-width="1">
    <path d="M0 120H1360M0 240H1360M0 360H1360M0 480H1360M0 600H1360"/>
    <path d="M120 0V760M240 0V760M360 0V760M480 0V760M600 0V760M720 0V760M840 0V760M960 0V760M1080 0V760M1200 0V760"/>
  </g>
  <g opacity=".54">
    <circle cx="124" cy="154" r="2.4" fill="#1C83D4"/><circle cx="205" cy="105" r="3" fill="#20C9C4"/>
    <circle cx="515" cy="116" r="2" fill="#082C4C"/><circle cx="747" cy="95" r="2.5" fill="#20C9C4"/>
    <circle cx="1050" cy="132" r="2.3" fill="#1C83D4"/><circle cx="1190" cy="265" r="3" fill="#20C9C4"/>
  </g>
  <g id="wordmark" transform="translate(140 500) scale(1)"><style>{word_style}</style>{wordmark}</g>
  <ellipse cx="{perch_x}" cy="{perch_y + 8}" rx="45" ry="9" fill="#082C4C" opacity=".07" filter="url(#soft-shadow)"/>
  <g id="perched-bird" data-perched-bird="true" transform="translate({perch_x} {perch_y}) scale({perched_scale}) translate({-local_perch[0]} {-local_perch[1]})">{compact}</g>
  <g id="outbound-bird" data-flight-bird="outbound" opacity="0">{primary}</g>
  <g id="inbound-bird" data-flight-bird="inbound" opacity="0">{primary}</g>
  <text x="1280" y="716" text-anchor="end" fill="#6E8798" font-size="14" letter-spacing="1.2">ANIMATION AUTONOME · AUCUNE RESSOURCE EXTERNE</text>
</svg>
</section>

<section class="info" aria-label="Principes de l’animation">
  <article class="card"><h2>Préparation et poussée</h2><p>L’oiseau se tasse, incline légèrement le corps, ouvre les ailes puis conserve le contact des pattes pendant le début du premier battement.</p></article>
  <article class="card"><h2>Arrondi d’approche</h2><p>L’oiseau entrant réduit progressivement son inclinaison, relève le bec, ouvre les ailes et déploie les pattes avant le contact.</p></article>
  <article class="card"><h2>Contact et stabilisation</h2><p>Le posé ne repose plus sur un fondu. Le second oiseau reste visible, amortit le contact puis replie ses ailes sur le perchoir.</p></article>
</section>
<footer>Source éditable : <code>Logo/Oiseau/source/bird_model.json</code></footer>

<script>{js}</script>
<script>
(() => {{
  const status = document.getElementById('status');
  const pause = document.getElementById('pause');
  const replay = document.getElementById('replay');
  const labels = {{
    perched:'PERCHÉ', preload:'PRÉPARATION', takeoff:'ENVOL', outbound:'SORTIE',
    empty:'HORS CHAMP', inbound:'APPROCHE', flare:'ARRONDI', touchdown:'CONTACT', settle:'STABILISATION'
  }};
  const controller = initPercoliaDirectionalScene({{
    stage: document.getElementById('flight-stage'),
    perched: document.getElementById('perched-bird'),
    outboundGroup: document.getElementById('outbound-bird'),
    inboundGroup: document.getElementById('inbound-bird'),
    autoplay: true,
    onState: (state) => {{ status.textContent = labels[state] || state.toUpperCase(); }},
    onFinish: () => {{ status.textContent = 'PERCHÉ'; pause.textContent = 'Pause'; }}
  }});
  window.percoliaDirectionalScene = controller;
  pause.addEventListener('click', () => {{
    if (controller.isRunning()) {{ controller.pause(); pause.textContent = 'Reprendre'; status.textContent = 'PAUSE'; }}
    else {{ controller.play(); pause.textContent = 'Pause'; status.textContent = 'VOL'; }}
  }});
  replay.addEventListener('click', () => {{ controller.restart(); pause.textContent = 'Pause'; status.textContent = 'VOL'; }});
  const params = new URLSearchParams(location.search);
  if (params.has('time')) {{
    const value = Number(params.get('time'));
    if (Number.isFinite(value)) {{ controller.seek(value); status.textContent = 'IMAGE TEST'; }}
  }}
}})();
</script>
</main>
</body>
</html>
'''
    (ROOT / "demo.html").write_text(html, encoding="utf-8")
    print("wrote demo.html")


if __name__ == "__main__":
    main()
