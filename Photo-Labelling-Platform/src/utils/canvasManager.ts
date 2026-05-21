import { BoundingBox, Point } from '../types';
import { getColorForLevel } from './colors';

export class CanvasManager {
  private canvas: HTMLCanvasElement;
  private ctx: CanvasRenderingContext2D;
  private image: HTMLImageElement;
  private scale: number;
  private boxes: BoundingBox[];
  private selectedBoxIds: Set<string>;
  private panOffset: { x: number; y: number };

  constructor(
    canvas: HTMLCanvasElement,
    image: HTMLImageElement,
    boxes: BoundingBox[],
    selectedBoxIds: Set<string>,
    scale: number,
    panOffset: { x: number; y: number } = { x: 0, y: 0 }
  ) {
    this.canvas = canvas;
    this.image = image;
    this.boxes = boxes;
    this.selectedBoxIds = selectedBoxIds;
    this.scale = scale;
    this.panOffset = panOffset;

    const ctx = canvas.getContext('2d');
    if (!ctx) throw new Error('Could not get canvas context');
    this.ctx = ctx;
  }

  draw(): void {
    this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
    this.ctx.drawImage(
      this.image,
      0,
      0,
      this.canvas.width,
      this.canvas.height
    );

    this.boxes.forEach((box) => {
      this.drawBox(box);
    });
  }

  private drawBox(box: BoundingBox): void {
    const isSelected = this.selectedBoxIds.has(box.id);

    this.ctx.strokeStyle = box.color;
    this.ctx.lineWidth = isSelected ? 4 : 2;
    this.ctx.strokeRect(
      box.x * this.scale,
      box.y * this.scale,
      box.width * this.scale,
      box.height * this.scale
    );

    this.ctx.fillStyle = box.color + '33';
    this.ctx.fillRect(
      box.x * this.scale,
      box.y * this.scale,
      box.width * this.scale,
      box.height * this.scale
    );

    this.ctx.fillStyle = box.color;
    this.ctx.font = 'bold 14px sans-serif';
    this.ctx.fillText(
      box.level,
      box.x * this.scale + 5,
      box.y * this.scale + 20
    );

    if (isSelected) {
      this.drawResizeHandles(box);

      this.ctx.strokeStyle = '#fff';
      this.ctx.lineWidth = 1;
      this.ctx.setLineDash([5, 5]);
      this.ctx.strokeRect(
        box.x * this.scale - 2,
        box.y * this.scale - 2,
        box.width * this.scale + 4,
        box.height * this.scale + 4
      );
      this.ctx.setLineDash([]);
    }
  }

  private drawResizeHandles(box: BoundingBox): void {
    const handleSize = 8;
    const positions = [
      { x: box.x, y: box.y }, // top-left
      { x: box.x + box.width, y: box.y }, // top-right
      { x: box.x, y: box.y + box.height }, // bottom-left
      { x: box.x + box.width, y: box.y + box.height }, // bottom-right
      { x: box.x + box.width / 2, y: box.y }, // top-center
      { x: box.x + box.width / 2, y: box.y + box.height }, // bottom-center
      { x: box.x, y: box.y + box.height / 2 }, // left-center
      { x: box.x + box.width, y: box.y + box.height / 2 }, // right-center
    ];

    this.ctx.fillStyle = '#fff';
    positions.forEach((pos) => {
      this.ctx.fillRect(
        pos.x * this.scale - handleSize / 2,
        pos.y * this.scale - handleSize / 2,
        handleSize,
        handleSize
      );
      this.ctx.strokeStyle = box.color;
      this.ctx.lineWidth = 2;
      this.ctx.strokeRect(
        pos.x * this.scale - handleSize / 2,
        pos.y * this.scale - handleSize / 2,
        handleSize,
        handleSize
      );
    });
  }

  drawPreviewBox(startPoint: Point, currentPoint: Point, level: string): void {
    this.draw();

    const x = Math.min(startPoint.x, currentPoint.x);
    const y = Math.min(startPoint.y, currentPoint.y);
    const width = Math.abs(currentPoint.x - startPoint.x);
    const height = Math.abs(currentPoint.y - startPoint.y);

    const color = getColorForLevel(level);
    this.ctx.strokeStyle = color;
    this.ctx.lineWidth = 2;
    this.ctx.strokeRect(x * this.scale, y * this.scale, width * this.scale, height * this.scale);

    this.ctx.fillStyle = color + '33';
    this.ctx.fillRect(x * this.scale, y * this.scale, width * this.scale, height * this.scale);
  }

  getImageData(): ImageData {
    return this.ctx.getImageData(0, 0, this.canvas.width, this.canvas.height);
  }

  export(imageName: string): Blob | null {
    return new Promise<Blob | null>((resolve) => {
      this.canvas.toBlob((blob) => {
        resolve(blob);
      });
    }) as any;
  }
}

export function calculateCanvasSize(
  image: HTMLImageElement,
  maxWidth: number = 1200,
  maxHeight: number = 800
): { width: number; height: number; scale: number } {
  let width = image.width;
  let height = image.height;

  const scaleX = maxWidth / width;
  const scaleY = maxHeight / height;
  const scale = Math.min(scaleX, scaleY, 1);

  return {
    width: width * scale,
    height: height * scale,
    scale,
  };
}
