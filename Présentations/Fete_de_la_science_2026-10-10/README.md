# Fête de la science, Antibes Juan-les-Pins, 10 octobre 2026

**Des points aux objets : apprendre aux machines à comprendre la 3D**

Louis Hauseux présente ses travaux de thèse et Percolia, cofondée avec Alban Hauseux à l'Inria Startup Studio. Présentation en français pour le grand public, sur le stand 3IA du Village des Sciences et de l'Innovation, Antipolis Palais des Congrès, 60 chemin des Sables.

## Projection

1. Télécharger `Fete_de_la_science_2026_Percolia_hors_connexion.zip` et le décompresser entièrement.
2. Ouvrir `lecteur.html`. Les diapositives et les vidéos fonctionnent hors connexion.
3. Naviguer avec les flèches ou la barre d'espace. **Plein écran** permet la projection ; **Boucle stand** fait défiler les pages et laisse les vidéos se terminer.

**Question 3D** et **Réponse 3D** ouvrent les animations du chantier naval aux pages 2 et 3 : points à gauche, modèle à droite. **Revenir à la diapositive** retrouve les vues fixes.

Le PDF permet une projection classique. Le lien de la page 8 ouvre le montage HGP–HDBSCAN lorsque le lecteur PDF accepte les fichiers locaux. Les MP4 peuvent aussi être ouverts directement dans `videos/`.

Prévoir environ six minutes d'explication, puis 1 min 41 s pour le montage HGP–HDBSCAN. Les animations navales durent 12 secondes chacune. `NOTES_ORATEUR.md` propose le fil oral et des précisions pour les ingénieurs. Pour un échange court : pages 2 et 3, puis 5 et 6, et la vidéo.

## Contenu

| Page | Sujet |
|---|---|
| 1 | Des points aux objets |
| 2 | Le LiDAR : une scène en points |
| 3 | Repérer les objets ajoutés |
| 4 | Le clustering : regrouper les points |
| 5 | K=1 : des boules qui se rejoignent |
| 6 | K=2 : les zones couvertes deux fois |
| 7 | HGP : conserver toute la hiérarchie |
| 8 | Les regroupements en mouvement |
| 9 | Les artefacts d'un capteur LiDAR |
| 10 | Perspective : des pièces géométriques pour l'IA |
| 11 | Percolia — Louis et Alban Hauseux, cofondateurs |
| 12 | Bibliographie |

## Vidéos et crédits

`videos/hgp_vs_hdbscan_light.mp4` compare HGP et HDBSCAN sur quatre scènes. H.264, 1080 × 1350, 30 images/s, 100,7 s, sans son ; légendes anglaises. Source : `E-HGP/Zoltan/demos/videos_hgp_hdbscan/reseaux_sociaux/LinkedIn/`, révision `ac2d5bab814e84db6e1c9340f54995aa9cda58aa`. L'URL et l'empreinte sont dans `external_assets.json`.

Les groupes présentés sont choisis dans les hiérarchies, avec un niveau adapté à chaque objet. Les trois premières scènes retirent le sol avec Patchwork++ ; la quatrième utilise les étiquettes de référence pour isoler les instances. Les coches comparent les groupes aux objets annotés. Une comparaison générale de performance demanderait un benchmark dédié.

Crédits : KITTI, Geiger et al., CVPR 2012 ; SemanticKITTI, Behley et al., ICCV 2019. Les conditions des données originales s'appliquent aux vidéos dérivées : KITTI, CC BY-NC-SA 3.0 ; SemanticKITTI, CC BY-NC-SA 4.0. Respecter les attributions et les restrictions d'utilisation des sources lors d'une réutilisation.

`videos/naval_chantier_question.mp4` montre le nuage brut à gauche et les 14 infrastructures du modèle à droite. `videos/naval_chantier_solution.mp4` suit la même orbite, avec les groupes v12 colorés à gauche et le même modèle à droite. Les panneaux partagent la même caméra à chaque instant. H.264, 1600 × 900, 24 images/s, 12 s, sans son. Scène synthétique fournie par Marie Aspro, © Naval Group.

Les animations utilisent les coordonnées originales sauvegardées dans `naval_v12/result.npz`, le maillage `naval_v12/bloc_full.ply` et la sélection CAD de référence. `naval_video_assets.json` décrit les sources, la caméra et les fichiers produits.

## Méthode de la scène navale

Les pages 2 et 3 montrent la même région en projections orthographiques XY et XZ. Le scan original contient 2 321 251 points ; la région étudiée en contient 330 543. Les vues affichent un point sur quatre, soit 82 636 points d'origine. Le calcul traite tous les points résiduels.

Le modèle comporte 14 infrastructures CAD : les 13 structures associées aux boîtes OFF et `Cube_3`. Les composants retenus sont décrits dans `naval_reference_components.json`. Le protocole est le suivant :

1. Filtrer les points compatibles avec 14 boîtes alignées sur les axes : min/max des 13 OFF, plus la boîte CAD de `Cube_3` avec une marge de 3 cm.
2. Retirer le fond connu à une distance d'au plus 3 cm des 104 triangles CAD `Background`.
3. Quantifier les 23 874 résidus sur 21 bits et calculer la tour Morse HGP 3D v12 complète pour K=1 à K=3.
4. Couper les composantes continues de K=3 au rayon fermé de 4 cm et les projeter sur les points par union des incidences fortes. Retenir les couvertures d'au moins 200 points d'origine.

| Étape | Points |
|---|---:|
| Région étudiée | 330 543 |
| Compatibles avec les boîtes du modèle | 290 878 |
| Fond connu retiré ensuite | 15 791 |
| Résidus traités par v12 | 23 874 |
| Cinq couvertures retenues, disjointes | 23 784 |
| Autres résidus | 90 |

Le préfiltrage et la projection vers les points sont externes au moteur v12. Cette couverture expérimentale des composantes continues est distincte d'une hiérarchie native des points Hr. Le rouge indique la compatibilité avec les boîtes, qui peuvent aussi couvrir une partie d'un ajout ; le gris représente le fond connu ou les résidus non retenus. Les géométries et étiquettes des ajouts sont exclues du filtrage, de la sélection et des couleurs. Les seuils décrivent cette démonstration ; la qualité de détection demanderait une évaluation dédiée.

`naval_v12_report.json` donne la révision du moteur, le protocole et les paramètres. `naval_v12/` contient aussi les coordonnées originales, les appartenances de la coupe, l'export complet `full.bin.gz` et les scripts de reproduction. `SHA256SUMS.txt` permet de vérifier les fichiers du kit.

## Compilation et reproduction

Les sources des schémas sont éditables en TikZ. Le thème est le **template Inria 2024** de la présentation EUVIP de Louis, révision `875202c0a9aa6cd11b001469d65ee7635459d3dd` du dépôt `Generalized-Frangi-for-Automatic-Crack-Extraction-on-FIND-dataset`. Latin Modern est la police utilisée lorsque `inriafontes` est absent.

Depuis un clone complet de Percolia :

```sh
cd Présentations/Fete_de_la_science_2026-10-10
python3 build.py
```

Dépendances : Python 3, pdfLaTeX, Beamer/TikZ, babel français, Latin Modern, QRcode, Poppler et FFmpeg. `build.py` compile le PDF à partir des sources et des animations présentes, vérifie les fichiers puis prépare le kit. Le workflow `.github/workflows/fete-science.yml` produit les animations et publie les livrables sur `main`.

Pour refaire les animations :

```sh
python3 render_naval_video.py --result naval_v12/result.npz --model naval_v12/bloc_full.ply --components naval_reference_components.json --output-dir videos --manifest naval_video_assets.json
```

Le rendu demande NumPy, Pillow, Matplotlib, DejaVu et un compilateur C++. Les paramètres et empreintes sont dans `naval_video_assets.json`.

`render_naval_views.py` produit les vues fixes avec les fonctions de lecture de `render_naval.py`. Le scan complet est nécessaire pour refaire le filtrage initial ; les données et paramètres sont décrits dans `naval_assets.json` et les manifestes de `naval_v12/`.

Pour rejouer le moteur sur les résidus sauvegardés : `python3 naval_v12/reproduce.py`. Cela demande NumPy et un compilateur C++20. Le script récupère les sources épinglées, ou accepte `--source-dir` pour des sources déjà téléchargées. Un rejeu complet a reproduit les empreintes et les appartenances.

## Événement

- [Programme de la Ville d'Antibes](https://www.antibes-juanlespins.com/information/agenda/village-des-sciences-et-de-linnovation-2026).
- [Programme 3IA](https://3ia.univ-cotedazur.eu/fete-de-la-science-2026-in-juan-les-pins).

Le village ouvre samedi 10 octobre de 13 h à 19 h et dimanche 11 octobre de 10 h à 18 h. Entrée gratuite.
