import { Platform } from 'react-native';

/**
 * Prefer the platform UI font. On Apple platforms this resolves to San Francisco;
 * web and other platforms fall back to their native UI sans-serif font.
 * Apple font files are intentionally not bundled in the app.
 */
export const ENGLISH_FONT_FAMILY = Platform.select({
  web: '-apple-system, BlinkMacSystemFont, system-ui, sans-serif',
  ios: 'System',
  android: 'sans-serif',
  default: 'sans-serif',
}) ?? 'sans-serif';
