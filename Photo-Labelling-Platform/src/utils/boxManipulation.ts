import { BoundingBox, Point } from '../types';

export type ResizeHandle =
  | 'top-left'
  | 'top-right'
  | 'bottom-left'
  | 'bottom-right'
  | 'top-center'
  | 'bottom-center'
  | 'left-center'
  | 'right-center'
  | null;

const HANDLE_SIZE = 8;

export class BoxManipulator {
  static getHandleAtPoint(
    box: BoundingBox,
    point: Point,
    scale: number,
    threshold: number = 10
  ): ResizeHandle {
    const handleSize = HANDLE_SIZE / scale;
    const handles = this.getHandlePositions(box);

    for (const [name, pos] of Object.entries(handles)) {
      const distance = Math.sqrt(
        Math.pow(point.x - pos.x, 2) + Math.pow(point.y - pos.y, 2)
      );
      if (distance <= threshold) {
        return name as ResizeHandle;
      }
    }
    return null;
  }

  private static getHandlePositions(box: BoundingBox): Record<string, Point> {
    return {
      'top-left': { x: box.x, y: box.y },
      'top-right': { x: box.x + box.width, y: box.y },
      'bottom-left': { x: box.x, y: box.y + box.height },
      'bottom-right': { x: box.x + box.width, y: box.y + box.height },
      'top-center': { x: box.x + box.width / 2, y: box.y },
      'bottom-center': { x: box.x + box.width / 2, y: box.y + box.height },
      'left-center': { x: box.x, y: box.y + box.height / 2 },
      'right-center': { x: box.x + box.width, y: box.y + box.height / 2 },
    };
  }

  static resizeBox(
    box: BoundingBox,
    handle: ResizeHandle,
    delta: Point
  ): BoundingBox {
    if (!handle) return box;

    const newBox = { ...box };
    const minSize = 10;

    switch (handle) {
      case 'top-left':
        newBox.x += delta.x;
        newBox.y += delta.y;
        newBox.width -= delta.x;
        newBox.height -= delta.y;
        break;
      case 'top-right':
        newBox.y += delta.y;
        newBox.width += delta.x;
        newBox.height -= delta.y;
        break;
      case 'bottom-left':
        newBox.x += delta.x;
        newBox.width -= delta.x;
        newBox.height += delta.y;
        break;
      case 'bottom-right':
        newBox.width += delta.x;
        newBox.height += delta.y;
        break;
      case 'top-center':
        newBox.y += delta.y;
        newBox.height -= delta.y;
        break;
      case 'bottom-center':
        newBox.height += delta.y;
        break;
      case 'left-center':
        newBox.x += delta.x;
        newBox.width -= delta.x;
        break;
      case 'right-center':
        newBox.width += delta.x;
        break;
    }

    if (newBox.width < minSize) newBox.width = minSize;
    if (newBox.height < minSize) newBox.height = minSize;

    return newBox;
  }

  static dragBox(box: BoundingBox, delta: Point): BoundingBox {
    return {
      ...box,
      x: box.x + delta.x,
      y: box.y + delta.y,
    };
  }

  static isPointInBox(box: BoundingBox, point: Point): boolean {
    return (
      point.x >= box.x &&
      point.x <= box.x + box.width &&
      point.y >= box.y &&
      point.y <= box.y + box.height
    );
  }

  static getCursorForHandle(handle: ResizeHandle): string {
    const cursors: Record<string, string> = {
      'top-left': 'nwse-resize',
      'top-right': 'nesw-resize',
      'bottom-left': 'nesw-resize',
      'bottom-right': 'nwse-resize',
      'top-center': 'ns-resize',
      'bottom-center': 'ns-resize',
      'left-center': 'ew-resize',
      'right-center': 'ew-resize',
    };
    return cursors[handle || ''] || 'default';
  }
}

export function mergeBoxes(selectedBoxes: BoundingBox[]): BoundingBox {
  if (selectedBoxes.length === 0) throw new Error('No boxes to merge');

  const minX = Math.min(...selectedBoxes.map((b) => b.x));
  const minY = Math.min(...selectedBoxes.map((b) => b.y));
  const maxX = Math.max(...selectedBoxes.map((b) => b.x + b.width));
  const maxY = Math.max(...selectedBoxes.map((b) => b.y + b.height));

  return {
    id: Date.now().toString(),
    x: minX,
    y: minY,
    width: maxX - minX,
    height: maxY - minY,
    level: selectedBoxes[0].level,
    color: selectedBoxes[0].color,
  };
}
