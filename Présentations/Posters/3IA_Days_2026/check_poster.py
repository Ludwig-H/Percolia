"""Check A0, embedded fonts, content ordering and the decoded LinkedIn QR."""
import argparse
from pathlib import Path
import fitz

LINKEDIN = 'https://www.linkedin.com/company/percolia/'

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('pdf',type=Path)
    parser.add_argument('--preview',type=Path)
    args = parser.parse_args()
    with fitz.open(args.pdf) as doc:
        if len(doc) != 1:
            raise ValueError('Expected exactly one page.')
        page = doc[0]
        size = page.rect.width*25.4/72,page.rect.height*25.4/72
        if abs(size[0]-841) > .1 or abs(size[1]-1189) > .1:
            raise ValueError(f'Not A0 portrait: {size}')
        text = page.get_text()
        for required in ['DBSCAN / Robust SL','Hartigan','HGP-Clusterer',
                         'Near','Far','Marie','Alban','Research hypothesis',
                         'Startup Studio','Naval Group','References']:
            if required not in text:
                raise ValueError(f'Missing content: {required}')
        for xref,_,_,name,*_ in page.get_fonts(full=True):
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
        reference_top = min(r.y0 for r in hits('6 References'))
        for phrase in ['HGP-Clusterer connects','share points.','Learning gains remain']:
            if max(r.y1 for r in hits(phrase)) >= reference_top-12:
                raise ValueError(f'Scientific text overlaps references: {phrase}')
        brand_top = min(r.y0 for r in hits('Percolia'))
        if max(r.y1 for r in hits('Inria Annual Report')) >= brand_top-12:
            raise ValueError('References overlap the footer.')
        import cv2
        import numpy as np
        crop = fitz.Rect(page.rect.width*.80,page.rect.height*.87,
                         page.rect.width*.98,page.rect.height*.945)
        pix = page.get_pixmap(matrix=fitz.Matrix(2,2),clip=crop,alpha=False)
        image = np.frombuffer(pix.samples,dtype=np.uint8).reshape(pix.height,pix.width,3)
        decoded,points,_ = cv2.QRCodeDetector().detectAndDecode(image)
        if decoded != LINKEDIN:
            raise ValueError(f'QR payload mismatch: {decoded!r}')
        if 'https://github.com/Ludwig-H/Percolia' in [l.get('uri','') for l in page.get_links()]:
            raise ValueError('Obsolete project QR link remains.')
        if args.preview:
            page.get_pixmap(dpi=55,alpha=False).save(args.preview)
        print('PASS: one A0 page; fonts embedded; scientific text and references separated; one LinkedIn QR.')

if __name__ == '__main__':
    main()
