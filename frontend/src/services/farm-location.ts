import { Platform } from 'react-native';
import * as Location from 'expo-location';
import { DivisionRef, loadLocations } from './m1-reference';

export type FarmLocationSelection = {
  latitude: number;
  longitude: number;
  divisionCode?: string;
  districtCode?: string;
  upazilaCode?: string;
  notice: string;
};

function key(value: string | null | undefined): string {
  return (value ?? '').trim().toLocaleLowerCase().replace(/\s+/g, ' ');
}

function exactLocationMatch(
  divisions: DivisionRef[],
  address: Location.LocationGeocodedAddress,
): Pick<FarmLocationSelection, 'divisionCode' | 'districtCode' | 'upazilaCode'> {
  const divisionTokens = [address.region, address.subregion, address.name].map(key).filter(Boolean);
  const division = divisions.find(item => divisionTokens.includes(key(item.name)) || divisionTokens.includes(key(item.name_bn)));
  if (!division) return {};

  const districtTokens = [address.district, address.subregion, address.city, address.name].map(key).filter(Boolean);
  const district = division.districts.find(item =>
    districtTokens.includes(key(item.name)) || item.aliases.some(alias => districtTokens.includes(key(alias))));
  if (!district) return { divisionCode: division.code };

  const upazilaTokens = [address.subregion, address.city, address.name].map(key).filter(Boolean);
  const upazila = district.upazilas.find(item => upazilaTokens.includes(key(item.name)) || upazilaTokens.includes(key(item.name_bn)));
  return {
    divisionCode: division.code,
    districtCode: district.code,
    ...(upazila ? { upazilaCode: upazila.code } : {}),
  };
}

function browserPosition(): Promise<{ latitude: number; longitude: number }> {
  return new Promise((resolve, reject) => {
    if (typeof navigator === 'undefined' || !navigator.geolocation) {
      reject(new Error('Location is not supported by this browser.'));
      return;
    }
    navigator.geolocation.getCurrentPosition(
      ({ coords }) => resolve({ latitude: coords.latitude, longitude: coords.longitude }),
      error => reject(error),
      { enableHighAccuracy: true, timeout: 15000, maximumAge: 60000 },
    );
  });
}

export async function captureCurrentFarmLocation(): Promise<FarmLocationSelection> {
  let coordinates: { latitude: number; longitude: number };

  try {
    if (Platform.OS === 'web') {
      coordinates = await browserPosition();
      return {
        ...coordinates,
        notice: 'Coordinates captured. Select Division, District, and Upazila manually in the browser.',
      };
    }

    const permission = await Location.requestForegroundPermissionsAsync();
    if (permission.status !== 'granted') {
      throw new Error(permission.canAskAgain
        ? 'Location permission was not granted. Allow access or enter the location manually.'
        : 'Location permission is blocked. Enable it in device settings or enter the location manually.');
    }

    const position = await Location.getCurrentPositionAsync({ accuracy: Location.Accuracy.Balanced });
    coordinates = { latitude: position.coords.latitude, longitude: position.coords.longitude };
  } catch (error) {
    const message = error instanceof Error ? error.message : '';
    if (message.startsWith('Location permission')) throw error;
    if (/denied|permission/i.test(message)) {
      throw new Error('Location permission was denied. Allow access or enter the location manually.');
    }
    if (/timeout/i.test(message)) {
      throw new Error('Location request timed out. Try again or enter the location manually.');
    }
    throw new Error('Could not get your current location. Check device/browser location access or enter it manually.');
  }

  try {
    const addresses = await Location.reverseGeocodeAsync(coordinates);
    const divisions = await loadLocations();
    const match = addresses[0] ? exactLocationMatch(divisions, addresses[0]) : {};
    const resolvedAll = Boolean(match.divisionCode && match.districtCode && match.upazilaCode);
    return {
      ...coordinates,
      ...match,
      notice: resolvedAll
        ? 'Coordinates captured and administrative location matched. Please review the selected fields.'
        : 'Coordinates captured. We could not reliably match all administrative fields; review or select them manually.',
    };
  } catch {
    return {
      ...coordinates,
      notice: 'Coordinates captured. Administrative location could not be resolved; select those fields manually.',
    };
  }
}
