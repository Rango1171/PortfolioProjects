import { Upload, Trash2, Merge, Download, ZoomIn, ZoomOut, RotateCcw } from 'lucide-react';
import { AVAILABLE_LEVELS } from '../utils/colors';

interface ToolbarProps {
  onUpload: (file: File) => void;
  onDelete: () => void;
  onMerge: () => void;
  onDownloadImage: () => void;
  onDownloadJSON: () => void;
  onZoomIn: () => void;
  onZoomOut: () => void;
  onReset: () => void;
  onJSONUpload: (file: File) => void;
  currentLevel: string;
  onLevelChange: (level: string) => void;
  selectedCount: number;
  hasBoxes: boolean;
  zoomLevel: number;
}

function Tooltip({ children, text }: { children: React.ReactNode; text: string }) {
  return (
    <div className="group relative">
      {children}
      <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-2 py-1 bg-slate-800 text-white text-xs rounded whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none">
        {text}
      </div>
    </div>
  );
}

export default function Toolbar({
  onUpload,
  onDelete,
  onMerge,
  onDownloadImage,
  onDownloadJSON,
  onZoomIn,
  onZoomOut,
  onReset,
  onJSONUpload,
  currentLevel,
  onLevelChange,
  selectedCount,
  hasBoxes,
  zoomLevel,
}: ToolbarProps) {
  return (
    <div className="bg-white rounded-lg shadow-lg p-4 mb-6">
      <div className="flex flex-wrap gap-3 items-center">
        <div className="border-r border-slate-300 pr-3 flex gap-2">
          <Tooltip text="Upload Image">
            <label className="flex items-center justify-center w-10 h-10 bg-blue-600 text-white rounded-lg cursor-pointer hover:bg-blue-700 transition">
              <Upload size={20} />
              <input type="file" accept="image/*" onChange={(e) => e.target.files?.[0] && onUpload(e.target.files[0])} className="hidden" />
            </label>
          </Tooltip>

          <Tooltip text="Load JSON">
            <label className="flex items-center justify-center w-10 h-10 bg-slate-600 text-white rounded-lg cursor-pointer hover:bg-slate-700 transition">
              <Upload size={20} />
              <input type="file" accept=".json" onChange={(e) => e.target.files?.[0] && onJSONUpload(e.target.files[0])} className="hidden" />
            </label>
          </Tooltip>
        </div>

        <div className="border-r border-slate-300 pr-3">
          <select value={currentLevel} onChange={(e) => onLevelChange(e.target.value)} className="px-3 py-2 border-2 border-slate-300 rounded-lg focus:outline-none focus:border-blue-500 text-sm">
            {AVAILABLE_LEVELS.map((level) => (
              <option key={level} value={level}>
                {level}
              </option>
            ))}
          </select>
        </div>

        <div className="border-r border-slate-300 pr-3 flex gap-2">
          <Tooltip text={`Delete (${selectedCount} selected)`}>
            <button onClick={onDelete} disabled={selectedCount === 0} className="flex items-center justify-center w-10 h-10 bg-red-600 text-white rounded-lg disabled:bg-slate-300 disabled:cursor-not-allowed hover:bg-red-700 transition">
              <Trash2 size={20} />
            </button>
          </Tooltip>

          <Tooltip text={`Merge (${selectedCount} selected)`}>
            <button onClick={onMerge} disabled={selectedCount < 2} className="flex items-center justify-center w-10 h-10 bg-green-600 text-white rounded-lg disabled:bg-slate-300 disabled:cursor-not-allowed hover:bg-green-700 transition">
              <Merge size={20} />
            </button>
          </Tooltip>
        </div>

        <div className="border-r border-slate-300 pr-3 flex gap-2">
          <Tooltip text="Zoom In">
            <button onClick={onZoomIn} className="flex items-center justify-center w-10 h-10 bg-slate-600 text-white rounded-lg hover:bg-slate-700 transition">
              <ZoomIn size={20} />
            </button>
          </Tooltip>

          <span className="text-sm text-slate-600 font-medium w-12 text-center">{Math.round(zoomLevel * 100)}%</span>

          <Tooltip text="Zoom Out">
            <button onClick={onZoomOut} className="flex items-center justify-center w-10 h-10 bg-slate-600 text-white rounded-lg hover:bg-slate-700 transition">
              <ZoomOut size={20} />
            </button>
          </Tooltip>

          <Tooltip text="Reset View">
            <button onClick={onReset} className="flex items-center justify-center w-10 h-10 bg-slate-600 text-white rounded-lg hover:bg-slate-700 transition">
              <RotateCcw size={20} />
            </button>
          </Tooltip>
        </div>

        <div className="ml-auto flex gap-2">
          <Tooltip text="Download Image">
            <button onClick={onDownloadImage} disabled={!hasBoxes} className="flex items-center justify-center w-10 h-10 bg-slate-700 text-white rounded-lg disabled:bg-slate-300 disabled:cursor-not-allowed hover:bg-slate-800 transition">
              <Download size={20} />
            </button>
          </Tooltip>

          <Tooltip text="Download JSON">
            <button onClick={onDownloadJSON} disabled={!hasBoxes} className="flex items-center justify-center w-10 h-10 bg-slate-700 text-white rounded-lg disabled:bg-slate-300 disabled:cursor-not-allowed hover:bg-slate-800 transition">
              <Download size={20} />
            </button>
          </Tooltip>
        </div>
      </div>

      {hasBoxes && (
        <div className="mt-3 text-sm text-slate-600">
          {selectedCount} box(es) selected
        </div>
      )}
    </div>
  );
}
