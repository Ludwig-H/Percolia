# Mot-symbole et monogramme Percolia

## Concept

La piste typographique cherche la reconnaissance par la **forme**, pas par un artifice ajouté au `O`. Le signe principal est le `P` : son fût et sa panse sont séparés par un intervalle portant deux nœuds. Cette coupure peut se lire comme :

- un seuil de percolation ;
- une connectivité que Percolia choisit de ne pas déclencher trop tôt ;
- deux structures proches que le bruit ne doit pas fusionner ;
- la lettre `P` comme porte d’entrée de la marque.

Le reste du mot est volontairement plus stable afin de ne pas accumuler les singularités. L’ensemble garde une parenté avec les réseaux et les trajectoires LiDAR sans devenir une imitation littérale d’un nuage de points.

## Fichiers

- `percolia-wordmark-primary.svg` : version couleur sur fond clair.
- `percolia-wordmark-inverse.svg` : version claire sur fond Encre.
- `percolia-wordmark-mono.svg` : version une couleur.
- `percolia-p-monogram-*.svg` : icône autonome.
- `percolia-glyph-sheet.svg` : planche de construction des huit lettres.
- `source/geometry.json` : géométrie source, avances et espacement.
- `build_wordmark.py` : générateur sans dépendance externe.

## Modifier le dessin

1. Modifier les chemins SVG dans `source/geometry.json`.
2. Ajuster `advance` et `tracking` si nécessaire.
3. Régénérer :

```bash
python Logo/Police/build_wordmark.py
python Logo/build_lockups.py
```

Les coordonnées utilisent un canevas de 210 unités, une ligne de capitale à `y=38`, une ligne de base à `y=172` et un trait nominal de 14 unités.

## Limite assumée

Il s’agit d’un **lettering de marque**, non d’un alphabet complet. Transformer cette piste en fonte OpenType exigerait notamment :

- l’ensemble des capitales, minuscules, chiffres, accents et ponctuation ;
- la définition d’overshoots et d’un hinting cohérent ;
- des tests multi-tailles ;
- une table de crénage ;
- une revue juridique des ressemblances typographiques.

Pour le site, le logo doit donc être utilisé en SVG et non comme une police de texte.
