import { apiRequest } from './api-client';

export type UpazilaRef = { code: string; region_code: string; name: string; name_bn: string };
export type DistrictRef = {
  code: string;
  region_code: string;
  name: string;
  name_bn: string;
  aliases: string[];
  upazilas: UpazilaRef[];
};
export type DivisionRef = { code: string; region_code: string; name: string; name_bn: string; districts: DistrictRef[] };

export type VocabularyItem = { code: string; label_en: string; label_bn: string; aliases: string[] };
export type ProfileVocabulary = {
  soil_textures: VocabularyItem[];
  land_types: VocabularyItem[];
  area_units: (VocabularyItem & { square_metres: string })[];
};

export type CropVarietyRef = { crop_variety_id: string; name: string; description: string | null };
export type CropCatalogItem = {
  crop_id: string;
  name: string;
  name_bn: string | null;
  scientific_name: string | null;
  catalog_key: string | null;
  aliases: string[];
  varieties: CropVarietyRef[];
};

let locationsPromise: Promise<DivisionRef[]> | null = null;
let vocabularyPromise: Promise<ProfileVocabulary> | null = null;

/** Division → district → upazila reference (BBS geocodes). Cached per app session. */
export function loadLocations(): Promise<DivisionRef[]> {
  locationsPromise ??= apiRequest<DivisionRef[]>('/reference/locations').catch(error => {
    locationsPromise = null;
    throw error;
  });
  return locationsPromise;
}

/** Canonical soil textures, land types, and area units. Cached per app session. */
export function loadProfileVocabulary(): Promise<ProfileVocabulary> {
  vocabularyPromise ??= apiRequest<ProfileVocabulary>('/reference/profile-vocabulary').catch(error => {
    vocabularyPromise = null;
    throw error;
  });
  return vocabularyPromise;
}

/** The M1 crop catalog changes when reference data is imported, so it is not cached. */
export function loadCropCatalog(): Promise<CropCatalogItem[]> {
  return apiRequest<CropCatalogItem[]>('/crops');
}

export function findDistrict(divisions: DivisionRef[], name: string | null | undefined): DistrictRef | undefined {
  if (!name) return undefined;
  const key = name.trim().toLowerCase();
  for (const division of divisions) {
    const match = division.districts.find(district =>
      district.name.toLowerCase() === key || district.aliases.some(alias => alias.toLowerCase() === key));
    if (match) return match;
  }
  return undefined;
}

export function divisionForDistrict(divisions: DivisionRef[], district: DistrictRef | undefined): DivisionRef | undefined {
  return district ? divisions.find(division => division.districts.some(item => item.code === district.code)) : undefined;
}

export function landTypeLabel(vocabulary: ProfileVocabulary | null, code: string | null | undefined): string {
  if (!code) return 'Not set';
  return vocabulary?.land_types.find(item => item.code === code)?.label_en ?? code;
}
