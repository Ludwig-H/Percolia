# Oiseau-réseau Percolia — direction 03, cinématique v0.9

Cette direction conserve le **premier oiseau triangulé** de Percolia. Le corps, la tête, le bec et la queue gardent leur topologie en réseau. Seules les ailes sont déformées image par image à partir d’une chaîne articulée.

## Séquence retenue

La démonstration `demo.html` met en scène deux oiseaux distincts :

1. un petit oiseau est perché sur le `P` ;
2. il se tasse légèrement, incline le corps et ouvre ses ailes ;
3. il pousse sur ses pattes, décolle et traverse la scène de gauche à droite ;
4. il quitte complètement le cadre ;
5. après un court silence, un second oiseau entre par la droite ;
6. il approche de droite à gauche, effectue un arrondi, sort ses pattes et touche le `P` ;
7. il amortit le contact, replie ses ailes et demeure perché, orienté dans le sens de son arrivée.

Le premier oiseau ne fait jamais demi-tour. L’arrivée est assurée par un second objet SVG venant de la direction opposée.

## Envol

L’envol est divisé en trois étapes :

- **préparation** : tassement léger, inclinaison vers l’avant et ouverture progressive des ailes ;
- **poussée** : les pattes conservent brièvement le contact avec le perchoir pendant le début du premier battement ;
- **transition** : la position et la tangente rejoignent sans cassure la courbe de vol sortante.

Le point d’ancrage de l’oiseau volant est distinct du point d’appui des pattes. Le contrôleur calcule donc la position du corps qui maintient les pieds sur le `P` avant la libération du contact. Cela supprime le saut qui existait entre l’oiseau statique et l’oiseau animé.

## Approche et atterrissage

L’atterrissage est séparé en trois phases :

- **arrondi** : ralentissement visuel, relèvement du bec, ouverture des ailes et sortie des pattes avant le contact ;
- **contact** : descente courte jusqu’au point d’appui, réduction de l’échelle vers la pose perchée et repli progressif des ailes ;
- **stabilisation** : petite oscillation amortie après le posé, sans fondu vers un autre dessin.

Le second oiseau reste visible après l’atterrissage. Il n’est plus remplacé brutalement par la silhouette statique orientée dans l’autre sens.

## Mouvement des ailes

Chaque aile est recalculée à partir d’une chaîne à trois segments :

```text
épaule → coude → poignet → extrémité
```

Pour une phase `θ = 2πt/T`, l’angle principal est :

```text
φ(t) = φ₀ + A cos(θ) + A₂ cos(2θ + δ)
```

Le repli de la remontée est commandé par :

```text
u(t) = ((1 - sin(θ + η)) / 2)^p
β(t) = β₀ + Δβ u(t)
γ(t) = γ₀ + Δγ u(t)
```

`β` et `γ` contrôlent le coude et le poignet. L’aile reste plus déployée pendant la descente et se replie pendant la remontée. La période nominale reste de `3,2 s`, afin que le battement demeure lisible et calme à la taille du logo.

## Continuité des trajectoires

Les courbes de Bézier sont raccordées en position et avec des tangentes presque colinéaires :

```text
poussée → sortie
retour → arrondi
arrondi → contact
```

Le contrôleur ne déduit pas aveuglément l’inclinaison du corps de la tangente lorsque l’oiseau est près du perchoir. L’envol et l’arrondi utilisent une orientation bornée et explicitement interpolée, ce qui évite les rotations verticales absurdes du prototype précédent.

## Fichiers canoniques

```text
Logo/Oiseau/
├── README.md
├── build_bird.py
├── build_demo.py
├── test_wing_model.py
├── bird-animation.js
├── bird-animation.css
├── demo.html
├── percolia-bird-primary.svg
├── percolia-bird-inverse.svg
├── percolia-bird-mono.svg
├── percolia-bird-compact.svg
└── source/
    ├── README.md
    └── bird_model.json
```

`source/bird_model.json` est la source de vérité. Les SVG et la page autonome sont générés et versionnés afin d’être consultables directement sur GitHub.

## Régénération et validation

```bash
python Logo/Police/build_wordmark.py
python Logo/Oiseau/build_bird.py
python Logo/build_lockups.py
python Logo/Oiseau/build_demo.py
python Logo/Oiseau/test_wing_model.py
node --check Logo/Oiseau/bird-animation.js
```

Les tests vérifient notamment :

- la fermeture et la continuité du cycle des ailes ;
- la conservation des longueurs des trois segments ;
- une aire d’aile toujours positive ;
- le déplacement strictement croissant en `x` pour l’oiseau sortant ;
- le déplacement strictement décroissant en `x` pour l’oiseau entrant ;
- les raccords de position et de tangente entre les phases ;
- la coïncidence du contact final avec le point du `P` ;
- l’absence de dépendance externe dans `demo.html`.

## Intégration

`demo.html` est autonome : aucun `fetch`, aucune police distante et aucune bibliothèque JavaScript externe. Le contrôleur expose :

```text
play()
pause()
restart()
seek(milliseconds)
```

`prefers-reduced-motion` désactive le vol et laisse simplement l’oiseau initial perché sur le `P`.
