# Oiseau-réseau Percolia

## Direction retenue

L’oiseau est désormais un **martinet géométrique articulé**. Il reste construit par des nœuds, des arêtes et quelques facettes, mais sa silhouette n’est plus un amas de triangles approximativement remué.

Dans la signature statique, il est petit et perché sur le `P`. Dans la démonstration animée, il :

1. reste brièvement au repos sur le `P` ;
2. déploie ses deux ailes ;
3. décolle en rétractant les pattes ;
4. suit une trajectoire fermée composée de quatre arcs de Bézier ;
5. scanne l’environnement avec un faisceau et un bref retour lumineux ;
6. gouverne avec la queue, étend les pattes et revient se poser.

## Pourquoi le battement est désormais crédible

Chaque aile est un rig emboîté à trois segments :

```text
épaule → bras → coude → avant-bras → poignet → main/rémiges
```

La descente est plus courte et plus énergique. Pendant la remontée, le coude et le poignet replient partiellement l’aile. Les deux ailes sont visibles avec une légère perspective ; la tête compense l’inclinaison du corps et la queue accompagne les virages.

## Fichiers

```text
Oiseau/
├── README.md
├── build_bird.py
├── build_demo.py
├── bird-animation.css
├── bird-animation.js
├── demo.html
├── percolia-bird-primary.svg
├── percolia-bird-inverse.svg
├── percolia-bird-mono.svg
├── percolia-bird-compact.svg
└── source/
    ├── README.md
    └── bird_model.json
```

- `bird_model.json` est la source de vérité géométrique et anatomique.
- `build_bird.py` génère les quatre SVG.
- `bird-animation.js` pilote le squelette et le trajet de vol.
- `demo.html` est **entièrement autonome** : il peut être téléchargé seul et ouvert hors ligne.
- `percolia-bird-compact.svg` utilise l’aile pliée et sert à la signature perchée.

## Régénération

```bash
python Logo/Police/build_wordmark.py
python Logo/Oiseau/build_bird.py
python Logo/build_lockups.py
python Logo/Oiseau/build_demo.py
```

Aucune dépendance Python externe n’est requise pour la génération.

## Intégration web

Le SVG doit être inline pour que le script puisse articuler ses groupes.

```html
<link rel="stylesheet" href="bird-animation.css">
<div class="percolia-flight-stage" data-flight-stage>
  <span id="perch"></span>
  <div id="bird" class="percolia-flight-bird" data-flight-bird>
    <!-- contenu inline de percolia-bird-primary.svg -->
  </div>
</div>
<script src="bird-animation.js"></script>
<script>
  const controller = PercoliaBird.init(document.querySelector('#bird svg'), {
    birdElement: document.querySelector('#bird'),
    stageElement: document.querySelector('[data-flight-stage]'),
    perchElement: document.querySelector('#perch')
  });
</script>
```

L’API expose `play()`, `pause()`, `replay()`, `scan()`, `pulse()`, `reveal()` et `destroy()`.

## Accessibilité

Avec `prefers-reduced-motion: reduce`, l’oiseau reste perché. Le logo statique ne dépend jamais de l’animation pour être compris.
