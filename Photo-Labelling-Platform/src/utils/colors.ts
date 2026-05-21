const LEVEL_COLORS: Record<string, string> = {
  'Level 1': '#ef4444',
  'Level 2': '#3b82f6',
  'Level 3': '#10b981',
  'Level 4': '#f59e0b',
  'Level 5': '#ec4899',
  'Level 6': '#8b5cf6',
  'Level 7': '#14b8a6',
  'Level 8': '#f97316',
};

export const getColorForLevel = (level: string): string => {
  return LEVEL_COLORS[level] || '#6b7280';
};

export const AVAILABLE_LEVELS = Object.keys(LEVEL_COLORS);
