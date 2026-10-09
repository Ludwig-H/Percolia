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
| 2 | Nuage LiDAR brut et modèle théorique : observer les différences |
| 3 | Repérer les objets ajoutés : résultat sur le chantier naval |
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

Les vues du nuage brut et du modèle théorique utilisent la même caméra et le même cadrage. Le fichier `scan_lidar.ply` contient 2 321 251 points avant cadrage et échantillonnage visuel. Les deux vues montrent la même portion de la scène. Le modèle de référence reprend les structures du maillage `bloc_full.ply` qui correspondent aux treize boîtes OFF fournies. Le nuage est montré dans une couleur neutre, sans étiquettes de segmentation. Leur provenance, les empreintes des fichiers, la sélection des structures et les paramètres de rendu sont conservés dans `naval_assets.json`. La compilation vérifie les PNG publiés ; elle ne nécessite pas l'accès aux fichiers 3D sur Google Drive.

`render_naval.py` permet de refaire ces deux vues depuis les fichiers 3D sources autorisés, avec NumPy, Matplotlib et Pillow. Pour cette scène, il utilise le nuage PLY, le maillage complet et les treize boîtes OFF pour sélectionner les structures du modèle de référence. Les fichiers sources doivent être récupérés séparément ; le kit de projection contient les images et leur provenance. Les paramètres exacts et versions des dépendances sont dans `naval_assets.json`, section `local_reproduction`.

```sh
NAVAL_SOURCES=/chemin/vers/naval_data
python3 render_naval.py \
  --raw "$NAVAL_SOURCES/scan_lidar.ply" \
  --model "$NAVAL_SOURCES/bloc_full.ply" \
  --reference-box-dir "$NAVAL_SOURCES/bounding_boxes" \
  --roi -3.4 3.4 -3.4 3.4 -0.09 3.1 \
  --azimuth 70 --elevation 20 --point-size .9 --point-alpha .8 --point-color '#39444c' --max-points 85000 \
  --width 1800 --height 1200
```

La figure de résultat est le benchmark synthétique du poster 3IA, avec deux millions de points, © Naval Group, travaux avec Marie Aspro (Inria Startup Studio). Le projet industriel « Usine du Futur » de Marie a été testé à Lorient ; cette illustration HGP ne désigne pas un navire ou un compartiment précis de ce site. Le modèle de fondation 3D guidé par la hiérarchie reste une perspective de recherche.

## Événement

- [Programme de la Ville d'Antibes](https://www.antibes-juanlespins.com/information/agenda/village-des-sciences-et-de-linnovation-2026).
- [Programme 3IA](https://3ia.univ-cotedazur.eu/fete-de-la-science-2026-in-juan-les-pins).

Le village ouvre samedi 10 octobre de 13 h à 19 h et dimanche 11 octobre de 10 h à 18 h. Entrée gratuite.
