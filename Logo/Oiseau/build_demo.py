#!/usr/bin/env python3
"""Build a single-file offline demonstration of the Percolia bird."""
from __future__ import annotations
import html
import json
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parent
LOGO_ROOT=ROOT.parent

def svg_without_declaration(path:Path)->str:
    text=path.read_text(encoding='utf-8')
    return re.sub(r'^<\?xml[^>]+>\s*','',text)

def main()->None:
    bird=svg_without_declaration(ROOT/'percolia-bird-primary.svg')
    wordmark=svg_without_declaration(LOGO_ROOT/'Police'/'percolia-wordmark-primary.svg')
    css=(ROOT/'bird-animation.css').read_text(encoding='utf-8')
    js=(ROOT/'bird-animation.js').read_text(encoding='utf-8')
    model_text=(ROOT/'source'/'bird_model.json').read_text(encoding='utf-8')
    model=json.loads(model_text)
    html_doc=f'''<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Percolia — oiseau-réseau articulé</title>
<style>
:root{{--ink:#082c4c;--blue:#1c83d4;--cyan:#20c9c4;--mist:#eaf5f7;--slate:#5d7385;--white:#fff;--border:#dcebed;--shadow:0 18px 60px rgb(8 44 76 / 10%)}}
*{{box-sizing:border-box}}
html,body{{margin:0;min-height:100%;background:linear-gradient(180deg,#f9fcfd 0%,#eef6f8 100%);color:var(--ink);font-family:Inter,ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif}}
body{{padding:28px 16px 52px}}
main{{width:min(1180px,100%);margin:auto}}
header{{display:flex;gap:24px;align-items:flex-end;justify-content:space-between;flex-wrap:wrap;margin-bottom:18px}}
.kicker{{margin:0 0 6px;color:var(--slate);font-size:.78rem;font-weight:760;letter-spacing:.18em;text-transform:uppercase}}
h1{{margin:0;font-size:clamp(2rem,4vw,3.65rem);letter-spacing:-.035em}}
.lead{{max-width:72ch;margin:.75rem 0 0;color:#31536a;line-height:1.65}}
.controls{{display:flex;flex-wrap:wrap;gap:9px;align-items:center}}
button{{border:1px solid rgb(8 44 76 / 18%);border-radius:999px;background:#fff;color:var(--ink);padding:.68rem 1rem;font:650 .94rem/1 inherit;cursor:pointer}}
button.primary{{background:var(--ink);color:#fff}}
button:hover{{border-color:rgb(28 131 212 / 60%)}}
.state{{min-width:82px;color:var(--slate);font-size:.86rem;text-transform:uppercase;letter-spacing:.09em}}
.logo-stage{{position:relative;height:clamp(430px,62vw,650px);overflow:hidden;border:1px solid var(--border);border-radius:28px;background:radial-gradient(circle at 24% 20%,rgb(32 201 196 / 9%),transparent 24%),linear-gradient(180deg,#fff 0%,#f7fbfc 100%);box-shadow:var(--shadow)}}
.logo-stage::before{{content:"";position:absolute;inset:0;background-image:linear-gradient(rgb(8 44 76 / 2.6%) 1px,transparent 1px),linear-gradient(90deg,rgb(8 44 76 / 2.6%) 1px,transparent 1px);background-size:32px 32px;mask-image:linear-gradient(180deg,transparent,#000 20%,#000 80%,transparent);pointer-events:none}}
.ambient{{position:absolute;inset:0;pointer-events:none}}
.ambient i{{position:absolute;width:5px;height:5px;border-radius:50%;background:var(--blue);opacity:.18;animation:twinkle 5s ease-in-out infinite}}
.ambient i:nth-child(1){{left:14%;top:16%}}.ambient i:nth-child(2){{left:31%;top:9%;width:3px;height:3px;animation-delay:1s}}.ambient i:nth-child(3){{left:52%;top:17%;background:var(--cyan);animation-delay:2.1s}}.ambient i:nth-child(4){{left:74%;top:11%;width:3px;height:3px;animation-delay:.7s}}.ambient i:nth-child(5){{left:86%;top:25%;background:var(--cyan);animation-delay:1.6s}}
.wordmark-frame{{position:absolute;left:4%;right:4%;bottom:24px;z-index:2}}
.wordmark-frame>svg{{display:block;width:100%;height:auto;overflow:visible}}
.perch-marker{{position:absolute;left:8.9%;top:18.2%;width:4px;height:4px;transform:translate(-50%,-50%);pointer-events:none}}
.scan-target{{position:absolute;right:10%;top:36%;width:7px;height:7px;border:1px solid var(--cyan);border-radius:50%;opacity:.42;box-shadow:0 0 0 8px rgb(32 201 196 / 5%)}}
.caption{{position:absolute;right:24px;bottom:18px;color:var(--slate);font-size:.82rem;letter-spacing:.04em}}
.grid{{display:grid;grid-template-columns:repeat(12,1fr);gap:18px;margin-top:18px}}
.card{{grid-column:span 6;padding:22px;border:1px solid var(--border);border-radius:22px;background:rgb(255 255 255 / 88%);box-shadow:0 10px 34px rgb(8 44 76 / 6%)}}
.card.wide{{grid-column:span 12}}
h2{{margin:.1rem 0 .9rem;font-size:1.18rem}}
p,li{{line-height:1.6}}
.rig-list{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px;padding:0;list-style:none}}
.rig-list li{{padding:12px;border-radius:14px;background:var(--mist);font-weight:650}}
.note{{border-left:4px solid var(--cyan);padding-left:13px;color:#294f67}}
details{{border:1px solid var(--border);border-radius:14px;background:#fff;padding:12px 14px}}
summary{{cursor:pointer;font-weight:700}}
pre{{max-height:420px;margin:12px 0 0;padding:15px;overflow:auto;border-radius:12px;background:#0d3556;color:#eff9fb;font:500 .79rem/1.5 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}}
footer{{margin-top:22px;text-align:center;color:var(--slate);font-size:.86rem}}
@keyframes twinkle{{0%,100%{{opacity:.12;transform:scale(.7)}}50%{{opacity:.62;transform:scale(1.22)}}}}
@media(max-width:780px){{.card{{grid-column:span 12}}.rig-list{{grid-template-columns:1fr 1fr}}.logo-stage{{height:480px}}}}
{css}
</style>
</head>
<body>
<main>
<header>
  <div>
    <p class="kicker">Percolia · modèle articulé v{html.escape(model['version'])}</p>
    <h1>Du perchoir au vrai vol</h1>
    <p class="lead">Le petit oiseau est perché sur le <strong>P</strong>, déploie ses ailes segment par segment, décolle, suit une trajectoire courbe, scanne son environnement avec un bref retour LiDAR, puis revient se poser. Ce n’est plus un polygone secoué comme une nappe au vent.</p>
  </div>
  <div class="controls" aria-label="Contrôles de l’animation">
    <span id="state" class="state">initialisation</span>
    <button id="play" type="button">Pause</button>
    <button id="scan" type="button">Scanner</button>
    <button id="replay" class="primary" type="button">Rejouer le vol</button>
  </div>
</header>
<section id="stage" class="logo-stage percolia-flight-stage" data-flight-stage>
  <div class="ambient"><i></i><i></i><i></i><i></i><i></i></div>
  <span class="scan-target" aria-hidden="true"></span>
  <div class="wordmark-frame">
    {wordmark}
    <span id="perch" class="perch-marker" aria-hidden="true"></span>
  </div>
  <div id="flight-bird" class="percolia-flight-bird" data-flight-bird>
    {bird}
  </div>
  <span class="caption">Animation autonome · aucune ressource externe</span>
</section>
<section class="grid">
  <article class="card">
    <h2>Un véritable rig 2-D</h2>
    <ul class="rig-list">
      <li>épaule</li><li>coude</li><li>poignet</li><li>tête</li><li>queue</li><li>pattes</li>
    </ul>
    <p>Chaque aile est constituée de trois segments emboîtés. La descente est plus rapide et plus ample ; durant la remontée, le coude et le poignet replient les rémiges. Le mouvement obtient ainsi une poussée et une récupération distinctes.</p>
  </article>
  <article class="card">
    <h2>Une séquence complète</h2>
    <p>Le cycle comporte un repos sur le P, un déploiement progressif, le décollage, quatre arcs de Bézier, le scan, l’approche, l’extension des pattes et l’atterrissage. La tête compense l’inclinaison du corps et la queue gouverne les virages.</p>
    <p class="note">Le mode <code>prefers-reduced-motion</code> conserve une pose perchée stable. Les utilisateurs n’ont pas à subir un volatile hyperactif parce qu’un designer avait découvert les animations CSS.</p>
  </article>
  <article class="card wide">
    <h2>Sources embarquées</h2>
    <details><summary>Modèle éditable <code>source/bird_model.json</code></summary><pre>{html.escape(model_text)}</pre></details>
  </article>
</section>
<footer>Percolia · mot-symbole en petites capitales · oiseau-réseau articulé et animable.</footer>
</main>
<script>{js}</script>
<script>
window.addEventListener('DOMContentLoaded', function () {{
  const svg=document.querySelector('#flight-bird svg');
  const button=document.getElementById('play');
  let paused=false;
  const controller=window.PercoliaBird.init(svg, {{
    birdElement:document.getElementById('flight-bird'),
    stageElement:document.getElementById('stage'),
    perchElement:document.getElementById('perch'),
    autoplay:true,
    loop:true,
    onState:function(state){{document.getElementById('state').textContent=state;}}
  }});
  window.percoliaBirdDemo=controller;
  button.addEventListener('click',function(){{
    paused=!paused;
    if(paused){{controller.pause();button.textContent='Reprendre';}}
    else{{controller.play();button.textContent='Pause';}}
  }});
  document.getElementById('scan').addEventListener('click',function(){{controller.scan();}});
  document.getElementById('replay').addEventListener('click',function(){{paused=false;button.textContent='Pause';controller.replay();}});
}});
</script>
</body>
</html>
'''
    (ROOT/'demo.html').write_text(html_doc,encoding='utf-8')
    print('wrote demo.html')

if __name__=='__main__': main()
