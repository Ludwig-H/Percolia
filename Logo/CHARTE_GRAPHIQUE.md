# Charte graphique Percolia — v0.4

## 1. Positionnement

Percolia transforme des données complexes et bruitées en structures fiables. L’identité traduit la géométrie, la sélection des bonnes connexions, la robustesse et la confiance industrielle, sans reprendre les codes interchangeables de « l’IA magique ».

## 2. Mot-symbole

- Le `P` conserve sa forme, sa coupure et ses deux nœuds distinctifs.
- `ERCOLIA` est composé en petites capitales à 78 % de la hauteur du `P`.
- Le mot-symbole reste un SVG et ne doit pas être reconstitué avec une police approchante.

## 3. Oiseau

### Signature statique

Le petit oiseau-réseau est perché sur le haut du `P`. Il reste un accent : il ne doit ni dominer le nom ni être agrandi comme une mascotte.

### Forme

La référence est le **premier modèle triangulé** :

- corps, tête et queue formés de facettes ;
- contour Encre ;
- alternance mesurée de Signal et Seuil ;
- points dispersés uniquement dans les grandes illustrations ;
- remplissages translucides.

Le modèle paramétrique lisse exploré précédemment est abandonné.

### Animation

La séquence complète emploie deux oiseaux :

1. l’oiseau perché part vers la droite et sort du cadre ;
2. aucun mouvement inverse n’est appliqué à cet objet ;
3. un second oiseau arrive depuis la droite et vole vers la gauche ;
4. il atterrit sur le `P`, puis l’animation s’arrête.

Les ailes sont déformables. La chaîne épaule–coude–poignet est plus ouverte pendant la descente et se replie pendant la remontée. Une simple rotation rigide du dessin est interdite.

## 4. Couleurs

| Nom | Hex | Usage |
|---|---:|---|
| Encre | `#082C4C` | contours, texte, couleur principale |
| Signal | `#1C83D4` | arêtes actives, facettes secondaires |
| Seuil | `#20C9C4` | nœuds critiques, bref retour LiDAR |
| Brume | `#EAF5F7` | surfaces et fonds techniques |
| Ardoise | `#5D7385` | texte secondaire |
| Blanc | `#FFFFFF` | fond principal et version inversée |

## 5. Densité graphique

- Les facettes restent translucides.
- Les contours dominent sur le remplissage.
- Les nœuds ne doivent pas former un semis illisible à petite taille.
- Sous 96 px, utiliser l’oiseau compact perché.

## 6. Rythme

- Période nominale d’un battement : `3200 ms`.
- Aucun battement rapide ou vibratoire.
- Un court intervalle vide sépare la sortie du premier oiseau de l’entrée du second.
- L’animation est exécutée une seule fois ; seul le bouton « Rejouer » la relance.
- `prefers-reduced-motion` laisse la signature statique.

## 7. Interdits

Ne pas :

- transformer l’oiseau en mascotte cartoon ;
- remettre le modèle lisse abandonné ;
- faire demi-tour au même oiseau hors champ ;
- secouer une aile rigide par rotation CSS ;
- épaissir les facettes jusqu’à masquer le réseau ;
- ajouter des effets néon, arc-en-ciel ou des ombres lourdes ;
- modifier seulement les SVG générés sans mettre à jour le JSON et les générateurs.
