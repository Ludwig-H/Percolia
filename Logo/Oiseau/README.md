# Oiseau-réseau Percolia — direction 05

Cette direction conserve le **premier oiseau triangulé** de Percolia et remplace la cinématique globale par une architecture inspirée des moteurs de jeu : clips keyframés, machine à états, root motion, événements d’animation, motion warping et IK de contact.

## Raffinement de la direction 05

Le corps, la tête, la queue et les pattes restent ceux du premier oiseau triangulé. L’aile principale reprend désormais le contour de la référence fournie : racine centrale, bord supérieur relevé, double pointe à gauche et large surface facettée. Ce dessin est déformé par **linear blend skinning 2D** autour des segments épaule–coude–poignet–extrémité ; les battements conservent donc l’identité graphique du premier oiseau.

Les à-coups sont réduits par une interpolation PCHIP périodique des clips cycliques, une progression par longueur d’arc sur les trajectoires et de courts fondus de pose aux changements d’état. La sortie du perchoir est raccordée en position et en vitesse au clip de décollage : les pattes se détendent, `toe_off` libère les appuis, puis deux battements puissants établissent le vol.

## Séquence

1. Le premier oiseau reste perché sur le `P`.
2. **Anticipation** : le corps se tasse, les ailes s’ouvrent et les pieds restent verrouillés.
3. **Poussée** : l’événement `toe_off` libère les pieds à une image précise.
4. **Décollage** : deux battements propres à l’envol remplacent le cycle de croisière.
5. L’oiseau traverse la scène de gauche à droite puis sort du cadre.
6. Après un court intervalle vide, un second oiseau arrive de droite à gauche.
7. **Approche** puis **arrondi** : il ralentit, relève le corps, ouvre les ailes et sort les pattes.
8. **Contact** : le root motion est légèrement adapté au point exact du `P` ; l’événement `touchdown` active l’IK.
9. **Stabilisation** : les pieds restent verrouillés tandis que le corps amortit son énergie et que les ailes se replient.

Le premier oiseau ne fait jamais demi-tour. Le retour est assuré par un second objet SVG distinct.

## Architecture

### Clips keyframés

Les clips sont stockés dans `source/animation_clips.json` :

```text
perched_idle
anticipation_push
push_off
takeoff
cruise
approach
flare
touchdown
settle
```

Chaque keyframe définit :

- la translation, l’orientation et l’échelle de la racine ;
- les angles épaule–coude–poignet des ailes ;
- l’échelle d’envergure et de corde ;
- le repli et la compression des pattes ;
- le poids de contact des pieds.

### Événements

Les événements jouent le rôle d’Animation Notifies :

- `toe_off` : fin exacte de l’appui au décollage ;
- `touchdown` : début exact du verrouillage des pieds ;
- `weight_transfer` : transfert du poids sur le perchoir ;
- `feet_locked` : maintien des appuis pendant la stabilisation.

### IK et motion warping

Pendant l’anticipation et le début de la poussée, les pieds sont verrouillés sur le `P` par une IK à deux segments. À l’atterrissage, le motion warping ne corrige que l’écart final entre le clip et le point de contact. Après `touchdown`, l’IK maintient les doigts sur le perchoir pendant l’amortissement du corps.

## Scan LiDAR

Le scan provient du nœud de capteur situé dans la tête (`h5`). Il prend la forme d’une onde circulaire brève, d’un trait de balayage court et d’un retour lumineux. Aucun élément graphique n’est émis depuis le bec.

## Fichiers canoniques

```text
Logo/Oiseau/
├── README.md
├── build_bird.py
├── build_demo.py
├── bird-animation.css
├── bird-animation.js
├── test_wing_model.py
└── source/
    ├── README.md
    ├── bird_model.json
    └── animation_clips.json
```

Les SVG et `demo.html` sont générés mais versionnés pour être consultables directement.

## Régénération et validation

```bash
python Logo/Oiseau/build_bird.py
python Logo/build_lockups.py
python Logo/Oiseau/build_demo.py
python Logo/Oiseau/test_wing_model.py
node --check Logo/Oiseau/bird-animation.js
```

Les tests vérifient les clips, les événements, la continuité des ailes, les directions de vol, l’amplitude du motion warping, les contacts IK, l’origine crânienne du scan, la palette et l’autonomie de la page HTML.
