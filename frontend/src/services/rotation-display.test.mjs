import assert from 'node:assert/strict';
import { test } from 'node:test';
import { describeRotationStep, comparisonRefreshKey, evidenceAvailabilityText } from './rotation-display.ts';

test('evidence status distinguishes bundled citations from cached data in both languages', () => {
  assert.equal(evidenceAvailabilityText('bundled_reference', 'en'), 'Bundled source reference');
  assert.equal(evidenceAvailabilityText('hit', 'en'), 'Available in cache');
  assert.equal(evidenceAvailabilityText('bundled_reference', 'bn'), 'রিপোজিটরিতে থাকা উৎসের রেফারেন্স');
  assert.equal(evidenceAvailabilityText('hit', 'bn'), 'ক্যাশে পাওয়া গেছে');
});

test('dated baseline identifies crop interval and expected versus recorded harvest', () => {
  const completed = describeRotationStep({crop_code:'wheat',start_date:'2026-01-01',end_date:'2026-04-10',event_basis:'farmer_reported'}, 'en');
  const active = describeRotationStep({crop_code:'rice',start_date:'2026-08-01',end_date:'2026-11-15',event_basis:'active_season_expected_harvest'}, 'en');
  assert.match(completed, /Wheat/);
  assert.match(completed, /2026-01-01.*2026-04-10/);
  assert.match(completed, /recorded interval/);
  assert.match(active, /Rice/);
  assert.match(active, /expected harvest/);
  assert.match(describeRotationStep({crop_code:'rice'},'bn'), /তারিখ নেই/);
});

test('season activation and corrected dates invalidate the comparison request context', () => {
  const planned = {season_id:'s1',status:'planned',planting_date:'2026-08-01'};
  assert.notEqual(comparisonRefreshKey(planned,0), comparisonRefreshKey({...planned,status:'active'},0));
  assert.notEqual(comparisonRefreshKey({...planned,status:'active'},0), comparisonRefreshKey({...planned,status:'active',planting_date:'2026-08-10'},0));
});

test('calendar weather label distinguishes historical bounds from unavailable values', async () => {
  const { calendarWeatherText } = await import('./rotation-display.ts');
  const weather={status:'available',short_interval_median_mm:88,long_interval_median_mm:125,valid_year_count:11};
  const label=calendarWeatherText(weather,'en');
  assert.match(label,/88.0–125.0 mm/);
  assert.match(label,/11 historical years/);
  assert.match(label,/not a forecast/);
  const missing=calendarWeatherText({...weather,status:'insufficient_data',short_interval_median_mm:null,long_interval_median_mm:null},'bn');
  assert.match(missing,/তথ্য অপর্যাপ্ত/);
  assert.doesNotMatch(missing,/0\.0/);
});

test('calendar low rainfall explanation names threshold and avoids false precision', async () => {
  const { calendarDrySpellText } = await import('./rotation-display.ts');
  const weather={status:'available',short_interval_dry_spell_median_days:4,long_interval_dry_spell_median_days:9,valid_year_count:11};
  assert.match(calendarDrySpellText(weather,'en'), /4\.0.*9\.0.*1 mm/);
  assert.match(calendarDrySpellText(weather,'bn'), /পূর্বাভাস নয়/);
  assert.match(calendarDrySpellText(weather,'bn'), /দীর্ঘতম/);
  assert.match(calendarDrySpellText({...weather,status:'insufficient_data'},'en'), /insufficient/i);
});

test('pilot observation is clearly unreviewed and not field rainfall', async () => {
  const { pilotObservationText } = await import('./rotation-display.ts');
  const pilot={date:'2024-01-01',mean_mm:0,coverage_fraction:1,native_support_count:9,bbox_wgs84:[88.5,24.2,88.8,24.5]};
  assert.match(pilotObservationText(pilot,'en'), /2024-01-01.*0\.0 mm/);
  assert.match(pilotObservationText(pilot,'en'), /not a field measurement/i);
  assert.match(pilotObservationText(pilot,'bn'), /জমির সরাসরি মাপ নয়/);
});
