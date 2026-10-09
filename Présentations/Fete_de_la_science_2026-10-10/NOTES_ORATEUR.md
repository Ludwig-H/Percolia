# Des points aux objets

Présentation de Louis Hauseux, Percolia avec Alban Hauseux, Fête de la science, Antibes Juan-les-Pins, 10 octobre 2026.

## Une conversation de cinq minutes

Les diapositives 1 à 7, 9 et 10 se racontent en cinq à six minutes. La vidéo ajoute environ une minute quarante. Pour un visiteur pressé : 2 et 3, puis 5 et 6, et la vidéo. Pour un enfant : montrer les groupes, faire suivre les contacts entre les disques du doigt et demander ce qu'un robot pourrait reconnaître.

### 1. Des points aux objets

« Une machine peut mesurer des millions de points sans savoir ce qu'elle regarde. Comment passer de ces points à des objets ? C'est une question que j'ai étudiée pendant ma thèse et que nous poursuivons avec mon frère Alban dans Percolia. »

### 2. Le LiDAR : observer avant d'expliquer

« Un LiDAR envoie de la lumière et mesure des distances. Chaque mesure donne un point dans l'espace. En haut, le nuage brut ; en bas, le modèle théorique. On regarde la même scène du dessus et de côté. Quels objets sont présents dans le scan mais absents du modèle ? »

Laisser quelques secondes au public pour comparer les vues et proposer une réponse. Garder l'explication pour la diapositive suivante. Les deux colonnes présentent deux projections de la même région ; pour chaque colonne, le scan et le modèle ont le même cadrage.

Le fichier source `scan_lidar.ply` contient **2 321 251 points** avant cadrage. Le modèle reprend 14 infrastructures du maillage CAD `bloc_full.ply` : les 13 références OFF, plus `Cube_3` identifié dans le CAD. La région étudiée contient 330 543 points ; un point sur quatre est affiché, soit 82 636 points communs aux huit images. Cet allègement visuel ne réduit pas les données utilisées par le calcul. La question montre des points gris, sans réutiliser les étiquettes de segmentation.

### 3. Repérer les objets ajoutés

« Le modèle nous indique où se trouvent les structures attendues. Nous regroupons les points qui restent. Le rouge est compatible avec le modèle ; les autres couleurs montrent les groupes repérés. On retrouve les deux mêmes vues. »

En haut : le nuage regroupé. En bas : les structures du modèle, avec les points des groupes repérés. Les couleurs des groupes restent les mêmes entre les deux vues. Le rouge représente la compatibilité avec les priors ; les boîtes peuvent aussi couvrir des portions d'objets ajoutés. Le gris représente le fond connu ou des résidus non retenus par la coupe. Les groupes colorés proviennent des résultats calculés sur les points résiduels. La vue du bas superpose ces points aux structures du modèle de référence.

**Pour les ingénieurs :** les priors sont appliqués avant le calcul : 290 878 points sont compatibles avec les 14 boîtes alignées sur les axes (min/max des 13 OFF ; boîte CAD de `Cube_3` élargie de 3 cm). Parmi les points restants, 15 791 se trouvent à au plus 3 cm des 104 triangles du fond CAD connu. Les 23 874 résidus sont tous quantifiés sur 21 bits et traités par le code Morse HGP 3D v12 inchangé, pour la tour complète K=1 à K=3.

La coupe fermée de K=3 au rayon de 4 cm est projetée sur les points par une union externe des incidences fortes. Le seuil de 200 points conserve cinq couvertures natives disjointes, totalisant 23 784 points ; 90 résidus restent gris. V12 n'offre pas d'API native de priors ni de hiérarchie des points Hr. Cette projection expérimentale des composantes continues est une étape externe. Les seuils de 3 cm, 4 cm et 200 points sont les paramètres de cette démonstration. Cinq groupes ne suffisent pas à certifier l'exactitude d'une détection d'anomalies.

Aucune géométrie d'anomalie ni étiquette de vérité terrain n'entre dans les priors, la sélection ou les couleurs. Le protocole, les paramètres, la révision du code et les limites figurent dans `naval_v12_report.json`, aussi copié dans `naval_v12/`. Les coordonnées et indices d'origine sont conservés dans `naval_v12/result.npz`. L'export natif complet et les scripts de reproduction sont livrés dans ce même dossier ; un rejeu complet a reproduit les empreintes et les appartenances.

Il s'agit du benchmark synthétique de chantier naval fourni par Marie Aspro, © Naval Group. Le projet industriel « Usine du Futur » a été testé à Lorient ; cette scène ne désigne pas un navire ou un compartiment précis du site.

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
- `naval_assets.json` et `naval_reference_components.json` : fichiers 3D d'origine, sélection du modèle, empreintes et paramètres des deux angles ; `render_naval_views.py` et `render_naval.py` : génération des vues.
- `naval_v12_report.json` et `naval_v12/` : révision Morse HGP v12, hiérarchie, prétraitement par les références géométriques et protocole de projection externe.
- Vidéos, protocole et définition HGP : [E-HGP, Zoltan](https://github.com/Ludwig-H/E-HGP/tree/ac2d5bab814e84db6e1c9340f54995aa9cda58aa/Zoltan/demos/videos_hgp_hdbscan), [définition HGP 3D](https://github.com/Ludwig-H/E-HGP/blob/ac2d5bab814e84db6e1c9340f54995aa9cda58aa/docs/math/DEFINITION_HGP_3D.md).
- A. Geiger et al., *Are we ready for Autonomous Driving? The KITTI Vision Benchmark Suite*, CVPR, 2012. [KITTI](https://www.cvlibs.net/datasets/kitti/).
- J. Behley et al., *SemanticKITTI: A Dataset for Semantic Scene Understanding of LiDAR Sequences*, ICCV, 2019. [SemanticKITTI](https://www.semantic-kitti.org/).
