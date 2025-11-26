# OBJ Vertex Visualizer

A Python script to visualize vertices from .obj (Wavefront OBJ) 3D model files. This tool extracts and displays only the vertex positions as points in 3D space.

## Features

- Parse .obj files and extract vertex data
- Display vertices as 3D scatter plot
- Interactive rotation and zoom (when showing live)
- Save visualizations to image files (PNG, JPG, etc.)
- Print detailed vertex information
- Shows bounding box and center point
- Equal aspect ratio for accurate representation

## Installation

### Prerequisites

Python 3.6 or higher is required.

### Install Dependencies

```bash
pip install -r requirements.txt
```

Or install manually:

```bash
pip install numpy matplotlib
```

## Usage

### Basic Usage (Interactive Window)

```bash
python3 visualize_obj.py <obj_file_path>
```

This will open an interactive 3D visualization window where you can:
- Rotate the view by clicking and dragging
- Zoom with mouse wheel or trackpad
- Pan by right-clicking and dragging

**Example:**
```bash
python3 visualize_obj.py sample_cube.obj
```

### Save to File (Non-Interactive)

```bash
python3 visualize_obj.py <obj_file_path> --save <output_file>
```

**Examples:**
```bash
python3 visualize_obj.py sample_cube.obj --save cube.png
python3 visualize_obj.py model.obj --save output.jpg
python3 visualize_obj.py mesh.obj --save visualization.pdf
```

Supported output formats: PNG, JPG, PDF, SVG

## Sample OBJ File

A sample cube OBJ file (`sample_cube.obj`) is included for testing. It contains 8 vertices representing the corners of a unit cube.

## Output Information

The script displays:

1. **Vertex Count**: Total number of vertices in the model
2. **Bounding Box**: Min/max coordinates for X, Y, Z axes
3. **Center Point**: Geometric center of all vertices
4. **Vertex List**: Coordinates of the first 10 vertices

Example output:
```
============================================================
VERTEX INFORMATION
============================================================
Total vertices: 8

Bounding box:
  X: [-1.0000, 1.0000]
  Y: [-1.0000, 1.0000]
  Z: [-1.0000, 1.0000]

Center:
  (0.0000, 0.0000, 0.0000)

First 10 vertices:
------------------------------------------------------------
  v0: ( -1.0000,  -1.0000,  -1.0000)
  v1: ( -1.0000,  -1.0000,   1.0000)
  ...
============================================================
```

## OBJ File Format

The script reads standard Wavefront OBJ files. It specifically looks for vertex lines:

```
v x y z
```

Where:
- `v` indicates a vertex
- `x`, `y`, `z` are floating-point coordinates

The script ignores:
- Comments (lines starting with `#`)
- Face definitions (`f`)
- Texture coordinates (`vt`)
- Normals (`vn`)
- Other OBJ elements

## Visualization Features

- **Point Color**: Purple (#667eea)
- **Point Size**: Adaptive based on model size
- **Grid**: Semi-transparent grid for spatial reference
- **Axes**: Labeled X, Y, Z axes
- **Equal Aspect**: All axes have the same scale
- **Info Box**: Shows total vertex count
- **High Resolution**: 150 DPI when saving to file

## Examples

### Example 1: Visualize a Cube
```bash
python3 visualize_obj.py sample_cube.obj
```

### Example 2: Save Icosahedron Visualization
```bash
python3 visualize_obj.py icosahedron.obj --save icosahedron.png
```

### Example 3: Complex Model
```bash
python3 visualize_obj.py complex_model.obj --save model_vertices.png
```

## Troubleshooting

### No vertices found
- Check that your OBJ file contains vertex lines (`v x y z`)
- Ensure the file is a valid text file
- Verify the file path is correct

### Import errors
Make sure dependencies are installed:
```bash
pip install numpy matplotlib
```

### Window doesn't open (macOS)
If using macOS and the window doesn't appear, try:
```bash
python3 visualize_obj.py file.obj --save output.png
```
to save directly to a file instead.

## Script Options

```
python3 visualize_obj.py <obj_file_path> [--save output_file]

Arguments:
  obj_file_path     Path to the .obj file to visualize
  --save            Optional: Save to file instead of showing window
  output_file       Output filename (PNG, JPG, PDF, SVG)
```

## How It Works

1. **Parse**: Reads the .obj file line by line
2. **Extract**: Finds all lines starting with 'v ' and extracts coordinates
3. **Analyze**: Calculates bounding box, center, and statistics
4. **Visualize**: Creates a 3D scatter plot with matplotlib
5. **Display/Save**: Shows interactive window or saves to file

## Performance

The script can handle models with thousands of vertices efficiently. For very large models (>100k vertices), consider:
- Using the `--save` option to avoid interactive rendering
- Reducing point size in the code if points overlap

## License

ISC

## Related Tools

This repository also includes a JavaScript-based Conway-Hart polyhedron viewer. See `README.md` for details.
