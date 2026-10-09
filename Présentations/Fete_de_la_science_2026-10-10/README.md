# Fête de la science, Antibes Juan-les-Pins, 10 octobre 2026

**Des points aux objets : apprendre aux machines à comprendre la 3D**

Louis Hauseux présente les travaux de sa thèse et le projet Percolia développé avec Alban Hauseux à l'Inria Startup Studio. Présentation en français pour le grand public, sur le stand 3IA au Village des Sciences et de l'Innovation, Antipolis Palais des Congrès, 60 chemin des Sables.

## Projection

1. Télécharger `Fete_de_la_science_2026_Percolia_hors_connexion.zip` et le décompresser entièrement.
2. Ouvrir `lecteur.html` dans un navigateur. Les diapositives et vidéos fonctionnent hors connexion.
3. Utiliser les flèches ou la barre d'espace. Le bouton plein écran permet la projection. La boucle « stand » défile automatiquement et laisse la vidéo aller jusqu'au bout.

Le PDF `Fete_de_la_science_2026_Percolia.pdf` permet une projection classique. À la diapositive 7, les liens ouvrent les MP4 si le lecteur PDF accepte les liens vers des fichiers locaux. Sinon, ouvrir directement les fichiers du dossier `videos/`. Le lecteur HTML assure la lecture sans dépendre des capacités multimédias du lecteur PDF.

Neuf diapositives, environ cinq minutes d'explication, puis 1 min 41 s de vidéo. Les notes sont dans `NOTES_ORATEUR.md`. Pour une explication courte, utiliser les pages 2, 4 et 5, puis la vidéo.

## Contenu

| Page | Sujet |
|---|---|
| 1 | Des points aux objets, Percolia et Inria |
| 2 | LiDAR et exemple de chantier naval |
| 3 | Regrouper les points |
| 4 | K=1, union des boules et lien simple |
| 5 | K=2, zones couvertes deux fois |
| 6 | La hiérarchie HGP |
| 7 | Démonstrations vidéo HGP et HDBSCAN |
| 8 | Perspective : pièces géométriques pour l'IA |
| 9 | Percolia avec Louis et Alban, QR LinkedIn |

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

L'image du chantier naval est un benchmark synthétique de deux millions de points, © Naval Group, travaux avec Marie Aspro (Inria Startup Studio). Le modèle de fondation 3D guidé par la hiérarchie reste une perspective de recherche.

## Événement

- [Programme de la Ville d'Antibes](https://www.antibes-juanlespins.com/information/agenda/village-des-sciences-et-de-linnovation-2026).
- [Programme 3IA](https://3ia.univ-cotedazur.eu/fete-de-la-science-2026-in-juan-les-pins).

Le village ouvre samedi 10 octobre de 13 h à 19 h et dimanche 11 octobre de 10 h à 18 h. Entrée gratuite.
