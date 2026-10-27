import { Text } from '@/components/BanglaTypography';
import { useState } from 'react';
import { ActivityIndicator, Pressable, StyleSheet,  View } from 'react-native';
import * as Linking from 'expo-linking';
import { Button, Card } from './ui';
import { compareRotations } from '../services/m2-advisor';
import type { RotationComparison as RotationComparisonResult, RotationPriority } from '../services/m2-advisor';
import { COLORS, SPACING, TYPOGRAPHY } from '../theme/theme';

const PRIORITIES: { value: RotationPriority; label: string }[] = [
  { value: 'match_farm_context', label: 'Published context match' },
  { value: 'fewer_fallow_slots', label: 'Fewer fallow slots' },
  { value: 'include_legume', label: 'Include a legume' },
  { value: 'more_crop_types', label: 'More crop types' },
];

const FIT_LABELS = {
  matches_published_conditions: 'Matches the published BR15 context',
  not_published_conditions: 'Does not match a published farm condition',
  not_current_source_crop: 'Source is for rice; current crop is different',
  source_variety_not_confirmed: 'BR15 variety is not confirmed for this farm',
  farm_context_incomplete: 'Farm details are incomplete',
} as const;

function formatDelta(value: number | null, unit: string, decimals = 1) {
  if (value === null) return 'Not available';
  const sign = value > 0 ? '+' : '';
  return `${sign}${value.toFixed(decimals)} ${unit}`;
}

export default function RotationComparison({ farmlandId }: { farmlandId: string }) {
  const [priorities, setPriorities] = useState<RotationPriority[]>(['match_farm_context']);
  const [result, setResult] = useState<RotationComparisonResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [linkError, setLinkError] = useState('');

  function togglePriority(priority: RotationPriority) {
    setPriorities(current => current.includes(priority)
      ? (current.length > 1 ? current.filter(item => item !== priority) : current)
      : [...current, priority].slice(0, 4));
  }

  async function runComparison() {
    setLoading(true);
    setError('');
    try {
      setResult(await compareRotations(farmlandId, priorities));
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Could not compare crop patterns.');
    } finally {
      setLoading(false);
    }
  }

  async function openSource(url: string) {
    setLinkError('');
    try {
      await Linking.openURL(url);
    } catch {
      setLinkError('Could not open this source link on the device.');
    }
  }

  return (
    <Card>
      <Text style={styles.title}>Explore published rotation examples</Text>
      <Text style={styles.copy}>
        These BRRI examples are for BR15 rice, not field-level advice. A farm-context match appears only when the active crop and variety plus the recorded land and irrigation conditions match the source.
      </Text>

      <Text style={styles.label}>What matters for this comparison?</Text>
      <View style={styles.priorityList}>
        {PRIORITIES.map(item => {
          const selected = priorities.includes(item.value);
          return (
            <Pressable
              key={item.value}
              accessibilityRole="checkbox"
              accessibilityState={{ checked: selected }}
              onPress={() => togglePriority(item.value)}
              style={[styles.priorityChip, selected && styles.priorityChipSelected]}
            >
              <Text style={[styles.priorityText, selected && styles.priorityTextSelected]}>{item.label}</Text>
            </Pressable>
          );
        })}
      </View>
      <Button
        accessibilityRole="button"
        title={loading ? 'Comparing documented patterns…' : 'Compare crop sequences'}
        disabled={loading}
        onPress={() => void runComparison()}
      />
      {loading && <ActivityIndicator accessibilityLabel="Comparing crop sequences" color={COLORS.primary} />}
      {error ? <Text accessibilityRole="alert" style={styles.error}>{error}</Text> : null}
      {result ? (
        <View style={styles.results}>
          <View style={styles.climateBox}>
            <View style={styles.climateHeading}>
              <Text style={styles.label}>NASA POWER historical climate context</Text>
              <Text style={styles.cacheBadge}>
                {result.climate_context.cache_status.replace('_', ' ')}
              </Text>
            </View>
            <Text style={styles.note}>
              Requested period: {result.climate_context.requested_period?.start} to {result.climate_context.requested_period?.end}
              {result.climate_context.observed_period?.start && result.climate_context.observed_period?.end
                ? ` · observations ${result.climate_context.observed_period.start} to ${result.climate_context.observed_period.end}`
                : ''}
            </Text>
            {result.climate_context.period_comparison ? (
              <>
                <Text style={styles.climateMetric}>
                  Change in mean annual rainfall (later minus earlier): {formatDelta(result.climate_context.period_comparison.difference_later_minus_earlier.annual_rainfall_mm, 'mm/year')}
                </Text>
                <Text style={styles.climateMetric}>
                  Change in mean annual temperature (later minus earlier): {formatDelta(result.climate_context.period_comparison.difference_later_minus_earlier.annual_mean_temperature_c, '°C', 2)}
                </Text>
                <Text style={styles.note}>
                  Earlier period ({result.climate_context.period_comparison.earlier.start_year}–{result.climate_context.period_comparison.earlier.end_year}; {result.climate_context.period_comparison.earlier.years_observed}/{result.climate_context.period_comparison.earlier.years_available} usable/available years; {result.climate_context.period_comparison.earlier.coverage_percent}% daily coverage): {result.climate_context.period_comparison.earlier.mean_annual_rainfall_mm ?? '—'} mm/year, {result.climate_context.period_comparison.earlier.mean_annual_temperature_c ?? '—'}°C
                </Text>
                <Text style={styles.note}>
                  Later period ({result.climate_context.period_comparison.later.start_year}–{result.climate_context.period_comparison.later.end_year}; {result.climate_context.period_comparison.later.years_observed}/{result.climate_context.period_comparison.later.years_available} usable/available years; {result.climate_context.period_comparison.later.coverage_percent}% daily coverage): {result.climate_context.period_comparison.later.mean_annual_rainfall_mm ?? '—'} mm/year, {result.climate_context.period_comparison.later.mean_annual_temperature_c ?? '—'}°C
                </Text>
                <Text style={styles.note}>Only years/months with at least 90% daily coverage contribute to their averages; coverage percentages include all valid observations.</Text>
                <Text style={styles.label}>Monthly climate difference (later minus earlier)</Text>
                {result.climate_context.monthly_comparison.map(item => (
                  <Text key={`month-${item.month}`} style={styles.note}>
                    {new Date(2000, item.month - 1, 1).toLocaleString(undefined, { month: 'short' })}: rainfall {formatDelta(item.difference_later_minus_earlier.rainfall_mm, 'mm/month')}; temperature {formatDelta(item.difference_later_minus_earlier.temperature_c, '°C', 2)} · coverage {item.earlier.coverage_percent}% / {item.later.coverage_percent}%
                  </Text>
                ))}
              </>
            ) : (
              <Text style={styles.note}>{result.climate_context.unavailable_reason ?? 'Historical climate context is unavailable.'}</Text>
            )}
            <Text style={styles.note}>{result.climate_context.observation_scale}</Text>
            <Text style={styles.note}>Daily time standard: {result.climate_context.time_standard}</Text>
            <Text style={styles.note}>
              Parameters: {result.climate_context.parameters.map(parameter => `${parameter.label} (${parameter.code}; ${parameter.unit})`).join(' · ')}
            </Text>
            {result.climate_context.query_coordinate ? (
              <Text style={styles.note}>
                Coordinate sent to NASA POWER (rounded to 0.1°): {result.climate_context.query_coordinate.latitude.toFixed(1)}, {result.climate_context.query_coordinate.longitude.toFixed(1)}
              </Text>
            ) : null}
            {result.climate_context.unavailable_reason ? (
              <Text style={styles.notice}>{result.climate_context.unavailable_reason}</Text>
            ) : null}
            <Text style={styles.note}>
              Retrieved: {result.climate_context.retrieved_at ? new Date(result.climate_context.retrieved_at).toLocaleString() : 'not retrieved'}
            </Text>
            <Pressable accessibilityRole="link" onPress={() => void openSource(result.climate_context.source_reference)}>
              <Text style={styles.sourceLink}>{result.climate_context.dataset} · NASA documentation</Text>
            </Pressable>
            <Pressable accessibilityRole="link" onPress={() => void openSource(result.climate_context.resolution_reference)}>
              <Text style={styles.sourceLink}>NASA POWER resolution guidance</Text>
            </Pressable>
            <Text style={styles.note}>Climate values are historical context alongside these options. They do not rank the sequences or establish field suitability.</Text>
          </View>
          {result.status === 'profile_incomplete' ? (
            <Text style={styles.notice}>Some farm details are missing. The comparison marks applicability as unknown where needed.</Text>
          ) : null}
          {result.patterns.length === 0 ? (
            <Text style={styles.notice}>No source-backed patterns are available for this comparison yet.</Text>
          ) : null}
          {result.patterns.map((pattern, index) => (
            <View key={pattern.pattern_id} style={styles.pattern}>
              <Text style={styles.patternTitle}>Option {index + 1}</Text>
              <Text style={styles.sequence}>{pattern.sequence.join('  →  ')}</Text>
              <Text style={styles.factLine}>{pattern.crop_slots} crop slots · {pattern.distinct_crop_types} crop types · {pattern.fallow_slots} fallow slots</Text>
              <Text style={styles.fit}>{FIT_LABELS[pattern.fit_status]}</Text>
              {pattern.fit_notes.map((note, noteIndex) => <Text key={`${pattern.pattern_id}-fit-${noteIndex}`} style={styles.note}>• {note}</Text>)}
              {pattern.sequence_notes.map((note, noteIndex) => <Text key={`${pattern.pattern_id}-note-${noteIndex}`} style={styles.note}>• {note}</Text>)}
              {pattern.priority_matches.length > 0 ? (
                <Text style={styles.priorityMatch}>Matches selected priority: {pattern.priority_matches.map(value => PRIORITIES.find(item => item.value === value)?.label ?? value).join(', ')}</Text>
              ) : null}
              <Pressable accessibilityRole="link" onPress={() => void openSource(pattern.source.source_reference)}>
                <Text style={styles.sourceLink}>{pattern.source.source_name} · Open source</Text>
              </Pressable>
              {pattern.source.limitation ? <Text style={styles.note}>{pattern.source.limitation}</Text> : null}
            </View>
          ))}
          <View style={styles.evidenceBox}>
            <Text style={styles.label}>Evidence and limits</Text>
            {result.additional_evidence.map(source => (
              <View key={source.source_reference}>
                <Text style={styles.note}>{source.claim}</Text>
                <Pressable accessibilityRole="link" onPress={() => void openSource(source.source_reference)}>
                  <Text style={styles.sourceLink}>{source.source_name} · Open source</Text>
                </Pressable>
                {source.limitation ? <Text style={styles.note}>{source.limitation}</Text> : null}
              </View>
            ))}
            {result.limitations.map((limitation, index) => <Text key={`limitation-${index}`} style={styles.note}>• {limitation}</Text>)}
            <Text style={styles.disclaimer}>No soil-health improvement is calculated or guaranteed. A legume in the sequence is a documented crop fact, not a measured farm outcome.</Text>
          </View>
          {linkError ? <Text accessibilityRole="alert" style={styles.error}>{linkError}</Text> : null}
        </View>
      ) : null}
      <Text style={styles.footer}>Comparison does not create a season or change farm tasks. Use the existing Crop Advisor season flow when you are ready to plan a crop.</Text>
    </Card>
  );
}

const styles = StyleSheet.create({
  title: { ...TYPOGRAPHY.h3, color: COLORS.text, marginBottom: SPACING.xs },
  copy: { ...TYPOGRAPHY.body, color: COLORS.textSecondary, marginBottom: SPACING.md },
  label: { ...TYPOGRAPHY.caption, color: COLORS.text, fontWeight: '700', marginBottom: SPACING.xs },
  priorityList: { flexDirection: 'row', flexWrap: 'wrap', gap: SPACING.xs, marginBottom: SPACING.md },
  priorityChip: { borderWidth: 1, borderColor: COLORS.border, borderRadius: 18, paddingHorizontal: 12, paddingVertical: 8 },
  priorityChipSelected: { backgroundColor: COLORS.primary, borderColor: COLORS.primary },
  priorityText: { ...TYPOGRAPHY.caption, color: COLORS.text },
  priorityTextSelected: { color: COLORS.surface },
  results: { gap: SPACING.sm, marginTop: SPACING.md },
  pattern: { borderTopWidth: 1, borderTopColor: COLORS.border, paddingTop: SPACING.md, gap: SPACING.xs },
  patternTitle: { ...TYPOGRAPHY.h3, color: COLORS.primary },
  sequence: { ...TYPOGRAPHY.body, color: COLORS.text, fontWeight: '700' },
  factLine: { ...TYPOGRAPHY.caption, color: COLORS.textSecondary },
  fit: { ...TYPOGRAPHY.caption, color: COLORS.primary, fontWeight: '700' },
  note: { ...TYPOGRAPHY.caption, color: COLORS.textSecondary },
  priorityMatch: { ...TYPOGRAPHY.caption, color: COLORS.primary, fontWeight: '600' },
  sourceLink: { ...TYPOGRAPHY.caption, color: COLORS.primary, textDecorationLine: 'underline' },
  evidenceBox: { backgroundColor: '#f4f7f2', borderRadius: 10, padding: SPACING.md, gap: SPACING.xs },
  climateBox: { backgroundColor: '#eef4f7', borderRadius: 10, padding: SPACING.md, gap: SPACING.xs },
  climateHeading: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: SPACING.xs },
  cacheBadge: { ...TYPOGRAPHY.caption, color: COLORS.primary, fontWeight: '700', textTransform: 'capitalize' },
  climateMetric: { ...TYPOGRAPHY.body, color: COLORS.text, fontWeight: '700' },
  disclaimer: { ...TYPOGRAPHY.caption, color: COLORS.text, fontWeight: '600', marginTop: SPACING.xs },
  footer: { ...TYPOGRAPHY.caption, color: COLORS.textSecondary, marginTop: SPACING.md },
  notice: { ...TYPOGRAPHY.caption, color: '#8a5b00' },
  error: { ...TYPOGRAPHY.caption, color: '#b42318', marginTop: SPACING.xs },
});
