# Charte graphique Percolia — v0.2

## 1. Positionnement

Percolia transforme des données complexes et bruitées en structures fiables. Le premier marché est le LiDAR 3D, mais l’identité doit rester valable pour les graphes, les logs et les données scientifiques.

| Idée | Traduction visuelle |
|---|---|
| Contrôle de la connectivité | coupure et deux nœuds du `P` |
| Hiérarchie de marque | `P` plein format, `ERCOLIA` en petites capitales |
| Structure issue du bruit | maillage géométrique de l’oiseau |
| Modèle réellement opérant | oiseau articulé, vol et scan cohérents |
| Confiance industrielle | bleu encre dominant, peu d’effets |

## 2. Signature

La signature principale place un **petit oiseau-réseau perché sur la partie supérieure du P**. Il doit rester un accent : sa largeur ne dépasse pas environ 18 % de celle du mot-symbole.

Le mot-symbole se compose de :

- `P` à 100 % de la hauteur de capitale ;
- `ERCOLIA` à 78 %, aligné sur la même ligne de base.

Ne pas reconstituer le nom avec une police approchante.

## 3. Oiseau articulé

Le modèle animé sépare :

- les deux épaules ;
- les bras ;
- les avant-bras ;
- les mains et rémiges ;
- la tête ;
- la queue ;
- les deux pattes.

La descente d’aile est rapide et ample. La remontée replie coude et poignet. L’oiseau décolle du P, suit une boucle, scanne, puis revient se poser. Il ne doit pas voler en permanence dans une interface de travail.

### Règles d’animation

- un cycle complet doit durer entre 8 et 12 secondes ;
- prévoir au moins 1,5 seconde de repos sur le P ;
- le scan reste bref et discret ;
- la tête compense partiellement l’inclinaison du corps ;
- les pattes se rétractent après le décollage et s’étendent avant l’atterrissage ;
- respecter `prefers-reduced-motion`.

## 4. Couleurs

| Nom | Hex | Rôle |
|---|---:|---|
| Encre | `#082C4C` | texte, contours, fonds inversés |
| Signal | `#1C83D4` | propagation, articulations |
| Seuil | `#20C9C4` | nœuds critiques, scan |
| Brume | `#EAF5F7` | surfaces secondaires |
| Ardoise | `#5D7385` | texte secondaire |
| Blanc | `#FFFFFF` | fond principal |

Le cyan n’est pas une couleur de petit texte sur fond blanc. Il reste un accent graphique.

## 5. Tailles minimales

| Actif | Écran | Impression |
|---|---:|---:|
| Monogramme P | 20 px | 6 mm |
| Mot-symbole seul | 150 px | 38 mm |
| Signature avec oiseau | 280 px | 70 mm |
| Oiseau compact seul | 64 px | 18 mm |
| Oiseau articulé détaillé | 120 px | 32 mm |

Sous 280 px, supprimer l’oiseau et conserver le mot-symbole ou le P seul.

## 6. Usages interdits

Ne pas :

- fermer la coupure du P ;
- remettre toutes les lettres à la même hauteur ;
- agrandir l’oiseau jusqu’à concurrencer le nom ;
- faire battre l’aile entière comme une planche rigide ;
- ajouter des effets néon, des traînées permanentes ou un scan agressif ;
- lancer le vol en boucle rapide ;
- utiliser l’oiseau comme mascotte humoristique.

## 7. Fichiers de référence

- signature : `Logo/percolia-lockup-horizontal.svg` ;
- mot-symbole : `Logo/Police/percolia-wordmark-primary.svg` ;
- oiseau statique : `Logo/Oiseau/percolia-bird-compact.svg` ;
- démonstration : `Logo/Oiseau/demo.html` ;
- modèle : `Logo/Oiseau/source/bird_model.json`.
