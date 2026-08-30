# Source de l’oiseau-réseau

`bird_model.json` contient :

- la topologie restaurée du premier oiseau Percolia ;
- les facettes, arêtes, nœuds et points dispersés ;
- les paramètres cinématiques des deux ailes ;
- la pose repliée utilisée sur le `P` ;
- les pattes ;
- les quatre courbes de Bézier de la séquence directionnelle ;
- les durées de décollage, sortie, silence, retour et atterrissage.

Les SVG générés ne doivent pas être modifiés isolément. Toute évolution de la forme ou du mouvement doit partir de ce JSON et des générateurs Python.
