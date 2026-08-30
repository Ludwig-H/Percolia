# Modèle paramétrique de l’oiseau

`bird_model.json` est la source de vérité. Les ailes ne sont plus des groupes rigides tournés autour de trois pivots.

Chaque aile est construite à chaque image à partir de :

- trois longueurs osseuses : humérus, avant-bras et main ;
- trois angles articulaires : balayage, flexion du coude et flexion du poignet ;
- un angle de battement hors du plan ;
- une loi de corde continue pour la membrane et les rémiges ;
- une projection orthographique oblique d’un modèle 3D vers le SVG 2D.

Le contour et le maillage intérieur sont recalculés à chaque image. Les paramètres de vitesse, d’amplitude, de repli et de projection restent éditables dans le JSON.
