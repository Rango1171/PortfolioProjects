import { useRef, useState, useEffect } from 'react';
import { BoundingBox, Point } from '../types';
import { getColorForLevel } from '../utils/colors';
import { CanvasManager, calculateCanvasSize } from '../utils/canvasManager';
import { BoxManipulator, mergeBoxes } from '../utils/boxManipulation';
import {
  parseJSONFile,
  jsonToBoxes,
  boxesToJSON,
  downloadJSON,
  downloadImage,
} from '../utils/jsonImportExport';
import Toolbar from './Toolbar';

type EditMode = 'draw' | 'drag' | 'resize' | 'pan' | 'none';

export default function ImageEditor() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [image, setImage] = useState<HTMLImageElement | null>(null);
  const [imageName, setImageName] = useState<string>('');
  const [boxes, setBoxes] = useState<BoundingBox[]>([]);
  const [selectedBoxIds, setSelectedBoxIds] = useState<Set<string>>(new Set());
  const [currentLevel, setCurrentLevel] = useState<string>('Level 1');
  const [scale, setScale] = useState(1);
  const [baseScale, setBaseScale] = useState(1);
  const [zoomLevel, setZoomLevel] = useState(1);
  const [panOffset, setPanOffset] = useState({ x: 0, y: 0 });
  const [isDrawing, setIsDrawing] = useState(false);
  const [startPoint, setStartPoint] = useState<Point | null>(null);
  const [editMode, setEditMode] = useState<EditMode>('none');
  const [draggedBoxId, setDraggedBoxId] = useState<string | null>(null);
  const [resizingBoxId, setResizingBoxId] = useState<string | null>(null);
  const [resizeHandle, setResizeHandle] = useState<string | null>(null);
  const [lastMousePoint, setLastMousePoint] = useState<Point | null>(null);
  const [canvasManager, setCanvasManager] = useState<CanvasManager | null>(null);

  useEffect(() => {
    if (image && canvasRef.current) {
      const canvas = canvasRef.current;
      const { width, height, scale: calculatedScale } = calculateCanvasSize(image);

      setBaseScale(calculatedScale);

      const scaledWidth = image.width * calculatedScale * zoomLevel;
      const scaledHeight = image.height * calculatedScale * zoomLevel;
      canvas.width = scaledWidth;
      canvas.height = scaledHeight;

      const actualScale = calculatedScale * zoomLevel;
      setScale(actualScale);

      const manager = new CanvasManager(canvas, image, boxes, selectedBoxIds, actualScale, panOffset);
      setCanvasManager(manager);
      manager.draw();
    }
  }, [image, boxes, selectedBoxIds, zoomLevel, panOffset]);

  const handleImageUpload = (file: File) => {
    const nameWithoutExt = file.name.replace(/\.[^/.]+$/, '');
    setImageName(nameWithoutExt);

    const reader = new FileReader();
    reader.onload = (event) => {
      const img = new Image();
      img.onload = () => {
        setImage(img);
        setBoxes([]);
        setSelectedBoxIds(new Set());
      };
      img.src = event.target?.result as string;
    };
    reader.readAsDataURL(file);
  };

  const handleJSONUpload = (file: File) => {
    const reader = new FileReader();
    reader.onload = (event) => {
      try {
        const content = event.target?.result as string;
        const data = parseJSONFile(content);
        const newBoxes = jsonToBoxes(data);
        setBoxes(newBoxes);
        setSelectedBoxIds(new Set());
      } catch (error) {
        alert(`Error loading JSON: ${error instanceof Error ? error.message : String(error)}`);
      }
    };
    reader.readAsText(file);
  };

  const getCanvasCoordinates = (e: React.MouseEvent<HTMLCanvasElement> | MouseEvent): Point => {
    const canvas = canvasRef.current;
    if (!canvas) return { x: 0, y: 0 };

    const rect = canvas.getBoundingClientRect();
    const clientX = 'clientX' in e ? e.clientX : (e as any).clientX || 0;
    const clientY = 'clientY' in e ? e.clientY : (e as any).clientY || 0;

    return {
      x: (clientX - rect.left - panOffset.x) / scale,
      y: (clientY - rect.top - panOffset.y) / scale,
    };
  };

  const handleMouseDown = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (zoomLevel > 1 && e.button === 2) {
      setLastMousePoint(getCanvasCoordinates(e));
      setEditMode('pan');
      return;
    }

    const point = getCanvasCoordinates(e);
    setLastMousePoint(point);

    const selectedBox = boxes.find((b) => selectedBoxIds.has(b.id));

    if (selectedBox) {
      const handle = BoxManipulator.getHandleAtPoint(selectedBox, point, scale);
      if (handle) {
        setResizingBoxId(selectedBox.id);
        setResizeHandle(handle);
        setEditMode('resize');
        return;
      }

      if (BoxManipulator.isPointInBox(selectedBox, point)) {
        setDraggedBoxId(selectedBox.id);
        setEditMode('drag');
        return;
      }
    }

    const clickedBox = boxes.find(
      (box) =>
        !selectedBoxIds.has(box.id) &&
        BoxManipulator.isPointInBox(box, point)
    );

    if (clickedBox) {
      if (e.shiftKey) {
        setSelectedBoxIds((prev) => {
          const newSet = new Set(prev);
          newSet.add(clickedBox.id);
          return newSet;
        });
      } else {
        setSelectedBoxIds(new Set([clickedBox.id]));
      }
    } else {
      if (!e.shiftKey) setSelectedBoxIds(new Set());
      setIsDrawing(true);
      setStartPoint(point);
      setEditMode('draw');
    }
  };

  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    const currentPoint = getCanvasCoordinates(e);

    if (editMode === 'pan' && lastMousePoint && canvas) {
      const delta = {
        x: (e.clientX - (lastMousePoint.x * scale + panOffset.x)) / scale,
        y: (e.clientY - (lastMousePoint.y * scale + panOffset.y)) / scale,
      };
      setPanOffset((prev) => ({
        x: prev.x + e.movementX,
        y: prev.y + e.movementY,
      }));
    } else if (editMode === 'draw' && isDrawing && startPoint && canvasManager) {
      canvasManager.drawPreviewBox(startPoint, currentPoint, currentLevel);
    } else if (editMode === 'drag' && draggedBoxId && lastMousePoint) {
      const delta = {
        x: currentPoint.x - lastMousePoint.x,
        y: currentPoint.y - lastMousePoint.y,
      };

      setBoxes((prev) =>
        prev.map((box) =>
          box.id === draggedBoxId ? BoxManipulator.dragBox(box, delta) : box
        )
      );
      setLastMousePoint(currentPoint);
    } else if (editMode === 'resize' && resizingBoxId && lastMousePoint && resizeHandle) {
      const delta = {
        x: currentPoint.x - lastMousePoint.x,
        y: currentPoint.y - lastMousePoint.y,
      };

      setBoxes((prev) =>
        prev.map((box) =>
          box.id === resizingBoxId
            ? BoxManipulator.resizeBox(box, resizeHandle as any, delta)
            : box
        )
      );
      setLastMousePoint(currentPoint);
    } else {
      const selectedBox = boxes.find((b) => selectedBoxIds.has(b.id));
      if (selectedBox) {
        const handle = BoxManipulator.getHandleAtPoint(selectedBox, currentPoint, scale);
        const cursor = BoxManipulator.getCursorForHandle(handle as any);
        if (canvas) canvas.style.cursor = cursor;
      } else if (canvas) {
        canvas.style.cursor = zoomLevel > 1 ? 'grab' : 'crosshair';
      }
    }
  };

  const handleMouseUp = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (editMode === 'draw' && isDrawing && startPoint) {
      const currentPoint = getCanvasCoordinates(e);

      const x = Math.min(startPoint.x, currentPoint.x);
      const y = Math.min(startPoint.y, currentPoint.y);
      const width = Math.abs(currentPoint.x - startPoint.x);
      const height = Math.abs(currentPoint.y - startPoint.y);

      if (width > 5 && height > 5) {
        const newBox: BoundingBox = {
          id: Date.now().toString(),
          x,
          y,
          width,
          height,
          level: currentLevel,
          color: getColorForLevel(currentLevel),
        };
        setBoxes([...boxes, newBox]);
      }
    }

    setIsDrawing(false);
    setStartPoint(null);
    setEditMode('none');
    setDraggedBoxId(null);
    setResizingBoxId(null);
    setResizeHandle(null);
    setLastMousePoint(null);
  };

  const handleDelete = () => {
    setBoxes(boxes.filter((box) => !selectedBoxIds.has(box.id)));
    setSelectedBoxIds(new Set());
  };

  const handleMerge = () => {
    if (selectedBoxIds.size < 2) return;

    const selectedBoxes = boxes.filter((box) => selectedBoxIds.has(box.id));
    const merged = mergeBoxes(selectedBoxes);

    setBoxes([...boxes.filter((box) => !selectedBoxIds.has(box.id)), merged]);
    setSelectedBoxIds(new Set());
  };

  const handleZoomIn = () => {
    setZoomLevel((prev) => Math.min(prev + 0.2, 3));
  };

  const handleZoomOut = () => {
    setZoomLevel((prev) => Math.max(prev - 0.2, 0.5));
  };

  const handleReset = () => {
    setZoomLevel(1);
    setPanOffset({ x: 0, y: 0 });
  };

  const handleWheel = (e: React.WheelEvent<HTMLCanvasElement>) => {
    e.preventDefault();
    const delta = e.deltaY > 0 ? -0.1 : 0.1;
    const newZoom = Math.min(Math.max(zoomLevel + delta, 0.5), 3);
    setZoomLevel(newZoom);
  };

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Delete' && selectedBoxIds.size > 0) {
        setBoxes(boxes.filter((box) => !selectedBoxIds.has(box.id)));
        setSelectedBoxIds(new Set());
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [boxes, selectedBoxIds]);

  const handleDownloadImage = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    downloadImage(canvas, `${imageName || 'annotated-image'}.png`);
  };

  const handleDownloadJSON = () => {
    const data = boxesToJSON(imageName, boxes);
    downloadJSON(data, `${imageName || 'annotations'}.json`);
  };

  return (
    <div className="min-h-screen bg-slate-50 p-6">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold text-slate-800 mb-6">
          Newspaper Archive Digitization
        </h1>

        <Toolbar
          onUpload={handleImageUpload}
          onJSONUpload={handleJSONUpload}
          onDelete={handleDelete}
          onMerge={handleMerge}
          onDownloadImage={handleDownloadImage}
          onDownloadJSON={handleDownloadJSON}
          onZoomIn={handleZoomIn}
          onZoomOut={handleZoomOut}
          onReset={handleReset}
          currentLevel={currentLevel}
          onLevelChange={setCurrentLevel}
          selectedCount={selectedBoxIds.size}
          hasBoxes={boxes.length > 0}
          zoomLevel={zoomLevel}
        />

        {image ? (
          <div ref={containerRef} className="bg-white rounded-lg shadow-lg p-6 flex justify-center overflow-hidden">
            <canvas
              ref={canvasRef}
              onMouseDown={handleMouseDown}
              onMouseMove={handleMouseMove}
              onMouseUp={handleMouseUp}
              onMouseLeave={handleMouseUp}
              onWheel={handleWheel}
              onContextMenu={(e) => e.preventDefault()}
              className="border-2 border-slate-300 rounded-lg"
              style={{ transform: `translate(${panOffset.x}px, ${panOffset.y}px)` }}
            />
          </div>
        ) : (
          <div className="bg-white rounded-lg shadow-lg p-12 text-center">
            <p className="text-slate-600 text-lg">Upload a newspaper image to begin</p>
          </div>
        )}
      </div>
    </div>
  );
}
