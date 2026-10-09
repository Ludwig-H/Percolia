#!/usr/bin/env python3
"""Render genuine Naval Group benchmark inputs using one shared camera.

This script does not infer segmentation labels or synthesize geometry. Raw points
are shown with one neutral colour; the model uses the supplied mesh faces.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
import numpy as np
from PIL import Image

PLY_DTYPES = {'char': 'i1', 'uchar': 'u1', 'int8': 'i1', 'uint8': 'u1',
              'short': 'i2', 'ushort': 'u2', 'int16': 'i2', 'uint16': 'u2',
              'int': 'i4', 'uint': 'u4', 'int32': 'i4', 'uint32': 'u4',
              'float': 'f4', 'double': 'f8', 'float32': 'f4', 'float64': 'f8'}


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def read_ply(path):
    """Read standard scalar vertices and optional list-valued polygon faces."""
    with open(path, 'rb') as f:
        if f.readline().strip() != b'ply':
            raise ValueError(f'{path}: not a PLY file')
        elements = []
        format_name = None
        while True:
            line = f.readline().decode('ascii').strip()
            tokens = line.split()
            if line == 'end_header':
                break
            if not tokens:
                continue
            if tokens[0] == 'format':
                format_name = tokens[1]
            elif tokens[0] == 'element':
                elements.append({'name': tokens[1], 'count': int(tokens[2]), 'properties': []})
            elif tokens[0] == 'property':
                elements[-1]['properties'].append(tokens[1:])
        vertices, faces = None, []
        endian = '<' if format_name == 'binary_little_endian' else '>'
        for el in elements:
            props, count = el['properties'], el['count']
            if format_name == 'ascii':
                rows = [f.readline().decode('ascii').split() for _ in range(count)]
                if el['name'] == 'vertex':
                    indices = {p[-1]: i for i, p in enumerate(props)}
                    vertices = np.asarray([[float(r[indices[k]]) for k in ['x', 'y', 'z']] for r in rows], dtype=np.float64)
                elif el['name'] == 'face':
                    for row in rows:
                        n = int(row[0])
                        faces.append([int(x) for x in row[1:1+n]])
            elif all(p[0] != 'list' for p in props):
                dtype = np.dtype([(p[1], endian + PLY_DTYPES[p[0]]) for p in props])
                records = np.frombuffer(f.read(count * dtype.itemsize), dtype=dtype)
                if len(records) != count:
                    raise ValueError(f'{path}: truncated {el["name"]}')
                if el['name'] == 'vertex':
                    vertices = np.column_stack([records[k] for k in ['x', 'y', 'z']]).astype(np.float64)
            else:
                for _ in range(count):
                    face = None
                    for p in props:
                        if p[0] == 'list':
                            size_dtype = np.dtype(endian + PLY_DTYPES[p[1]])
                            n = int(np.frombuffer(f.read(size_dtype.itemsize), dtype=size_dtype)[0])
                            item_dtype = np.dtype(endian + PLY_DTYPES[p[2]])
                            val = np.frombuffer(f.read(n * item_dtype.itemsize), dtype=item_dtype)
                            if p[3] in ('vertex_indices', 'vertex_index'):
                                face = val.tolist()
                        else:
                            dtype = np.dtype(endian + PLY_DTYPES[p[0]])
                            f.read(dtype.itemsize)
                    if el['name'] == 'face' and face is not None:
                        faces.append(face)
        if vertices is None:
            raise ValueError(f'{path}: no XYZ vertices')
        return vertices, faces


def read_off(path):
    with open(path, encoding='utf-8') as f:
        rows = [line.split('#', 1)[0].strip() for line in f]
    rows = [row for row in rows if row]
    if rows[0] == 'OFF':
        rows = rows[1:]
    elif rows[0].startswith('OFF'):
        rows[0] = rows[0][3:].strip()
    else:
        raise ValueError(f'{path}: not OFF')
    nv, nf, *_ = map(int, rows[0].split())
    vertices = np.asarray([[float(s) for s in row.split()[:3]] for row in rows[1:1+nv]])
    faces = []
    for row in rows[1+nv:1+nv+nf]:
        entries = [int(s) for s in row.split()]
        faces.append(entries[1:1+entries[0]])
    return vertices, faces


def load_xyz(path):
    if path.suffix.lower() == '.ply':
        return read_ply(path)[0]
    if path.suffix.lower() == '.npy':
        arr = np.load(path, allow_pickle=False)
    else:
        arr = np.loadtxt(path)
    if arr.ndim != 2 or arr.shape[1] < 3:
        raise ValueError(f'{path}: expected N x 3 coordinates')
    return np.asarray(arr[:, :3], dtype=np.float64)


def camera_basis(azimuth, elevation):
    az, el = np.deg2rad([azimuth, elevation])
    toward_eye = np.array([np.cos(el) * np.cos(az), np.cos(el) * np.sin(az), np.sin(el)])
    right = np.array([-np.sin(az), np.cos(az), 0.])
    up = np.cross(toward_eye, right)
    return np.stack([right, up, toward_eye], axis=1)


def project(xyz, basis, center, perspective_distance=None):
    camera = (xyz - center) @ basis
    if perspective_distance is not None:
        scale = perspective_distance / (perspective_distance - camera[:, 2])
        camera[:, :2] *= scale[:, None]
    return camera


def clip_polygon(poly, roi):
    """Clip supplied mesh faces, without creating a surface at the crop boundary."""
    result = np.asarray(poly, dtype=float)
    if roi is None:
        return result
    for axis in range(3):
        for limit, keep_above in [(roi[2*axis], True), (roi[2*axis+1], False)]:
            if not len(result):
                return result
            clipped = []
            prev = result[-1]
            prev_inside = prev[axis] >= limit if keep_above else prev[axis] <= limit
            for cur in result:
                inside = cur[axis] >= limit if keep_above else cur[axis] <= limit
                if inside != prev_inside:
                    t = (limit-prev[axis])/(cur[axis]-prev[axis])
                    clipped.append(prev+t*(cur-prev))
                if inside:
                    clipped.append(cur)
                prev, prev_inside = cur, inside
            result = np.asarray(clipped, dtype=float).reshape(-1, 3)
    return result


def select_reference_components(vertices, faces, box_dir):
    """Keep actual connected mesh objects paired one-to-one with reference OFFs.

    Matching uses containment of each object's coordinate bounds in a supplied
    expanded reference box. Ambiguous/non-unique matching aborts generation.
    The boxes are selection references, never substituted for mesh geometry.
    """
    parent = np.arange(len(vertices))
    def root(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    for face in faces:
        a = root(face[0])
        for index in face[1:]:
            b = root(index)
            if a != b:
                parent[b] = a
    labels = np.asarray([root(i) for i in range(len(vertices))])
    boxes = []
    for path in sorted(box_dir.glob('*.off')):
        v, _ = read_off(path)
        boxes.append((path, v.min(0), v.max(0)))
    if len(boxes) != 13:
        raise ValueError(f'Expected 13 original reference boxes, got {len(boxes)}')
    matched, selections = {}, []
    for key in np.unique(labels):
        ids = np.flatnonzero(labels == key)
        lo, hi = vertices[ids].min(0), vertices[ids].max(0)
        candidates = [path for path, blo, bhi in boxes if np.all(lo >= blo-1e-5) and np.all(hi <= bhi+1e-5)]
        if len(candidates) > 1:
            raise ValueError(f'Ambiguous reference match for mesh component {key}: {candidates}')
        if candidates:
            path = candidates[0]
            if path.name in matched:
                raise ValueError(f'Multiple components match {path.name}')
            matched[path.name] = int(key)
            selections.append({'box': path.name, 'box_sha256': sha256(path), 'component_root_vertex': int(key), 'vertices': len(ids), 'min': lo.tolist(), 'max': hi.tolist()})
    if len(matched) != 13:
        raise ValueError(f'Only {len(matched)} of 13 reference boxes match actual objects')
    selected = set(matched.values())
    kept_faces = [face for face in faces if int(labels[face[0]]) in selected]
    kept_vertices = np.unique(np.concatenate([np.asarray(face) for face in kept_faces]))
    return kept_faces, {'selection': '13 actual connected mesh components uniquely matched to the 13 supplied reference OFF boxes; intrusive objects and enclosing room excluded', 'components_in_source': len(np.unique(labels)), 'objects_kept': 13, 'vertices_kept': len(kept_vertices), 'faces_kept': len(kept_faces), 'matches': selections}


def canvas(bounds, width, height):
    fig = plt.figure(figsize=(width/200, height/200), dpi=200, facecolor='white')
    ax = fig.add_axes([0, 0, 1, 1], facecolor='white')
    ax.set_xlim(bounds[0], bounds[1])
    ax.set_ylim(bounds[2], bounds[3])
    ax.set_aspect('equal')
    ax.set_axis_off()
    return fig, ax


def save(fig, output):
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=200, facecolor='white', edgecolor='white', metadata={'Software': 'Percolia Naval benchmark renderer'})
    plt.close(fig)
    with Image.open(output) as im:
        converted = im.convert('L' if output.name == 'naval_raw.png' else 'RGB').copy()
    temporary = output.with_suffix('.tmp.png')
    converted.save(temporary, optimize=True)
    temporary.replace(output)


def rasterize_model(polygons, colors, depths_per_vertex, bounds, width, height, output):
    """Opaque mesh rasterization with a real depth buffer and 2x antialiasing."""
    scale = 2
    w, h = width*scale, height*scale
    pixels = np.full((h, w, 3), 255, dtype=np.uint8)
    zbuffer = np.full((h, w), -np.inf, dtype=np.float32)
    for poly, color, depths in zip(polygons, colors, depths_per_vertex):
        screen = np.asarray(poly).copy()
        screen[:, 0] = (screen[:, 0]-bounds[0])/(bounds[1]-bounds[0])*(w-1)
        screen[:, 1] = (bounds[3]-screen[:, 1])/(bounds[3]-bounds[2])*(h-1)
        for i in range(1, len(screen)-1):
            ids = [0, i, i+1]
            triangle = screen[ids]
            zz = np.asarray(depths)[ids]
            x0 = max(0, int(np.floor(triangle[:, 0].min())))
            x1 = min(w-1, int(np.ceil(triangle[:, 0].max())))
            y0 = max(0, int(np.floor(triangle[:, 1].min())))
            y1 = min(h-1, int(np.ceil(triangle[:, 1].max())))
            if x0 > x1 or y0 > y1:
                continue
            a, b, c = triangle
            den = (b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
            if abs(den) < 1e-9:
                continue
            xx = np.arange(x0, x1+1, dtype=np.float32)[None, :]+.5
            yy = np.arange(y0, y1+1, dtype=np.float32)[:, None]+.5
            wa = ((b[1]-c[1])*(xx-c[0])+(c[0]-b[0])*(yy-c[1]))/den
            wb = ((c[1]-a[1])*(xx-c[0])+(a[0]-c[0])*(yy-c[1]))/den
            wc = 1-wa-wb
            inside = (wa >= -1e-6)&(wb >= -1e-6)&(wc >= -1e-6)
            depth = wa*zz[0]+wb*zz[1]+wc*zz[2]
            region = zbuffer[y0:y1+1, x0:x1+1]
            visible = inside & (depth > region)
            region[visible] = depth[visible]
            pixels[y0:y1+1, x0:x1+1][visible] = np.round(np.asarray(color)*255).astype(np.uint8)
    result = Image.fromarray(pixels, mode='RGB').resize((width, height), Image.Resampling.LANCZOS)
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix('.tmp.png')
    result.save(temporary, optimize=True)
    temporary.replace(output)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--raw', type=Path, required=True)
    parser.add_argument('--model', type=Path, nargs='+', required=True)
    parser.add_argument('--output-dir', type=Path, default=Path(__file__).parent/'assets')
    parser.add_argument('--azimuth', type=float, default=45.)
    parser.add_argument('--elevation', type=float, default=35.264389)
    parser.add_argument('--up-axis', choices=['x', 'y', 'z'], default='z')
    parser.add_argument('--max-points', type=int, default=450000)
    parser.add_argument('--perspective', type=float, default=0., help='Eye distance / scene diagonal; 0 = orthographic')
    parser.add_argument('--width', type=int, default=1800)
    parser.add_argument('--height', type=int, default=1200)
    parser.add_argument('--point-size', type=float, default=.9)
    parser.add_argument('--point-alpha', type=float, default=.8)
    parser.add_argument('--point-color', default='#39444c')
    parser.add_argument('--roi', type=float, nargs=6, metavar=('XMIN','XMAX','YMIN','YMAX','ZMIN','ZMAX'), help='Geographic clipping box applied identically to scan and supplied mesh')
    parser.add_argument('--reference-box-dir', type=Path, help='Use 13 original OFF boxes to select actual reference objects from complete-scene PLY mesh')
    parser.add_argument('--provenance', type=Path, help='Optional JSON map of source paths to origin IDs/URLs')
    args = parser.parse_args()
    raw = load_xyz(args.raw)
    raw = raw[np.isfinite(raw).all(axis=1)]
    total_valid_points = len(raw)
    roi = np.asarray(args.roi) if args.roi else None
    if roi is not None:
        raw = raw[((raw >= roi[[0, 2, 4]]) & (raw <= roi[[1, 3, 5]])).all(axis=1)]
    perm = {'z': [0, 1, 2], 'y': [0, 2, 1], 'x': [1, 2, 0]}[args.up_axis]
    raw = raw[:, perm]
    models = []
    source_models = []
    selection_metadata = []
    for path in args.model:
        verts, faces = read_off(path) if path.suffix.lower() == '.off' else read_ply(path)
        if not faces:
            raise ValueError(f'{path}: theoretical model has no faces; supply actual OFF/PLY surface mesh')
        source_models.append((verts, faces, path))
        if args.reference_box_dir:
            faces, selection_info = select_reference_components(verts, faces, args.reference_box_dir)
            selection_metadata.append(selection_info)
        clipped_faces = [clip_polygon(verts[np.asarray(face, dtype=int)], roi) for face in faces]
        clipped_faces = [poly[:, perm] for poly in clipped_faces if len(poly) >= 3]
        local_verts = np.vstack(clipped_faces)
        local_faces = []
        offset = 0
        for poly in clipped_faces:
            local_faces.append(np.arange(offset, offset+len(poly)))
            offset += len(poly)
        models.append((local_verts, local_faces, path))
    all_model = np.concatenate([v for v, _, _ in models])
    low = np.minimum(raw.min(axis=0), all_model.min(axis=0))
    high = np.maximum(raw.max(axis=0), all_model.max(axis=0))
    center = (low + high)/2
    diagonal = float(np.linalg.norm(high-low))
    eye_distance = args.perspective * diagonal if args.perspective else None
    basis = camera_basis(args.azimuth, args.elevation)
    stride = max(1, int(np.ceil(len(raw)/args.max_points)))
    drawn = raw[::stride]
    projected_raw = project(drawn, basis, center, eye_distance)
    projected_models = [project(v, basis, center, eye_distance) for v, _, _ in models]
    all_projected = np.vstack([projected_raw, *projected_models])
    lo, hi = all_projected[:, :2].min(axis=0), all_projected[:, :2].max(axis=0)
    mid = (lo+hi)/2
    half = (hi-lo)*.535
    target_ratio = args.width/args.height
    half[0] = max(half[0], half[1]*target_ratio)
    half[1] = max(half[1], half[0]/target_ratio)
    bounds = [mid[0]-half[0], mid[0]+half[0], mid[1]-half[1], mid[1]+half[1]]

    fig, ax = canvas(bounds, args.width, args.height)
    order = np.argsort(projected_raw[:, 2], kind='stable')
    ax.scatter(projected_raw[order, 0], projected_raw[order, 1], s=args.point_size,
               c=args.point_color, edgecolors='none', alpha=args.point_alpha, rasterized=True, linewidths=0)
    save(fig, args.output_dir/'naval_raw.png')

    polygons, colors, depths, is_ground, depth_vertices = [], [], [], [], []
    light = np.array([-.3, -.2, .93]); light /= np.linalg.norm(light)
    base_color = np.array([.56, .68, .76])
    for (verts, faces, _), projected in zip(models, projected_models):
        for face in faces:
            if len(face) < 3:
                continue
            face = np.asarray(face, dtype=int)
            poly = verts[face]
            n = np.cross(poly[1]-poly[0], poly[2]-poly[0])
            norm = np.linalg.norm(n)
            shade = .74 + .26*abs(float(n@light))/norm if norm else .85
            colors.append(np.clip(base_color*shade+.13, 0, 1))
            polygons.append(projected[face, :2])
            depths.append(projected[face, 2].mean())
            depth_vertices.append(projected[face, 2] if eye_distance is None else 1/(eye_distance-projected[face, 2]))
            ground = float(np.ptp(poly[:, 2])) < .01 and float(poly[:, 2].mean()) < .08
            is_ground.append(ground)
            if ground:
                colors[-1] = np.array([.935, .95, .963])
    rasterize_model(polygons, colors, depth_vertices, bounds, args.width, args.height, args.output_dir/'naval_model.png')

    origins = json.loads(args.provenance.read_text()) if args.provenance else {}
    metadata = {
        'description': 'Same projection and crop for measured/synthetic raw scan and supplied theoretical mesh; no segmentation labels used.',
        'renderer': 'render_naval.py',
        'raw': {'file': args.raw.name, 'sha256': sha256(args.raw), 'valid_points_before_crop': total_valid_points, 'points_in_crop': len(raw), 'drawn_points': len(drawn), 'stride': stride, 'origin': origins.get(str(args.raw), origins.get(args.raw.name))},
        'model': [{'file': path.name, 'sha256': sha256(path), 'vertices_in_source': len(v), 'faces_in_source': len(f), 'origin': origins.get(str(path), origins.get(path.name))} for v, f, path in source_models],
        'geographic_crop_in_source_coordinates': args.roi,
        'crop_note': 'Same XYZ clipping volume in both panels. Mesh polygons are clipped geometrically; no synthetic cap or geometry is added at the clipping boundary.',
        'reference_model_selection': selection_metadata,
        'camera': {'projection': 'perspective' if eye_distance else 'orthographic', 'azimuth_degrees': args.azimuth, 'elevation_degrees': args.elevation, 'up_axis_in_source': args.up_axis, 'center': center.tolist(), 'basis_columns_right_up_eye': basis.tolist(), 'eye_distance': eye_distance, 'bounds_2d': [float(v) for v in bounds]},
        'render': {'width': args.width, 'height': args.height, 'point_size_pt2': args.point_size, 'point_color_before_grayscale_conversion': args.point_color, 'point_alpha': args.point_alpha, 'background': '#ffffff', 'raw_png_mode': 'L (8-bit neutral grayscale)', 'mesh_depth_buffer': True, 'mesh_supersampling': 2},
        'outputs': {name: sha256(args.output_dir/name) for name in ['naval_raw.png', 'naval_model.png']},
    }
    (args.output_dir/'naval_render_metadata.json').write_text(json.dumps(metadata, indent=2, ensure_ascii=False)+'\n')
    print(json.dumps({'raw_points': len(raw), 'drawn': len(drawn), 'model_faces': len(polygons), 'bounds_3d': [low.tolist(), high.tolist()], 'images': metadata['outputs']}, indent=2))


if __name__ == '__main__':
    main()
