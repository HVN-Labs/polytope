#!/usr/bin/env python3
"""
OBJ File Vertex Visualizer
Reads an .obj file and displays only the vertices in 3D space
"""

import sys
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D


def parse_obj_file(filepath):
    """
    Parse an .obj file and extract vertices

    Args:
        filepath: Path to the .obj file

    Returns:
        numpy array of vertices (n x 3)
    """
    vertices = []

    try:
        with open(filepath, 'r') as f:
            for line in f:
                line = line.strip()

                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue

                # Parse vertex lines (v x y z)
                if line.startswith('v '):
                    parts = line.split()
                    if len(parts) >= 4:
                        x, y, z = float(parts[1]), float(parts[2]), float(parts[3])
                        vertices.append([x, y, z])

        if not vertices:
            print(f"Warning: No vertices found in {filepath}")
            return np.array([])

        return np.array(vertices)

    except FileNotFoundError:
        print(f"Error: File '{filepath}' not found")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading file: {e}")
        sys.exit(1)


def visualize_vertices(vertices, title="OBJ Vertices Visualization", output_file=None):
    """
    Visualize vertices in 3D space using matplotlib

    Args:
        vertices: numpy array of vertices (n x 3)
        title: Title for the plot
        output_file: If specified, save to this file instead of showing
    """
    if len(vertices) == 0:
        print("No vertices to visualize")
        return

    # Create figure and 3D axis
    fig = plt.figure(figsize=(12, 9))
    ax = fig.add_subplot(111, projection='3d')

    # Extract x, y, z coordinates
    x = vertices[:, 0]
    y = vertices[:, 1]
    z = vertices[:, 2]

    # Plot vertices as scatter points
    scatter = ax.scatter(x, y, z, c='#667eea', marker='o', s=50, alpha=0.8, edgecolors='white', linewidth=0.5)

    # Set labels
    ax.set_xlabel('X', fontsize=12, fontweight='bold')
    ax.set_ylabel('Y', fontsize=12, fontweight='bold')
    ax.set_zlabel('Z', fontsize=12, fontweight='bold')
    ax.set_title(title, fontsize=14, fontweight='bold', pad=20)

    # Set equal aspect ratio for all axes
    max_range = np.array([x.max()-x.min(), y.max()-y.min(), z.max()-z.min()]).max() / 2.0
    mid_x = (x.max()+x.min()) * 0.5
    mid_y = (y.max()+y.min()) * 0.5
    mid_z = (z.max()+z.min()) * 0.5
    ax.set_xlim(mid_x - max_range, mid_x + max_range)
    ax.set_ylim(mid_y - max_range, mid_y + max_range)
    ax.set_zlim(mid_z - max_range, mid_z + max_range)

    # Add grid
    ax.grid(True, alpha=0.3)

    # Add vertex count text
    vertex_count_text = f"Total Vertices: {len(vertices)}"
    ax.text2D(0.05, 0.95, vertex_count_text, transform=ax.transAxes,
              fontsize=12, verticalalignment='top',
              bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    # Enable rotation
    plt.tight_layout()

    if output_file:
        plt.savefig(output_file, dpi=150, bbox_inches='tight')
        print(f"Saved visualization to: {output_file}")
        plt.close()
    else:
        plt.show()


def print_vertex_info(vertices):
    """
    Print information about the vertices

    Args:
        vertices: numpy array of vertices (n x 3)
    """
    if len(vertices) == 0:
        return

    print("\n" + "="*60)
    print("VERTEX INFORMATION")
    print("="*60)
    print(f"Total vertices: {len(vertices)}")
    print(f"\nBounding box:")
    print(f"  X: [{vertices[:, 0].min():.4f}, {vertices[:, 0].max():.4f}]")
    print(f"  Y: [{vertices[:, 1].min():.4f}, {vertices[:, 1].max():.4f}]")
    print(f"  Z: [{vertices[:, 2].min():.4f}, {vertices[:, 2].max():.4f}]")
    print(f"\nCenter:")
    center = vertices.mean(axis=0)
    print(f"  ({center[0]:.4f}, {center[1]:.4f}, {center[2]:.4f})")
    print("\nFirst 10 vertices:")
    print("-"*60)
    for i, v in enumerate(vertices[:10]):
        print(f"  v{i}: ({v[0]:8.4f}, {v[1]:8.4f}, {v[2]:8.4f})")
    if len(vertices) > 10:
        print(f"  ... and {len(vertices) - 10} more vertices")
    print("="*60 + "\n")


def main():
    """Main function"""
    # Check command line arguments
    if len(sys.argv) < 2:
        print("Usage: python visualize_obj.py <obj_file_path> [--save output.png]")
        print("\nExamples:")
        print("  python visualize_obj.py model.obj")
        print("  python visualize_obj.py model.obj --save output.png")
        sys.exit(1)

    obj_filepath = sys.argv[1]
    output_file = None

    # Check for --save option
    if len(sys.argv) >= 4 and sys.argv[2] == '--save':
        output_file = sys.argv[3]

    print(f"\nLoading OBJ file: {obj_filepath}")

    # Parse the OBJ file
    vertices = parse_obj_file(obj_filepath)

    if len(vertices) == 0:
        print("No vertices found. Exiting.")
        sys.exit(1)

    # Print vertex information
    print_vertex_info(vertices)

    # Visualize the vertices
    if output_file:
        print(f"Generating visualization...")
        visualize_vertices(vertices, title=f"Vertices from {obj_filepath}", output_file=output_file)
    else:
        print("Opening 3D visualization...")
        print("(Close the window to exit)\n")
        visualize_vertices(vertices, title=f"Vertices from {obj_filepath}")


if __name__ == "__main__":
    main()
