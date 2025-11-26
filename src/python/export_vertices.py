#!/usr/bin/env python3
"""
Export vertices to Skybrush .skyc format
Supports rotation and vertical scale animations at 25 keyframes/second
"""

import numpy as np
import json
import sys
from skybrush_export_v2 import export_vertices_to_skybrush


def find_shortest_edge(vertices, faces):
    """
    Find the shortest edge length in the polyhedron.
    """
    vertices = np.array(vertices, dtype=float)
    min_edge_length = float('inf')

    for face in faces:
        for i in range(len(face)):
            v1_idx = face[i]
            v2_idx = face[(i + 1) % len(face)]
            v1 = vertices[v1_idx]
            v2 = vertices[v2_idx]
            edge_length = np.linalg.norm(v2 - v1)
            if edge_length > 1e-10 and edge_length < min_edge_length:
                min_edge_length = edge_length

    return min_edge_length if min_edge_length != float('inf') else 1.0


def rescale_by_shortest_edge(vertices, faces, target_edge_length=4.0, altitude_offset=15.0):
    """
    Rescale vertices so the shortest edge equals target_edge_length,
    then add altitude_offset to all Z coordinates.
    """
    vertices = np.array(vertices, dtype=float)

    if len(vertices) == 0:
        return vertices

    # Find shortest edge
    shortest_edge = find_shortest_edge(vertices, faces)

    # Calculate scale factor
    scale = target_edge_length / shortest_edge

    print(f"  Shortest edge: {shortest_edge:.4f}")
    print(f"  Scale factor: {scale:.4f} (target edge: {target_edge_length})")

    # Center the vertices first
    center = np.mean(vertices, axis=0)
    rescaled = (vertices - center) * scale

    # Re-center at origin for XY, but shift Z up
    rescaled[:, 0] -= np.mean(rescaled[:, 0])
    rescaled[:, 1] -= np.mean(rescaled[:, 1])

    # Shift Z so minimum is at altitude_offset
    z_min = np.min(rescaled[:, 2])
    rescaled[:, 2] += (altitude_offset - z_min)

    print(f"  Altitude offset: +{altitude_offset} units")

    return rescaled


def rescale_vertices_to_bounds(vertices, xy_bounds=(-50, 50), z_bounds=(0, 100)):
    """
    Rescale vertices to target bounds while maintaining aspect ratio.
    (Legacy function - kept for compatibility)
    """
    vertices = np.array(vertices, dtype=float)

    if len(vertices) == 0:
        return vertices

    min_vals = np.min(vertices, axis=0)
    max_vals = np.max(vertices, axis=0)
    ranges = max_vals - min_vals
    max_range = np.max(ranges)

    if max_range < 1e-10:
        xy_center = (xy_bounds[0] + xy_bounds[1]) / 2
        z_center = (z_bounds[0] + z_bounds[1]) / 2
        return np.column_stack([
            np.full(len(vertices), xy_center),
            np.full(len(vertices), xy_center),
            np.full(len(vertices), z_center)
        ])

    center = (min_vals + max_vals) / 2
    xy_range = xy_bounds[1] - xy_bounds[0]
    z_range = z_bounds[1] - z_bounds[0]
    target_range = min(xy_range, z_range)
    scale = target_range / max_range

    rescaled = (vertices - center) * scale

    xy_center = (xy_bounds[0] + xy_bounds[1]) / 2
    z_center = (z_bounds[0] + z_bounds[1]) / 2

    rescaled[:, 0] += xy_center
    rescaled[:, 1] += xy_center
    rescaled[:, 2] += z_center

    return rescaled


def export_with_config(config):
    """
    Export vertices using a configuration dictionary.
    """
    try:
        vertices = config.get('vertices', [])
        faces = config.get('faces', [])
        output_file = config.get('outputFile', 'vertices_show.skyc')
        animation = config.get('animation', {})
        bounds = config.get('bounds', {})

        if len(vertices) == 0:
            print("Error: No vertices to export")
            return False

        # Get scaling settings
        target_edge_length = bounds.get('targetEdgeLength', 4.0)
        altitude_offset = bounds.get('altitudeOffset', 10.0)

        # Get animation settings
        fps = animation.get('fps', 25)
        duration = animation.get('duration', 30)

        print(f"\n[Vertex Export] Processing {len(vertices)} vertices...")
        print(f"  Animation config: {animation}")

        # Rescale vertices based on shortest edge
        if len(faces) > 0:
            rescaled = rescale_by_shortest_edge(
                np.array(vertices),
                faces,
                target_edge_length=target_edge_length,
                altitude_offset=altitude_offset
            )
        else:
            # Fallback if no faces provided - use legacy bounds-based scaling
            xy_min = bounds.get('xyMin', -50)
            xy_max = bounds.get('xyMax', 50)
            z_min = bounds.get('zMin', 0)
            z_max = bounds.get('zMax', 100)
            rescaled = rescale_vertices_to_bounds(
                np.array(vertices),
                xy_bounds=(xy_min, xy_max),
                z_bounds=(z_min, z_max)
            )
            # Add altitude offset
            rescaled[:, 2] += altitude_offset

        print(f"  Final range: X[{np.min(rescaled[:, 0]):.2f}, {np.max(rescaled[:, 0]):.2f}], "
              f"Y[{np.min(rescaled[:, 1]):.2f}, {np.max(rescaled[:, 1]):.2f}], "
              f"Z[{np.min(rescaled[:, 2]):.2f}, {np.max(rescaled[:, 2]):.2f}]")

        # Export to Skybrush
        success = export_vertices_to_skybrush(
            rescaled,
            output_file=output_file,
            fps=fps,
            show_title="Polyhedron Animation",
            animation=animation
        )

        return success

    except Exception as e:
        print(f"\n✗ Export failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python export_vertices.py <config_json>")
        sys.exit(1)

    try:
        config_json = sys.argv[1]
        config = json.loads(config_json)

        if 'vertices' in config and 'outputFile' in config:
            success = export_with_config(config)
        else:
            # Legacy format
            vertices = config if isinstance(config, list) else config.get('vertices', [])
            output_file = sys.argv[2] if len(sys.argv) > 2 else "vertices_show.skyc"
            legacy_config = {
                'vertices': vertices,
                'outputFile': output_file,
                'animation': {'enableRotation': False, 'duration': 30, 'fps': 25},
                'bounds': {'xyMin': -50, 'xyMax': 50, 'zMin': 0, 'zMax': 100}
            }
            success = export_with_config(legacy_config)

        sys.exit(0 if success else 1)

    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
