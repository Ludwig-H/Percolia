"""Check A0, embedded fonts, block separation and the single LinkedIn QR."""
import argparse
from pathlib import Path
import fitz

LINKEDIN = 'https://www.linkedin.com/company/percolia/'

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('pdf', type=Path)
    parser.add_argument('--preview', type=Path)
    args = parser.parse_args()
    with fitz.open(args.pdf) as doc:
        if len(doc) != 1:
            raise ValueError('Expected exactly one page.')
        page = doc[0]
        size = page.rect.width * 25.4 / 72, page.rect.height * 25.4 / 72
        if abs(size[0] - 841) > .1 or abs(size[1] - 1189) > .1:
            raise ValueError(f'Not A0 portrait: {size}')
        text = page.get_text()
        for required in ['DBSCAN / Robust SL', 'HGP-Clusterer', 'Near', 'Far',
                         'Marie', 'Alban', 'Research hypothesis', 'Naval Group',
                         'model and hierarchy', 'Key quantity',
                         '6 Inria Startup Studio: Percolia', '7 References']:
            if required.casefold() not in text.casefold():
                raise ValueError(f'Missing content: {required}')
        for xref, _, _, name, *_ in page.get_fonts(full=True):
            if not doc.extract_font(xref)[3]:
                raise ValueError(f'Font not embedded: {name}')
        for block in page.get_text('blocks'):
            if not page.rect.contains(fitz.Rect(block[:4])):
                raise ValueError('Text outside page bounds.')
        # Fixed-height minipages can overflow without an Overfull warning.
        def hits(phrase: str):
            rects = page.search_for(phrase)
            if not rects:
                raise ValueError(f'Cannot locate {phrase}')
            return rects
        boundaries = {
            'unit-ball volume.': '3 Same six points',
            'Geometric priors select': '5 Perspective',
            'Learning gains remain': '6 Inria Startup Studio: Percolia',
            'share points.': '7 References',
            'Geometry-aware tools': '7 References',
        }
        for last_text, next_heading in boundaries.items():
            bottom = max(r.y1 for r in hits(last_text))
            top = min(r.y0 for r in hits(next_heading))
            if bottom >= top - 12:
                raise ValueError(f'Insufficient separation: {last_text} / {next_heading}')
        # Locate the QR in the Percolia block; its caption carries the link.
        links = page.get_links()
        qr_links = [link for link in links if link.get('uri') == LINKEDIN]
        if len(qr_links) != 1:
            raise ValueError(f'Expected one LinkedIn QR link, found {len(qr_links)}.')
        import cv2
        import numpy as np
        crop = fitz.Rect(page.rect.width / 2,
                         min(r.y0 for r in hits('6 Inria Startup Studio: Percolia')),
                         page.rect.width, min(r.y0 for r in hits('7 References')) - 12)
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), clip=crop, alpha=False)
        image = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, 3)
        ok, payloads, _, _ = cv2.QRCodeDetector().detectAndDecodeMulti(image)
        if not ok or list(payloads) != [LINKEDIN]:
            raise ValueError(f'QR payload mismatch: {payloads!r}')
        if any(link.get('uri') == 'https://github.com/Ludwig-H/Percolia' for link in links):
            raise ValueError('Obsolete project QR link remains.')
        if args.preview:
            page.get_pixmap(dpi=55, alpha=False).save(args.preview)
        print('PASS: one A0 page; fonts embedded; blocks separated; one decoded LinkedIn QR.')

if __name__ == '__main__':
    main()
