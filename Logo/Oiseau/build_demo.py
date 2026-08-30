#!/usr/bin/env python3
"""Build the single-file mathematical flight demonstration."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LOGO = ROOT.parent


def svg_body(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    text = re.sub(r"^<\?xml[^>]*>\s*", "", text)
    return text


def main() -> None:
    model = json.loads((ROOT / "source" / "bird_model.json").read_text(encoding="utf-8"))
    bird = svg_body(ROOT / "percolia-bird-compact.svg")
    wordmark = svg_body(LOGO / "Police" / "percolia-wordmark-primary.svg")
    animation_css = (ROOT / "bird-animation.css").read_text(encoding="utf-8")
    animation_js = (ROOT / "bird-animation.js").read_text(encoding="utf-8")
    period = model["wing"]["flight"]["period_ms"] / 1000
    html = f'''<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Percolia — vol paramétrique</title>
<style>
:root {{
  --ink:#082c4c; --blue:#1c83d4; --cyan:#20c9c4; --mist:#eaf5f7;
  --slate:#5d7385; --white:#fff; --radius:28px;
}}
* {{ box-sizing:border-box; }}
html,body {{ margin:0; background:linear-gradient(180deg,#f8fbfc,#eef6f8); color:var(--ink); font-family:Inter,ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif; }}
body {{ min-height:100vh; }}
main {{ width:min(1200px,calc(100vw - 32px)); margin:0 auto; padding:34px 0 52px; }}
header {{ display:flex; justify-content:space-between; gap:24px; align-items:flex-end; flex-wrap:wrap; margin-bottom:20px; }}
.kicker {{ margin:0 0 8px; color:var(--slate); text-transform:uppercase; letter-spacing:.18em; font-size:.78rem; font-weight:750; }}
h1 {{ margin:0; font-size:clamp(2.2rem,4vw,4.4rem); line-height:1.02; letter-spacing:-.03em; }}
.lede {{ max-width:72ch; margin:.9rem 0 0; color:#31566f; line-height:1.65; }}
.controls {{ display:flex; flex-wrap:wrap; gap:10px; align-items:center; }}
button {{ border:1px solid rgba(8,44,76,.18); border-radius:999px; padding:.74rem 1rem; background:white; color:var(--ink); font:inherit; font-weight:650; cursor:pointer; }}
button.primary {{ background:var(--ink); color:white; }}
.status {{ color:var(--slate); font-size:.82rem; letter-spacing:.14em; text-transform:uppercase; min-width:88px; text-align:right; }}
.stage {{ position:relative; height:min(66vw,690px); min-height:520px; overflow:hidden; border:1px solid #d9e8ec; border-radius:var(--radius); background:radial-gradient(circle at 20% 20%,rgba(32,201,196,.10),transparent 25%),linear-gradient(180deg,#fff,#f7fbfc); box-shadow:0 20px 60px rgba(8,44,76,.09); }}
.stage::before {{ content:""; position:absolute; inset:0; background-image:linear-gradient(rgba(8,44,76,.026) 1px,transparent 1px),linear-gradient(90deg,rgba(8,44,76,.026) 1px,transparent 1px); background-size:30px 30px; mask-image:linear-gradient(180deg,transparent,#000 18%,#000 82%,transparent); pointer-events:none; }}
.wordmark {{ position:absolute; left:50%; bottom:30px; width:min(92%,1030px); transform:translateX(-50%); }}
.wordmark svg {{ width:100%; height:auto; display:block; }}
.perch {{ position:absolute; left:12.7%; bottom:222px; width:4px; height:4px; border-radius:50%; opacity:0; }}
.flight-bird {{ position:absolute; left:12.7%; bottom:222px; width:176px; transform:translate(-50%,-100%); transform-origin:50% 100%; z-index:3; }}
.flight-bird svg {{ width:100%; height:auto; display:block; overflow:visible; filter:drop-shadow(0 10px 22px rgba(8,44,76,.09)); }}
.flight-bird[data-flight-state="perched"] {{ width:132px; }}
.grid {{ display:grid; grid-template-columns:repeat(12,1fr); gap:18px; margin-top:18px; }}
.card {{ grid-column:span 4; padding:22px; border:1px solid #d9e8ec; border-radius:22px; background:rgba(255,255,255,.92); box-shadow:0 10px 34px rgba(8,44,76,.055); }}
.card.wide {{ grid-column:span 8; }}
.card h2 {{ margin:.1rem 0 .8rem; font-size:1.15rem; }}
.card p {{ color:#31566f; line-height:1.62; }}
.eq {{ overflow:auto; border-radius:14px; padding:14px 16px; background:#0c3557; color:#eef8fb; font:500 .89rem/1.55 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace; }}
.metric {{ display:flex; align-items:baseline; justify-content:space-between; gap:12px; padding:.7rem 0; border-bottom:1px solid #e1ecef; }}
.metric:last-child {{ border-bottom:0; }}
.metric strong {{ font-size:1.2rem; }}
.note {{ border-left:4px solid var(--cyan); padding-left:12px; }}
footer {{ margin-top:24px; text-align:center; color:var(--slate); font-size:.9rem; }}
{animation_css}
@media (max-width:900px) {{ .card,.card.wide {{ grid-column:span 12; }} .stage {{ min-height:500px; }} .flight-bird {{ width:145px; }} .perch,.flight-bird {{ left:12%; bottom:175px; }} }}
@media (max-width:640px) {{ main {{ width:min(100% - 18px,1200px); padding-top:20px; }} .stage {{ min-height:430px; }} .wordmark {{ bottom:22px; }} .perch,.flight-bird {{ left:11%; bottom:145px; }} .flight-bird {{ width:118px; }} }}
</style>
</head>
<body>
<main>
<header>
  <div>
    <p class="kicker">Percolia · modèle d’aile paramétrique v{model['version']}</p>
    <h1>Un battement lent, calculé</h1>
    <p class="lede">L’aile n’est plus un assemblage de polygones que l’on fait pivoter. Sa forme continue, ses articulations et sa projection sont recalculées à chaque image. Un cycle complet dure {period:.1f} secondes.</p>
  </div>
  <div class="controls">
    <span id="status" class="status">PERCHED</span>
    <button id="pause" type="button">Pause</button>
    <button id="scan" type="button">Scanner</button>
    <button id="restart" class="primary" type="button">Rejouer le vol</button>
  </div>
</header>
<section id="stage" class="stage" data-flight-stage>
  <div class="wordmark">{wordmark}</div>
  <span id="perch" class="perch" aria-hidden="true"></span>
  <div id="bird" class="flight-bird percolia-bird-shell" data-flight-bird>{bird}</div>
</section>
<section class="grid">
  <article class="card wide">
    <h2>Modèle cinématique</h2>
    <p>L’humérus, l’avant-bras et la main définissent quatre points de squelette. Une spline de Catmull–Rom produit le bord d’attaque. La corde varie continûment le long de l’envergure, puis la membrane est projetée depuis un espace 3D oblique.</p>
    <div class="eq">θ = 2πt/T
φ(t) = φ₀ + A₁ cos θ + A₂ cos(2θ − δ)
f(t) = ((1 + sin(θ − η))/2)^p
β(t) = β₀ + Δβ f(t)
γ(t) = γ₀ + Δγ f(t)
c(s) = c₀(1 − s)^q(1 + b sin πs)</div>
  </article>
  <aside class="card">
    <h2>Paramètres</h2>
    <div class="metric"><span>Période</span><strong>{period:.1f} s</strong></div>
    <div class="metric"><span>Stations par aile</span><strong>{len(model['wing']['stations'])}</strong></div>
    <div class="metric"><span>Segments osseux</span><strong>3</strong></div>
    <div class="metric"><span>Trajectoire</span><strong>4 Bézier</strong></div>
  </aside>
  <article class="card">
    <h2>Ce qui bouge vraiment</h2>
    <p>Le coude et le poignet se replient pendant la remontée. L’envergure projetée diminue, la corde se tord légèrement et les facettes du réseau suivent la surface.</p>
  </article>
  <article class="card">
    <h2>Vol lent</h2>
    <p>Le battement est volontairement ample et calme. Le second harmonique évite le mouvement purement sinusoïdal, trop mécanique, sans introduire de secousses de marionnette.</p>
  </article>
  <article class="card">
    <h2>Scan LiDAR</h2>
    <p>Le scan reste bref et secondaire : balayage angulaire, retour ponctuel et onde de mesure. Le logo reste un oiseau avant de devenir un diagramme technique.</p>
  </article>
</section>
<footer>Démonstration autonome : aucun chargement externe, aucune dépendance.</footer>
<script>{animation_js}</script>
<script>
const svg = document.querySelector('#bird svg');
const status = document.querySelector('#status');
const controller = initPercoliaBird(svg, {{
  birdElement: document.querySelector('#bird'),
  stageElement: document.querySelector('#stage'),
  perchElement: document.querySelector('#perch'),
  onState: (state) => {{ status.textContent = state; }}
}});
const pause = document.querySelector('#pause');
let paused = false;
pause.addEventListener('click', () => {{
  paused = !paused;
  if (paused) {{ controller.pause(); pause.textContent = 'Reprendre'; }}
  else {{ controller.play(); pause.textContent = 'Pause'; }}
}});
document.querySelector('#scan').addEventListener('click', () => controller.scan());
document.querySelector('#restart').addEventListener('click', () => {{ paused = false; pause.textContent = 'Pause'; controller.restart(); }});
</script>
</main>
</body>
</html>'''
    (ROOT / "demo.html").write_text(html, encoding="utf-8")
    print("wrote demo.html")


if __name__ == "__main__":
    main()
