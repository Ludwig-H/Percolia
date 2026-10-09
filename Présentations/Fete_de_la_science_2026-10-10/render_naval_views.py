#!/usr/bin/env python3
"""Exact 2D projections of the Naval scan and reference CAD, with optional v12 labels.

All point panels use precisely the same original representative points. Reference
CAD is projected from its supplied triangles; its 2D outlines are a raster union
of triangle projections, without invented geometry or ground-truth anomaly mesh.
"""
from __future__ import annotations
import argparse
import colorsys
import importlib.util
import json
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw, ImageFilter, ImageChops

EXPECTED_CAD_NAMES = ['Cube_1', 'Cube_2', 'Cube_3', 'Equerre_1', 'Equerre_2',
                      'Equerre_3', 'Pipe_1', 'Pipe_2', 'Pipe_3', 'Pipe_4',
                      'Pipe_10', 'Pipe_11', 'Plane_1', 'Plane_2']
PALETTE = ['#e69f00', '#0072b2', '#009e73', '#8e55a1', '#b85c9d', '#55a6cf', '#9a7a2f', '#437b3a']


def load_base(path):
    spec = importlib.util.spec_from_file_location('naval_base', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def bounds_for(points, polys, plane, width, height):
    allpts = np.concatenate([points[:, plane], *[p[:, plane] for _, p in polys]])
    lo, hi = allpts.min(0), allpts.max(0)
    mid = (lo+hi)/2
    half = (hi-lo)*.545
    ratio = width/height
    half[0] = max(half[0], half[1]*ratio)
    half[1] = max(half[1], half[0]/ratio)
    return [float(mid[0]-half[0]), float(mid[0]+half[0]), float(mid[1]-half[1]), float(mid[1]+half[1])]


def screen_coords(points, bounds, width, height):
    p = np.asarray(points).copy()
    p[:, 0] = (p[:, 0]-bounds[0])/(bounds[1]-bounds[0])*(width-1)
    p[:, 1] = (bounds[3]-p[:, 1])/(bounds[3]-bounds[2])*(height-1)
    return p


def render_model(polys, plane, bounds, width, height, path):
    scale = 3
    w, h = width*scale, height*scale
    masks = {}
    for name, poly in polys:
        if name not in masks:
            masks[name] = Image.new('L', (w, h), 0)
        p = screen_coords(poly[:, plane], bounds, w, h)
        # Projected vertical/edge-on faces legitimately have zero area.
        if len(p) < 3:
            continue
        ImageDraw.Draw(masks[name]).polygon([tuple(x) for x in p], fill=255)
    out = Image.new('RGB', (w, h), 'white')
    if 'Plane_1' in masks:
        out.paste('#f1f4f6', mask=masks['Plane_1'])
    objects = [mask for name, mask in masks.items() if name != 'Plane_1']
    if objects:
        union = objects[0].copy()
        for mask in objects[1:]:
            union = ImageChops.lighter(union, mask)
        out.paste('#d8e4eb', mask=union)
    for name, mask in masks.items():
        edge = ImageChops.subtract(mask.filter(ImageFilter.MaxFilter(5)), mask.filter(ImageFilter.MinFilter(5)))
        out.paste('#5c7585' if name != 'Plane_1' else '#a7b7c0', mask=edge)
    out = out.resize((width, height), Image.Resampling.LANCZOS)
    path.parent.mkdir(parents=True, exist_ok=True)
    out.save(path, optimize=True)


def point_panel(points, plane, bounds, width, height, output, colors=None, model_background=None, anomaly_only=None, class_priority=None):
    fig = plt.figure(figsize=(width/200, height/200), dpi=200, facecolor='white')
    ax = fig.add_axes([0, 0, 1, 1], facecolor='white')
    if model_background is not None:
        with Image.open(model_background) as im:
            background = np.asarray(im.convert('RGB'))
        ax.imshow(background, extent=[bounds[0], bounds[1], bounds[2], bounds[3]], origin='upper')
    selected = np.arange(len(points)) if anomaly_only is None else np.flatnonzero(anomaly_only)
    if class_priority is not None:
        selected = selected[np.argsort(np.asarray(class_priority)[selected],kind='stable')]
    coords = points[selected][:, plane]
    c = '#39444c' if colors is None else np.asarray(colors)[selected]
    # One projection means every point is displayed: no opaque 3D occlusion.
    ax.scatter(coords[:, 0], coords[:, 1], c=c, s=.95 if colors is None else 1.3,
               alpha=.82 if colors is None else .92, edgecolors='none', linewidths=0, rasterized=True)
    ax.set_xlim(bounds[0], bounds[1]); ax.set_ylim(bounds[2], bounds[3]); ax.set_aspect('equal'); ax.axis('off')
    fig.savefig(output, dpi=200, facecolor='white', metadata={'Software': 'Percolia exact Naval 2D projections'})
    plt.close(fig)
    with Image.open(output) as im:
        final = im.convert('L' if colors is None else 'RGB').copy()
    temp = output.with_suffix('.tmp.png'); final.save(temp, optimize=True); temp.replace(output)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--data-dir', type=Path, required=True)
    ap.add_argument('--base-renderer', type=Path, default=Path(__file__).with_name('render_naval.py'))
    ap.add_argument('--reference-components', type=Path, default=Path(__file__).with_name('naval_reference_components.json'))
    ap.add_argument('--output-dir', type=Path, default=Path(__file__).parent/'assets')
    ap.add_argument('--labels-npz', type=Path, help='coords, original_ids, cluster_id (or labels), class_id: 0 reference-supported, 1 unexpected, -1 unassigned')
    ap.add_argument('--segmentation-metadata', type=Path)
    ap.add_argument('--roi', type=float, nargs=6, default=[-3.4, 3.4, -3.4, 3.4, -.09, 3.1])
    ap.add_argument('--preview-max-points', type=int, default=50000, help='Only used before labels are available')
    ap.add_argument('--display-stride', type=int, default=4, help='Blind visual subsampling shared by all question/result panels; does not affect the v12 calculation')
    args = ap.parse_args(); base = load_base(args.base_renderer)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    scan_path = args.data_dir/'scan_lidar.ply'
    scan = np.load(args.data_dir/'scan_points.npy') if (args.data_dir/'scan_points.npy').exists() else base.load_xyz(scan_path)
    vertices, faces = base.read_ply(args.data_dir/'bloc_full.ply')
    component_reference = json.loads(args.reference_components.read_text())
    if component_reference['mesh_sha256'] != base.sha256(args.data_dir/'bloc_full.ply'):
        raise ValueError('Reference component map does not match the supplied CAD mesh SHA256')
    source_ids = np.flatnonzero(((scan >= np.asarray(args.roi)[[0,2,4]]) & (scan <= np.asarray(args.roi)[[1,3,5]])).all(axis=1))
    classes, labels = None, None
    input_labelled_points, full_original_ids_hash, full_class_counts = None, None, None
    if args.labels_npz:
        data = np.load(args.labels_npz, allow_pickle=False)
        source_ids = np.asarray(data['original_ids'], dtype=np.int64).reshape(-1)
        if len(np.unique(source_ids)) != len(source_ids) or source_ids.min() < 0 or source_ids.max() >= len(scan):
            raise ValueError('v12 representative indices are duplicated or outside original scan')
        classes = np.asarray(data['class_id'], dtype=int).reshape(-1)
        key = 'cluster_id' if 'cluster_id' in data else 'labels'
        labels = np.asarray(data[key], dtype=int).reshape(-1)
        if not (len(classes) == len(labels) == len(source_ids)):
            raise ValueError('v12 labels do not align with original representative IDs')
        if not set(np.unique(classes)) <= {-1,0,1}:
            raise ValueError('Unsupported class enum; expected -1 unassigned, 0 model-supported, 1 unexpected')
        if np.any((classes == 1)&(labels < 0)):
            raise ValueError('Unexpected displayed points must carry a real nonnegative extracted cluster ID')
        input_labelled_points = len(source_ids)
        full_original_ids_hash = base.hashlib.sha256(source_ids.astype('<i8').tobytes()).hexdigest()
        values, counts = np.unique(classes,return_counts=True)
        full_class_counts = {str(int(k)):int(v) for k,v in zip(values,counts)}
        if args.display_stride < 1:
            raise ValueError('Display stride must be positive')
        source_ids, classes, labels = source_ids[::args.display_stride], classes[::args.display_stride], labels[::args.display_stride]
    else:
        stride = max(1, int(np.ceil(len(source_ids)/args.preview_max_points)))
        source_ids = source_ids[::stride]
    points = scan[source_ids]
    roi = np.asarray(args.roi)
    polys = []; model_sources = []
    for name, vertex_ids in component_reference['named_vertex_ids'].items():
        ids = np.asarray(vertex_ids,dtype=int)
        member = np.zeros(len(vertices), dtype=bool); member[ids] = True
        object_faces = [face for face in faces if member[face[0]]]
        for face in object_faces:
            poly = base.clip_polygon(vertices[np.asarray(face)], roi)
            if len(poly) >= 3:
                polys.append((name, poly))
        model_sources.append({'name': name, 'vertices': len(ids), 'faces': len(object_faces), 'source_component_map': args.reference_components.name})
    if len(model_sources) != 14 or set(x['name'] for x in model_sources) != set(EXPECTED_CAD_NAMES):
        raise ValueError('Expected 14 named infrastructure objects in complete reference CAD')
    colors, palette = None, {}
    if labels is not None:
        groups = sorted(int(k) for k in np.unique(labels[classes == 1]))
        for i, label in enumerate(groups):
            if i < len(PALETTE):
                palette[label] = PALETTE[i]
            else:
                rgb = colorsys.hsv_to_rgb((i*.61803398875)%1, .62, .72)
                palette[label] = '#'+''.join(f'{int(255*c):02x}' for c in rgb)
        colors = np.full(len(points), '#b6bdc3', dtype='U7')
        colors[classes == 0] = '#c9191e'
        for label, color in palette.items():
            colors[(classes == 1)&(labels == label)] = color
    views = []
    for index, name, plane, size in [(1, 'dessus', [0,1], [1000,800]), (2, 'côté', [0,2], [1600,680])]:
        width, height = size
        bounds = bounds_for(points, polys, plane, width, height)
        model_path = args.output_dir/f'naval_model_view{index}.png'
        render_model(polys, plane, bounds, width, height, model_path)
        point_panel(points, plane, bounds, width, height, args.output_dir/f'naval_raw_view{index}.png')
        if colors is not None:
            point_panel(points, plane, bounds, width, height, args.output_dir/f'naval_result_view{index}.png', colors=colors, class_priority=classes)
            point_panel(points, plane, bounds, width, height, args.output_dir/f'naval_result_model_view{index}.png', colors=colors, model_background=model_path, anomaly_only=classes==1)
        views.append({'view': index, 'name': name, 'projection': ''.join('XYZ'[i] for i in plane), 'width': width, 'height': height, 'bounds_2d': bounds, 'raw_result_identical_original_ids': True})
    files = {}
    for path in sorted(args.output_dir.glob('naval_*_view*.png')):
        with Image.open(path) as im:
            w,h=im.size; mode=im.mode
        files['assets/'+path.name]={'sha256':base.sha256(path), 'size':path.stat().st_size,'width':w,'height':h,'mode':mode}
    metadata = {
        'files': files, 'views': views, 'credit': '© Naval Group, benchmark synthétique fourni par Marie Aspro',
        'rendering': 'Exact orthographic 2D projections. Reference image shows projected supplied mesh triangle unions and object silhouettes, with all projected objects visible rather than opaque 3D occlusion.',
        'question_answer_point_identity': {'source': scan_path.name, 'source_sha256': base.sha256(scan_path), 'source_points': len(scan), 'labelled_roi_points_before_visual_sampling':input_labelled_points, 'full_original_ids_sha256':full_original_ids_hash, 'class_counts_before_visual_sampling':full_class_counts, 'displayed_points': len(points), 'displayed_original_ids_sha256': base.hashlib.sha256(source_ids.astype('<i8').tobytes()).hexdigest(), 'sampling': f'blind common original_ids[::{args.display_stride}] for all question/result panels; calculation unchanged' if labels is not None else 'deterministic preview subsampling pending v12 results'},
        'reference_mesh_clip_roi': args.roi,
        'source_points_bounds_xyz': {'min':points.min(axis=0).tolist(), 'max':points.max(axis=0).tolist()},
        'roi_note': 'The source original_ids in result.npz define the full point ROI; they are never recropped by the renderer. The numeric reference_mesh_clip_roi only clips the supplied mesh triangles. It adds no geometry.',
        'reference_model': {'source': 'bloc_full.ply', 'sha256':base.sha256(args.data_dir/'bloc_full.ply'), 'infrastructure_count':14, 'objects':model_sources, 'component_map':{'file':args.reference_components.name,'sha256':base.sha256(args.reference_components)}, 'classification_note':'14 expected CAD infrastructure objects, including Cube_3. No Anomaly_* ground-truth geometry is used to draw the reference or determine result colours.'},
        'result_colors': {'model_supported':'#c9191e','unassigned':'#b6bdc3','unexpected_clusters':{str(k):v for k,v in palette.items()}},
        'lower_answer': 'Same projected reference CAD plus only points of actual v12 extracted clusters classified unexpected; no anomaly meshes or oracle painting.',
        'segmentation_npz': {'file':args.labels_npz.name,'sha256':base.sha256(args.labels_npz), 'size':args.labels_npz.stat().st_size} if args.labels_npz else None,
        'segmentation_metadata_source': {'file':args.segmentation_metadata.name, 'sha256':base.sha256(args.segmentation_metadata)} if args.segmentation_metadata else None,
        'segmentation': json.loads(args.segmentation_metadata.read_text()) if args.segmentation_metadata else None,
    }
    (args.output_dir/'naval_projection_metadata.json').write_text(json.dumps(metadata,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps({'files':files,'displayed_points':len(points),'views':views,'result_colors':metadata['result_colors']},indent=2))


if __name__ == '__main__':
    main()
