# Des points aux objets

Présentation de Louis Hauseux, Percolia avec Alban Hauseux, Fête de la science, Antibes Juan-les-Pins, 10 octobre 2026.

## Une conversation de cinq minutes

Les diapositives 1 à 7, 9 et 10 se racontent en cinq à six minutes. La vidéo ajoute environ une minute quarante. Pour un visiteur pressé : 2 et 3, puis 5 et 6, et la vidéo. Pour un enfant : montrer les groupes, faire suivre les contacts entre les disques du doigt et demander ce qu'un robot pourrait reconnaître.

### 1. Des points aux objets

« Une machine peut mesurer des millions de points sans savoir ce qu'elle regarde. Comment passer de ces points à des objets ? C'est une question que j'ai étudiée pendant ma thèse et que nous poursuivons avec mon frère Alban dans Percolia. »

### 2. Le LiDAR : observer avant d'expliquer

« Un LiDAR envoie de la lumière et mesure des distances. Chaque mesure donne un point dans l'espace. À gauche, le nuage de points brut ; à droite, le modèle théorique de la scène. Quels objets sont présents dans le scan mais absents du modèle ? »

Laisser quelques secondes au public pour comparer les deux vues. Demander ce qu'il remarque et où il chercherait. Garder la réponse pour la diapositive suivante ; ne pas montrer ni désigner à l'avance les objets ajoutés. Les deux vues utilisent le même point de vue pour faciliter cette comparaison.

Le fichier source `scan_lidar.ply` contient **2 321 251 points**, avant le cadrage et l'échantillonnage utilisés pour l'illustration. Les deux vues montrent la même portion de la scène. Le modèle de référence reprend les structures du maillage `bloc_full.ply` qui correspondent aux treize boîtes OFF fournies. La provenance, la sélection des structures et les paramètres de caméra figurent dans `naval_assets.json`. Le scan est affiché en couleur neutre, sans réutiliser les étiquettes de segmentation.

### 3. Repérer les objets ajoutés

« Voici ce que le regroupement des points permet de faire apparaître. Le rouge correspond au modèle. Les autres couleurs isolent les objets ajoutés. On peut maintenant les examiner un par un. »

La figure de résultat est celle du poster 3IA : **benchmark synthétique de chantier naval**, deux millions de points. Rouge : points conformes au modèle de référence ; autres couleurs : objets ajoutés ; gris : fond. Travaux avec Marie Aspro, à l'Inria Startup Studio. Crédit : © Naval Group. La comparaison au modèle guide la segmentation ; les couleurs ne sont pas des catégories apprises comme « voiture » ou « arbre ».

« Deux millions » est l'ordre de grandeur donné dans le poster et le rapport AYANA ; le fichier de scan utilisé pour les vues d'entrée contient précisément 2 321 251 points.

Le projet industriel de Marie, « Usine du Futur », a été testé sur le site Naval Group de Lorient. Cette illustration HGP porte sur un benchmark synthétique : ne pas l'attribuer à un navire ou à un compartiment précis de Lorient.

### 4. Le clustering

« Une première étape consiste à regrouper les points proches. On appelle cela le clustering. On peut le faire avec de la géométrie, avant même d'apprendre les mots “voiture” ou “arbre”. Un groupe de points et un objet reconnu sont deux étapes différentes. »

La figure est l'exemple HDBSCAN déjà utilisé dans le poster, pas une sortie HGP. Les points gris n'ont pas reçu de groupe.

### 5. Le cas K=1

« Imaginons une petite boule autour de chaque point. Quand les boules grandissent et se touchent, les groupes se rejoignent. On peut suivre un chemin de contacts d'un bout à l'autre. Ici, un petit pont suffit à réunir les deux ensembles. »

Faire suivre le chemin B–C–D–F. À gauche, six boules séparées. À droite, une seule région reliée. Le dessin en dessous garde l'histoire de leur fusion.

**Pour les ingénieurs :** l'ensemble est \(E_1(r)=\bigcup_i B(x_i,r)\). Deux boules se touchent dès que \(\|x_i-x_j\|\leq 2r\). C'est la hiérarchie du lien simple, avec une échelle de distance égale à deux fois le rayon. Sur ces six points précis, les sept plus courtes paires ont toutes distance 2,4 : les six composantes fusionnent simultanément à r=1,2. Il n'y a pas de niveau intermédiaire à deux groupes.

### 6. Le cas K=2

« Maintenant, on change la règle : on garde les endroits couverts par au moins deux boules. Ce sont les petites lentilles bleues. Quand le rayon augmente, on voit sept zones, puis trois, puis une seule. Les mêmes points font apparaître une autre organisation. »

Bien montrer que la lentille du milieu reste une zone distincte au stade intermédiaire : les trois groupes sont ABC, CD et DEF. Le paramètre K compte les points proches **d'une position de l'espace**, pas un nombre de classes à reconnaître. La règle ne garantit pas que tous les ponts entre objets disparaissent.

**Pour les ingénieurs :** \(E_K(r)=\{y:\#\{i:\|y-x_i\|\leq r\}\geq K\}\). C'est le superniveau de l'estimateur de densité K-NN après changement de variable entre densité et rayon. À K=2, les composantes sont des unions de lentilles. Leur rattachement nécessite des recouvrements, notamment des intersections triples. Ne pas assimiler directement K au `min_samples` de toutes les bibliothèques DBSCAN/HDBSCAN : leurs conventions diffèrent.

### 7. La hiérarchie HGP

« Choisir une seule taille de groupe oblige à choisir une seule échelle. Nous conservons toute l'histoire : quelles petites pièces apparaissent, et quand elles se réunissent. HGP généralise le lien simple avec des interactions entre plusieurs points. »

Le diagramme de droite représente des groupes qui peuvent partager des points. C et D apparaissent dans plusieurs branches. Les hauteurs sont schématiques : on compare l'ordre des fusions, pas des valeurs numériques mesurées sur les axes du dessin. HGP calcule la hiérarchie exacte du modèle géométrique choisi, ce qui ne suffit pas à garantir une reconnaissance sémantique parfaite dans toutes les scènes.

### 8. La vidéo

« Le haut montre HGP, le bas HDBSCAN. L'échelle change pendant la vidéo. On regarde si les objets restent séparés ou s'ils se rejoignent trop tôt. Ici, A est un piéton et B et C sont des vélos. »

Les versions claire et sombre sont le **même montage**, avec quatre scènes. Choisir une seule version pendant l'explication. Le montage dure 100,7 secondes, sans son. Les légendes d'origine sont en anglais.

Ce sont des exemples de groupes présents dans les hiérarchies, avec un niveau choisi pour chaque objet, et non une segmentation finale automatiquement sélectionnée. Les trois premières scènes retirent le sol avec Patchwork++ et conservent le voisinage. La quatrième isole les instances à partir des étiquettes de référence. Les coches proviennent de la comparaison aux objets annotés. Ces scènes illustrent des comportements, sans établir une supériorité générale de HGP.

### 9. Les pièces pour l'IA

« Les modèles de langage travaillent sur des morceaux de texte. Pour la 3D, nous proposons des pièces géométriques : leur forme, leur taille, leur voisinage et la manière dont elles se réunissent. Nous voulons tester si cette organisation aide une IA à apprendre. »

Le schéma représente des morceaux de surface qui se réunissent. Le modèle de fondation 3D guidé par HGP est une **piste de recherche**. Aucun résultat d'apprentissage n'est revendiqué ici. L'association avec un modèle de langage est une perspective pour dialoguer avec des robots sur leur environnement.

### 10. Percolia

« Avec Alban, nous avons rejoint l'Inria Startup Studio en octobre. Nous développons des outils pour exploiter la géométrie des données 3D. Notre ambition est de contribuer à des machines qui comprennent mieux ce qu'elles voient. Qu'aimeriez-vous apprendre à un robot à reconnaître ? »

Le QR code mène à la page LinkedIn de Percolia.

## Sources

- Poster Scientific Days 3IA : `../Posters/3IA_Days_2026/poster.tex`, état Percolia `d0214d0a38dbb4c97c2e872e19891df16cc82a88`.
- J. A. Hartigan, *Consistency of single linkage for high-density clusters*, JASA, 1981.
- G. Biau et L. Devroye, *Lectures on the Nearest Neighbor Method*, Springer, 2015.
- L. Hauseux, K. Avrachenkov, J. Zerubia, [Generalization of single-linkage with higher-order interactions](https://doi.org/10.1007/s41109-025-00756-1), Applied Network Science, 2026.
- L. Hauseux, K. Avrachenkov, J. Zerubia, [Benefits of hypergraphs for density-based clustering](https://doi.org/10.23919/EUSIPCO63174.2024.10715271), EUSIPCO, 2024.
- R. Campello, D. Moulavi, J. Sander, *Density-Based Clustering Based on Hierarchical Density Estimates*, PAKDD, 2013.
- [Rapport d'activité AYANA 2025, section 7.7](https://radar.inria.fr/report/2025/ayana/index.html#AYANA-RA-2025_label_NavalResult) : application LiDAR du poster.
- [Rapport d'activité ACENTAURI 2025, section 9.1.1](https://radar.inria.fr/report/2025/acentauri/index.html) : projet « Usine du Futur » avec Naval Group et validation à Lorient.
- `naval_assets.json` : fichiers 3D d'origine, empreintes et paramètres des deux vues d'entrée ; `render_naval.py` : génération des vues sans étiquettes de segmentation.
- Vidéos, protocole et définition HGP : [E-HGP, Zoltan](https://github.com/Ludwig-H/E-HGP/tree/ac2d5bab814e84db6e1c9340f54995aa9cda58aa/Zoltan/demos/videos_hgp_hdbscan), [définition HGP 3D](https://github.com/Ludwig-H/E-HGP/blob/ac2d5bab814e84db6e1c9340f54995aa9cda58aa/docs/math/DEFINITION_HGP_3D.md).
- A. Geiger et al., *Are we ready for Autonomous Driving? The KITTI Vision Benchmark Suite*, CVPR, 2012. [KITTI](https://www.cvlibs.net/datasets/kitti/).
- J. Behley et al., *SemanticKITTI: A Dataset for Semantic Scene Understanding of LiDAR Sequences*, ICCV, 2019. [SemanticKITTI](https://www.semantic-kitti.org/).
