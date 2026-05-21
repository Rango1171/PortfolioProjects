import { BoundingBox } from '../types';
import { getColorForLevel } from './colors';

export interface AnnotationData {
  image: string;
  boxes: Array<{
    x: number;
    y: number;
    width: number;
    height: number;
    level: string;
  }>;
}

export function parseJSONFile(content: string): AnnotationData {
  try {
    const data = JSON.parse(content);

    let boxes = data.boxes;
    if (!Array.isArray(boxes)) {
      if (Array.isArray(data.layout_blocks)) {
        boxes = data.layout_blocks
          .filter((block: any) => block.bbox)
          .map((block: any) => {
            const bbox = block.bbox;
            return {
              x: bbox[0],
              y: bbox[1],
              width: bbox[2] - bbox[0],
              height: bbox[3] - bbox[1],
              level: block.level || 'Level 1',
            };
          });
      } else {
        throw new Error('Invalid JSON format: boxes or layout_blocks must be present');
      }
    }

    return { image: data.image || '', boxes } as AnnotationData;
  } catch (error) {
    throw new Error(`Failed to parse JSON: ${error instanceof Error ? error.message : String(error)}`);
  }
}

export function jsonToBoxes(data: AnnotationData): BoundingBox[] {
  return data.boxes.map((box) => ({
    id: `${Date.now()}-${Math.random()}`,
    x: box.x,
    y: box.y,
    width: box.width,
    height: box.height,
    level: box.level,
    color: getColorForLevel(box.level),
  }));
}

export function boxesToJSON(imageName: string, boxes: BoundingBox[]): AnnotationData {
  return {
    image: imageName,
    boxes: boxes.map((box) => ({
      x: box.x,
      y: box.y,
      width: box.width,
      height: box.height,
      level: box.level,
    })),
  };
}

export function downloadJSON(data: AnnotationData, filename: string): void {
  const blob = new Blob([JSON.stringify(data, null, 2)], {
    type: 'application/json',
  });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename.endsWith('.json') ? filename : `${filename}.json`;
  a.click();
  URL.revokeObjectURL(url);
}

export function downloadImage(canvas: HTMLCanvasElement, filename: string): void {
  canvas.toBlob((blob) => {
    if (!blob) return;
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename.endsWith('.png') ? filename : `${filename}.png`;
    a.click();
    URL.revokeObjectURL(url);
  });
}
