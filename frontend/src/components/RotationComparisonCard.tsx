import {
  ActivityIndicator,
  Linking,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { Button, Card } from './ui';
import type { RotationComparison } from '../services/m2-advisor';
import { COLORS, SPACING, TYPOGRAPHY } from '../theme/theme';
import ClimateEvidenceCharts from './ClimateEvidenceCharts';

type Props = {
  comparison: RotationComparison | null;
  loading: boolean;
  error: string;
  language: 'bn' | 'en';
  onRetry: () => void;
};

export default function RotationComparisonCard({
  comparison,
  loading,
  error,
  language,
  onRetry,
}: Props) {
  const bn = language === 'bn';
  const currentSequence = comparison?.current_sequence ?? [];
  const strategies = comparison?.strategies ?? [];
  const evidence = comparison?.evidence ?? [];
  const unknowns = bn ? comparison?.unknowns_bn ?? [] : comparison?.unknowns_en ?? [];
  const scopeNotes = bn ? comparison?.scope_notes_bn ?? [] : comparison?.scope_notes_en ?? [];
  const notAssessed = bn ? comparison?.not_assessed_bn ?? [] : comparison?.not_assessed_en ?? [];
  const status = comparison?.status ?? 'insufficient_evidence';
  const displayCrop = (crop: string) => {
    const normalized = crop.trim().toLocaleLowerCase('en-US').replace(/[\s-]+/g, '_');
    const labels: Record<string, { en: string; bn: string }> = {
      rice: { en: 'Rice', bn: 'ধান' },
      chickpea: { en: 'Chickpea', bn: 'ছোলা' },
      sesbania_rostrata: { en: 'Sesbania rostrata (green manure)', bn: 'ধৈঞ্চা (সবুজ সার)' },
      mustard: { en: 'Mustard', bn: 'সরিষা' },
      lentil: { en: 'Lentil', bn: 'মসুর' },
      wheat: { en: 'Wheat', bn: 'গম' },
      maize: { en: 'Maize', bn: 'ভুট্টা' },
      potato: { en: 'Potato', bn: 'আলু' },
    };
    return labels[normalized]?.[bn ? 'bn' : 'en'] ?? crop;
  };

  return (
    <Card>
      <Text style={styles.title}>{bn ? 'ফসলের ধারা তুলনা' : 'Compare crop sequences'}</Text>
      <Text style={styles.helper}>
        {bn
          ? 'আপনার নথিভুক্ত ফসলের সঙ্গে BRRI-তে প্রকাশিত মিল থাকা উদাহরণ দেখুন। এটি সেরা ফসল বেছে দেয় না।'
          : 'See documented BRRI examples beside your recorded crops. This does not choose a best rotation.'}
      </Text>

      {loading ? (
        <View style={styles.loading}>
          <ActivityIndicator accessibilityLabel={bn ? 'ফসলের ধারা তুলনা হচ্ছে' : 'Loading crop sequence comparison'} color={COLORS.primary} />
          <Text style={styles.helper}>{bn ? 'প্রকাশিত উদাহরণ যাচাই হচ্ছে…' : 'Checking documented examples…'}</Text>
        </View>
      ) : null}

      {!loading && error ? (
        <View>
          <Text accessibilityRole="alert" style={styles.warning}>{error}</Text>
          <Button
            accessibilityRole="button"
            title={bn ? 'আবার চেষ্টা করুন' : 'Try again'}
            variant="outline"
            onPress={onRetry}
          />
        </View>
      ) : null}

      {!loading && !error && comparison ? (
        <View style={styles.content}>
          <Text style={status === 'available' ? styles.status : styles.warning}>
            {(bn ? comparison.message_bn : comparison.message_en) ?? ''}
          </Text>

          <View style={styles.sequenceBlock}>
            <Text style={styles.label}>{bn ? 'আপনার নথিভুক্ত ফসল' : 'Your recorded crops'}</Text>
            {currentSequence.length > 0 ? (
              <Text style={styles.body}>{currentSequence.map(displayCrop).join(' → ')}</Text>
            ) : (
              <Text style={styles.helper}>{bn ? 'এখনও কোনো মৌসুম নথিভুক্ত নেই।' : 'No crop season is recorded yet.'}</Text>
            )}
            {comparison.farmer_reported_previous_crop ? (
              <Text style={styles.helper}>
                {bn ? 'প্রোফাইলে আগের ফসল:' : 'Previous crop reported in profile:'} {comparison.farmer_reported_previous_crop}
                {bn ? ' · এর তারিখ নথিভুক্ত নয়' : ' · date not recorded'}
              </Text>
            ) : null}
            <Text style={styles.helper}>
              {comparison.current_sequence_basis === 'active_and_completed_seasons'
                ? (bn ? 'সম্পন্ন মৌসুম ও চলমান মৌসুম থেকে' : 'From completed seasons and the active season')
                : comparison.current_sequence_basis === 'completed_seasons_only'
                  ? (bn ? 'শুধু সম্পন্ন মৌসুম থেকে' : 'From completed seasons only')
                  : comparison.current_sequence_basis === 'active_season_only'
                    ? (bn ? 'চলমান মৌসুম থেকে' : 'From the active season only')
                    : (bn ? 'নথিভুক্ত মৌসুম থেকে নয়' : 'No recorded-season baseline')}
            </Text>
            {comparison.active_season?.planting_date ? <Text style={styles.helper}>{bn ? 'চলমান ফসলের নথিভুক্ত শুরুর তারিখ' : 'Recorded start of active crop'}: {comparison.active_season.planting_date}</Text> : null}
            {(comparison.recorded_history ?? []).map(item => <Text key={item.season_id} style={styles.helper}>{displayCrop(item.crop_code)} · {item.planting_date ?? '—'} → {item.harvest_date ?? '—'} ({bn ? 'সম্পন্ন মৌসুম' : 'completed season'})</Text>)}
          </View>

          {unknowns.map((item, index) => (
            <Text key={`rotation-unknown-${index}`} style={styles.warning}>{item}</Text>
          ))}
          {scopeNotes.map((item, index) => (
            <Text key={`rotation-scope-${index}`} style={styles.warning}>{item}</Text>
          ))}

          {strategies.map((strategy, strategyIndex) => (
            <View key={strategy.strategy_id} style={styles.strategy}>
              <Text style={styles.strategyTitle}>
                {bn ? 'প্রকাশিত উদাহরণ' : 'Published example'} {strategyIndex + 1}: {bn ? strategy.name_bn : strategy.name_en}
              </Text>
              <Text style={styles.scope}>
                {bn ? 'BRRI-র বর্ণিত জমির শর্ত:' : 'BRRI stated scope:'} {bn ? strategy.documented_scope_bn : strategy.documented_scope_en}
              </Text>
              {strategy.steps.map((step, stepIndex) => (
                <View key={`${strategy.strategy_id}-${stepIndex}`} style={styles.step}>
                  <Text style={styles.stepNumber}>{stepIndex + 1}</Text>
                  <View style={styles.stepCopy}>
                    <Text style={styles.body}>
                      {bn ? step.season_label_bn : step.season_label_en}: {bn ? step.crop_name_bn : step.crop_name_en}
                    </Text>
                    {step.practice_note_en ? (
                      <Text style={styles.helper}>
                        {bn ? step.practice_note_bn ?? step.practice_note_en : step.practice_note_en}
                      </Text>
                    ) : null}
                      {step.calendar_evidence ? <View>
                        <Text style={styles.helper}>{bn ? 'ক্যালেন্ডারের অবস্থা' : 'Calendar support'}: {step.calendar_evidence.status === 'source_reference_available' ? (bn ? 'প্রকাশিত তথ্য আছে; review বাকি' : 'source reference; review pending') : step.calendar_evidence.status === 'cultivation_method_mismatch' ? (bn ? 'চাষের পদ্ধতি মেলে না' : 'establishment method mismatch') : (bn ? 'মিল থাকা ক্যালেন্ডার নেই' : 'matching calendar unavailable')}</Text>
                        {(step.calendar_evidence.references ?? []).map(reference => <Text key={reference.profile_id} style={styles.helper}>{bn ? reference.variety_name_bn ?? reference.variety_name : reference.variety_name}: {reference.transplanting_window.start} – {reference.transplanting_window.end} · {reference.source_url}</Text>)}
                        {(bn ? step.calendar_evidence.gaps_bn ?? [] : step.calendar_evidence.gaps_en ?? []).map((gap, index) => <Text key={index} style={styles.helper}>{gap}</Text>)}
                      </View> : null}
                  </View>
                </View>
              ))}
              {(strategy.tradeoffs ?? []).map((tradeoff, tradeoffIndex) => (
                <View key={`${strategy.strategy_id}-tradeoff-${tradeoffIndex}`} style={styles.tradeoff}>
                  <Text style={styles.label}>{bn ? tradeoff.label_bn : tradeoff.label_en}</Text>
                  <Text style={styles.helper}>{bn ? tradeoff.detail_bn : tradeoff.detail_en}</Text>
                </View>
              ))}
              <Text style={styles.warning}>{bn ? 'সব ধাপের reviewed ক্যালেন্ডার নেই; তাই তারিখের মিল, পূর্ণ rotation feasibility বা ranking হিসাব করা হয়নি।' : 'Reviewed calendars are incomplete; date compatibility, full rotation feasibility and ranking have not been calculated.'}</Text>
            </View>
          ))}

          {comparison.climate_evidence ? <View>
            <Text style={styles.label}>{bn ? 'জেলার NASA ইতিহাস—প্রেক্ষাপট' : 'District NASA history — context'}</Text>
            <ClimateEvidenceCharts comparison={comparison.climate_evidence.annual_comparison} language={language} />
            <Text style={styles.helper}>{comparison.climate_evidence.data_provenance.temporal_start} – {comparison.climate_evidence.data_provenance.temporal_end} · {bn ? 'ক্যাশের তথ্য' : 'cached evidence'}</Text>
            {(bn ? comparison.climate_evidence.limitations_bn : comparison.climate_evidence.limitations_en).map((item, index) => <Text key={index} style={styles.helper}>{item}</Text>)}
          </View> : null}

          <View style={styles.limitBlock}>
            <Text style={styles.label}>{bn ? 'এখানে যা যাচাই করা হয়নি' : 'What this comparison does not assess'}</Text>
            {notAssessed.map((item, index) => (
              <Text key={`rotation-limit-${index}`} style={styles.helper}>• {item}</Text>
            ))}
          </View>

          {evidence.map((source, index) => (
            <View key={`${source.source_id}-${index}`}>
              <Text style={styles.label}>{bn ? 'তথ্যসূত্র' : 'Source'}</Text>
              <Text style={styles.helper}>{source.source_name}{source.dataset_version ? ` · ${source.dataset_version}` : ''}</Text>
              {source.source_url ? (
                <Text
                  accessibilityRole="link"
                  accessibilityLabel={bn ? 'BRRI তথ্যসূত্র খুলুন' : 'Open BRRI source'}
                  selectable
                  style={styles.source}
                  onPress={() => {
                    if (source.source_url) void Linking.openURL(source.source_url).catch(() => undefined);
                  }}
                >
                  {source.source_url}
                </Text>
              ) : null}
              <Text style={styles.helper}>
                {bn ? 'তথ্যের অবস্থা:' : 'Evidence status:'} {source.quality_status ?? (bn ? 'অজানা' : 'unknown')} · {source.retrieved_at}
              </Text>
            </View>
          ))}

          <Text style={styles.footer}>
            {bn
              ? 'এটি শুধু তুলনার জন্য। আপনার ফসলের পরিকল্পনা বা মৌসুম পরিবর্তন হয়নি।'
              : 'Comparison only. Your crop plan and active season have not changed.'}
          </Text>
          <Button
            accessibilityRole="button"
            title={bn ? 'তুলনা হালনাগাদ করুন' : 'Refresh comparison'}
            variant="outline"
            onPress={onRetry}
          />
        </View>
      ) : null}
    </Card>
  );
}

const styles = StyleSheet.create({
  title: { ...TYPOGRAPHY.h3, marginBottom: SPACING.xs },
  helper: { ...TYPOGRAPHY.caption, color: COLORS.textSecondary, lineHeight: 20, marginBottom: SPACING.xs },
  loading: { flexDirection: 'row', alignItems: 'center', gap: SPACING.sm, paddingVertical: SPACING.sm },
  content: { gap: SPACING.sm },
  status: { ...TYPOGRAPHY.body, color: COLORS.primaryDark, fontWeight: '600', paddingVertical: SPACING.xs },
  warning: { ...TYPOGRAPHY.body, color: '#8a4b07', backgroundColor: '#fff8ea', padding: SPACING.sm, borderRadius: 8, marginVertical: SPACING.xs },
  sequenceBlock: { paddingVertical: SPACING.sm, borderBottomWidth: 1, borderBottomColor: COLORS.border },
  label: { ...TYPOGRAPHY.caption, color: COLORS.text, fontWeight: '700', marginBottom: 3 },
  body: { ...TYPOGRAPHY.body, color: COLORS.text, lineHeight: 23 },
  strategy: { borderWidth: 1, borderColor: COLORS.border, borderRadius: 12, backgroundColor: COLORS.surface, padding: SPACING.md, gap: SPACING.xs },
  strategyTitle: { ...TYPOGRAPHY.body, color: COLORS.text, fontWeight: '700', lineHeight: 23 },
  scope: { ...TYPOGRAPHY.caption, color: COLORS.textSecondary, lineHeight: 19 },
  step: { flexDirection: 'row', alignItems: 'flex-start', gap: SPACING.sm, paddingVertical: SPACING.xs },
  stepNumber: { minWidth: 28, height: 28, borderRadius: 14, overflow: 'hidden', textAlign: 'center', textAlignVertical: 'center', backgroundColor: '#e7f0e8', color: COLORS.primaryDark, fontWeight: '700' },
  stepCopy: { flex: 1, minWidth: 0 },
  tradeoff: { borderTopWidth: 1, borderTopColor: COLORS.border, paddingTop: SPACING.xs },
  limitBlock: { backgroundColor: '#f4f5f1', borderRadius: 10, padding: SPACING.sm },
  source: { ...TYPOGRAPHY.caption, color: COLORS.primary, textDecorationLine: 'underline', lineHeight: 18, marginBottom: SPACING.xs },
  footer: { ...TYPOGRAPHY.caption, color: COLORS.text, fontWeight: '600', lineHeight: 19 },
});
