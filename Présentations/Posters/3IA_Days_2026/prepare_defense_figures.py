"""Vendor the defense TikZ, preserving its geometry and tree topology.

Only English labels, typography and requested comparison signs are adapted.
Normal builds use the committed files and require no network access.
"""
from pathlib import Path
import argparse
import hashlib
import urllib.request

HERE = Path(__file__).resolve().parent
REV = '3593fbf25434c4715b37537eae1287bf49239fa7'
BASE = f'https://raw.githubusercontent.com/Ludwig-H/Manuscrit-de-th-se/{REV}/Soutenance/soutenance/figs/'
SOURCES = {
    'deuxnn_r_boules.tex': 'a573cc43fe9310ad8335752711191c5d8dc00e22',
    'deuxnn_rp_boules.tex': '53163804fa744353e9d9cb2ade144417c749e932',
    'deuxnn_rs_boules.tex': '7ed6ec6b9f274e93f80dfaa93cd305b51cc2e89f',
    'comp_dendro_rsl.tex': 'ba049ea61cb2659e3822f82867c0386418ac4ee3',
    'comp_dendro_2nn.tex': 'e772c93813addccdf6a339ee8a30ce0731cc37e8',
    'verrou_portee.tex': '9cca660433532a16af3cf736cf9383184d3ba9e6',
    'hierarchie_surfaces.tex': 'a0d8fff49a7ccd75cf59e7a16094ddb209e4cdde',
}

def git_sha(data: bytes) -> str:
    return hashlib.sha1(f'blob {len(data)}\0'.encode() + data).hexdigest()

def adapt(name: str, text: str) -> str:
    text = text.replace('[scale=0.52]', r'[scale=0.52,font=\fontsize{10}{11}\selectfont]')
    text = text.replace(r'\scriptsize', r'\fontsize{8}{9}\selectfont')
    text = text.replace(r'\small', r'\fontsize{10}{11}\selectfont')
    text = text.replace(r'\Large', r'\fontsize{14}{15}\selectfont')
    if name in {'comp_dendro_rsl.tex', 'comp_dendro_2nn.tex'}:
        text = text.replace(r' node[above] {Seuil $\epsilon$}', '')
        # Retain the requested r label; epsilon/2 is the displayed DBSCAN scale.
        text = text.replace('(resolution 2r)', '(display radius r)')
    elif name == 'verrou_portee.tex':
        text = text.replace(r'objet \textbf{proche}', r'\textbf{Near} object')
        text = text.replace(r'objet \textbf{lointain}', r'\textbf{Far} object')
        text = text.replace(r'le \textbf{nuage}\\dépend du capteur\\et de la portée',
                            r'\textbf{Sampling}\\depends on\\sensor and range')
        text = text.replace("la \\textbf{surface} varierait\\\\beaucoup moins :\\\\c'est l'\\emph{hypothèse}",
                            r'\textbf{Geometry}\\may vary less\\(hypothesis)')
        old = r'\node[font=\fontsize{14}{15}\selectfont\bfseries, text=inria-rouge] at (6.15,-1.86) {$\approx$};'
        new = (r'% Both comparison signs share the midpoint between the two panels.' '\n'
               r'\def\comparisonx{5.15}' '\n'
               r'\node[font=\fontsize{18}{20}\selectfont\bfseries, text=inriablue] at (\comparisonx,0.95) {$\ne$};' '\n'
               r'\node[font=\fontsize{18}{20}\selectfont\bfseries, text=inria-rouge] at (\comparisonx,-1.86) {$\approx$};')
        if text.count(old) != 1:
            raise ValueError('Cannot locate the original car comparison sign.')
        text = text.replace(old, new)
    elif name == 'hierarchie_surfaces.tex':
        text = text.replace('rayon (m)', 'merging radius')
    return f'% Adapted from the defense at {REV}; original blob {SOURCES[name]}.\n' + text

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--source-dir', type=Path, help='Optional local defense figs directory')
    parser.add_argument('--force', action='store_true', help='Explicitly regenerate existing figures')
    args = parser.parse_args()
    target_dir = HERE / 'figures/defense'
    target_dir.mkdir(parents=True, exist_ok=True)
    for name, expected in SOURCES.items():
        target = target_dir / name
        if target.exists() and not args.force:
            continue
        if args.source_dir:
            raw = (args.source_dir / name).read_bytes()
        else:
            with urllib.request.urlopen(BASE + name, timeout=60) as response:
                raw = response.read()
        if git_sha(raw) != expected:
            raise ValueError(f'Unexpected source for {name}')
        target.write_text(adapt(name, raw.decode('utf-8')), encoding='utf-8')
    svg = HERE / 'assets/percolia-p.svg'
    src = HERE.parents[2] / 'Logo/Police/percolia-p-monogram-primary.svg'
    if src.exists():
        raw = src.read_bytes()
        if git_sha(raw) != 'ba4aa350425a3057d584321fa93854f3cafcb90a':
            raise ValueError('Percolia monogram changed: review the new logo before use.')
        svg.write_bytes(raw)
    if not svg.exists():
        raise FileNotFoundError('Missing standalone Percolia P SVG')
    import cairosvg
    cairosvg.svg2pdf(url=str(svg), write_to=str(HERE / 'assets/percolia-p.pdf'))

if __name__ == '__main__':
    main()
