# Modèle source de l’oiseau

`bird_model.json` décrit :

- la palette ;
- les nœuds, arêtes et facettes du corps, de la tête, de la queue et de l’aile pliée ;
- trois maillages locaux pour chaque aile articulée : bras, avant-bras et main ;
- les pivots d’épaule, de coude et de poignet ;
- les pattes et le point d’émission du scan ;
- les poses statiques `perched` et `glide`.

Les coordonnées des avant-bras et des mains sont locales au segment parent. Cette hiérarchie doit être conservée : c’est elle qui permet un vrai battement plutôt qu’une rotation globale de la silhouette.
