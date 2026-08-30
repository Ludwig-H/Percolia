# Source géométrique

`geometry.json` est la source de vérité du mot-symbole. Chaque glyphe contient :

- `advance` : largeur utilisée pour le placement ;
- `paths` : tracés SVG éditables ;
- `nodes` : nœuds colorés éventuels et leur rôle sémantique.

Le générateur conserve des identifiants stables (`letter-1-P`, `threshold-origin`, etc.) pour permettre des interactions ou animations ciblées côté web.
