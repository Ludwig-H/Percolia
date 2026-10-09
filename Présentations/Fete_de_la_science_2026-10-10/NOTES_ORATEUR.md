# Des points aux objets

Louis Hauseux, Percolia — Fête de la science, Antibes Juan-les-Pins, 10 octobre 2026.

## Fil de présentation

Prévoir environ six minutes d'explication. Le montage HGP–HDBSCAN de la page 8 dure 1 min 41 s ; les animations du chantier naval durent 12 secondes chacune. Pour un échange court : la comparaison des pages 2 et 3, les exemples K=1 et K=2 des pages 5 et 6, puis la vidéo.

### 1. Des points aux objets

« Une machine peut mesurer des millions de points. Comment passer de ces points à des objets ? C'est une question que j'ai étudiée pendant ma thèse et que nous poursuivons dans Percolia. »

### 2. Le LiDAR : une scène en points

« Un LiDAR envoie de la lumière et mesure des distances. Chaque mesure donne un point dans l'espace. En haut, le nuage mesuré ; en bas, le modèle théorique. On regarde la même scène du dessus et de côté. Quels objets sont présents dans le scan mais absents du modèle ? »

*Laisser quelques secondes pour comparer. Le bouton **Question 3D** montre la scène en rotation : points à gauche, modèle à droite. Revenir ensuite à la diapositive.*

### 3. Repérer les objets ajoutés

« Le modèle indique où se trouvent les structures attendues. Nous regroupons les points qui restent. Le rouge est compatible avec le modèle ; les autres couleurs montrent les groupes repérés. En bas, ces groupes sont superposés aux structures du modèle. On retrouve les deux mêmes vues. »

*Le bouton **Réponse 3D** montre les groupes colorés à gauche et le même modèle à droite.*

« Cette scène synthétique de chantier naval a été fournie par Marie Aspro. »

### 4. Le clustering : regrouper les points

« Une première étape consiste à regrouper les points proches. On appelle cela le clustering. On peut le faire avec de la géométrie, avant même d'apprendre les mots “voiture” ou “arbre”. Reconnaître ce que représente chaque groupe vient ensuite. »

« Ici, les couleurs montrent les groupes trouvés par HDBSCAN. Les points gris restent sans groupe. »

### 5. K=1 : des boules qui se rejoignent

« On place une boule autour de chaque point. Quand les boules grandissent et se touchent, les groupes se rejoignent. Un chemin de contacts suffit à les relier. Ici, les six points finissent dans une seule région. Le dessin en dessous garde l'histoire de cette fusion. »

### 6. K=2 : les zones couvertes deux fois

« Maintenant, on garde les endroits couverts par au moins deux boules : ce sont les lentilles bleues. Quand le rayon augmente, on voit sept zones, puis trois, puis une seule. Avec les mêmes points, cette règle fait apparaître une autre organisation. »

« K compte les points proches d'une position dans l'espace. Ce n'est pas le nombre de groupes que nous cherchons. »

### 7. HGP : conserver toute la hiérarchie

« Les regroupements changent avec l'échelle. Nous conservons toute leur histoire : quelles petites pièces apparaissent et quand elles se réunissent. HGP généralise le lien simple avec des interactions entre plusieurs points. »

« Dans ce diagramme, des groupes peuvent partager des points. C et D apparaissent dans plusieurs branches. »

### 8. Les regroupements en mouvement

« Le haut montre HGP, le bas HDBSCAN. L'échelle change pendant la vidéo. On regarde si les objets restent séparés ou s'ils se rejoignent. Ici, A est un piéton et B et C sont des vélos. »

*Lancer le montage. Il contient quatre scènes, sans son, avec les légendes d'origine en anglais.*

### 9. Les artefacts d'un capteur LiDAR

« Une même voiture ne donne pas le même nuage quand elle est proche ou loin du capteur. De loin, on a moins de points et davantage d'espace entre eux. Pourtant, c'est toujours la même voiture. Nous cherchons à retrouver sa forme malgré ces différences de mesure. »

« À droite, la reconstruction est plus grossière. La géométrie pourrait donner une description plus stable que le seul échantillonnage : c'est une piste que nous voulons explorer. »

### 10. Perspective : des pièces géométriques pour l'IA

« Les modèles de langage travaillent sur des morceaux de texte. Pour la 3D, nous proposons des pièces géométriques : leur forme, leur taille, leur voisinage et la manière dont elles se réunissent. Nous voulons tester si cette organisation aide une IA à apprendre. »

### 11. Percolia

« Avec Alban Hauseux, nous avons cofondé Percolia et rejoint l'Inria Startup Studio en octobre. Nous développons des outils pour exploiter la géométrie des données 3D. »

« Le QR code mène à notre page LinkedIn, pour suivre le projet et retrouver nos actualités. »

### 12. Bibliographie

« Voici quelques références pour approfondir les méthodes de clustering et HGP, dont nos deux articles. »

## Pour les ingénieurs

### Scène navale : données et protocole

Le scan original contient 2 321 251 points. La région étudiée en contient 330 543. Les vues fixes et les animations affichent un point sur quatre, soit 82 636 points d'origine ; le calcul traite tous les points résiduels.

Le modèle de référence comporte 14 infrastructures CAD : les 13 structures associées aux boîtes OFF, plus `Cube_3`. Le filtrage précède le calcul v12 :

- 290 878 points sont compatibles avec les 14 boîtes alignées sur les axes : min/max des 13 OFF et boîte CAD de `Cube_3` élargie de 3 cm.
- Parmi les points restants, 15 791 sont à au plus 3 cm des 104 triangles du fond CAD connu.
- Les 23 874 résidus sont quantifiés sur 21 bits et traités par Morse HGP 3D v12 pour la tour complète K=1 à K=3.

La coupe fermée de K=3 au rayon de 4 cm est projetée sur les points par une union externe des incidences fortes. Le seuil de 200 points retient cinq couvertures natives disjointes, soit 23 784 points ; 90 résidus restent gris. Le préfiltrage et cette projection sont réalisés autour du moteur v12 ; la couverture de points obtenue est expérimentale, distincte d'une hiérarchie native des points Hr.

Le rouge indique la compatibilité avec les boîtes, qui peuvent aussi couvrir une partie d'un ajout. Le gris représente le fond connu ou les résidus non retenus. Les géométries et étiquettes des ajouts sont exclues du filtrage, de la sélection des groupes et des couleurs. Les seuils de 3 cm, 4 cm et 200 points décrivent cette démonstration ; la qualité de détection demanderait une évaluation dédiée.

La hiérarchie native porte sur les résidus quantifiés. Les figures utilisent leurs coordonnées originales. Le protocole et les paramètres sont dans `naval_v12_report.json` ; `naval_v12/result.npz` conserve les coordonnées et indices d'origine. L'export complet, les appartenances et les scripts de reproduction sont dans `naval_v12/`. Un rejeu complet a reproduit les empreintes et les appartenances.

### K=1 et K=2

À K=1, \(E_1(r)=\bigcup_i B(x_i,r)\). Deux boules se touchent dès que \(\|x_i-x_j\|\leq 2r\). C'est la hiérarchie du lien simple, avec une distance égale à deux fois le rayon. Dans l'exemple, les sept plus courtes paires ont toutes distance 2,4 : les six composantes fusionnent simultanément à r=1,2.

Plus généralement, \(E_K(r)=\{y:\#\{i:\|y-x_i\|\leq r\}\geq K\}\). Il correspond au superniveau de l'estimateur de densité K-NN après changement de variable entre densité et rayon. À K=2, les composantes sont des unions de lentilles dont le rattachement dépend des recouvrements, notamment des intersections triples. Au stade intermédiaire, les trois groupes sont ABC, CD et DEF. Les conventions de K et de `min_samples` dans DBSCAN/HDBSCAN diffèrent.

### Hiérarchies, vidéo et perspectives

Les hauteurs du diagramme HGP sont schématiques : elles indiquent l'ordre des fusions. Les groupes géométriques doivent ensuite être interprétés pour reconnaître les objets.

La vidéo compare des groupes présents dans les hiérarchies, avec un niveau choisi pour chaque objet. Les trois premières scènes retirent le sol avec Patchwork++ et conservent le voisinage. La quatrième isole les instances à partir des étiquettes de référence. Les coches viennent de la comparaison aux objets annotés. Une comparaison générale de performance demanderait un benchmark dédié.

La variation de l'échantillonnage avec la portée motive l'étude d'une représentation géométrique plus stable. Le modèle de fondation 3D guidé par HGP et son association avec un modèle de langage sont des perspectives de recherche.

## Références et crédits

- J. A. Hartigan, *Clustering Algorithms*, Wiley, 1975.
- G. Biau et L. Devroye, *Lectures on the Nearest Neighbor Method*, Springer, 2015.
- L. Hauseux, K. Avrachenkov, J. Zerubia, [Generalization of single-linkage with higher-order interactions](https://doi.org/10.1007/s41109-025-00756-1), Applied Network Science, 2026.
- L. Hauseux, K. Avrachenkov, J. Zerubia, [Benefits of hypergraphs for density-based clustering](https://doi.org/10.23919/EUSIPCO63174.2024.10715271), EUSIPCO, 2024.
- R. Campello, D. Moulavi, J. Sander, *Density-Based Clustering Based on Hierarchical Density Estimates*, PAKDD, 2013.
- Scène navale synthétique : Marie Aspro, © Naval Group. [AYANA 2025, section 7.7](https://radar.inria.fr/report/2025/ayana/index.html#AYANA-RA-2025_label_NavalResult) : application LiDAR ; [ACENTAURI 2025, section 9.1.1](https://radar.inria.fr/report/2025/acentauri/index.html) : projet « Usine du Futur » avec Naval Group.
- `naval_assets.json`, `naval_reference_components.json` et `naval_video_assets.json` : données, modèle et paramètres des vues ; `naval_v12_report.json` : méthode et résultats v12.
- Vidéo et définition HGP : [E-HGP, Zoltan](https://github.com/Ludwig-H/E-HGP/tree/ac2d5bab814e84db6e1c9340f54995aa9cda58aa/Zoltan/demos/videos_hgp_hdbscan), [définition HGP 3D](https://github.com/Ludwig-H/E-HGP/blob/ac2d5bab814e84db6e1c9340f54995aa9cda58aa/docs/math/DEFINITION_HGP_3D.md).
- A. Geiger et al., *Are we ready for Autonomous Driving? The KITTI Vision Benchmark Suite*, CVPR, 2012. [KITTI](https://www.cvlibs.net/datasets/kitti/).
- J. Behley et al., *SemanticKITTI: A Dataset for Semantic Scene Understanding of LiDAR Sequences*, ICCV, 2019. [SemanticKITTI](https://www.semantic-kitti.org/).
