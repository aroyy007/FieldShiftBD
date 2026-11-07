import type { RotationStepV2 } from '../modules/shared/contracts-v2.generated';

export function evidenceAvailabilityText(status: string, language: 'bn' | 'en'): string {
  const labels: Record<string, [string, string]> = {
    hit: ['Available in cache', 'ক্যাশে পাওয়া গেছে'],
    missing: ['Cache entry missing', 'ক্যাশে তথ্য নেই'],
    corrupt: ['Cache entry failed validation', 'ক্যাশের তথ্য যাচাই হয়নি'],
    not_acquired: ['Not acquired', 'সংগ্রহ করা হয়নি'],
    bundled_reference: ['Bundled source reference', 'রিপোজিটরিতে থাকা উৎসের রেফারেন্স'],
  };
  return labels[status]?.[language === 'bn' ? 1 : 0] ?? status;
}

export function describeRotationStep(step: RotationStepV2, language: 'bn' | 'en'): string {
  const bn = language === 'bn';
  const labels: Record<string, [string, string]> = {
    rice: ['Rice', 'ধান'], wheat: ['Wheat', 'গম'], chickpea: ['Chickpea', 'ছোলা'],
    mustard: ['Mustard', 'সরিষা'], mungbean: ['Mungbean', 'মুগ'],
    sesbania_rostrata: ['Green manure', 'সবুজ সার'],
  };
  const crop = labels[step.crop_code]?.[bn ? 1 : 0] ?? step.crop_code;
  const seasons: Record<string, [string, string]> = {aman:['Aman','আমন'],aus:['Aus','আউশ'],boro:['Boro','বোরো'],rabi:['Rabi','রবি']};
  const season = step.season_code ? ` · ${seasons[step.season_code]?.[bn ? 1 : 0] ?? step.season_code}` : '';
  const missing = bn ? 'তারিখ নেই' : 'date not recorded';
  const interval = `${step.start_date ?? missing} → ${step.end_date ?? missing}`;
  const basis = step.event_basis === 'active_season_expected_harvest'
    ? (bn ? 'সম্ভাব্য ফসল কাটার তারিখ' : 'expected harvest')
    : (bn ? 'নথিভুক্ত সময়' : 'recorded interval');
  return `${crop}${season} · ${interval}${step.start_date || step.end_date ? ` · ${basis}` : ''}`;
}

type SeasonContext = {season_id: string;status: string;planting_date?: string | null;expected_harvest_date?: string | null};
export function comparisonRefreshKey(season: SeasonContext | null, revision: number): string {
  return JSON.stringify([revision, season?.season_id, season?.status, season?.planting_date, season?.expected_harvest_date]);
}

export function calendarWeatherText(weather: {
  status: string; short_interval_median_mm: number | null; long_interval_median_mm: number | null; valid_year_count: number;
}, language: 'bn' | 'en'): string {
  const bn=language==='bn';
  if (weather.status !== 'available' || weather.short_interval_median_mm == null || weather.long_interval_median_mm == null) {
    return bn ? 'ঐতিহাসিক বৃষ্টির তথ্য অপর্যাপ্ত।' : 'Insufficient historical rainfall data.';
  }
  const interval=`${weather.short_interval_median_mm.toFixed(1)}–${weather.long_interval_median_mm.toFixed(1)} mm`;
  return bn ? `${interval} · ${weather.valid_year_count} বছরের ঐতিহাসিক মধ্যক; ছোট ও বড় ক্যালেন্ডার-সময়ের তুলনা, পূর্বাভাস নয়।`
    : `${interval} · ${weather.valid_year_count} historical years; medians for shorter/longer calendar intervals, not a forecast.`;
}

export function calendarDrySpellText(weather: {
  status: string; short_interval_dry_spell_median_days?: number | null; long_interval_dry_spell_median_days?: number | null; valid_year_count: number;
}, language: 'bn' | 'en'): string {
  const bn = language === 'bn';
  const short = weather.short_interval_dry_spell_median_days;
  const long = weather.long_interval_dry_spell_median_days;
  if (weather.status !== 'available' || short == null || long == null) {
    return bn ? 'স্বল্পবৃষ্টির ঐতিহাসিক তথ্য অপর্যাপ্ত।' : 'Insufficient historical low-rainfall data.';
  }
  const values = `${short.toFixed(1)}–${long.toFixed(1)}`;
  return bn ? `${values} দিন · প্রতি বছর ছোট ও বড় সময়ে দীর্ঘতম স্বল্পবৃষ্টির ধারার মধ্যক; দৈনিক বৃষ্টি সর্বোচ্চ ১ মিমি। এটি পূর্বাভাস নয়।`
    : `${values} days · median longest low-rainfall spells for shorter/longer intervals (≤ 1 mm per day); not a forecast.`;
}

export function pilotObservationText(pilot: {date: string; mean_mm: number; coverage_fraction: number; native_support_count: number; bbox_wgs84: number[]}, language: 'bn' | 'en'): string {
  const mean = pilot.mean_mm.toFixed(1);
  const coverage = (pilot.coverage_fraction * 100).toFixed(0);
  return language === 'bn'
    ? `${pilot.date} · ${mean} মিমি · নমুনা আয়তক্ষেত্রের বৈধ তথ্যযুক্ত অংশের ক্ষেত্রফল-ওজনযুক্ত গড়; ${coverage}% বৈধ coverage, ${pilot.native_support_count} উৎস-কোষ। এটি জমির সরাসরি মাপ নয়।`
    : `${pilot.date} · ${mean} mm · area-weighted mean over the valid covered area of the pilot rectangle; ${coverage}% valid coverage, ${pilot.native_support_count} source cells. Not a field measurement.`;
}
