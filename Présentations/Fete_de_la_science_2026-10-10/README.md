# Fête de la science, Antibes Juan-les-Pins, 10 octobre 2026

**Des points aux objets : apprendre aux machines à comprendre la 3D**

Louis Hauseux présente les travaux de sa thèse et le projet Percolia développé avec Alban Hauseux à l'Inria Startup Studio. Présentation en français pour le grand public, sur le stand 3IA au Village des Sciences et de l'Innovation, Antipolis Palais des Congrès, 60 chemin des Sables.

## Projection

1. Télécharger `Fete_de_la_science_2026_Percolia_hors_connexion.zip` et le décompresser entièrement.
2. Ouvrir `lecteur.html` dans un navigateur. Les diapositives et vidéos fonctionnent hors connexion.
3. Utiliser les flèches ou la barre d'espace. Le bouton plein écran permet la projection. La boucle « stand » défile automatiquement et laisse la vidéo aller jusqu'au bout.

Le PDF `Fete_de_la_science_2026_Percolia.pdf` permet une projection classique. À la diapositive 8, les liens ouvrent les MP4 si le lecteur PDF accepte les liens vers des fichiers locaux. Sinon, ouvrir directement les fichiers du dossier `videos/`. Le lecteur HTML assure la lecture sans dépendre des capacités multimédias du lecteur PDF.

Dix diapositives, environ cinq à six minutes d'explication, puis 1 min 41 s de vidéo. Les notes sont dans `NOTES_ORATEUR.md`. Pour une explication courte, utiliser les pages 2 et 3, puis 5 et 6, et la vidéo.

## Contenu

| Page | Sujet |
|---|---|
| 1 | Des points aux objets, Percolia et Inria |
| 2 | Nuage LiDAR brut et modèle théorique, vus du dessus et de côté |
| 3 | Groupes Morse HGP v12 et comparaison au modèle, aux mêmes angles |
| 4 | Regrouper les points |
| 5 | K=1, union des boules et lien simple |
| 6 | K=2, zones couvertes deux fois |
| 7 | La hiérarchie HGP |
| 8 | Démonstrations vidéo HGP et HDBSCAN |
| 9 | Perspective : pièces géométriques pour l'IA |
| 10 | Percolia avec Louis et Alban, QR LinkedIn |

## Les deux vidéos

`videos/hgp_vs_hdbscan_light.mp4` et `videos/hgp_vs_hdbscan_dark.mp4` sont les variantes claire et sombre du **même montage** de quatre scènes, avec légendes anglaises. Format H.264, 1080 × 1350, 30 images/s, 100,7 s, sans son.

Sources : `E-HGP/Zoltan/demos/videos_hgp_hdbscan/reseaux_sociaux/LinkedIn/`, révision `ac2d5bab814e84db6e1c9340f54995aa9cda58aa`. Les empreintes et URLs précises sont dans `external_assets.json`. Les fichiers copiés sont inchangés.

Ces scènes illustrent des groupes présents dans les hiérarchies. Le niveau est choisi pour chaque objet et la quatrième scène utilise les étiquettes pour isoler les instances. Le montage ne constitue pas un résultat de segmentation finale automatiquement sélectionnée, ni un benchmark général. Le détail est dans les notes.

Crédits : KITTI, Geiger et al., CVPR 2012 ; SemanticKITTI, Behley et al., ICCV 2019. Les conditions des données originales s'appliquent aux vidéos dérivées : KITTI, CC BY-NC-SA 3.0 ; SemanticKITTI, CC BY-NC-SA 4.0. Respecter les attributions et les restrictions d'utilisation des sources lors d'une réutilisation.

## Sources et édition

La présentation adapte le [poster Scientific Days 3IA](../Posters/3IA_Days_2026/README.md), avec les figures d'origine en TikZ et un nouveau dessin exact pour K=1 sur les mêmes six points. Les sources des schémas restent éditables. Le cas K=1 fusionne les six points au même rayon : aucun palier artificiel à deux groupes n'a été ajouté.

Le thème est le **template Inria 2024**, repris de la présentation EUVIP de Louis, révision `875202c0a9aa6cd11b001469d65ee7635459d3dd` du dépôt `Generalized-Frangi-for-Automatic-Crack-Extraction-on-FIND-dataset`. Les quatre `.sty` sont conservés. La police Latin Modern est le remplacement prévu par ce thème lorsque le paquet `inriafontes` est absent, comme dans la source EUVIP.

`slides.tex` utilise certains actifs du poster voisin. Depuis un clone complet de Percolia, lancer :

```sh
cd Présentations/Fete_de_la_science_2026-10-10
python3 build.py
```

Dépendances : Python 3, pdfLaTeX, Beamer/TikZ, babel français, Latin Modern, QRcode, Poppler et FFmpeg. Les images du thème et les vidéos sont récupérées à des révisions précises, avec vérification SHA256. Le workflow `.github/workflows/fete-science.yml` compile, vérifie et publie les livrables sur `main`.

Les pages 2 et 3 montrent la même région sous deux projections orthographiques : vue du dessus (XY) et vue de côté (XZ). Le nuage brut et le modèle occupent les deux lignes de la question. La réponse montre les groupes de points calculés, puis le modèle superposé aux groupes repérés. Les cadrages restent identiques entre la question et la réponse pour chaque angle.

Le fichier `scan_lidar.ply` contient 2 321 251 points avant cadrage. Le modèle de référence reprend 14 infrastructures du maillage CAD `bloc_full.ply` : celles associées aux 13 boîtes OFF d'origine, plus `Cube_3`, identifié dans le CAD. La sélection est documentée dans `naval_assets.json` et `naval_reference_components.json`. Les huit images utilisent les mêmes 82 636 points d'origine, obtenus par un pas d'affichage de quatre dans les 330 543 points de la région étudiée. Cet allègement visuel intervient après le calcul. Le nuage de la question reste neutre, sans utiliser les étiquettes de segmentation pour sa couleur.

Les priors géométriques sont appliqués **avant** Morse HGP 3D v12, selon ce protocole :

1. Retirer les points compatibles avec 14 boîtes alignées sur les axes : règle min/max des 13 OFF d'origine, complétée par la boîte CAD de `Cube_3` avec une marge de 3 cm.
2. Retirer le fond connu : distance euclidienne d'au plus 3 cm aux 104 triangles CAD `Background`.
3. Quantifier les 23 874 points résiduels sur 21 bits, sans sous-échantillonnage, puis calculer la tour native complète pour K=1 à K=3 avec le code v12 inchangé.
4. Couper les composantes continues natives de K=3 au rayon fermé de 4 cm ; une union externe des incidences fortes les projette sur les points. Conserver les couvertures d'au moins 200 points d'origine.

| Étape | Points |
|---|---:|
| Région étudiée | 330 543 |
| Compatibles avec les boîtes du modèle | 290 878 |
| Fond connu retiré ensuite | 15 791 |
| Résidus réellement calculés par v12 | 23 874 |
| Cinq couvertures retenues, disjointes | 23 784 |
| Autres résidus | 90 |

Le préfiltrage et la projection sont externes : v12 n'a pas d'API native de priors ni de hiérarchie des points Hr. Les couleurs montrent des groupes candidats, pas une mesure d'exactitude de détection ; les boîtes peuvent aussi couvrir une partie d'un ajout. Le rouge indique la compatibilité avec les références, le gris le fond connu ou les résidus non retenus. Aucune géométrie d'anomalie ni étiquette de vérité terrain ne sert au filtrage, au choix des groupes ou aux couleurs. La hiérarchie native porte sur les résidus quantifiés ; l'affichage retrouve leurs coordonnées originales.

`naval_v12_report.json` conserve la révision `ac2d5bab814e84db6e1c9340f54995aa9cda58aa`, le protocole, les paramètres et les limites. Le même rapport est présent dans `naval_v12/`, avec `result.npz`, les appartenances de la coupe, l'export natif complet `full.bin.gz`, les scripts et les manifestes de reproduction. Le kit conserve tous ces fichiers ; `SHA256SUMS.txt` permet de contrôler chaque membre. Les deux illustrations 3D historiques sont aussi conservées pour que toutes les entrées de `naval_assets.json` soient vérifiables dans le kit.

`render_naval_views.py` produit les images à partir des données sources et des résultats calculés, avec les fonctions de lecture de `render_naval.py`. `naval_reference_components.json` conserve la sélection des composants CAD. Les sources 3D doivent être récupérées séparément pour refaire le filtrage et les images. Les commandes exactes, paramètres de caméra et versions des dépendances figurent dans `naval_assets.json`.

Pour rejouer le moteur sur les coordonnées résiduelles sauvegardées et vérifier l'export complet et les appartenances, lancer `python3 naval_v12/reproduce.py`. Cela demande NumPy et un compilateur C++20 ; le script récupère les sources CPU épinglées, ou accepte `--source-dir` pour un dossier déjà téléchargé. Ce rejeu a été vérifié jusqu'au bout avec les mêmes empreintes et appartenances. La compilation des slides et le workflow utilisent les PNG et résultats déjà calculés : ils vérifient les empreintes, dimensions et archives sans installer NumPy ni relancer le calcul 3D.

Les deux vidéos de la page 8 sont conservées dans leur version d'origine. Elles proviennent du dossier LinkedIn épinglé ci-dessus et restent distinctes de ce nouveau calcul v12 sur la scène navale.

Cette scène synthétique de chantier naval a été fournie par Marie Aspro, © Naval Group. Le projet industriel « Usine du Futur » de Marie a été testé à Lorient ; cette illustration ne désigne pas un navire ou un compartiment précis de ce site. Le modèle de fondation 3D guidé par la hiérarchie reste une perspective de recherche.

## Événement

- [Programme de la Ville d'Antibes](https://www.antibes-juanlespins.com/information/agenda/village-des-sciences-et-de-linnovation-2026).
- [Programme 3IA](https://3ia.univ-cotedazur.eu/fete-de-la-science-2026-in-juan-les-pins).

Le village ouvre samedi 10 octobre de 13 h à 19 h et dimanche 11 octobre de 10 h à 18 h. Entrée gratuite.
