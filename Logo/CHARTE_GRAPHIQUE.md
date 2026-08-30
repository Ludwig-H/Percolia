# Charte graphique Percolia — v0.3

## 1. Positionnement

Percolia transforme des données complexes et bruitées en structures fiables. L’identité doit exprimer la géométrie, le contrôle de la connectivité, la robustesse et la confiance industrielle, sans adopter les codes visuels interchangeables de « l’IA magique ».

## 2. Mot-symbole

- Le `P` conserve sa forme et ses deux nœuds distinctifs.
- `ERCOLIA` est composé en petites capitales à 78 % de la hauteur du `P`.
- Le mot-symbole doit rester un SVG ; il ne doit pas être reconstitué avec une police approchante.

## 3. Oiseau

### Signature statique

Le petit oiseau est perché sur le haut du `P`. Il reste un accent et ne doit pas rivaliser avec le nom.

### Version animée

Le vol suit quatre principes :

1. battement lent, période nominale de 5,2 secondes ;
2. déformation continue de l’aile, sans rotation rigide de polygones ;
3. repli du coude et du poignet pendant la remontée ;
4. scan LiDAR bref et discret, une fois par boucle.

L’oiseau ne doit pas battre des ailes en permanence dans une interface de travail. L’animation complète est réservée à la page d’accueil, à une transition ou à une démonstration.

## 4. Couleurs

| Nom | Hex | Usage |
|---|---:|---|
| Encre | `#082C4C` | contours, texte, couleur principale |
| Signal | `#1C83D4` | arêtes actives, articulation secondaire |
| Seuil | `#20C9C4` | nœuds critiques, retour LiDAR |
| Brume | `#EAF5F7` | surfaces et arrière-plans techniques |
| Ardoise | `#5D7385` | texte secondaire |
| Blanc | `#FFFFFF` | fond principal et version inversée |

## 5. Densité graphique

- Les facettes sont translucides.
- Les nœuds sont rares et petits.
- Les contours dominent sur le remplissage.
- Le réseau doit rester lisible à 96 px ; sous cette taille, utiliser l’oiseau compact.

## 6. Animation

- Période nominale : `5200 ms`.
- Trajectoire complète : environ `24,5 s`.
- Pas d’accélération brutale aux extrêmes du battement.
- Aucun clignotement répété du scan.
- Respect obligatoire de `prefers-reduced-motion`.

## 7. Interdits

Ne pas :

- transformer l’oiseau en mascotte cartoon ;
- épaissir les facettes jusqu’à masquer la silhouette ;
- accélérer le battement pour produire un effet de vibration ;
- ajouter des dégradés arc-en-ciel, effets néon ou ombres lourdes ;
- dissocier le petit oiseau du `P` dans la signature statique ;
- modifier uniquement les SVG générés sans mettre à jour les sources JSON et Python.
