# Sources de l’oiseau Percolia

- `bird_model.json` décrit la topologie, la palette, le contour de référence des ailes, les points d’ancrage, les contraintes graphiques et la pose finale utilisée par le logo statique.
- `animation_clips.json` contient les clips keyframés, les événements et les trajectoires du monde.

La trajectoire sortante est stockée sous forme d’offsets relatifs à la fin réelle du décollage. Les fichiers SVG et `demo.html` sont générés ; ils ne doivent pas devenir des sources concurrentes.

Le bloc `static_logo` désigne le clip, le point d’appui et le miroir horizontal de la pose finale exportée.
