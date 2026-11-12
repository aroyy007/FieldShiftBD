import { useMemo } from 'react';
import { StyleSheet, Text, View } from 'react-native';
import Svg, { Circle, G, Path, Rect, Text as SvgText } from 'react-native-svg';
import { BD_DISTRICTS, BD_MAP, BD_MAP_CREDIT } from '../data/bd-districts.generated';

/** Weather-station reference points behind the bundled NASA POWER caches (see backend cache manifests). */
export const NASA_REFERENCE_POINTS: { district: string; latitude: number; longitude: number }[] = [
  { district: 'Rajshahi', latitude: 24.37, longitude: 88.7 },
  { district: 'Chattogram', latitude: 22.22, longitude: 91.8 },
  { district: 'Dhaka', latitude: 23.78, longitude: 90.38 },
];
// NASA POWER meteorology grid (MERRA-2): 0.5° latitude × 0.625° longitude cells.
const CELL_LAT = 0.5;
const CELL_LON = 0.625;

const key = (value?: string | null) => (value ?? '').toLowerCase().replace(/[^a-z]/g, '');
// Old and new English spellings map to one key (map shapes use current official spellings).
const ALIASES: Record<string, string> = {
  chittagong: 'chattogram', barisal: 'barishal', bogra: 'bogura', comilla: 'cumilla', jessore: 'jashore', nawabganj: 'chapainawabganj',
  jhalokathi: 'jhalakathi', jhalokati: 'jhalakathi', brahamanbaria: 'brahmanbaria', khagrachhari: 'khagrachari',
  netrakona: 'netrokona', maulvibazar: 'moulvibazar',
};
const sameDistrict = (a?: string | null, b?: string | null) => {
  const x = ALIASES[key(a)] ?? key(a);
  const y = ALIASES[key(b)] ?? key(b);
  return x.length > 0 && x === y;
};

const project = (latitude: number, longitude: number): [number, number] =>
  [(longitude - BD_MAP.lon0) * BD_MAP.kx, (BD_MAP.lat1 - latitude) * BD_MAP.scale];

const insideBangladesh = (latitude: number, longitude: number) => latitude > 20.4 && latitude < 26.8 && longitude > 87.9 && longitude < 92.8;

function distanceKm(aLat: number, aLon: number, bLat: number, bLon: number) {
  const r = 6371;
  const dLat = ((bLat - aLat) * Math.PI) / 180;
  const dLon = ((bLon - aLon) * Math.PI) / 180;
  const h = Math.sin(dLat / 2) ** 2 + Math.cos((aLat * Math.PI) / 180) * Math.cos((bLat * Math.PI) / 180) * Math.sin(dLon / 2) ** 2;
  return 2 * r * Math.asin(Math.sqrt(h));
}

export function powerCell(latitude: number, longitude: number) {
  const centerLat = Math.round(latitude / CELL_LAT) * CELL_LAT;
  const centerLon = -180 + Math.round((longitude + 180) / CELL_LON) * CELL_LON;
  return { south: centerLat - CELL_LAT / 2, north: centerLat + CELL_LAT / 2, west: centerLon - CELL_LON / 2, east: centerLon + CELL_LON / 2 };
}

type Props = {
  latitude?: number | null;
  longitude?: number | null;
  district?: string | null;
  /** 'locate': whole country with the field pin. 'nasa': zoom on the field and the NASA POWER data cell. */
  mode?: 'locate' | 'nasa';
  language?: 'bn' | 'en';
  height?: number;
};

export default function FieldMap({ latitude, longitude, district, mode = 'locate', language = 'en', height = 300 }: Props) {
  const bn = language === 'bn';
  const hasPin = latitude != null && longitude != null && insideBangladesh(latitude, longitude);
  const reference = NASA_REFERENCE_POINTS.find(point => sameDistrict(point.district, district));
  const cell = reference ? powerCell(reference.latitude, reference.longitude) : null;

  const viewBox = useMemo(() => {
    if (mode !== 'nasa' || (!hasPin && !reference)) return `0 0 ${BD_MAP.width} ${BD_MAP.height}`;
    const lats = [latitude, reference?.latitude, cell?.north, cell?.south].filter((v): v is number => v != null);
    const lons = [longitude, reference?.longitude, cell?.east, cell?.west].filter((v): v is number => v != null);
    const pad = 0.45;
    const [x1, y1] = project(Math.max(...lats) + pad, Math.min(...lons) - pad);
    const [x2, y2] = project(Math.min(...lats) - pad, Math.max(...lons) + pad);
    const w = x2 - x1;
    const h = y2 - y1;
    const size = Math.max(w, h * 1.4);
    const cx = x1 + w / 2;
    const cy = y1 + h / 2;
    return `${cx - size / 2} ${cy - size / 2.8} ${size} ${size / 1.4}`;
  }, [mode, hasPin, reference, latitude, longitude, cell]);

  const zoom = mode === 'nasa' ? 0.55 : 1;
  const pin = hasPin ? project(latitude as number, longitude as number) : null;
  const refPoint = reference ? project(reference.latitude, reference.longitude) : null;
  const cellBox = cell ? { topLeft: project(cell.north, cell.west), bottomRight: project(cell.south, cell.east) } : null;
  const km = hasPin && reference ? distanceKm(latitude as number, longitude as number, reference.latitude, reference.longitude) : null;

  return (
    <View style={styles.wrap}>
      <View style={[styles.mapBox, { height }]} accessible accessibilityRole="image"
        accessibilityLabel={bn ? 'জমির অবস্থানের মানচিত্র' : 'Map of the field location'}>
        <Svg width="100%" height="100%" viewBox={viewBox} preserveAspectRatio="xMidYMid meet">
          <Rect x={-2000} y={-2000} width={6000} height={6000} fill="#eceee8" />
          <G>
            {BD_DISTRICTS.map(item => {
              const mine = sameDistrict(item.name, district);
              const hasData = NASA_REFERENCE_POINTS.some(point => sameDistrict(point.district, item.name));
              return <Path key={item.name} d={item.d} fill={mine ? '#b9dca4' : hasData && mode === 'nasa' ? '#e7efd9' : '#f6f1e2'}
                stroke="#5d7a5f" strokeWidth={(mine ? 2.2 : 1) * zoom} />;
            })}
          </G>
          {mode === 'nasa' && BD_DISTRICTS.map(item => (
            <SvgText key={`label-${item.name}`} x={item.center[0]} y={item.center[1]} fontSize={13 * zoom} fill="#6b7f6c" textAnchor="middle">{item.name}</SvgText>
          ))}
          {mode === 'nasa' && cellBox && (
            <Rect x={cellBox.topLeft[0]} y={cellBox.topLeft[1]} width={cellBox.bottomRight[0] - cellBox.topLeft[0]}
              height={cellBox.bottomRight[1] - cellBox.topLeft[1]} fill="rgba(31,111,178,0.14)" stroke="#1f6fb2" strokeWidth={3 * zoom} strokeDasharray={`${10 * zoom},${6 * zoom}`} />
          )}
          {mode === 'nasa' && refPoint && <Circle cx={refPoint[0]} cy={refPoint[1]} r={9 * zoom} fill="#1f6fb2" stroke="#fff" strokeWidth={2 * zoom} />}
          {pin && (
            <G>
              <Circle cx={pin[0]} cy={pin[1]} r={(mode === 'nasa' ? 12 : 16) * zoom * (mode === 'nasa' ? 1.6 : 1)} fill="rgba(200,69,47,0.25)" />
              <Circle cx={pin[0]} cy={pin[1]} r={(mode === 'nasa' ? 6 : 8) * zoom * (mode === 'nasa' ? 1.6 : 1)} fill="#c8452f" stroke="#fff" strokeWidth={2.5 * zoom} />
            </G>
          )}
        </Svg>
      </View>

      <View style={styles.legend}>
        {pin && <Legend color="#c8452f" round text={bn ? 'আপনার জমি' : 'Your field'} />}
        {!pin && <Text style={styles.note}>{district
          ? (bn ? 'জমির সঠিক জায়গা যোগ করতে জমিতে দাঁড়িয়ে "বর্তমান অবস্থান" চাপুন।' : 'Stand in the field and tap "Use current location" to add its exact spot.')
          : (bn ? 'জমির অবস্থান এখনও সেভ হয়নি। "বর্তমান অবস্থান" চাপুন বা জেলা বাছুন।' : 'Field location not saved yet. Use your current location or pick a district.')}</Text>}
        {mode === 'nasa' && refPoint && <Legend color="#1f6fb2" round text={bn ? 'NASA POWER-এর নমুনা পয়েন্ট (আবহাওয়া কেন্দ্র)' : 'NASA POWER reference point (weather station)'} />}
        {mode === 'nasa' && cellBox && <Legend color="#1f6fb2" text={bn ? 'NASA POWER-এর একটি ঘর (প্রায় ৫৫ × ৬৩ কিমি)' : 'One NASA POWER grid cell (about 55 × 63 km)'} />}
      </View>

      {mode === 'nasa' && (
        <Text style={styles.body}>
          {reference
            ? (bn
              ? `NASA POWER বৃষ্টি ও তাপমাত্রার তথ্য এই বড় ঘরের গড় (উপগ্রহ ও মডেল থেকে তৈরি), আপনার জমির মাপ নয়।${km != null ? ` আপনার জমি নমুনা পয়েন্ট থেকে প্রায় ${String(Math.round(km)).replace(/[0-9]/g, d => '০১২৩৪৫৬৭৮৯'[Number(d)])} কিমি দূরে।` : ''} তাই এটি এলাকার আবহাওয়ার ইতিহাস বোঝায়; আপনার জমির পানি, মাটি ও অভিজ্ঞতা এর সঙ্গে মিলিয়ে দেখুন।`
              : `NASA POWER rainfall and temperature describe this whole grid cell (built from satellites and weather models), not a measurement in your field.${km != null ? ` Your field is about ${Math.round(km)} km from the reference point.` : ''} Read it as the area's weather history and compare it with what you see on your land.`)
            : (bn
              ? 'আপনার জেলার জন্য NASA POWER-এর সংরক্ষিত তথ্য এখনও নেই (এখন রাজশাহী, চট্টগ্রাম ও ঢাকা)।'
              : 'No saved NASA POWER history for your district yet (currently Rajshahi, Chattogram and Dhaka).')}
        </Text>
      )}
      <Text style={styles.credit}>{BD_MAP_CREDIT}</Text>
    </View>
  );
}

function Legend({ color, text, round }: { color: string; text: string; round?: boolean }) {
  return (
    <View style={styles.legendRow}>
      <View style={[styles.swatch, { borderColor: color, backgroundColor: round ? color : 'rgba(31,111,178,0.14)', borderRadius: round ? 99 : 3, borderStyle: round ? 'solid' : 'dashed' }]} />
      <Text style={styles.legendText}>{text}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: { gap: 8 },
  mapBox: { width: '100%', borderRadius: 14, overflow: 'hidden', borderWidth: 1, borderColor: '#d9e3d4', backgroundColor: '#eceee8' },
  legend: { gap: 6 },
  legendRow: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  swatch: { width: 16, height: 16, borderWidth: 2 },
  legendText: { fontSize: 14, color: '#2c3b30', flexShrink: 1 },
  body: { fontSize: 15, lineHeight: 22, color: '#2c3b30' },
  note: { fontSize: 14, lineHeight: 20, color: '#5c6b60' },
  credit: { fontSize: 11, color: '#7a867c' },
});
