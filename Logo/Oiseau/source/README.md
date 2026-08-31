# Sources de l’oiseau Percolia

- `bird_model.json` décrit la topologie, la palette, le contour de référence des ailes, les points d’ancrage et les contraintes graphiques.
- `animation_clips.json` contient les clips keyframés, les événements et les trajectoires du monde.

La trajectoire sortante est stockée sous forme d’offsets relatifs à la fin réelle du décollage. Les fichiers SVG et `demo.html` sont générés ; ils ne doivent pas devenir des sources concurrentes.
