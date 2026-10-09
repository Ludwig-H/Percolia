#!/usr/bin/env python3
"""Build and check the Percolia Fête de la science presentation.

Run from this directory with Python 3. No Python packages are required.
External binary assets are pinned to source commits and SHA-256 checksums.
The neighbouring 3IA poster supplies its existing figures and illustrations.
"""

from __future__ import annotations

import calendar
from fractions import Fraction
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
PAGE_COUNT = 12
PDF = HERE / f"{JOB}.pdf"
ZIP = HERE / f"{JOB}_hors_connexion.zip"
VIDEO_NAMES = ("hgp_vs_hdbscan_light.mp4",)
NAVAL_VIDEO_NAMES = ("naval_chantier_question.mp4", "naval_chantier_solution.mp4")
NAVAL_VIDEO_POSTERS = ("assets/naval_chantier_question_affiche.png", "assets/naval_chantier_solution_affiche.png")
NAVAL_IMAGES = tuple(
    f"assets/naval_{kind}_view{view}.png"
    for kind in ("raw", "model", "result", "result_model")
    for view in (1, 2)
)
LEGACY_NAVAL_IMAGES = ("assets/naval_raw.png", "assets/naval_model.png")


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
        still = HERE / "assets" / "linkedin_light_affiche.png"
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


def check_naval_videos() -> dict:
    """Check rendered orbital views without rerunning the native v12 engine."""
    manifest_path = HERE / "naval_video_assets.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    sources = {}
    for entry in manifest["sources"].values():
        if not isinstance(entry, dict) or "file" not in entry:
            continue
        relative = entry["file"]
        source = HERE / relative
        if not source.resolve().is_relative_to(HERE) or not source.is_file() or sha256(source) != entry["sha256"]:
            raise ValueError(f"Naval Group orbital video source checksum mismatch: {relative}")
        if "bytes" in entry and source.stat().st_size != entry["bytes"]:
            raise ValueError(f"Naval Group orbital video source size mismatch: {relative}")
        sources[relative] = {"sha256": entry["sha256"], "bytes": source.stat().st_size}
    outputs = manifest["outputs"]
    required = {*(f"videos/{name}" for name in NAVAL_VIDEO_NAMES), *NAVAL_VIDEO_POSTERS}
    if set(outputs) != required:
        raise ValueError("The Naval Group video manifest must describe exactly two videos and two posters")
    checked = {}
    for relative, entry in sorted(outputs.items()):
        path = HERE / relative
        if not path.is_file() or sha256(path) != entry["sha256"] or path.stat().st_size != entry["bytes"]:
            raise ValueError(f"Naval Group video output checksum or size mismatch: {relative}")
        checked[relative] = {"sha256": entry["sha256"], "bytes": entry["bytes"]}
        if path.suffix == ".png":
            header = path.read_bytes()[:24]
            if header[:8] != b"\x89PNG\r\n\x1a\n":
                raise ValueError(f"Expected a Naval Group video poster in PNG: {relative}")
            width, height = struct.unpack(">II", header[16:24])
            if (width, height) != (entry["width"], entry["height"]):
                raise ValueError(f"Naval Group video poster dimensions mismatch: {relative}")
            checked[relative].update(width=width, height=height)
            continue
        probe = json.loads(command([
            "ffprobe", "-v", "error", "-count_frames", "-show_streams", "-show_format", "-of", "json", str(path),
        ]))
        picture = [stream for stream in probe["streams"] if stream["codec_type"] == "video"]
        if len(picture) != 1 or any(stream["codec_type"] == "audio" for stream in probe["streams"]):
            raise ValueError(f"Expected one video stream and no audio: {relative}")
        stream = picture[0]
        width, height = stream["width"], stream["height"]
        duration = float(probe["format"]["duration"])
        fps = Fraction(stream["avg_frame_rate"])
        frames = int(stream["nb_read_frames"])
        if stream["codec_name"] != "h264" or stream["pix_fmt"] != "yuv420p" or (width, height) != (1600, 900):
            raise ValueError(f"Unexpected Naval Group orbital video format: {relative}")
        if fps != 24 or frames != 288 or abs(duration - 12.0) > 0.02:
            raise ValueError(f"Expected a 12-second, 288-frame, 24-fps orbital video: {relative}")
        if ((width, height) != (entry["width"], entry["height"]) or fps != Fraction(str(entry["fps"]))
                or frames != entry["frames"] or abs(duration - entry["duration_seconds"]) > 0.02):
            raise ValueError(f"Naval Group orbital video manifest metadata mismatch: {relative}")
        checked[relative].update(codec=stream["codec_name"], width=width, height=height,
                                 duration_seconds=duration, fps=float(fps), frames=frames, audio=False)
    return {"manifest_sha256": sha256(manifest_path), "sources": sources, "outputs": checked}


def check_naval_assets() -> dict:
    """Check the committed views; original Drive source data are not CI inputs."""
    manifest = json.loads((HERE / "naval_assets.json").read_text(encoding="utf-8"))
    files = manifest["files"]
    required = {*NAVAL_IMAGES, *LEGACY_NAVAL_IMAGES, "naval_reference_components.json",
                "render_naval.py", "render_naval_views.py"}
    if not required.issubset(files):
        raise ValueError(f"Naval Group manifest is missing package inputs: {sorted(required - files.keys())}")
    checked = {}
    for relative, entry in sorted(files.items()):
        path = HERE / relative
        if not path.resolve().is_relative_to(HERE):
            raise ValueError(f"Invalid Naval Group asset path: {relative}")
        if not path.is_file():
            raise FileNotFoundError(f"Missing committed Naval Group asset: {relative}")
        if sha256(path) != entry["sha256"] or path.stat().st_size != entry["size"]:
            raise ValueError(f"Naval Group asset checksum or size mismatch: {relative}")
        checked[relative] = {"sha256": entry["sha256"], "size": entry["size"]}
        if path.suffix == ".png":
            with path.open("rb") as picture:
                header = picture.read(24)
            if header[:8] != b"\x89PNG\r\n\x1a\n":
                raise ValueError(f"Expected a PNG illustration: {relative}")
            width, height = struct.unpack(">II", header[16:24])
            if (width, height) != (entry["width"], entry["height"]):
                raise ValueError(f"Naval Group view dimensions mismatch: {relative}")
            checked[relative].update(width=width, height=height)
        elif path.suffix == ".json":
            json.loads(path.read_text(encoding="utf-8"))
        print(f"SHA-256 and size verified: {relative}", flush=True)
    return checked


def check_naval_v12_artifacts() -> dict:
    """Verify published analysis outputs without rerunning the 3D computation."""
    report_path = HERE / "naval_v12_report.json"
    if report_path.read_bytes() != (HERE / "naval_v12/naval_v12_report.json").read_bytes():
        raise ValueError("The deck and reproduction copies of the v12 report differ")
    report = json.loads(report_path.read_text(encoding="utf-8"))
    files = report["artifacts"]
    if "naval_v12/result.npz" not in files:
        raise ValueError("The v12 report must identify its representative-point result")
    checked = {}
    for relative, entry in sorted(files.items()):
        path = HERE / relative
        if not path.resolve().is_relative_to(HERE):
            raise ValueError(f"Invalid analysis artifact path: {relative}")
        if not path.is_file() or sha256(path) != entry["sha256"] or path.stat().st_size != entry["size"]:
            raise ValueError(f"Analysis artifact checksum or size mismatch: {relative}")
        if relative.endswith(".npz"):
            with zipfile.ZipFile(path) as archive:
                if archive.testzip() is not None:
                    raise ValueError(f"Analysis NPZ CRC check failed: {relative}")
                if relative == "naval_v12/result.npz":
                    required = {f"{name}.npy" for name in ("coords", "original_ids", "quantized_coords", "cluster_id", "class_id")}
                    if not required.issubset(archive.namelist()):
                        raise ValueError("Representative-point output is missing declared data fields")
        checked[relative] = {"sha256": entry["sha256"], "size": entry["size"]}
        print(f"SHA-256 verified: {relative}", flush=True)
    reproduction = {
        path.relative_to(HERE).as_posix(): {"sha256": sha256(path), "size": path.stat().st_size}
        for path in sorted((HERE / "naval_v12").rglob("*"))
        if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc"
    }
    if report["reproduction"]["entrypoint"] not in reproduction:
        raise ValueError("The v12 reproduction entrypoint is missing")
    return {"report_sha256": sha256(report_path), "artifacts": checked, "reproduction_files": reproduction}


def compile_pdf() -> dict:
    required_poster_files = (
        "assets/percolia.pdf",
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
    for path in (f"videos/{name}" for name in VIDEO_NAMES):
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
    files = [f"{JOB}.pdf", "lecteur.html", "NOTES_ORATEUR.md", "README.md", "external_assets.json", "build_report.json",
             "naval_assets.json", "naval_v12_report.json", "naval_video_assets.json", "render_naval_video.py"]
    naval = json.loads((HERE / "naval_assets.json").read_text(encoding="utf-8"))
    files += sorted(naval["files"])
    files += [path.relative_to(HERE).as_posix() for path in sorted((HERE / "naval_v12").rglob("*"))
              if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc"]
    files += slides
    files += [f"videos/{name}" for name in VIDEO_NAMES]
    files += [f"videos/{name}" for name in NAVAL_VIDEO_NAMES]
    files += list(NAVAL_VIDEO_POSTERS)
    files += ["assets/linkedin_light_affiche.png"]
    if len(files) != len(set(files)):
        raise ValueError("Offline package input list contains duplicate paths")
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
    naval = check_naval_assets()
    analysis = check_naval_v12_artifacts()
    videos = check_videos_and_extract_stills()
    naval_videos = check_naval_videos()
    pdf = compile_pdf()
    slides = render_slides()
    report = {"pdf": pdf, "videos": videos, "renders": {"count": len(slides), "width": 1600, "height": 900},
              "external_assets_sha256_verified": len(manifest["files"]), "naval_assets": naval,
              "naval_v12": analysis, "naval_videos": naval_videos}
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
