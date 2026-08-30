# Charte graphique Percolia — v0.1

## 1. Positionnement traduit en image

Percolia transforme des ensembles de données massifs, complexes et bruités en structures fiables. Son premier marché est le traitement de nuages de points LiDAR 3D pour les jumeaux numériques, l’inspection, la robotique et les environnements industriels. L’identité doit cependant rester valable pour de futures applications aux logs, graphes et données scientifiques.

La marque repose sur quatre idées :

| Idée | Traduction visuelle |
|---|---|
| Rigueur scientifique | géométrie nette, rythme régulier, peu d’effets décoratifs |
| Structure issue du bruit | particules dispersées à gauche, réseau organisé au centre |
| Percolation contrôlée | chemin bleu/cyan, seuil visible dans le `P` |
| Confiance industrielle | bleu encre dominant, forte lisibilité, variantes monochromes |

Le ton recherché est **scientifique, calme, précis et ambitieux**. Il faut éviter les codes trop ludiques, ésotériques ou « crypto ».

## 2. Architecture de marque

### Signature principale

`percolia-lockup-horizontal.svg` est la version par défaut sur le site, les présentations et les documents commerciaux.

### Signature verticale

`percolia-lockup-stacked.svg` convient aux couvertures, affiches et formats presque carrés.

### Mot-symbole seul

Le mot `PERCOLIA` peut être utilisé seul lorsque le contexte rend la marque explicite : barre de navigation, pied de page, produit logiciel.

### Monogramme P

Le `P` est l’actif prioritaire pour construire la reconnaissance à long terme : favicon, avatar, icône d’application, filigrane et animation de chargement. Sa coupure et ses deux nœuds ne doivent pas être supprimés dans les versions en couleur.

### Oiseau-réseau

L’oiseau est un symbole narratif et cinétique. Il peut apparaître seul sur une page d’accueil, dans une démonstration, au début d’une vidéo ou comme illustration de section. À petite taille, utiliser la version `compact`.

## 3. Couleurs

| Nom | Hex | Rôle |
|---|---:|---|
| Encre | `#082C4C` | couleur principale, texte, contours, fonds inversés |
| Signal | `#1C83D4` | propagation, interaction, accent actif |
| Seuil | `#20C9C4` | seuil critique, nœud terminal, accent rare |
| Brume | `#EAF5F7` | fond secondaire, panneaux, surfaces techniques |
| Ardoise | `#5D7385` | texte secondaire sur fond clair |
| Blanc | `#FFFFFF` | fond principal et version inversée |

### Contraste

- Encre sur blanc : environ `14.2:1`.
- Ardoise sur blanc : environ `4.9:1`.
- Signal sur blanc : environ `4.0:1` ; ne pas l’utiliser pour du petit texte normal.
- Seuil sur blanc : environ `2.1:1` ; réserver aux formes graphiques, grands éléments ou fonds sombres.
- Seuil sur Encre : environ `6.9:1`.

## 4. Typographie

### Typographie de marque

`PERCOLIA Display` désigne ici une **construction vectorielle propriétaire**, pas encore une fonte de texte installable. Les huit lettres du nom sont décrites dans `Police/source/geometry.json` et visualisées dans `percolia-glyph-sheet.svg`.

Caractéristiques :

- capitales géométriques monolinéaires ;
- terminaisons rondes ;
- largeur généreuse ;
- détails distinctifs concentrés sur le `P` ;
- `I` muni de traverses afin d’éviter l’effet de simple barre.

Ne pas reconstituer le mot-symbole avec une police approchante.

### Typographie d’accompagnement

Pour l’interface et les documents, utiliser une sans-sérif sobre :

```css
font-family: Inter, ui-sans-serif, system-ui, -apple-system, "Segoe UI", sans-serif;
```

Le mot-symbole doit rester un SVG ; la police d’accompagnement n’a pas vocation à l’imiter.

## 5. Espace de protection et tailles minimales

Prendre comme unité `x` le diamètre d’un grand nœud cyan du `P`.

- autour du mot-symbole : au moins `2x` ;
- autour du monogramme : au moins `1.5x` ;
- autour de la signature complète : au moins `2x`.

Tailles minimales recommandées :

| Actif | Écran | Impression |
|---|---:|---:|
| Monogramme P | 20 px | 6 mm |
| Mot-symbole | 140 px | 35 mm |
| Oiseau compact | 48 px | 15 mm |
| Oiseau détaillé | 96 px | 28 mm |
| Signature horizontale | 240 px | 60 mm |

Sous ces tailles, privilégier le `P` seul.

## 6. Fonds et variantes

- Sur fond blanc ou Brume : version `primary`.
- Sur fond Encre : version `inverse`.
- Pour gravure, tampon, fax, découpe ou contrainte stricte : version `mono`.
- Sur photographie : placer le logo dans une zone calme ou sur un aplat ; ne pas ajouter d’ombre portée.

## 7. Animation

L’animation doit expliquer la promesse plutôt que simplement décorer.

Séquence recommandée :

1. apparition discrète des points dispersés ;
2. construction progressive des arêtes, de la queue vers la tête ;
3. apparition des facettes ;
4. bref passage lumineux sur le chemin critique ;
5. état final immobile.

Règles :

- durée de révélation inférieure à deux secondes ;
- pas de battement d’ailes cartoon ;
- pulsation secondaire espacée d’au moins trois secondes ;
- parallaxe limitée aux particules libres ;
- respect obligatoire de `prefers-reduced-motion` ;
- ne pas animer en boucle continue dans une interface de travail.

Le fichier `Oiseau/bird-animation.js` fournit une implémentation de référence sans dépendance.

## 8. Usages interdits

Ne pas :

- étirer ou incliner le logo ;
- recolorer arbitrairement les nœuds ;
- fermer la coupure du `P` ;
- épaissir les traits sans recalculer les espacements ;
- utiliser un dégradé arc-en-ciel ou des effets néon ;
- isoler une facette aléatoire comme symbole de marque ;
- placer la version détaillée de l’oiseau à une taille où les arêtes deviennent illisibles ;
- employer l’oiseau comme mascotte humoristique.

## 9. Validation avant identité définitive

Cette piste a une logique de marque forte, mais son caractère distinctif doit être objectivé. Le protocole minimal conseillé est un test non assisté : montrer pendant deux secondes le `P`, puis demander à des participants de le redessiner et de l’associer au nom Percolia. Comparer ensuite trois variantes de densité de l’oiseau sur les cibles industrielles.

Une recherche d’antériorités reste nécessaire avant dépôt ou adoption définitive ; aucun contrôle juridique exhaustif n’est revendiqué dans cette version.
