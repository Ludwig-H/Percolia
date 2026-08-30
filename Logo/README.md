# Identité visuelle Percolia — direction 03

## Principe

**La structure fiable qui émerge du bruit.**

La marque associe :

- un `P` distinctif, conservé dans sa forme initiale ;
- `ERCOLIA` en petites capitales géométriques ;
- un petit oiseau-réseau perché sur le `P` ;
- une version animée dont les ailes sont calculées par un modèle paramétrique continu.

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
    ├── test_wing_model.py
    └── source/bird_model.json
```

Les SVG, la planche de marque et `Oiseau/demo.html` sont des fichiers générés. Ils sont néanmoins versionnés pour être consultables directement sur GitHub.

## Construction

```bash
python Logo/Police/build_wordmark.py
python Logo/Oiseau/build_bird.py
python Logo/build_lockups.py
python Logo/Oiseau/build_demo.py
python Logo/Oiseau/test_wing_model.py
```

La démonstration autonome est disponible dans [`Oiseau/demo.html`](Oiseau/demo.html).

## Statut

Cette direction est un prototype de marque éditable. Une recherche d’antériorités graphique et typographique reste nécessaire avant dépôt définitif.
