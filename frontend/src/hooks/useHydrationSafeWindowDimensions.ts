import { useSyncExternalStore } from 'react';
import { Dimensions, Platform, type ScaledSize } from 'react-native';

// Expo's static renderer reports a zero-sized window. Keep the server render
// and the browser's first render aligned, then switch to the measured viewport.
const INITIAL_DIMENSIONS: ScaledSize = {
  width: 393,
  height: 852,
  scale: 1,
  fontScale: 1,
};

let cachedSnapshot: ScaledSize | undefined;

function subscribe(onChange: () => void): () => void {
  if (Platform.OS === 'web' && typeof window !== 'undefined') {
    window.addEventListener('resize', onChange);
    return () => window.removeEventListener('resize', onChange);
  }

  const subscription = Dimensions.addEventListener('change', onChange);
  return () => subscription.remove();
}

function getSnapshot(): ScaledSize {
  const measured = Platform.OS === 'web' && typeof window !== 'undefined'
    ? {
        width: window.innerWidth,
        height: window.innerHeight,
        scale: window.devicePixelRatio || 1,
        fontScale: 1,
      }
    : Dimensions.get('window');
  const next = measured.width > 0 && measured.height > 0
    ? measured
    : INITIAL_DIMENSIONS;
  if (
    cachedSnapshot
    && cachedSnapshot.width === next.width
    && cachedSnapshot.height === next.height
    && cachedSnapshot.scale === next.scale
    && cachedSnapshot.fontScale === next.fontScale
  ) {
    return cachedSnapshot;
  }
  cachedSnapshot = next;
  return next;
}

function getServerSnapshot(): ScaledSize {
  return INITIAL_DIMENSIONS;
}

export function useHydrationSafeWindowDimensions(): ScaledSize {
  return useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);
}
