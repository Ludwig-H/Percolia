"""Restore missing illustration assets from pinned sources with SHA-256 checks.
Normal LaTeX builds are offline: all required assets are committed.
No font files are downloaded, copied or redistributed.
"""
from pathlib import Path
import hashlib
import json
import urllib.request

HERE = Path(__file__).resolve().parent

def main() -> None:
    manifest = json.loads((HERE / 'assets/sources.json').read_text())
    for name, entry in manifest.items():
        target = HERE / 'assets' / name
        if target.exists():
            data = target.read_bytes()
        else:
            request = urllib.request.Request(entry['url'], headers={'User-Agent':'Percolia-poster-build'})
            with urllib.request.urlopen(request, timeout=90) as response:
                data = response.read()
        if hashlib.sha256(data).hexdigest() != entry['sha256']:
            raise ValueError(f'Checksum mismatch for {name}; existing files are not overwritten.')
        if not target.exists():
            target.write_bytes(data)
        print(f'Verified {name}')
    # Reuse the pinned Inria colour theme and the defense's polyhedral drawing.
    # These files are committed after their first restoration.
    base = 'https://raw.githubusercontent.com/'
    extras = {
        'beamercolorthemeinria.sty': base + 'Ludwig-H/Generalized-Frangi-for-Automatic-Crack-Extraction-on-FIND-dataset/46b40eab4992515b6fde10bb2cd6924b63ab9db6/EUVIP/poster/beamercolorthemeinria.sty',
        'figures/polyhedral_hierarchy.tex': base + 'Ludwig-H/Manuscrit-de-th-se/3593fbf25434c4715b37537eae1287bf49239fa7/Soutenance/soutenance/figs/hierarchie_surfaces.tex',
        'assets/HDBSCAN-LICENSE': base + 'scikit-learn-contrib/hdbscan/master/LICENSE',
        'GEMINI-LICENSE.md': base + 'anishathalye/gemini/master/LICENSE.md',
    }
    for name, url in extras.items():
        target = HERE / name
        if target.exists():
            continue
        with urllib.request.urlopen(url, timeout=90) as response:
            text = response.read().decode('utf-8')
        if name.endswith('polyhedral_hierarchy.tex'):
            text = text.replace('gris_fonce_inria', 'inriagrayblue')
            text = text.replace('inria-rouge', 'inriared')
            text = text.replace('inria-2024-bleu-canard!', 'inriablue!')
            text = text.replace('inria-2024-bleu-canard', 'inriablue!80!black')
            text = text.replace(r'\scriptsize', r'\fontsize{9}{10}\selectfont')
            text = text.replace('rayon (m)', 'merging radius')
            text = '% Static diagram adapted from the defense, English label; schematic radii.\n' + text
        target.write_text(text, encoding='utf-8')
    import cairosvg
    cairosvg.svg2pdf(url=str(HERE / 'assets/percolia.svg'),
                    write_to=str(HERE / 'assets/percolia.pdf'))

if __name__ == '__main__':
    main()
