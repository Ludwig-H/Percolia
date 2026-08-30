# Identité visuelle Percolia — direction 01

<p align="center">
  <img src="brand-board.svg" alt="Planche de marque Percolia" width="960">
</p>

## Idée directrice

**La structure fiable qui émerge du bruit.**

Percolia ne doit pas ressembler à une marque d’« IA magique » ou à un fournisseur générique de données. Son avantage vient d’une construction scientifique précise : géométrie, interactions d’ordre supérieur, percolation, robustesse et passage à l’échelle. La direction retenue traduit ce positionnement sans enfermer la marque dans une seule application LiDAR.

- Le **mot-symbole** est une construction géométrique monolinéaire, stable et industrielle.
- Le **P** contient une coupure volontaire : deux nœuds séparés représentent un seuil critique, la maîtrise de la connectivité et la capacité à éviter les fusions parasites.
- L’**oiseau-réseau** montre des points dispersés qui deviennent une forme structurée. L’oiseau suggère la vision, la hauteur de vue et le mouvement, mais reste un objet géométrique plutôt qu’une mascotte.
- Le chemin bleu/cyan qui traverse l’oiseau matérialise une propagation contrôlée au sein du réseau.

## Contenu

```text
Logo/
├── CHARTE_GRAPHIQUE.md
├── tokens.css
├── tokens.json
├── build_lockups.py
├── brand-board.svg
├── percolia-lockup-horizontal.svg
├── percolia-lockup-horizontal-mono.svg
├── percolia-lockup-horizontal-inverse.svg
├── percolia-lockup-stacked.svg
├── Police/
│   ├── README.md
│   ├── build_wordmark.py
│   ├── source/geometry.json
│   ├── percolia-wordmark-*.svg
│   ├── percolia-p-monogram-*.svg
│   └── percolia-glyph-sheet.svg
└── Oiseau/
    ├── README.md
    ├── build_bird.py
    ├── source/topology.json
    ├── percolia-bird-*.svg
    ├── bird-animation.js
    ├── bird-animation.css
    └── demo.html
```

## Régénération

Aucune dépendance Python externe n’est requise.

```bash
python Logo/Police/build_wordmark.py
python Logo/Oiseau/build_bird.py
python Logo/build_lockups.py
```

Les fichiers SVG produits restent lisibles et modifiables à la main dans Inkscape, Illustrator, Figma ou un éditeur de texte. Les groupes, nœuds et arêtes portent des identifiants sémantiques pour l’animation web.

## Statut

Cette livraison est une **direction créative v0.1**, suffisamment cohérente pour être testée sur le site, une présentation commerciale et un favicon. Avant dépôt de marque et diffusion définitive, il faudra encore mener :

1. une recherche d’antériorités graphique et typographique ;
2. des tests de reconnaissance du `P` à petite taille ;
3. un test de perception auprès de cibles LiDAR/robotique et d’acheteurs logiciels industriels ;
4. la finalisation éventuelle d’une vraie fonte OpenType si le besoin dépasse le seul mot `PERCOLIA`.
