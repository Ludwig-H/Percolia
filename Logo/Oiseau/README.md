# Oiseau-réseau Percolia

## Rôle du symbole

L’oiseau ne représente pas directement un secteur ou un capteur. Il fournit une image plus large de la promesse Percolia : **percevoir, organiser et faire émerger une structure fiable à partir d’observations dispersées**.

Sa construction reprend trois niveaux :

1. des points libres à gauche, assimilables au bruit ou aux observations non structurées ;
2. un maillage géométrique qui forme progressivement le corps ;
3. un chemin bleu/cyan continu qui traverse le réseau jusqu’au bec, image d’une propagation maîtrisée.

Les triangles évoquent les interactions d’ordre supérieur et les objets géométriques employés par la technologie, sans faire du logo un diagramme scientifique littéral.

## Fichiers

- `percolia-bird-primary.svg` : dessin complet sur fond clair.
- `percolia-bird-inverse.svg` : version pour fond Encre.
- `percolia-bird-mono.svg` : version une couleur.
- `percolia-bird-compact.svg` : réseau simplifié pour les petites tailles.
- `source/topology.json` : nœuds, arêtes, facettes, phases et rôles.
- `build_bird.py` : générateur SVG sans dépendance.
- `bird-animation.js` et `bird-animation.css` : animation web de référence.
- `demo.html` : démonstrateur local.

## Structure sémantique du SVG

Les éléments exposent les attributs suivants :

- `data-layer="faces|edges|nodes|scatter"` ;
- `data-anim="face|edge|node|scatter"` ;
- `data-kind="critical|outline|mesh"` ;
- `data-phase="0…5"`.

Cette structure permet d’animer la construction du réseau sans dépendre des numéros de nœuds.

## Intégration web

Le SVG doit être **inline** pour que le script puisse accéder à ses groupes.

```html
<link rel="stylesheet" href="bird-animation.css">
<div id="hero-bird" class="percolia-bird-shell">
  <!-- contenu de percolia-bird-primary.svg -->
</div>
<script type="module">
  import { initPercoliaBird } from "./bird-animation.js";
  initPercoliaBird(document.querySelector("#hero-bird svg"));
</script>
```

L’API renvoie `reveal()`, `pulse()` et `destroy()`. Les mouvements sont automatiquement neutralisés lorsque l’utilisateur demande une réduction des animations.

## Régénération

```bash
python Logo/Oiseau/build_bird.py
python Logo/build_lockups.py
```

Pour changer la silhouette, modifier d’abord `source/topology.json` : c’est la source de vérité. Éviter de modifier seulement les SVG générés, faute de quoi les changements seraient perdus à la prochaine génération.
