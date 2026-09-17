"""Check A0, numbering, horizontal Perspective separators, spacing and QR."""
import argparse
from pathlib import Path
import re

import fitz

LINKEDIN = 'https://www.linkedin.com/company/percolia/'
BODY_COLOUR = (0.961, 0.963, 0.967)


def check_source(directory: Path) -> None:
    """Keep the notation and the GPT -> LiDAR -> hierarchy reading order."""
    source = (directory / 'poster.tex').read_text(encoding='utf-8')
    theme = (directory / 'beamerthemegemini.sty').read_text(encoding='utf-8')
    forbidden = [r'\rho', r'\begin{gathered}', r'\begin{aligned}',
                 'Its branches may share points.',
                 'Range, scan pattern and occlusion change the point cloud.',
                 'Polyhedra as tokens; hierarchy as multiscale context.']
    for token in forbidden:
        if token in source:
            raise ValueError(f'Obsolete or multiline content: {token}')
    numbers = re.findall(r'\\begin\{posterbox\}(?:\[[^\]]*\])?\{(\d+)\}', source)
    if numbers != [str(i) for i in range(1, 8)]:
        raise ValueError(f'Expected numbered blocks 1 to 7, found {numbers}.')
    sequence = [r'\widehat f\gets\widehat f_{K\text{-NN}}',
                r'\widehat f_{K\text{-NN}}(y)=', 'Change of variable:']
    positions = [source.index(token) for token in sequence]
    if positions != sorted(positions):
        raise ValueError('Estimator / formula / change-of-variable order changed.')
    parts = re.findall(r'\\begin\{perspectivesubblock\}\{[^}]+\}(.*?)'
                       r'\\end\{perspectivesubblock\}', source, re.S)
    figures = ['figures/gpt_subwords.tex', 'figures/defense/verrou_portee.tex',
               'figures/defense/hierarchie_surfaces.tex']
    if len(parts) != 3 or not all(fig in part for fig, part in zip(figures, parts)):
        raise ValueError('Perspective must contain GPT, LiDAR and hierarchy, in that order.')
    if source.count(r'\perspectivesubgap') != 2:
        raise ValueError('Perspective requires exactly two horizontal separators.')
    if 'perspective subbody' in theme:
        raise ValueError('The separate painted Perspective panels must not return.')
    if source.count('Research hypothesis:') != 1:
        raise ValueError('Use one combined research-hypothesis sentence.')
    if r'\includegraphics[width=0.84\linewidth]{assets/shipyard.png}' not in source:
        raise ValueError('The Naval Group illustration should remain reduced to 84%.')


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('pdf', type=Path)
    parser.add_argument('--preview', type=Path)
    args = parser.parse_args()
    check_source(Path(__file__).resolve().parent)
    with fitz.open(args.pdf) as doc:
        if len(doc) != 1:
            raise ValueError('Expected exactly one page.')
        page = doc[0]
        size = page.rect.width * 25.4 / 72, page.rect.height * 25.4 / 72
        if abs(size[0] - 841) > .1 or abs(size[1] - 1189) > .1:
            raise ValueError(f'Not A0 portrait: {size}')
        text = page.get_text()
        required = ['DBSCAN / Robust SL', 'HGP-Clusterer', 'Near', 'Far',
                    'Marie', 'Alban', 'Research hypothesis', 'Naval Group',
                    'model and hierarchy', 'Euclidean distance',
                    'non-parametric', 'Change of variable', 'parts of words',
                    'geometric pieces as tokens', 'Language Models are Few-Shot Learners',
                    'Inria Startup Studio: Percolia', 'References']
        for phrase in required:
            if phrase.casefold() not in text.casefold():
                raise ValueError(f'Missing content: {phrase}')
        if '\u03c1' in text or 'Its branches may share points.' in text:
            raise ValueError('Obsolete notation or prose remains in the PDF.')
        for xref, _, _, name, *_ in page.get_fonts(full=True):
            if not doc.extract_font(xref)[3]:
                raise ValueError(f'Font not embedded: {name}')
        for block in page.get_text('blocks'):
            if not page.rect.contains(fitz.Rect(block[:4])):
                raise ValueError('Text outside page bounds.')

        def hits(phrase: str):
            rects = page.search_for(phrase)
            if not rects:
                raise ValueError(f'Cannot locate {phrase}')
            return rects

        drawings = page.get_drawings()
        bodies, headers = [], []
        for drawing in drawings:
            rect, fill = drawing['rect'], drawing['fill']
            if fill is None or rect.width < 1000:
                continue
            if all(abs(a - b) < .004 for a, b in zip(fill, BODY_COLOUR)) and rect.height > 100:
                bodies.append(rect)
            if 45 < rect.height < 60 and rect.y0 > 280:
                headers.append(rect)
        if len(bodies) != 7 or len(headers) != 7:
            raise ValueError(f'Expected seven cards, found {len(bodies)} bodies / {len(headers)} headers.')
        for body in bodies:
            adjoining = [h for h in headers if abs(h.x0 - body.x0) < 1 and abs(h.y1 - body.y0) < 1]
            if len(adjoining) != 1:
                raise ValueError('Card title and body are not joined.')
        reference_header = next(h for h in headers if h.width > 2000)
        gap_target = 8 * 72 / 25.4
        for right_column in (False, True):
            column = sorted([b for b in bodies if b.width < 2000 and
                             (b.x0 > page.rect.width / 2) == right_column], key=lambda r: r.y0)
            if len(column) != 3:
                raise ValueError('Each narrative column must have three cards.')
            for body in column:
                next_titles = [h for h in headers if h.y0 > body.y1 and
                               (abs(h.x0 - body.x0) < 1 or h.width > 2000)]
                next_title = min(next_titles, key=lambda h: h.y0)
                if abs(next_title.y0 - body.y1 - gap_target) > .75:
                    raise ValueError('Irregular inter-block spacing.')

        reading_order = sorted(headers, key=lambda r: (r.width > 2000,
                               r.x0 > page.rect.width / 2, r.y0))
        for number, header in enumerate(reading_order, 1):
            heading = page.get_textbox(header).strip()
            if not re.match(rf'^{number}\s', heading):
                raise ValueError(f'Wrong rendered block number: {heading!r}')

        layout_top, layout_bottom = min(h.y0 for h in headers), max(b.y1 for b in bodies)
        allowed = [fitz.Rect(r.x0 - 1, r.y0 - 1, r.x1 + 1, r.y1 + 1) for r in bodies + headers]
        lines = [line for block in page.get_text('dict')['blocks']
                 for line in block.get('lines', [])]
        for line in lines:
            rect = fitz.Rect(line['bbox'])
            if layout_top <= rect.y0 < layout_bottom and not any(r.contains(rect) for r in allowed):
                content = ''.join(span['text'] for span in line['spans'])
                raise ValueError(f'Text exceeds its card: {content}')

        # A single background and two thin, full-width horizontal rules.
        right_bodies = sorted([b for b in bodies if b.x0 > page.rect.width / 2], key=lambda r: r.y0)
        naval_body, perspective_body, _ = right_bodies
        white_panels = [d for d in drawings if d['fill'] is not None
                        and all(abs(v - 1) < .004 for v in d['fill'])
                        and d['rect'].width > 1000 and d['rect'].height > 100
                        and perspective_body.contains(d['rect'])]
        if white_panels:
            raise ValueError('Separate white backgrounds remain in Perspective.')
        rules = sorted([d['rect'] for d in drawings if d['fill'] is None
                        and d['color'] is not None and d['rect'].width > 1000
                        and d['rect'].height < .1 and .8 < (d['width'] or 0) < 1.2
                        and perspective_body.contains(d['rect'])], key=lambda r: r.y0)
        if len(rules) != 2:
            raise ValueError(f'Expected two Perspective separators, found {len(rules)}.')
        if abs(rules[0].x0 - rules[1].x0) > .5 or abs(rules[0].x1 - rules[1].x1) > .5:
            raise ValueError('Perspective separators are not aligned.')
        if abs(rules[0].width - (perspective_body.width - 10 * 72 / 25.4)) > .75:
            raise ValueError('Perspective separators must follow the inner text margins.')
        # No text may cross a separator or touch it within 3 mm.
        clearance = 3 * 72 / 25.4
        for line in lines:
            rect = fitz.Rect(line['bbox'])
            if perspective_body.contains(rect):
                for rule in rules:
                    if rect.y0 < rule.y0 + clearance and rect.y1 > rule.y0 - clearance:
                        raise ValueError('Perspective text touches a separator.')
        if max(r.y1 for r in hits('parts of words') + hits('geometric pieces as tokens')) >= rules[0].y0:
            raise ValueError('The GPT analogy must be above the first separator.')
        if not all(rules[0].y0 < r.y0 < rules[1].y0 for r in hits('Near object') + hits('Far object')):
            raise ValueError('The LiDAR figure must be between the separators.')
        if min(r.y0 for r in hits('Research hypothesis')) <= rules[1].y0:
            raise ValueError('The combined hypothesis must follow the hierarchy.')

        naval_images = [fitz.Rect(i['bbox']) for i in page.get_image_info()
                        if naval_body.contains(fitz.Rect(i['bbox']))]
        if len(naval_images) != 1:
            raise ValueError('Cannot identify the Naval Group illustration.')
        inner_width = naval_body.width - 10 * 72 / 25.4
        if abs(naval_images[0].width / inner_width - .84) > .002:
            raise ValueError('Unexpected Naval Group illustration size.')

        links = page.get_links()
        qr_links = [link for link in links if link.get('uri') == LINKEDIN]
        if len(qr_links) != 1:
            raise ValueError(f'Expected one LinkedIn link, found {len(qr_links)}.')
        import cv2
        import numpy as np
        crop = fitz.Rect(page.rect.width / 2,
                         min(r.y0 for r in hits('Inria Startup Studio: Percolia')),
                         page.rect.width, reference_header.y0 - 12)
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), clip=crop, alpha=False)
        image = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, 3)
        ok, payloads, _, _ = cv2.QRCodeDetector().detectAndDecodeMulti(image)
        if not ok or list(payloads) != [LINKEDIN]:
            raise ValueError(f'QR payload mismatch: {payloads!r}')
        if any(link.get('uri') == 'https://github.com/Ludwig-H/Percolia' for link in links):
            raise ValueError('Obsolete project QR link remains.')
        if args.preview:
            page.get_pixmap(dpi=55, alpha=False).save(args.preview)
        print('PASS: A0, embedded fonts, seven numbered cards, two Perspective separators, '
              'no white panels, 8 mm card gaps, reduced Naval image and LinkedIn QR.')


if __name__ == '__main__':
    main()
