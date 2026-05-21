# Newspaper Archive Digitization

A professional image annotation tool for digitizing newspaper archives. Draw, resize, and manage bounding boxes on newspaper images with intuitive controls and export capabilities.

## Features

- **Image Upload** - Load newspaper images for annotation
- **Bounding Box Drawing** - Click and drag to create rectangular annotations
- **Box Management** - Drag, resize, and delete bounding boxes with ease
- **Level Classification** - Assign hierarchy levels to boxes (Level 1, Level 2, etc.)
- **Multi-selection** - Hold Shift to select multiple boxes
- **Zoom & Pan** - Zoom in/out with smooth scrolling and pan when zoomed
- **Keyboard Shortcuts** - Press Delete to remove selected boxes
- **Export Options** - Download annotated images and annotations as JSON
- **JSON Import** - Load previously annotated data

## Getting Started

### Installation

```bash
npm install
```

### Development

```bash
npm run dev
```

Opens the application at `http://localhost:5173`

### Building

```bash
npm run build
```

## Usage

### Drawing Boxes

1. Upload a newspaper image
2. Click and drag on the image to create a bounding box
3. Boxes are automatically assigned the current level color
4. All boxes are outlined with their assigned level label

### Manipulating Boxes

- **Select** - Click on a box to select it
- **Multi-select** - Hold Shift while clicking to select multiple boxes
- **Drag** - Click and drag inside a selected box to move it
- **Resize** - Grab the resize handles (8 white squares) around selected boxes
- **Delete** - Press Delete key or use the Delete button to remove selected boxes

### Zoom & Navigation

- **Zoom In** - Click "Zoom In" button or scroll up with mouse wheel
- **Zoom Out** - Click "Zoom Out" button or scroll down with mouse wheel
- **Pan** - Right-click and drag to pan around the image when zoomed
- **Reset** - Click "Reset" to return to default zoom and position

### Levels

Assign boxes to different hierarchy levels:
- **Level 1** - Primary content (default)
- **Level 2** - Secondary content
- **Level 3** - Tertiary content
- **Level 4** - Additional content

Each level has a distinct color for easy visual identification.

### Merging Boxes

Select multiple boxes and click "Merge" to combine them into a single bounding box that encompasses all selected boxes.

### Export

- **Download Image** - Exports the annotated image as PNG
- **Download JSON** - Exports all box coordinates and metadata as JSON for future use

### Import

- **Upload JSON** - Load a previously saved annotation file to continue editing

## Keyboard Shortcuts

| Action | Shortcut |
|--------|----------|
| Delete Selected Boxes | Delete |
| Zoom In | Scroll Up |
| Zoom Out | Scroll Down |
| Pan Image | Right-click + Drag |

## Technologies

- **React** - UI framework
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **Canvas API** - Image rendering and annotation
- **Lucide React** - Icons
- **Vite** - Build tool

## Project Structure

```
src/
├── components/
│   ├── ImageEditor.tsx      # Main editor component
│   └── Toolbar.tsx          # Control toolbar
├── utils/
│   ├── canvasManager.ts     # Canvas rendering logic
│   ├── boxManipulation.ts   # Box manipulation utilities
│   ├── colors.ts            # Level color mapping
│   ├── jsonImportExport.ts  # JSON handling
│   └── supabaseClient.ts    # Database client
├── types/
│   └── index.ts             # TypeScript type definitions
└── App.tsx                  # Application root
```

## Tips

- Use precise clicks on box corners for accurate resize operations
- Right-click drag works best for smooth panning when zoomed in
- Merge boxes to create encompassing annotations for grouped content
- Save your work frequently by downloading JSON files

## Browser Support

Works on modern browsers supporting:
- Canvas API
- ES2020+
- CSS3 Transforms
