#!/usr/bin/env python3
"""Two matching 360-degree Naval benchmark videos, from exact existing inputs.

The raw XYZ coordinates and actual v12 node labels come from result.npz. The
right panel contains only the supplied triangles of the 14 named CAD objects.
It never uses bounding boxes or anomaly meshes as displayed model geometry.
Both point panels preserve the same original PointIds, camera and crop. A small
embedded C++ rasterizer provides an opaque depth buffer for points and triangles.
No HGP calculation, geometric classification, or external download is performed.
"""
from __future__ import annotations

import argparse
import ctypes
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import time

import numpy as np
from PIL import Image, ImageDraw, ImageFont


RESULT_SHA256 = '6535e19d52d62b24c7bdee6fb8f16c5212e0dfe66de2131b8aae05449de7bdd2'
MODEL_SHA256 = '18405ab5a78149749f6146dbc91ea8cfbb939eedfeca4c6053748ecf51f72d3f'
CAD_NAMES = ['Cube_1', 'Cube_2', 'Cube_3', 'Equerre_1', 'Equerre_2',
             'Equerre_3', 'Pipe_1', 'Pipe_2', 'Pipe_3', 'Pipe_4',
             'Pipe_10', 'Pipe_11', 'Plane_1', 'Plane_2']
PALETTE = ['#e69f00', '#0072b2', '#009e73', '#8e55a1', '#b85c9d']

RASTER_SOURCE = r'''
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <vector>
extern "C" void points(const float* xyz, const uint8_t* color, int n,
                         int w, int h, float radius, uint8_t* rgb) {
  std::fill(rgb, rgb + 3*w*h, 255);
  std::vector<float> zbuf(w*h, -INFINITY);
  const float rr = radius*radius;
  for (int i=0; i<n; ++i) {
    const float x=xyz[3*i], y=xyz[3*i+1], z=xyz[3*i+2];
    const int x0=std::max(0,int(std::floor(x-radius)));
    const int x1=std::min(w-1,int(std::ceil(x+radius)));
    const int y0=std::max(0,int(std::floor(y-radius)));
    const int y1=std::min(h-1,int(std::ceil(y+radius)));
    for (int yy=y0; yy<=y1; ++yy) for (int xx=x0; xx<=x1; ++xx) {
      const float dx=xx+.5f-x, dy=yy+.5f-y;
      if (dx*dx+dy*dy > rr) continue;
      const int p=yy*w+xx;
      if (z <= zbuf[p]) continue;
      zbuf[p]=z;
      rgb[3*p]=color[3*i]; rgb[3*p+1]=color[3*i+1]; rgb[3*p+2]=color[3*i+2];
    }
  }
}
extern "C" void triangles(const float* xyz, const int32_t* tri,
                            const uint8_t* color, int n, int w, int h,
                            uint8_t* rgb) {
  std::fill(rgb, rgb + 3*w*h, 255);
  std::vector<float> zbuf(w*h, -INFINITY);
  for (int i=0; i<n; ++i) {
    const float* a=xyz+3*tri[3*i];
    const float* b=xyz+3*tri[3*i+1];
    const float* c=xyz+3*tri[3*i+2];
    const float den=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1]);
    if (std::abs(den)<1e-7f) continue;
    const int x0=std::max(0,int(std::floor(std::min({a[0],b[0],c[0]}))));
    const int x1=std::min(w-1,int(std::ceil(std::max({a[0],b[0],c[0]}))));
    const int y0=std::max(0,int(std::floor(std::min({a[1],b[1],c[1]}))));
    const int y1=std::min(h-1,int(std::ceil(std::max({a[1],b[1],c[1]}))));
    for (int yy=y0; yy<=y1; ++yy) for (int xx=x0; xx<=x1; ++xx) {
      const float x=xx+.5f, y=yy+.5f;
      const float wa=((b[1]-c[1])*(x-c[0])+(c[0]-b[0])*(y-c[1]))/den;
      const float wb=((c[1]-a[1])*(x-c[0])+(a[0]-c[0])*(y-c[1]))/den;
      const float wc=1-wa-wb;
      if (wa < -1e-6f || wb < -1e-6f || wc < -1e-6f) continue;
      const float z=wa*a[2]+wb*b[2]+wc*c[2];
      const int p=yy*w+xx;
      if (z <= zbuf[p]) continue;
      zbuf[p]=z;
      rgb[3*p]=color[3*i]; rgb[3*p+1]=color[3*i+1]; rgb[3*p+2]=color[3*i+2];
    }
  }
}
'''


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for part in iter(lambda: f.read(1024 * 1024), b''):
            h.update(part)
    return h.hexdigest()


def rgb(hex_color):
    return [int(hex_color[i:i+2], 16) for i in (1, 3, 5)]


def load_helper():
    path = Path(__file__).with_name('render_naval.py')
    spec = importlib.util.spec_from_file_location('naval_video_base', path)
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    return helper


def font(size, bold=False):
    filename = 'DejaVuSans-Bold.ttf' if bold else 'DejaVuSans.ttf'
    for root in [Path('/usr/share/fonts/truetype/dejavu'), Path('/usr/share/fonts/dejavu')]:
        if (root / filename).exists():
            return ImageFont.truetype(str(root / filename), size)
    return ImageFont.truetype(filename, size)


def build_rasterizer(folder):
    compiler = shutil.which('g++')
    if not compiler:
        raise RuntimeError('g++ is required for the temporary depth-buffer renderer')
    source, library = folder / 'raster.cpp', folder / 'raster.so'
    source.write_text(RASTER_SOURCE)
    subprocess.run([compiler, '-O3', '-std=c++17', '-fPIC', '-shared',
                    str(source), '-o', str(library)], check=True)
    lib = ctypes.CDLL(str(library))
    floats = np.ctypeslib.ndpointer(dtype=np.float32, flags='C_CONTIGUOUS')
    ints = np.ctypeslib.ndpointer(dtype=np.int32, flags='C_CONTIGUOUS')
    bytes_ = np.ctypeslib.ndpointer(dtype=np.uint8, flags='C_CONTIGUOUS')
    lib.points.argtypes = [floats, bytes_, ctypes.c_int, ctypes.c_int,
                           ctypes.c_int, ctypes.c_float, bytes_]
    lib.triangles.argtypes = [floats, ints, bytes_, ctypes.c_int,
                              ctypes.c_int, ctypes.c_int, bytes_]
    return lib


def screen_projection(xyz, helper, azimuth, elevation, center, bounds, w, h):
    view = helper.project(xyz, helper.camera_basis(azimuth, elevation), center)
    view[:, 0] = (view[:, 0] - bounds[0]) / (bounds[1] - bounds[0]) * w
    view[:, 1] = (bounds[3] - view[:, 1]) / (bounds[3] - bounds[2]) * h
    return np.ascontiguousarray(view, dtype=np.float32)


def prepare(args, helper):
    if sha256(args.result) != RESULT_SHA256:
        raise ValueError('result.npz differs from the pinned, reviewed v12 result')
    if sha256(args.model) != MODEL_SHA256:
        raise ValueError('bloc_full.ply differs from the original supplied Naval geometry')
    data = np.load(args.result, allow_pickle=False)
    coords = np.asarray(data['coords'], dtype=np.float64)
    ids = np.asarray(data['original_ids'], dtype=np.int64)
    classes, labels = np.asarray(data['class_id']), np.asarray(data['cluster_id'])
    if coords.shape != (330543, 3) or ids.shape != (len(coords),):
        raise ValueError('Unexpected reviewed ROI dimensions')
    if len(np.unique(ids)) != len(ids) or not np.isfinite(coords).all():
        raise ValueError('PointId duplication or nonfinite raw XYZ')
    if args.raw:
        original = helper.load_xyz(args.raw)
        if not np.array_equal(original[ids], coords):
            raise ValueError('NPZ raw coordinates are not exactly the original scan coordinates')
    selection = np.arange(0, len(coords), args.stride)
    points, drawn_ids = coords[selection], ids[selection]
    raw_colors = np.tile(np.asarray(rgb('#39444c'), dtype=np.uint8), (len(points), 1))
    colors = np.tile(np.asarray(rgb('#b6bdc3'), dtype=np.uint8), (len(points), 1))
    colors[classes[selection] == 0] = rgb('#c9191e')
    palette = {int(k): PALETTE[i] for i, k in enumerate(np.unique(labels[classes == 1]))}
    if len(palette) != 5 or np.any(labels[classes == 1] < 0):
        raise ValueError('Expected the five real, nonnegative native K3 node identifiers')
    for label, color in palette.items():
        colors[(classes[selection] == 1) & (labels[selection] == label)] = rgb(color)
    vertices, source_faces = helper.read_ply(args.model)
    components = json.loads(args.components.read_text())
    if components['mesh_sha256'] != MODEL_SHA256 or sorted(components['known_object_names']) != sorted(CAD_NAMES):
        raise ValueError('CAD component provenance differs from the 14 reviewed infrastructure objects')
    vertex_object = np.full(len(vertices), -1, np.int32)
    for object_index, name in enumerate(CAD_NAMES):
        v = np.asarray(components['named_vertex_ids'][name], dtype=np.int64)
        if np.any(vertex_object[v] != -1):
            raise ValueError('Named CAD vertex groups overlap')
        vertex_object[v] = object_index
    faces = []
    for face in source_faces:
        if len(face) != 3:
            raise ValueError('Original CAD mesh must contain triangle faces')
        groups = vertex_object[np.asarray(face)]
        if groups[0] >= 0:
            if np.any(groups != groups[0]):
                raise ValueError('Original triangle crosses named component groups')
            faces.append(face)
    triangles = np.ascontiguousarray(faces, dtype=np.int32)
    kept_vertices = np.unique(triangles)
    if len(triangles) != 4152 or len(kept_vertices) != 2102:
        raise ValueError('Expected exactly 4152 real CAD triangles and 2102 vertices')
    light = np.asarray([-.35, -.3, .88]); light /= np.linalg.norm(light)
    polygons = vertices[triangles]
    normals = np.cross(polygons[:, 1] - polygons[:, 0], polygons[:, 2] - polygons[:, 0])
    lengths = np.linalg.norm(normals, axis=1)
    if np.any(lengths <= 0):
        raise ValueError('Degenerate triangle in original CAD geometry')
    normals /= lengths[:, None]
    shade = .66 + .30 * np.abs(normals @ light)
    mesh_colors = np.asarray(np.round(255 * np.clip(
        np.asarray([.48, .61, .70])[None, :] * shade[:, None] + .13, 0, 1)), dtype=np.uint8)
    ground = vertex_object[triangles[:, 0]] == CAD_NAMES.index('Plane_1')
    mesh_colors[ground] = rgb('#e1e8ed')
    low = np.minimum(coords.min(0), vertices[kept_vertices].min(0))
    high = np.maximum(coords.max(0), vertices[kept_vertices].max(0))
    center = (low + high) / 2
    half = (high - low) / 2
    xy_radius = float(np.hypot(half[0], half[1]))
    el = np.deg2rad(args.elevation)
    horizontal = xy_radius * 1.055
    vertical = (np.sin(el) * xy_radius + np.cos(el) * half[2]) * 1.055
    width = (args.width - 3 * args.margin) // 2
    height = args.height - args.top - args.bottom
    horizontal = max(horizontal, vertical * width / height)
    vertical = max(vertical, horizontal * height / width)
    bounds = [-horizontal, horizontal, -vertical, vertical]
    return {'coords': points, 'vertices': vertices, 'triangles': triangles,
            'raw_colors': np.ascontiguousarray(raw_colors), 'colors': np.ascontiguousarray(colors),
            'mesh_colors': np.ascontiguousarray(mesh_colors), 'palette': palette,
            'center': center, 'bounds': bounds, 'panel_width': width, 'panel_height': height,
            'original_ids': drawn_ids, 'source_points': len(coords), 'source_bounds': [low.tolist(), high.tolist()]}


def template(args, state, solution):
    im = Image.new('RGB', (args.width, args.height), 'white')
    draw = ImageDraw.Draw(im)
    left = args.margin
    right = 2 * args.margin + state['panel_width']
    title_size = round(args.width / 52)
    titles = ['Nuage LiDAR — résultat HGP' if solution else 'Nuage LiDAR',
              'Modèle 3D de référence']
    for x, text in [(left, titles[0]), (right, titles[1])]:
        draw.text((x + 6, 31), text, font=font(title_size, True), fill='#242c31')
    draw.line([(args.width // 2, args.top), (args.width // 2, args.height - args.bottom)],
              fill='#e5e8eb', width=1)
    small = font(round(args.width / 78))
    if solution:
        y = args.height - 69
        x = left + 6
        for color, text in [('#c9191e', 'Compatible avec le modèle'), ('#0072b2', 'Groupes repérés'),
                            ('#b6bdc3', 'Contexte')]:
            draw.ellipse((x, y + 4, x + 12, y + 16), fill=color)
            draw.text((x + 20, y), text, font=small, fill='#4b555d')
            x += 20 + draw.textlength(text, font=small) + 23
    else:
        draw.text((left + 6, args.height - 69), 'Les points du scan, sans regroupement',
                  font=small, fill='#4b555d')
    draw.text((right + 6, args.height - 69), 'La géométrie attendue sur le chantier',
              font=small, fill='#4b555d')
    footer = font(round(args.width / 97))
    foot = 'Scène de test synthétique · © Naval Group'
    draw.text((args.width - args.margin - draw.textlength(foot, font=footer), args.height - 29),
              foot, font=footer, fill='#727b83')
    return im


def render_panels(args, state, helper, raster, angle):
    w = state['panel_width'] * args.supersampling
    h = state['panel_height'] * args.supersampling
    points = screen_projection(state['coords'], helper, angle, args.elevation,
                               state['center'], state['bounds'], w, h)
    vertices = screen_projection(state['vertices'], helper, angle, args.elevation,
                                 state['center'], state['bounds'], w, h)
    raw, result, model = [np.empty((h, w, 3), dtype=np.uint8) for _ in range(3)]
    raster.points(points, state['raw_colors'], len(points), w, h, args.point_radius * args.supersampling, raw)
    raster.points(points, state['colors'], len(points), w, h, args.point_radius * args.supersampling, result)
    raster.triangles(vertices, state['triangles'], state['mesh_colors'],
                     len(state['triangles']), w, h, model)
    size = (state['panel_width'], state['panel_height'])
    return [Image.fromarray(x).resize(size, Image.Resampling.LANCZOS) for x in (raw, result, model)]


def frame(base, left_panel, right_panel, args, state):
    im = base.copy()
    im.paste(left_panel, (args.margin, args.top))
    im.paste(right_panel, (2 * args.margin + state['panel_width'], args.top))
    return im


def encoder(path, args):
    command = ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-f', 'rawvideo',
               '-vcodec', 'rawvideo', '-pixel_format', 'rgb24', '-video_size', f'{args.width}x{args.height}',
               '-framerate', str(args.fps), '-i', '-', '-an', '-c:v', 'libx264',
               '-preset', 'fast', '-crf', '18', '-pix_fmt', 'yuv420p', '-movflags', '+faststart',
               '-threads', '2', '-metadata', 'comment=Naval synthetic benchmark; exact CAD and v12 results', str(path)]
    return subprocess.Popen(command, stdin=subprocess.PIPE)


def file_info(path, args=None):
    info = {'sha256': sha256(path), 'bytes': path.stat().st_size}
    if path.suffix == '.mp4':
        probe = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-show_streams',
                                                   '-show_format', '-of', 'json', str(path)]))
        streams = [x for x in probe['streams'] if x['codec_type'] == 'video']
        v = streams[0]
        n, d = map(int, v['avg_frame_rate'].split('/'))
        info.update(width=int(v['width']), height=int(v['height']), frames=int(v['nb_frames']),
                    fps=n/d, duration_seconds=float(probe['format']['duration']),
                    codec=v['codec_name'], pixel_format=v['pix_fmt'],
                    audio_streams=sum(x['codec_type'] == 'audio' for x in probe['streams']))
        if args and (info['width'] != args.width or info['height'] != args.height or
                     info['frames'] != round(args.duration * args.fps) or info['fps'] != args.fps or
                     info['audio_streams'] or info['pixel_format'] != 'yuv420p'):
            raise ValueError(f'Unexpected video encoding: {info}')
    else:
        with Image.open(path) as im:
            info.update(width=im.width, height=im.height)
    return info


def main():
    root = Path(__file__).resolve().parent
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--result', type=Path, default=root/'naval_v12/result.npz')
    ap.add_argument('--model', type=Path, default=root/'naval_v12/bloc_full.ply')
    ap.add_argument('--components', type=Path, default=root/'naval_reference_components.json')
    ap.add_argument('--raw', type=Path, help='Optional full original PLY/NPY, to certify XYZ/PointIds again')
    ap.add_argument('--output-dir', type=Path, default=root/'videos')
    ap.add_argument('--poster-dir', type=Path, default=root/'assets')
    ap.add_argument('--manifest', type=Path, default=root/'naval_video_assets.json')
    ap.add_argument('--preview-dir', type=Path)
    ap.add_argument('--preview-only', action='store_true')
    ap.add_argument('--width', type=int, default=1600)
    ap.add_argument('--height', type=int, default=900)
    ap.add_argument('--duration', type=float, default=12.)
    ap.add_argument('--fps', type=int, default=24)
    ap.add_argument('--stride', type=int, default=4)
    ap.add_argument('--elevation', type=float, default=24.)
    ap.add_argument('--start-azimuth', type=float, default=45.)
    ap.add_argument('--point-radius', type=float, default=.95)
    ap.add_argument('--supersampling', type=int, default=2)
    ap.add_argument('--margin', type=int, default=34)
    ap.add_argument('--top', type=int, default=96)
    ap.add_argument('--bottom', type=int, default=100)
    args = ap.parse_args()
    if args.width % 2 or args.height % 2 or args.stride < 1 or args.supersampling < 1:
        ap.error('Even video dimensions, positive stride and supersampling are required')
    if args.preview_only and not args.preview_dir:
        ap.error('--preview-only requires --preview-dir')
    helper = load_helper()
    state = prepare(args, helper)
    bases = [template(args, state, False), template(args, state, True)]
    args.output_dir.mkdir(parents=True, exist_ok=True)
    args.poster_dir.mkdir(parents=True, exist_ok=True)
    if args.preview_dir:
        args.preview_dir.mkdir(parents=True, exist_ok=True)
    output_paths = [args.output_dir/'naval_chantier_question.mp4', args.output_dir/'naval_chantier_solution.mp4']
    poster_paths = [args.poster_dir/'naval_chantier_question_affiche.png', args.poster_dir/'naval_chantier_solution_affiche.png']
    started = time.monotonic()
    with tempfile.TemporaryDirectory(prefix='naval_raster_') as temporary:
        raster = build_rasterizer(Path(temporary))
        if args.preview_only:
            for offset in (0, 90, 180, 270):
                angle = args.start_azimuth + offset
                raw, result, model = render_panels(args, state, helper, raster, angle)
                for index, left in enumerate((raw, result)):
                    image = frame(bases[index], left, model, args, state)
                    image.save(args.preview_dir/f'{("question", "solution")[index]}_{offset:03}.png')
            print(json.dumps({'preview_directory': str(args.preview_dir), 'seconds': time.monotonic()-started,
                              'drawn_points': len(state['coords']), 'actual_model_triangles': len(state['triangles'])}))
            return
        encoders = [encoder(path, args) for path in output_paths]
        try:
            total_frames = round(args.duration * args.fps)
            for index in range(total_frames):
                # One complete constant-speed orbit; the loop closes at the next, unencoded frame.
                angle = args.start_azimuth + 360. * index / total_frames
                raw, result, model = render_panels(args, state, helper, raster, angle)
                for video_index, left in enumerate((raw, result)):
                    image = frame(bases[video_index], left, model, args, state)
                    encoders[video_index].stdin.write(image.tobytes())
                    if index == 0:
                        image.save(poster_paths[video_index], optimize=True)
                    if args.preview_dir and index in (0, total_frames//4, total_frames//2, 3*total_frames//4):
                        image.save(args.preview_dir/f'{("question", "solution")[video_index]}_{index:03}.png')
                if index % args.fps == 0:
                    print(f'frame={index}/{total_frames} elapsed={time.monotonic()-started:.1f}s', flush=True)
        finally:
            for proc in encoders:
                proc.stdin.close()
            codes = [proc.wait() for proc in encoders]
        if any(codes):
            raise RuntimeError(f'ffmpeg failed: {codes}')
    trajectory = np.column_stack((args.start_azimuth + 360. * np.arange(total_frames) / total_frames,
                                  np.full(total_frames, args.elevation))).astype('<f8')
    trajectory_hash = hashlib.sha256(trajectory.tobytes()).hexdigest()
    manifest = {
        'renderer': 'render_naval_video.py', 'schema_version': 1,
        'description': 'Two matching 360-degree views of exact raw LiDAR XYZ and the true reference CAD; the second only changes point colours using the reviewed real v12 result.',
        'sources': {'result': {'file': 'naval_v12/result.npz', 'sha256': sha256(args.result),
                               'bytes': args.result.stat().st_size, 'coordinates': 'reviewed exact original scan XYZ indexed by original PointId',
                               'engine_commit': 'ac2d5bab814e84db6e1c9340f54995aa9cda58aa'},
                    'model': {'file': 'naval_v12/bloc_full.ply', 'sha256': sha256(args.model),
                              'bytes': args.model.stat().st_size,
                              'source_url': 'https://drive.google.com/file/d/1C3sSBzJmAS2mKlxhAacEPQcUiInUO_VV/view'},
                    'named_components': {'file': 'naval_reference_components.json', 'sha256': sha256(args.components)},
                    'renderer': {'file': 'render_naval_video.py', 'sha256': sha256(Path(__file__))},
                    'projection_helper': {'file': 'render_naval.py', 'sha256': sha256(root/'render_naval.py')},
                    'source_manifest': {'file': 'naval_v12/data_source_manifest.json',
                                        'sha256': sha256(root/'naval_v12/data_source_manifest.json')},
                    'original_scan_sha256': 'fbcbe22be7d4bca36d15e5e0549a26af6218303668bf5ee4f1119c7246da8ab1'},
        'model': {'selection': CAD_NAMES, 'actual_original_triangles': len(state['triangles']),
                  'actual_original_vertices': 2102, 'bounding_boxes_are_not_display_geometry': True,
                  'anomaly_meshes_used': False, 'background_mesh_displayed': False},
        'point_sampling': {'ROI_original_points': state['source_points'], 'stride': args.stride,
                           'drawn_points_each_video': len(state['coords']),
                           'same_original_PointIds_in_both_videos': True,
                           'original_PointIds_le_i64_sha256': hashlib.sha256(state['original_ids'].astype('<i8').tobytes()).hexdigest()},
        'camera': {'projection': 'orthographic', 'elevation_degrees': args.elevation,
                   'start_azimuth_degrees': args.start_azimuth, 'total_rotation_degrees': 360,
                   'azimuth_formula': 'start + 360 * frame_index / frame_count',
                   'shared_azimuth_elevation_le_f64_sha256': trajectory_hash,
                   'trajectory_columns': ['azimuth_degrees', 'elevation_degrees'],
                   'video_trajectory_sha256': {'question': trajectory_hash, 'solution': trajectory_hash},
                   'center_xyz_m': state['center'].tolist(), 'fixed_projected_bounds_m': state['bounds'],
                   'bounds_for_entire_orbit': True, 'same_camera_and_axes_for_every_panel': True,
                   'same_right_panel_pixels_in_both_videos_before_encoding': True,
                   'same_left_geometry_and_depth_in_both_videos_before_encoding': True,
                   'source_bounds_xyz_m': state['source_bounds']},
        'render': {'width': args.width, 'height': args.height, 'duration_seconds': args.duration,
                   'fps': args.fps, 'frames': round(args.duration*args.fps), 'background': '#ffffff',
                   'point_radius_pixels': args.point_radius, 'supersampling': args.supersampling,
                   'triangle_depth_buffer': True, 'point_depth_buffer': True,
                   'surface_reconstruction_of_LiDAR': False,
                   'panel_width': state['panel_width'], 'panel_height': state['panel_height']},
        'result_colours': {'supported_by_geometric_reference': '#c9191e', 'context': '#b6bdc3',
                          'native_v12_node_palette': {str(k): v for k, v in state['palette'].items()},
                          'semantics': 'geometry-filtered reference points; real K3 strong-incidence component cover at 4 cm, minimum 200 points; candidate objects to check, not native Hr/EOM or anomaly ground truth'},
        'encoding': {'codec': 'H.264', 'pixel_format': 'yuv420p', 'audio': False,
                     'faststart': True, 'crf': 18, 'preset': 'fast'},
        'outputs': {},
    }
    for path in output_paths + poster_paths:
        relative = f'{"videos" if path.suffix == ".mp4" else "assets"}/{path.name}'
        manifest['outputs'][relative] = file_info(path, args)
    args.manifest.write_text(json.dumps(manifest, indent=2, ensure_ascii=False)+'\n')
    print(json.dumps({'manifest': str(args.manifest), 'seconds': time.monotonic()-started,
                      'outputs': manifest['outputs']}, indent=2))


if __name__ == '__main__':
    main()
