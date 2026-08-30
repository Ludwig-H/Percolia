# Source du modèle d’oiseau

`bird_model.json` est la source de vérité de l’oiseau-réseau Percolia.

Le fichier décrit :

- la topologie triangulée du corps initial ;
- les points dispersés autour de la silhouette ;
- la chaîne cinématique des deux ailes ;
- les pattes et leurs points d’appui ;
- les ancres distinctes du corps en vol et des pieds au repos ;
- les durées des phases `preload`, `takeoff`, `flare`, `touchdown` et `settle` ;
- les courbes de Bézier raccordées du vol directionnel.

Les fichiers SVG et `demo.html` sont générés. Ils ne doivent pas être modifiés comme sources primaires.
