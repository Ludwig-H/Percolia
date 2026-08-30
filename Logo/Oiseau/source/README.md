# Sources du rig de l’oiseau-réseau

Deux fichiers constituent la source de vérité de la direction 04 :

- `bird_model.json` contient la topologie du réseau, la géométrie des ailes et des pattes, la palette, les points de contact, les trajectoires globales et le capteur LiDAR de tête ;
- `animation_clips.json` contient les clips keyframés, la machine à états, les durées et les événements `toe_off`, `touchdown`, `weight_transfer` et `feet_locked`.

Les SVG et la page HTML sont générés à partir de ces sources. Toute modification durable doit être faite dans les fichiers JSON ou dans les générateurs, puis régénérée et testée.
