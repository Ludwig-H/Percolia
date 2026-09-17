"""Check the print format, text, fonts and QR destination; optionally render."""
import argparse
from pathlib import Path
import fitz


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('pdf', type=Path)
    parser.add_argument('--preview', type=Path)
    args = parser.parse_args()
    with fitz.open(args.pdf) as document:
        if len(document) != 1:
            raise ValueError('The poster must contain exactly one page.')
        page = document[0]
        width, height = page.rect.width * 25.4 / 72, page.rect.height * 25.4 / 72
        if abs(width - 841) > .1 or abs(height - 1189) > .1:
            raise ValueError(f'Not ISO A0 portrait: {width:.3f} x {height:.3f} mm')
        text = page.get_text()
        for expected in ['Higher-order clustering', 'HDBSCAN', 'Hartigan', 'HGP-Clusterer',
                         'Marie', 'Alban', 'Research hypothesis', 'Startup Studio', 'Naval Group']:
            if expected not in text:
                raise ValueError(f'Missing required poster text: {expected}')
        for xref, ext, kind, name, *_ in page.get_fonts(full=True):
            if not document.extract_font(xref)[3]:
                raise ValueError(f'Font not embedded: {name}')
        for block in page.get_text('blocks'):
            if not page.rect.contains(fitz.Rect(block[:4])):
                raise ValueError(f'Text outside the page: {block[4][:60]}')
        links = [link.get('uri', '') for link in page.get_links()]
        if 'https://github.com/Ludwig-H/Percolia' not in links:
            raise ValueError('Project/QR destination missing from PDF links.')
        if args.preview:
            page.get_pixmap(dpi=55, alpha=False).save(args.preview)
        print(f'PASS: 1 page, A0 portrait ({width:.2f} x {height:.2f} mm), fonts embedded, required text and links present.')

if __name__ == '__main__':
    main()
