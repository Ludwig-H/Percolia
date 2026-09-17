# Poster scientifique · Journées 3IA 2026

[**PDF A0 portrait**](Poster_3IA_2026_Hauseux_A0.pdf) · [Source LaTeX](poster.tex)

[![Aperçu](apercu.png)](Poster_3IA_2026_Hauseux_A0.pdf)

**Higher-order clustering for 3D point clouds**  
Louis Hauseux · Konstantin Avrachenkov · Josiane Zerubia  
AI Cluster 3IA Côte d’Azur Days, 24–25 septembre 2026.

Une page **841 × 1189 mm**, à imprimer à **100 % / taille réelle**. Gabarit Inria / Gemini, logos institutionnels en bas : 3IA principal entre Inria et DS4H. Percolia et la bibliographie ont chacun leur propre bloc. Les publications des auteurs sont signalées en rouge.

## Mise en page

L’exemple HDBSCAN est réduit à 88 % de la largeur intérieure du bloc introductif. Le bloc suivant présente explicitement le modèle et la **hiérarchie de Hartigan**. Les quatre formules structurantes ont un véritable cadre ; la définition de **r_K(y)** est agrandie et colorée en bleu.

Le bloc **Inria Startup Studio: Percolia**, en bas à droite, rassemble Louis et Alban Hauseux, le monogramme P et un unique QR LinkedIn. Le pied de page ne répète ni le logo Percolia ni le QR.

## L’exemple exact à six points

Sources : [TikZ de la soutenance](https://github.com/Ludwig-H/Manuscrit-de-th-se/tree/3593fbf25434c4715b37537eae1287bf49239fa7/Soutenance/soutenance/figs). Les empreintes Git sont contrôlées par `prepare_defense_figures.py`.

`figures/defense/deuxnn_r_boules.tex`, `deuxnn_rp_boules.tex` et `deuxnn_rs_boules.tex` conservent les six points A–F et les étapes **7 → 3 → 1** composantes. Les deux topologies de la soutenance sont regroupées dans `figures/six_point_hierarchies.tex` : même canevas TikZ, même ligne de base, même échelle verticale et mêmes hauteurs de titre. Aucun nom de variable n’est ajouté aux axes.

La fusion plate de DBSCAN / Robust SL est étiquetée **r**, conformément à la présentation demandée. Pour garder une convention cohérente avec le rayon des boules, le rayon affiché de DBSCAN est **ε/2** ; le paramètre brut de DBSCAN au seuil reste ε = 2r. Le test numérique utilise ce paramètre brut. Les hauteurs des dendrogrammes sont schématiques, comme dans les slides.

Les branches 2-NN sont AB, BC, AC, CD, DE, EF, DF. Les trois branches ABC, CD et DEF restent distinctes entre r′ et r″. Les étiquettes répétées sont volontaires : ces composantes de recouvrements peuvent partager des points de l’échantillon. Ce n’est pas une partition des six sommets.

La longueur commune des sept arêtes courtes est 2r ; r′ = 2r/√3 et r″ = r√(2+√3). K=2 correspond à deux voisins autres que le point lui-même, donc à `min_samples=3` pour le test DBSCAN. Dans l’identité de recouvrement, r₂(y) est le deuxième rang dans l’échantillon entier, avec des boules fermées. `test_six_point_geometry.py` contrôle les composantes et la fusion plate ; ce test n’est pas une implémentation de HGP.

## Perspective et application

`figures/defense/verrou_portee.tex` conserve **exactement les voitures, nappes de balayage, retours et contours de la soutenance**. Le signe **≠ bleu** entre les nuages et le **≈ rouge** entre les contours utilisent la même abscisse `\comparisonx=5.15`. Les deux signes sont centrés entre les panneaux. `hierarchie_surfaces.tex` conserve les pièces recollées, orientations et coutures rouges.

Le bénéfice pour un modèle de fondation 3D reste une **hypothèse**, pas un résultat acquis. La figure LiDAR avec Marie Aspro est le benchmark **synthétique de 2 millions de points**, crédité **© Naval Group**, publié dans la soutenance et décrit dans le [rapport AYANA 2025, §7.7](https://radar.inria.fr/report/2025/ayana/index.html). Aucune donnée industrielle confidentielle n’est ajoutée.

## Percolia et QR

Le monogramme vient de `Logo/Police/percolia-p-monogram-primary.svg`, sans redessin. Le QR encode `https://www.linkedin.com/company/percolia/`, réglable avec `\PercoliaLinkedIn` dans `poster.tex`. Sa légende est également cliquable. Le décodage est contrôlé sur le PDF rendu ; il ne constitue pas une vérification de disponibilité de la page LinkedIn.

## Compilation

```bash
cd 'Présentations/Posters/3IA_Days_2026'
make
```

La compilation ordinaire utilise les fichiers versionnés, sans réseau ni Python. Dépendances : XeLaTeX, Beamer/beamerposter, TikZ, multicol, qrcode et EB Garamond. Debian/Ubuntu : `texlive-xetex texlive-latex-extra texlive-fonts-recommended fonts-ebgaramond`. Sur Overleaf : **XeLaTeX**, fichier principal `poster.tex`. Aucun fichier de police n’est redistribué.

```bash
python3 -m pip install -r requirements-build.txt
make check preview
```

Les contrôles portent sur le format A0, les polices incorporées, les contenus attendus, la séparation des blocs, le QR unique et l’exemple géométrique. L’inspection visuelle reste nécessaire. Les auxiliaires restent dans `build/`, ignoré par Git. Le workflow reconstruit et enregistre les livrables sur `main`.

`prepare_defense_figures.py` restaure les figures absentes depuis la révision figée ; `--force` applique à nouveau les adaptations documentées. L’exemple introductif conserve les données et paramètres HDBSCAN initiaux (`min_cluster_size=15`, `min_samples=16`, qui inclut le point lui-même).

Licences et provenances : `GEMINI-LICENSE.md`, `assets/HDBSCAN-LICENSE`, `assets/sources.json`. Le gabarit est adapté du [poster Inria/EUVIP](https://github.com/Ludwig-H/Generalized-Frangi-for-Automatic-Crack-Extraction-on-FIND-dataset/tree/46b40eab4992515b6fde10bb2cd6924b63ab9db6/EUVIP/poster), lui-même adapté de [Gemini](https://github.com/anishathalye/gemini).
