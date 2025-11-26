#!/usr/bin/env python3
"""
Export vertices to Skybrush .skyc format
Rescales vertices to (-20, 20) bounds for X,Y and (0, 50) for Z
"""

import numpy as np
import json
import sys
from skybrush_export_v2 import export_vertices_to_skybrush


def rescale_vertices_to_bounds(vertices, xy_bounds=(-20, 20), z_bounds=(0, 50)):
    """
    Rescale vertices to target bounds while maintaining aspect ratio.
    X and Y use xy_bounds, Z uses z_bounds.

    Args:
        vertices: Array of shape (n, 3) with XYZ coordinates
        xy_bounds: Tuple of (min, max) for X and Y directions
        z_bounds: Tuple of (min, max) for Z direction

    Returns:
        Rescaled vertices array
    """
    vertices = np.array(vertices)

    if len(vertices) == 0:
        return vertices

    # Find current bounds
    min_vals = np.min(vertices, axis=0)
    max_vals = np.max(vertices, axis=0)

    # Calculate current ranges
    ranges = max_vals - min_vals
    max_range = np.max(ranges)

    if max_range < 1e-10:
        # All points are the same, center them
        xy_center = (xy_bounds[0] + xy_bounds[1]) / 2
        z_center = (z_bounds[0] + z_bounds[1]) / 2
        return np.column_stack([
            np.full(len(vertices), xy_center),
            np.full(len(vertices), xy_center),
            np.full(len(vertices), z_center)
        ])

    # Calculate center
    center = (min_vals + max_vals) / 2

    # Use the smaller of the two bounds ranges to maintain aspect ratio
    xy_range = xy_bounds[1] - xy_bounds[0]
    z_range = z_bounds[1] - z_bounds[0]
    target_range = min(xy_range, z_range)

    # Scale to fit within target bounds
    scale = target_range / max_range

    # Center and scale
    rescaled = (vertices - center) * scale

    # Shift to target centers for each axis
    xy_center = (xy_bounds[0] + xy_bounds[1]) / 2
    z_center = (z_bounds[0] + z_bounds[1]) / 2

    rescaled[:, 0] += xy_center  # X
    rescaled[:, 1] += xy_center  # Y
    rescaled[:, 2] += z_center   # Z

    return rescaled


def vertices_to_skybrush(vertices, output_file="vertices_show.skyc",
                         n_frames=100, fps=4.0,
                         show_title="Polyhedron Vertices"):
    """
    Export vertices to Skybrush format as stationary positions.

    Args:
        vertices: List of [x, y, z] vertex positions
        output_file: Output .skyc filename
        n_frames: Number of trajectory frames (default 100)
        fps: Frames per second
        show_title: Show title

    Returns:
        True if successful, False otherwise
    """
    try:
        if len(vertices) == 0:
            print("Error: No vertices to export")
            return False

        print(f"\n[Vertex Export] Processing {len(vertices)} vertices...")
        print(f"  Original bounds: X[{min(v[0] for v in vertices):.2f}, {max(v[0] for v in vertices):.2f}], "
              f"Y[{min(v[1] for v in vertices):.2f}, {max(v[1] for v in vertices):.2f}], "
              f"Z[{min(v[2] for v in vertices):.2f}, {max(v[2] for v in vertices):.2f}]")

        # Rescale vertices: X,Y to (-20, 20), Z to (0, 50)
        rescaled = rescale_vertices_to_bounds(np.array(vertices), xy_bounds=(-20, 20), z_bounds=(0, 50))

        print(f"  Rescaled bounds: X[{np.min(rescaled[:, 0]):.2f}, {np.max(rescaled[:, 0]):.2f}], "
              f"Y[{np.min(rescaled[:, 1]):.2f}, {np.max(rescaled[:, 1]):.2f}], "
              f"Z[{np.min(rescaled[:, 2]):.2f}, {np.max(rescaled[:, 2]):.2f}]")

        # Export to Skybrush using V2 format
        success = export_vertices_to_skybrush(
            rescaled,
            output_file=output_file,
            n_frames=n_frames,
            fps=fps,
            show_title=show_title
        )

        duration = (n_frames - 1) / fps
        if success:
            print(f"\n✓ Successfully exported {len(vertices)} vertices to {output_file}")
            print(f"  Each drone will hover at its vertex position for {duration:.2f}s ({n_frames} frames at {fps} FPS)")

        return success

    except Exception as e:
        print(f"\n✗ Export failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python export_vertices.py <vertices_json>")
        print("\nExample:")
        print('  python export_vertices.py \'[[1,2,3], [4,5,6], [7,8,9]]\'')
        sys.exit(1)

    try:
        # Parse vertices from command line argument
        vertices_json = sys.argv[1]
        vertices = json.loads(vertices_json)

        # Optional parameters
        output_file = sys.argv[2] if len(sys.argv) > 2 else "vertices_show.skyc"

        # Export to Skybrush
        success = vertices_to_skybrush(vertices, output_file)

        sys.exit(0 if success else 1)

    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON format: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
