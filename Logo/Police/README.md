# Mot-symbole Percolia

## Construction

Le `P` distinctif est conservé sans modification. Sa coupure et ses deux nœuds matérialisent un seuil de connectivité.

Les lettres `ERCOLIA` utilisent désormais la même construction géométrique, mais à **78 % de la hauteur du P** et sur la même ligne de base. L’effet obtenu est celui de petites capitales : le P devient un signe de marque autonome, tandis que le reste du nom reste calme, lisible et industriel.

## Fichiers

- `source/geometry.json` : géométrie, échelle des petites capitales et métriques ;
- `build_wordmark.py` : générateur sans dépendance ;
- `percolia-wordmark-primary.svg` ;
- `percolia-wordmark-inverse.svg` ;
- `percolia-wordmark-mono.svg` ;
- `percolia-p-monogram-*.svg` ;
- `percolia-glyph-sheet.svg`.

## Modification

```bash
python Logo/Police/build_wordmark.py
python Logo/build_lockups.py
python Logo/Oiseau/build_demo.py
```

Le mot-symbole reste un lettering vectoriel propriétaire, pas une fonte de texte généraliste.
