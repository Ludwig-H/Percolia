# Poster scientifique — Journées 3IA 2026

[**PDF A0 portrait**](Poster_3IA_2026_Hauseux_A0.pdf) · [Source LaTeX](poster.tex)

[![Aperçu](apercu.png)](Poster_3IA_2026_Hauseux_A0.pdf)

**Higher-order clustering for 3D point clouds**  
Louis Hauseux · Konstantin Avrachenkov · Josiane Zerubia  
AI Cluster 3IA Côte d’Azur Days, 24–25 septembre 2026.

Une page **841 × 1189 mm**, à imprimer à **100 % / taille réelle**. Le gabarit Inria / Gemini est conservé. Tous les logos sont en bas : monogramme P de Percolia, puis 3IA principal entre Inria et DS4H. La bibliographie possède son propre bloc, en corps réduit. Les publications des auteurs sont signalées en rouge.

## L’exemple exact à six points

Les fichiers `figures/defense/` reprennent les **coordonnées et topologies de la soutenance**, et non un exemple de remplacement. Sources : [Soutenance/soutenance/figs](https://github.com/Ludwig-H/Manuscrit-de-th-se/tree/3593fbf25434c4715b37537eae1287bf49239fa7/Soutenance/soutenance/figs), dont les empreintes Git sont contrôlées dans `prepare_defense_figures.py`.

- `deuxnn_r_boules.tex`, `deuxnn_rp_boules.tex`, `deuxnn_rs_boules.tex` : les six points A–F et les trois étapes de recouvrement, **7 → 3 → 1** composantes.
- `comp_dendro_rsl.tex` : fusion plate du côté DBSCAN / Robust Single-Linkage.
- `comp_dendro_2nn.tex` : les sept branches AB, BC, AC, CD, DE, EF, DF ; fusion des triangles ABC et DEF à r′ ; CD reste isolé jusqu’à r″.

La longueur commune des sept arêtes courtes est 2r. Ainsi r′ = 2r/√3 et r″ = r√(2+√3). La hauteur du dendrogramme est schématique, comme dans les slides. L’axe DBSCAN explicite **ε = 2r**, le rayon de voisinage, plutôt que le rayon des boules ; cela corrige l’ambiguïté d’unité de la slide sans changer son arbre. K=2 désigne deux voisins autres que le point lui-même, soit `min_samples=3` dans DBSCAN de scikit-learn.

L’arbre 2-NN conserve volontairement les étiquettes de points répétées : il représente les composantes des recouvrements, qui peuvent partager des points de l’échantillon, et non une partition des six sommets. Pour l’identité de recouvrement, r₂(y) est le deuxième rang dans l’échantillon entier, avec des boules fermées.

`test_six_point_geometry.py` vérifie numériquement les composantes des intersections de disques et la fusion DBSCAN. Ce petit test ne constitue pas une implémentation de HGP.

## Perspective et application

La perspective reprend également les TikZ de la soutenance :

- `verrou_portee.tex` : **la même voiture proche et lointaine**, les nappes de balayage et les contours géométriques correspondants. Les seules modifications sont les textes anglais et les tailles de caractères.
- `hierarchie_surfaces.tex` : **le même arbre de pièces recollées**, avec les coutures de fusion en rouge. Géométrie, orientation, recollements et structure de l’arbre sont conservés.

Le bénéfice pour un modèle de fondation 3D reste présenté comme une **hypothèse**, pas un résultat acquis. La figure LiDAR avec Marie Aspro reste le benchmark **synthétique de 2 millions de points**, crédité **© Naval Group**, publié dans la soutenance et décrit au [rapport AYANA 2025, §7.7](https://radar.inria.fr/report/2025/ayana/index.html). Aucune donnée industrielle confidentielle n’est ajoutée.

## Percolia

Monogramme repris de `Logo/Police/percolia-p-monogram-primary.svg`, sans redessin. Un seul QR code, vers `https://www.linkedin.com/company/percolia/`, réglable par `\PercoliaLinkedIn` dans `poster.tex`. Son décodage est testé dans le PDF rendu. La disponibilité de cette page LinkedIn n’a pas pu être vérifiée par le navigateur de travail ; le décodage du QR ne vaut pas vérification de la page cible.

Louis et Alban Hauseux ainsi qu’Inria Startup Studio sont mentionnés dans le bandeau du bas.

## Compilation et contrôles

```bash
cd 'Présentations/Posters/3IA_Days_2026'
make
```

La compilation ordinaire utilise les figures et images versionnées, sans réseau ni Python. Dépendances : XeLaTeX, Beamer/beamerposter, TikZ, multicol, qrcode et EB Garamond. Sur Debian/Ubuntu : `texlive-xetex texlive-latex-extra texlive-fonts-recommended fonts-ebgaramond`. Sur Overleaf, choisir **XeLaTeX** et `poster.tex`. Aucun fichier de police n’est redistribué.

```bash
python3 -m pip install -r requirements-build.txt
make check preview
```

Les contrôles couvrent le format A0, les polices incorporées, les contenus attendus, la séparation du texte et de la bibliographie, le décodage du QR et l’exemple géométrique. Vérifier également le rendu visuel. Les fichiers auxiliaires restent dans `build/`, ignoré par Git.

`prepare_defense_figures.py` restaure les nouvelles figures absentes depuis la révision figée ; il ne remplace pas une figure déjà modifiée sans `--force`. Le workflow reconstruit et enregistre les livrables sur `main`, sans créer de branche.

Les données 2D et paramètres HDBSCAN restent ceux du poster initial (`min_cluster_size=15`, `min_samples=16`, qui inclut le point lui-même). Licences et provenances initiales sont conservées dans `GEMINI-LICENSE.md`, `assets/HDBSCAN-LICENSE` et `assets/sources.json`. Le code du gabarit provient du [poster Inria/EUVIP](https://github.com/Ludwig-H/Generalized-Frangi-for-Automatic-Crack-Extraction-on-FIND-dataset/tree/46b40eab4992515b6fde10bb2cd6924b63ab9db6/EUVIP/poster), adapté de [Gemini](https://github.com/anishathalye/gemini).
