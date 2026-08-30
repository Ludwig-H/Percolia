# Oiseau-réseau Percolia — direction 03

Cette direction revient au **premier oiseau triangulé** de Percolia. Le corps, la tête, le bec et la queue conservent leur topologie en réseau. Les essais fondés sur une silhouette paramétrique lisse sont abandonnés : ils perdaient le caractère du premier jet et produisaient une animation inutilement démonstrative.

## Séquence retenue

La démonstration `demo.html` est volontairement simple :

1. un petit oiseau est perché sur le `P` ;
2. un **premier oiseau** déploie ses ailes, décolle et traverse la scène de gauche à droite ;
3. il sort entièrement du cadre et disparaît ;
4. la scène reste vide pendant un court instant ;
5. un **second oiseau**, objet SVG distinct, arrive depuis la droite et vole vers la gauche ;
6. il ralentit, sort ses pattes et se pose sur le `P` ;
7. l’animation s’arrête sur la signature finale.

Le premier oiseau ne fait donc jamais demi-tour. Le retour est assuré par un second oiseau venant de la direction opposée.

## Mouvement des ailes

Le réseau du corps reste fixe. Chaque aile est recalculée à partir d’une chaîne à trois segments :

```text
épaule → coude → poignet → extrémité
```

Pour une phase `θ = 2πt/T`, l’angle principal est :

```text
φ(t) = φ₀ + A cos(θ) + A₂ cos(2θ + δ)
```

La seconde harmonique évite un mouvement parfaitement sinusoïdal. Le repli de la remontée est commandé par :

```text
u(t) = ((1 - sin(θ + η)) / 2)^p
β(t) = β₀ + Δβ u(t)
γ(t) = γ₀ + Δγ u(t)
```

`β` et `γ` contrôlent respectivement le coude et le poignet. Pendant la descente, l’aile est plus déployée. Pendant la remontée, elle se replie pour réduire visuellement la surface exposée. La période nominale est de `3,2 s`, suffisamment lente pour rester lisible à la taille du logo.

À chaque image, les sept sommets du contour, les sept facettes, les arêtes et les nœuds de l’aile sont recalculés. Il ne s’agit donc pas d’un polygone rigide simplement tourné autour d’un point.

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

## Régénération

```bash
python Logo/Oiseau/build_bird.py
python Logo/build_lockups.py
python Logo/Oiseau/build_demo.py
python Logo/Oiseau/test_wing_model.py
node --check Logo/Oiseau/bird-animation.js
```

Le test vérifie notamment :

- la fermeture exacte du cycle d’aile ;
- la continuité image par image ;
- la conservation des longueurs des trois segments ;
- une aire d’aile toujours positive ;
- le déplacement strictement croissant en `x` pour l’oiseau sortant ;
- le déplacement strictement décroissant en `x` pour l’oiseau entrant ;
- le départ et l’arrivée au même point du `P`.

## Intégration

`demo.html` est autonome : aucun `fetch`, aucune police distante et aucune bibliothèque JavaScript externe. Pour le site, le contrôleur expose :

```text
play()
pause()
restart()
seek(milliseconds)
```

`prefers-reduced-motion` désactive le vol et laisse simplement l’oiseau perché sur le `P`.
