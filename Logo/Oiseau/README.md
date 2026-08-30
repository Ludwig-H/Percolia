# Oiseau-réseau Percolia — modèle paramétrique v0.6

L’oiseau n’est plus animé par rotation de morceaux de SVG. Le contour de chaque aile, sa triangulation et ses nœuds sont **recalculés à chaque image** à partir d’un modèle cinématique continu.

## Intention graphique

L’oiseau reste un accent discret de la marque :

- petit et perché sur le `P` dans la signature statique ;
- silhouette calme, profilée et lisible ;
- ailes longues et légères plutôt qu’un assemblage de losanges ;
- maillage intérieur peu contrasté ;
- scan LiDAR bref, secondaire et non décoratif.

La version animée décolle du `P`, suit une trajectoire fermée, effectue un scan, puis revient se poser.

## Modèle mathématique des ailes

On note

\[
\theta(t)=\frac{2\pi t}{T}, \qquad T=5{,}2\ \mathrm{s}.
\]

L’angle de battement est une série de Fourier à deux harmoniques :

\[
\phi(t)=\phi_0+A_1\cos\theta(t)+A_2\cos\bigl(2\theta(t)-\delta\bigr).
\]

Le repli pendant la remontée est commandé par

\[
f(t)=\left(\frac{1+\sin(\theta(t)-\eta)}{2}\right)^p,
\]

puis

\[
\beta(t)=\beta_0+\Delta\beta f(t),
\qquad
\gamma(t)=\gamma_0+\Delta\gamma f(t),
\]

où `β` est la flexion du coude et `γ` celle du poignet.

Les quatre points du squelette sont obtenus par cinématique directe :

\[
E=S+L_1u(\chi),
\quad
W=E+L_2u(\chi+\beta),
\quad
T=W+L_3u(\chi+\beta+\gamma),
\]

avec `u(a)=(cos a,sin a)`.

Une spline de Catmull–Rom passant par `S,E,W,T` définit le bord d’attaque. La corde locale est

\[
c(s)=c_0(1-s)^q\bigl(1+b\sin(\pi s)\bigr), \qquad s\in[0,1].
\]

Le bord de fuite, les facettes et les diagonales du réseau sont construits à partir de sept stations le long de l’envergure. L’aile est ensuite plongée en 3D, tournée autour de l’axe du corps et projetée dans le plan du SVG par une projection orthographique oblique.

## Fichiers

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

`source/bird_model.json` est la source de vérité. Les SVG et la page autonome sont générés.

## Régénération et validation

```bash
python Logo/Oiseau/build_bird.py
python Logo/build_lockups.py
python Logo/Oiseau/build_demo.py
python Logo/Oiseau/test_wing_model.py
node --check Logo/Oiseau/bird-animation.js
```

Le test numérique vérifie notamment :

- la fermeture exacte du cycle ;
- la continuité image par image ;
- l’absence de coordonnées non finies ;
- la positivité de la corde ;
- une période de battement réellement lente.

## Intégration web

La page `demo.html` est autonome. Elle ne charge aucune ressource externe et peut être téléchargée puis ouverte directement dans un navigateur.

Pour une intégration dans le site, le SVG doit être inline :

```html
<div id="bird" data-flight-bird>
  <!-- percolia-bird-compact.svg inline -->
</div>
<script src="bird-animation.js"></script>
<script>
  const controller = initPercoliaBird(document.querySelector('#bird svg'), {
    birdElement: document.querySelector('#bird'),
    stageElement: document.querySelector('[data-flight-stage]'),
    perchElement: document.querySelector('[data-perch]')
  });
</script>
```

L’API expose `play()`, `pause()`, `restart()`, `scan()`, `pulse()` et `destroy()`.

## Accessibilité

`prefers-reduced-motion` désactive le vol continu. Le SVG reste visible dans une pose statique et le contenu de marque demeure lisible.
