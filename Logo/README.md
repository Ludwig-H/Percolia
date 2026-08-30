# Identité visuelle Percolia — direction 04

## Principe

**La structure fiable qui émerge du bruit.**

La marque associe :

- le `P` distinctif conservé dans sa forme initiale ;
- `ERCOLIA` en petites capitales géométriques ;
- le premier oiseau-réseau, restauré et perché sur le `P` ;
- une animation directionnelle utilisant deux oiseaux distincts ;
- une cinématique inspirée des moteurs de jeu, fondée sur des clips, du root motion, des événements et des contacts IK.

## Sources canoniques

```text
Logo/
├── CHARTE_GRAPHIQUE.md
├── build_lockups.py
├── Police/
│   ├── build_wordmark.py
│   └── source/geometry.json
└── Oiseau/
    ├── build_bird.py
    ├── build_demo.py
    ├── bird-animation.js
    ├── test_wing_model.py
    └── source/
        ├── bird_model.json
        └── animation_clips.json
```

Les SVG, la planche de marque et `Oiseau/demo.html` sont générés mais versionnés pour rester visibles immédiatement.

## Construction

```bash
python Logo/Police/build_wordmark.py
python Logo/Oiseau/build_bird.py
python Logo/build_lockups.py
python Logo/Oiseau/build_demo.py
python Logo/Oiseau/test_wing_model.py
node --check Logo/Oiseau/bird-animation.js
```

La démonstration autonome se trouve dans [`Oiseau/demo.html`](Oiseau/demo.html).

## Animation

Le dessin en réseau et la palette restent inchangés. Le mouvement est organisé en clips keyframés : anticipation, poussée, décollage, croisière, approche, arrondi, contact et stabilisation. Les événements `toe_off` et `touchdown` commandent les appuis, tandis qu’une IK à deux segments verrouille les pattes sur le `P`.

Le scan LiDAR part du nœud de capteur de la tête et reste graphiquement distinct du bec.

## Statut

Cette direction reste un prototype de marque éditable. Une recherche d’antériorités graphique et typographique demeure nécessaire avant dépôt définitif.
