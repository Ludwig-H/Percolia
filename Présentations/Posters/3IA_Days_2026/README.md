# Poster scientifique · Journées 3IA 2026

[**PDF A0 portrait**](Poster_3IA_2026_Hauseux_A0.pdf) · [Source LaTeX](poster.tex)

[![Aperçu](apercu.png)](Poster_3IA_2026_Hauseux_A0.pdf)

**Higher-order clustering for 3D point clouds**  
Louis Hauseux · Konstantin Avrachenkov · Josiane Zerubia  
AI Cluster 3IA Côte d’Azur Days, 24–25 septembre 2026.

Une page **841 × 1189 mm**, à imprimer à **100 % / taille réelle**. Gabarit Inria / Gemini ; logos institutionnels en bas, 3IA principal entre Inria et DS4H. Les publications des auteurs restent signalées en rouge.

## Contenu et mise en page

Les sept blocs sont **sans numérotation**. L’introduction définit les clusters comme des groupes de points similaires et précise que la similarité est mesurée ici par la distance euclidienne. L’exemple HDBSCAN conserve sa largeur réduite à 88 % du contenu du bloc.

Le bloc de Hartigan présente la hiérarchie des composantes de sur-niveaux. La partie estimation suit cet ordre : **densité inconnue f → choix non paramétrique f̂ ← f̂_K-NN → formule de l’estimateur → changement de variable par r_K**. Les formules encadrées tiennent chacune sur une ligne. Le niveau de densité est noté **λ**, son rayon associé **r(λ)** ; aucun ρ n’est affiché. La définition de r_K est mise en bleu. Dans l’exemple à six points, les étapes géométriques restent repérées par r, r′ et r″.

Un même espacement de **8 mm** sépare tous les blocs, y compris la bibliographie. Le paramètre `\posterblockgap` est défini dans `beamerthemegemini.sty`. Les deux colonnes ont la même hauteur totale ; la colle interligne implicite est supprimée entre les blocs afin de ne pas modifier cet espacement.

Percolia possède son propre bloc en bas à droite. Le monogramme P est affiché à **5,3 cm de hauteur**, après retrait des seules marges blanches de son canevas, et centré verticalement avec le texte et le QR. Le dessin du logo n’est pas modifié. Le pied de page ne répète ni le logo Percolia ni le QR.

## Figures originales de la soutenance

Sources : [TikZ de la soutenance](https://github.com/Ludwig-H/Manuscrit-de-th-se/tree/3593fbf25434c4715b37537eae1287bf49239fa7/Soutenance/soutenance/figs). Les empreintes Git sont contrôlées par `prepare_defense_figures.py`.

`figures/defense/deuxnn_r_boules.tex`, `deuxnn_rp_boules.tex` et `deuxnn_rs_boules.tex` conservent les six points A–F et les étapes **7 → 3 → 1**. Les deux topologies de la soutenance sont regroupées dans `figures/six_point_hierarchies.tex`, sur un canevas commun : mêmes ligne de base, échelle verticale et hauteurs de titre, sans nom de variable sur les axes.

La fusion plate de DBSCAN / Robust SL est étiquetée **r**. Le rayon affiché de DBSCAN est ε/2 ; son paramètre brut au seuil reste ε = 2r, utilisé par le test numérique. Les hauteurs des arbres sont schématiques. Les sept branches 2-NN sont AB, BC, AC, CD, DE, EF, DF ; ABC, CD et DEF restent distincts entre r′ et r″. Les étiquettes répétées du dendrogramme sont intentionnelles : ce n’est pas une partition des six sommets.

Les sept arêtes courtes ont longueur 2r ; r′ = 2r/√3 et r″ = r√(2+√3). K=2 désigne deux voisins autres que le point lui-même, donc `min_samples=3` pour le test DBSCAN. Dans l’identité de recouvrement, r₂(y) est le deuxième rang dans l’échantillon entier, avec des boules fermées. `test_six_point_geometry.py` contrôle cette géométrie ; ce n’est pas une implémentation de HGP.

`figures/defense/verrou_portee.tex` conserve les voitures, nappes, retours et contours de la soutenance. Le **≠ bleu** et le **≈ rouge** partagent l’abscisse `\comparisonx=5.15`. `hierarchie_surfaces.tex` conserve les pièces recollées et les coutures rouges. Le guidage d’un modèle de fondation reste présenté comme une **hypothèse de recherche**.

La figure LiDAR avec Marie Aspro est le benchmark **synthétique de 2 millions de points**, crédité **© Naval Group**, publié dans la soutenance et décrit dans le [rapport AYANA 2025, §7.7](https://radar.inria.fr/report/2025/ayana/index.html). Aucune donnée industrielle confidentielle n’est ajoutée.

## Percolia et QR

Le monogramme vient de `Logo/Police/percolia-p-monogram-primary.svg`, sans redessin. L’unique QR encode `https://www.linkedin.com/company/percolia/`, réglable par `\PercoliaLinkedIn` dans `poster.tex`. Sa légende est cliquable. Le décodage est testé dans le PDF ; cela ne vérifie pas la disponibilité de la page LinkedIn.

## Compilation et contrôles

```bash
cd 'Présentations/Posters/3IA_Days_2026'
make
```

La compilation ordinaire utilise les fichiers versionnés, sans réseau ni Python. Dépendances : XeLaTeX, Beamer/beamerposter, TikZ, multicol, qrcode et EB Garamond. Debian/Ubuntu : `texlive-xetex texlive-latex-extra texlive-fonts-recommended fonts-ebgaramond`. Sur Overleaf : **XeLaTeX**, fichier principal `poster.tex`. Aucun fichier de police n’est redistribué.

```bash
python3 -m pip install -r requirements-build.txt
make check preview
```

Les contrôles portent sur l’A0, les polices incorporées, l’ordre des formules, l’absence de ρ et de numéros de blocs, le contenu à l’intérieur des blocs, les **espacements mesurés dans le PDF**, le QR unique et l’exemple géométrique. Ils complètent l’inspection visuelle. Les auxiliaires restent dans `build/`, ignoré par Git. Le workflow reconstruit et enregistre les livrables sur `main`.

`prepare_defense_figures.py` restaure les figures absentes depuis la révision figée ; `--force` applique à nouveau les adaptations documentées. L’exemple introductif conserve les données et paramètres HDBSCAN initiaux (`min_cluster_size=15`, `min_samples=16`, qui inclut le point lui-même).

Licences et provenances : `GEMINI-LICENSE.md`, `assets/HDBSCAN-LICENSE`, `assets/sources.json`. Le gabarit provient du [poster Inria/EUVIP](https://github.com/Ludwig-H/Generalized-Frangi-for-Automatic-Crack-Extraction-on-FIND-dataset/tree/46b40eab4992515b6fde10bb2cd6924b63ab9db6/EUVIP/poster), adapté de [Gemini](https://github.com/anishathalye/gemini).
