export const COLORS = {
  primary: '#2e7d32', // restrained green
  primaryLight: '#60ad5e',
  primaryDark: '#005005',
  background: '#f5f7f5', // neutral natural background
  surface: '#ffffff',
  text: '#1f2923',
  textSecondary: '#5a6b5d',
  border: '#d0d6d1',
  error: '#d32f2f',
  warning: '#f57c00',
  success: '#388e3c',
};

export const SPACING = {
  xs: 4,
  sm: 8,
  md: 16,
  lg: 24,
  xl: 32,
  xxl: 48,
};

export const BORDER_RADIUS = {
  sm: 4,
  md: 8,
  lg: 12,
  xl: 16,
  round: 9999,
};

export const TYPOGRAPHY = {
  h1: { fontSize: 32, fontWeight: 'bold' as const, color: COLORS.text },
  h2: { fontSize: 24, fontWeight: 'bold' as const, color: COLORS.text },
  h3: { fontSize: 18, fontWeight: '600' as const, color: COLORS.text },
  body: { fontSize: 16, fontWeight: '400' as const, color: COLORS.text },
  bodySecondary: { fontSize: 16, fontWeight: '400' as const, color: COLORS.textSecondary },
  caption: { fontSize: 12, fontWeight: '400' as const, color: COLORS.textSecondary },
};

export const SHADOWS = {
  sm: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 2,
  },
  md: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.08,
    shadowRadius: 4,
    elevation: 4,
  },
};
