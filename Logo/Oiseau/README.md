# Oiseau-réseau Percolia

Cette version est la source canonique de l’oiseau Percolia. Elle reprend la silhouette triangulée du premier jet et conserve strictement la charte : Encre `#082C4C`, Signal `#1C83D4`, Seuil `#20C9C4`, Brume `#EAF5F7`, Ardoise `#5D7385` et blanc.

## Séquence

1. Un premier oiseau est perché sur le `P`.
2. Il se tasse, pousse sur ses pattes, libère le perchoir à l’événement `toe_off`, puis effectue deux battements de décollage.
3. Il poursuit son vol de gauche à droite et sort naturellement du cadre.
4. Un second oiseau entre depuis la droite, ralentit, sort ses pattes et se pose sur le `P`.
5. Après `touchdown`, l’IK verrouille les pieds pendant l’amortissement final.

Le premier oiseau ne fait jamais demi-tour. Les deux traversées utilisent deux objets SVG distincts.

## Logo statique

Les signatures principales utilisent désormais la **dernière pose de l’animation** : le second oiseau, arrivé depuis la droite, reste perché sur le `P` et regarde vers la gauche. La pose provient directement du clip `perched_idle`, avec les deux ailes visibles. Le miroir est effectué autour du point d’appui, de sorte que les pattes restent exactement au même endroit sur le `P`.

## Principes géométriques

### Trajectoire cohérente

La trajectoire sortante est définie **relativement à la pose terminale réelle du décollage**. Le premier point est exactement cette pose et le premier segment possède la même direction que sa vitesse terminale. Il n’existe donc plus de raccord absolu capable de ramener l’oiseau vers le bas entre `takeoff` et `outbound`.

Le SVG est transformé autour du centre visuel du réseau, proche du centre de masse du corps. Les rotations ne se font plus autour des pattes, ce qui supprimait une oscillation apparente de la tête malgré une trajectoire ascendante. La sortie se fait par le bord du viewport, sans fondu anticipé.

### Ailes stables

Le contour extérieur de chaque aile est toujours le même polygone de référence, à une similitude près. Le battement change son orientation ; seule la triangulation intérieure reçoit une articulation légère. L’aile ne change donc plus de dessin au cours du vol.

Au repos, l’aile conserve 96 % de son envergure et 100 % de sa corde. Elle est rabattue le long du corps par rotation au lieu d’être réduite comme une vignette.

### Contact

Les clips `anticipation_push`, `push_off`, `takeoff`, `approach`, `flare`, `touchdown` et `settle` sont keyframés. Les événements `toe_off`, `touchdown`, `weight_transfer` et `feet_locked` commandent les changements de contrainte. Une IK à deux segments ne sert qu’à maintenir les pattes sur le `P` pendant les phases de contact.

## Scan LiDAR

Le scan part du nœud cyan `h5`, situé dans la tête. Rien n’est émis par le bec.

## Fichiers

```text
Logo/Oiseau/
├── README.md
├── bird-animation.css
├── bird-animation.js
├── build_bird.py
├── build_demo.py
├── demo.html
├── percolia-bird-{primary,inverse,mono,compact}.svg
├── test_wing_model.py
└── source/
    ├── README.md
    ├── animation_clips.json
    └── bird_model.json
```

`demo.html` est autonome : aucun chargement réseau n’est nécessaire.

## Régénération

```bash
python Logo/Oiseau/build_bird.py
python Logo/build_lockups.py
python Logo/Oiseau/build_demo.py
python Logo/Oiseau/test_wing_model.py
node --check Logo/Oiseau/bird-animation.js
```
