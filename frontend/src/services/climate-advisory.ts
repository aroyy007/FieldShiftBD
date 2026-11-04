import { apiRequest } from './api-client';
import type { DistrictCacheInventory } from '../modules/shared/contracts.generated';
import type { PlantingWindowEvidence, VarietyCalendarReference } from './m2-advisor';

export type PublicAdvisory = {
  status: 'needs_selection' | 'provisional' | 'insufficient_data';
  district_code: string;
  district_name: string;
  district_name_bn: string;
  crop_code: 'rice';
  season: string | null;
  season_choices: string[];
  message_bn: string;
  message_en: string;
  sms_bn: string;
  sms_en: string;
  definition_review_status: 'exploratory_pending_review';
  annual_comparison: PlantingWindowEvidence['annual_comparison'];
  recommended_shift_days: null;
  gdd_summary: null;
  calendar_references: VarietyCalendarReference[];
  data_provenance: PlantingWindowEvidence['data_provenance'] | null;
  limitations_bn: string[];
  limitations_en: string[];
};

export function loadPublicAdvisory(district: string, season: string) {
  return apiRequest<PublicAdvisory>(`/advisory?district=${encodeURIComponent(district)}&crop=rice&season=${encodeURIComponent(season)}`);
}

export function loadDistrictCacheInventory() {
  return apiRequest<DistrictCacheInventory>('/advisory/districts');
}
