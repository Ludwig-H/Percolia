"""Raster the checked A0 poster to a PNG with the same content, at print resolution."""
import argparse
from pathlib import Path

import fitz

DEFAULT_DPI = 300
A0_MM = (841.0, 1189.0)


def render(pdf: Path, png: Path, dpi: int) -> tuple[int, int]:
    """Render the single poster page to an opaque RGB PNG and return its size."""
    with fitz.open(pdf) as doc:
        if len(doc) != 1:
            raise ValueError('Expected exactly one page.')
        page = doc[0]
        size = page.rect.width * 25.4 / 72, page.rect.height * 25.4 / 72
        if abs(size[0] - A0_MM[0]) > .1 or abs(size[1] - A0_MM[1]) > .1:
            raise ValueError(f'Not A0 portrait: {size}')
        pixmap = page.get_pixmap(dpi=dpi, alpha=False, colorspace=fitz.csRGB)
    expected = tuple(mm / 25.4 * dpi for mm in A0_MM)
    if any(abs(got - want) > 1 for got, want in
           zip((pixmap.width, pixmap.height), expected)):
        raise ValueError(f'Unexpected raster size: {pixmap.width}x{pixmap.height}')
    pixmap.set_dpi(dpi, dpi)
    png.parent.mkdir(parents=True, exist_ok=True)
    pixmap.save(png)
    return pixmap.width, pixmap.height


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('pdf', type=Path)
    parser.add_argument('png', type=Path)
    parser.add_argument('--dpi', type=int, default=DEFAULT_DPI)
    args = parser.parse_args()
    if args.dpi < 72:
        raise ValueError('Use at least 72 dpi.')
    width, height = render(args.pdf, args.png, args.dpi)
    print(f'PASS: {args.png} rendered at {args.dpi} dpi, {width}x{height} px, A0 portrait.')


if __name__ == '__main__':
    main()
