# Identité visuelle Percolia — direction 03

## Principe

**La structure fiable qui émerge du bruit.**

La marque associe :

- le `P` distinctif conservé dans sa forme initiale ;
- `ERCOLIA` en petites capitales géométriques ;
- le premier oiseau-réseau, restauré et perché sur le `P` ;
- une animation directionnelle utilisant deux oiseaux distincts.

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
    └── source/bird_model.json
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

## Choix abandonné

Le modèle d’oiseau paramétrique lisse des essais précédents n’est plus utilisé. Il a été remplacé par la topologie triangulée du premier jet, jugée plus reconnaissable et plus cohérente avec Percolia.

## Statut

Cette direction reste un prototype de marque éditable. Une recherche d’antériorités graphique et typographique demeure nécessaire avant dépôt définitif.
