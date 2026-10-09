#!/usr/bin/env python3
"""Build and check the Percolia Fête de la science presentation.

Run from this directory with Python 3. No Python packages are required.
External binary assets are pinned to source commits and SHA-256 checksums.
The neighbouring 3IA poster supplies its existing figures and illustrations.
"""

from __future__ import annotations

import calendar
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import tempfile
import urllib.parse
import urllib.request
import zipfile
import zlib


HERE = Path(__file__).resolve().parent
JOB = "Fete_de_la_science_2026_Percolia"
PAGE_COUNT = 9
PDF = HERE / f"{JOB}.pdf"
ZIP = HERE / f"{JOB}_hors_connexion.zip"
VIDEO_NAMES = ("hgp_vs_hdbscan_light.mp4", "hgp_vs_hdbscan_dark.mp4")


def sha256(path: Path) -> str:
    with path.open("rb") as handle:
        digest = hashlib.file_digest(handle, "sha256")
    return digest.hexdigest()


def command(args: list[str], *, env: dict[str, str] | None = None) -> str:
    print("+", " ".join(args), flush=True)
    completed = subprocess.run(
        args, cwd=HERE, env=env, check=False,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
    )
    if completed.returncode:
        print(completed.stdout, flush=True)
        raise RuntimeError(f"Command failed ({completed.returncode}): {args[0]}")
    return completed.stdout


def restore_external_assets() -> dict:
    manifest = json.loads((HERE / "external_assets.json").read_text(encoding="utf-8"))
    for relative, entry in manifest["files"].items():
        target = HERE / relative
        if not target.resolve().is_relative_to(HERE):
            raise ValueError(f"Invalid destination: {relative}")
        source = urllib.parse.urlsplit(entry["url"])
        parts = source.path.strip("/").split("/")
        if (source.scheme != "https" or source.netloc != "raw.githubusercontent.com"
                or len(parts) < 4 or not re.fullmatch(r"[0-9a-f]{40}", parts[2])):
            raise ValueError(f"External asset must use an immutable public GitHub revision: {relative}")
        if not target.is_file() or sha256(target) != entry["sha256"]:
            request = urllib.request.Request(entry["url"], headers={"User-Agent": "Percolia-science-build"})
            with urllib.request.urlopen(request, timeout=120) as response:
                data = response.read()
            if hashlib.sha256(data).hexdigest() != entry["sha256"]:
                raise ValueError(f"Downloaded SHA-256 mismatch: {relative}")
            target.parent.mkdir(parents=True, exist_ok=True)
            temporary = target.with_suffix(target.suffix + ".download")
            temporary.write_bytes(data)
            temporary.replace(target)
        if target.stat().st_size != entry["size"]:
            raise ValueError(f"Size mismatch: {relative}")
        print(f"SHA-256 verified: {relative}", flush=True)
    return manifest


def check_videos_and_extract_stills() -> dict:
    videos = {}
    for name in VIDEO_NAMES:
        path = HERE / "videos" / name
        probe = json.loads(command([
            "ffprobe", "-v", "error", "-show_streams", "-show_format",
            "-of", "json", str(path),
        ]))
        streams = probe["streams"]
        picture = [stream for stream in streams if stream["codec_type"] == "video"]
        if len(picture) != 1 or any(stream["codec_type"] == "audio" for stream in streams):
            raise ValueError(f"Expected one video stream and no audio: {name}")
        video = picture[0]
        duration = float(probe["format"]["duration"])
        if video["codec_name"] != "h264" or (video["width"], video["height"]) != (1080, 1350):
            raise ValueError(f"Unexpected video format: {name}")
        if abs(duration - 100.7) > 0.1:
            raise ValueError(f"Unexpected video duration ({duration}): {name}")
        theme = "light" if "light" in name else "dark"
        still = HERE / "assets" / f"linkedin_{theme}_affiche.png"
        still.parent.mkdir(exist_ok=True)
        command([
            "ffmpeg", "-v", "error", "-y", "-ss", "14", "-i", str(path),
            "-frames:v", "1", "-update", "1", str(still),
        ])
        videos[name] = {
            "codec": video["codec_name"], "width": video["width"], "height": video["height"],
            "duration_seconds": duration, "audio": False, "sha256": sha256(path),
            "still_at_seconds": 14,
        }
    return videos


def compile_pdf() -> dict:
    required_poster_files = (
        "assets/shipyard.png", "assets/percolia.pdf",
        "figures/defense/deuxnn_r_boules.tex", "figures/defense/deuxnn_rp_boules.tex",
        "figures/defense/deuxnn_rs_boules.tex",
    )
    poster = HERE.parent / "Posters" / "3IA_Days_2026"
    for relative in required_poster_files:
        if not (poster / relative).is_file():
            raise FileNotFoundError(f"Missing existing 3IA-poster input: {relative}")
    environment = os.environ.copy()
    environment.setdefault("SOURCE_DATE_EPOCH", str(calendar.timegm((2026, 10, 10, 0, 0, 0))))
    environment["FORCE_SOURCE_DATE"] = "1"
    for number in (1, 2):
        output = command([
            "pdflatex", "-interaction=nonstopmode", "-halt-on-error", "-file-line-error",
            "-no-shell-escape", f"-jobname={JOB}", "slides.tex",
        ], env=environment)
        (HERE / f"compile-{number}.log").write_text(output, encoding="utf-8")
    log = (HERE / f"{JOB}.log").read_text(encoding="utf-8", errors="replace")
    excess = [(kind, float(amount)) for kind, amount in re.findall(
        r"Overfull \\([hv])box \(([0-9.]+)pt too (?:wide|high)\)", log
    ) if float(amount) > 1.0]
    if excess:
        raise ValueError(f"LaTeX overflow larger than 1 pt: {excess}")
    if any(problem in log for problem in ("undefined references", "undefined citations", "Missing character:")):
        raise ValueError("LaTeX has unresolved references, citations, or missing characters")
    info = command(["pdfinfo", str(PDF)])
    (HERE / "pdfinfo.txt").write_text(info, encoding="utf-8")
    pages = re.search(r"^Pages:\s+(\d+)$", info, flags=re.MULTILINE)
    if not pages or int(pages[1]) != PAGE_COUNT:
        raise ValueError(f"Expected {PAGE_COUNT} pages; pdfinfo says {pages[1] if pages else 'unknown'}")
    size = re.search(r"^Page size:\s+([0-9.]+) x ([0-9.]+) pts", info, flags=re.MULTILINE)
    if not size or abs(float(size[1]) / float(size[2]) - 16 / 9) > 0.002:
        raise ValueError("Expected 16:9 slides")
    # pdfLaTeX normally compresses its annotation objects; inspect Flate streams too.
    pdf_data = PDF.read_bytes()
    expanded_pdf = bytearray(pdf_data)
    for stream in re.finditer(rb"\bstream\r?\n(.*?)\r?\nendstream", pdf_data, flags=re.DOTALL):
        try:
            expanded_pdf.extend(zlib.decompress(stream[1]))
        except zlib.error:
            pass
    for path in ("videos/hgp_vs_hdbscan_light.mp4", "videos/hgp_vs_hdbscan_dark.mp4"):
        if path.encode() not in expanded_pdf:
            raise ValueError(f"Missing local video hyperlink in PDF: {path}")
    command(["pdftotext", str(PDF), str(HERE / "slides.txt")])
    return {"pages": PAGE_COUNT, "aspect_ratio": "16:9", "sha256": sha256(PDF), "overfull_boxes_over_1pt": 0}


def render_slides() -> list[str]:
    output = HERE / "diapositives"
    output.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="percolia-slides-") as temporary:
        prefix = Path(temporary) / "page"
        command(["pdftoppm", "-png", "-scale-to-x", "1600", "-scale-to-y", "900", str(PDF), str(prefix)])
        pages = sorted(Path(temporary).glob("page-*.png"), key=lambda path: int(path.stem.split("-")[-1]))
        if len(pages) != PAGE_COUNT:
            raise ValueError("Rendered page count differs from PDF page count")
        for number, page in enumerate(pages, 1):
            with page.open("rb") as image:
                header = image.read(24)
            if header[:8] != b"\x89PNG\r\n\x1a\n" or struct.unpack(">II", header[16:24]) != (1600, 900):
                raise ValueError(f"Unexpected render dimensions: {page}")
            shutil.copyfile(page, output / f"slide-{number:02}.png")
    return [f"diapositives/slide-{number:02}.png" for number in range(1, PAGE_COUNT + 1)]


def make_offline_zip(slides: list[str]) -> list[str]:
    files = [f"{JOB}.pdf", "lecteur.html", "NOTES_ORATEUR.md", "README.md", "external_assets.json", "build_report.json"]
    files += slides
    files += [f"videos/{name}" for name in VIDEO_NAMES]
    files += ["assets/linkedin_light_affiche.png", "assets/linkedin_dark_affiche.png"]
    html = (HERE / "lecteur.html").read_text(encoding="utf-8")
    if "http://" in html or "https://" in html:
        # External source links are allowed, but no script, CSS, image or video is fetched remotely.
        if re.search(r"(?:src|href)\s*=\s*['\"]https?://", html, flags=re.IGNORECASE):
            raise ValueError("The offline reader has an external resource dependency")
    for relative in files:
        if not (HERE / relative).is_file():
            raise FileNotFoundError(f"Offline package input missing: {relative}")
    checksums = "".join(f"{sha256(HERE / relative)}  {relative}\n" for relative in sorted(files))
    (HERE / "SHA256SUMS.txt").write_text(checksums, encoding="utf-8")
    files.append("SHA256SUMS.txt")
    with zipfile.ZipFile(ZIP, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for relative in sorted(files):
            data = (HERE / relative).read_bytes()
            item = zipfile.ZipInfo(relative, date_time=(2026, 10, 10, 0, 0, 0))
            item.compress_type = zipfile.ZIP_STORED if relative.endswith((".mp4", ".png")) else zipfile.ZIP_DEFLATED
            item.external_attr = 0o100644 << 16
            archive.writestr(item, data)
    with zipfile.ZipFile(ZIP) as archive:
        if archive.testzip() is not None:
            raise ValueError("Offline ZIP CRC check failed")
    return files


def main() -> None:
    for executable in ("pdflatex", "pdfinfo", "pdftotext", "pdftoppm", "ffmpeg", "ffprobe"):
        if shutil.which(executable) is None:
            raise RuntimeError(f"Required tool is not installed: {executable}")
    manifest = restore_external_assets()
    videos = check_videos_and_extract_stills()
    pdf = compile_pdf()
    slides = render_slides()
    report = {"pdf": pdf, "videos": videos, "renders": {"count": len(slides), "width": 1600, "height": 900},
              "external_assets_sha256_verified": len(manifest["files"])}
    (HERE / "build_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    files = make_offline_zip(slides)
    published = files + [ZIP.name]
    (HERE / "SHA256SUMS_RELEASE.txt").write_text(
        "".join(f"{sha256(HERE / relative)}  {relative}\n" for relative in sorted(published)),
        encoding="utf-8",
    )
    print(f"Checked PDF: {PDF.name} ({PAGE_COUNT} pages)")
    print(f"Offline ZIP: {ZIP.name} ({len(files)} files, SHA-256 {sha256(ZIP)})")


if __name__ == "__main__":
    main()
