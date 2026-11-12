import { useEffect, useState } from 'react';
import { ActivityIndicator, Linking, Pressable, StyleSheet, Text, View } from 'react-native';
import { Button, Card } from '../ui';
import CalendarStepDetails from './CalendarStepDetails';
import { COLORS, SPACING, TYPOGRAPHY } from '../../theme/theme';
import { describeRotationStep, pilotObservationText, evidenceAvailabilityText } from '../../services/rotation-display';
import { loadRegionalComparison } from '../../services/rotation-comparison';
import type { RotationCompareRequest, RotationComparisonV2 } from '../../modules/shared/contracts-v2.generated';

type Props = { farmlandId: string; language: 'bn' | 'en'; refreshKey?: string };
type Priority = NonNullable<RotationCompareRequest['priorities']>[number];
const goals: { key: Priority; bn: string; en: string }[] = [
  { key: 'water', bn: 'কম সেচের পানি', en: 'Use less irrigation water' },
  { key: 'rainfall', bn: 'কম শুকনো সময় (NASA বৃষ্টি)', en: 'Fewer dry spells (NASA rainfall)' },
  { key: 'diversity', bn: 'ফসলের বৈচিত্র্য ও মাটির স্বাস্থ্য', en: 'Crop variety & soil health' },
  { key: 'calendar', bn: 'প্রকাশিত তারিখ আছে', en: 'Has published dates' },
  { key: 'income', bn: 'আয় (তথ্য এখনও নেই)', en: 'Income (no data yet)' },
];
const ORDER: Priority[] = ['water', 'diversity', 'rainfall', 'calendar'];
const BASIS_LABEL: Record<string, [string, string, (v: number) => string]> = {
  irrigated_dry_season_steps: ['dry-season irrigated crops', 'শুকনো মৌসুমে সেচের ফসল', v => v.toFixed(0)],
  dry_spell_exposure_days: ['longest typical dry spell (days)', 'দীর্ঘতম সাধারণ শুকনো সময় (দিন)', v => v.toFixed(0)],
  crop_family_count: ['plant families', 'উদ্ভিদ পরিবার', v => v.toFixed(0)],
  calendar_coverage_share: ['crops with dates', 'তারিখসহ ফসল', v => `${Math.round(v * 100)}%`],
  market_income_evidence: ['income data', 'আয়ের তথ্য', v => v.toFixed(0)],
};

export default function ComparisonPanel({ farmlandId, language, refreshKey }: Props) {
  const bn = language === 'bn';
  const [priority, setPriority] = useState<Priority>('water');
  const [year, setYear] = useState(new Date().getFullYear() + 1);
  const [data, setData] = useState<RotationComparisonV2 | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [revision, setRevision] = useState(0);
  const [details, setDetails] = useState(false);

  useEffect(() => {
    const controller = new AbortController();
    let current = true;
    void Promise.resolve().then(() => {
      if (!current) return null;
      setLoading(true);
      setData(null);
      setError('');
      return loadRegionalComparison(farmlandId, { planning_year: year, priorities: [priority, ...ORDER.filter(item => item !== priority)] }, controller.signal);
    })
      .then(value => { if (current) setData(value); })
      .catch(reason => { if (current) setError(reason instanceof Error ? reason.message : 'Could not load comparison'); })
      .finally(() => { if (current) setLoading(false); });
    return () => { current = false; controller.abort(); };
  }, [farmlandId, priority, year, revision, refreshKey]);

  return <Card>
    <View style={styles.stack}>
      <Text accessibilityRole="header" style={styles.title}>{bn ? 'পরের বছরে কী চাষ করব?' : 'What could I grow next year?'}</Text>
      <Text style={styles.body}>{bn ? 'আপনার বর্তমান ফসলের সঙ্গে BRRI-প্রকাশিত তিনটি বিকল্প তুলনা করুন। আপনার অগ্রাধিকার বদলালে ক্রমও বদলাবে; প্রতিটি মান ও উৎস নিচে দেখানো আছে।' : 'Compare your current crops with three BRRI-published options. Change your priority and the order changes; every value and source is shown below.'}</Text>
      <View style={styles.banner}><Text style={styles.bannerText}>{bn ? 'এই টুল আপনার সিদ্ধান্তে সাহায্য করে, সিদ্ধান্ত নেয় না। আপনার অভিজ্ঞতা ও উপজেলা কৃষি কর্মকর্তার পরামর্শই চূড়ান্ত।' : 'This tool supports your decision; it does not make it. Your experience and your Upazila Agriculture Officer have the final say.'}</Text></View>
      <Text style={styles.label}>{bn ? 'আপনার প্রধান অগ্রাধিকার' : 'Your main priority'}</Text>
      <View style={styles.chips} accessibilityRole="radiogroup">
        {goals.map(goal => {
          const on = priority === goal.key;
          return <Pressable key={goal.key} accessibilityRole="radio" accessibilityState={{ checked: on }} onPress={() => setPriority(goal.key)} style={[styles.chip, on && styles.chipOn]}>
            <Text style={[styles.chipText, on && styles.chipTextOn]}>{on ? '✓ ' : ''}{bn ? goal.bn : goal.en}</Text>
          </Pressable>;
        })}
      </View>
      <Text style={styles.label}>{bn ? 'পরিকল্পনার বছর' : 'Planning year'}: {year}</Text>
      <View style={styles.row}>
        <Button accessibilityRole="button" title={bn ? 'আগের বছর' : 'Previous year'} variant="outline" disabled={year <= 2001} onPress={() => setYear(v => v - 1)} />
        <Button accessibilityRole="button" title={bn ? 'পরের বছর' : 'Next year'} variant="outline" disabled={year >= 2040} onPress={() => setYear(v => v + 1)} />
      </View>
      {loading && <ActivityIndicator accessibilityLabel={bn ? 'তুলনা লোড হচ্ছে' : 'Loading comparison'} color={COLORS.primary} />}
      {!!error && <View style={styles.stack}><Text accessibilityRole="alert" style={styles.warning}>{error}</Text><Button accessibilityRole="button" title={bn ? 'আবার চেষ্টা' : 'Try again'} onPress={() => setRevision(v => v + 1)} /></View>}
      {data && data.planning_year === year && data.priorities[0] === priority && <>
        <Text accessibilityLiveRegion="polite" style={styles.body}>{bn ? data.message_bn : data.message_en}</Text>
        {data.status !== 'unsupported_region' && <View style={styles.ranking}>
          <Text style={styles.label}>{bn ? 'আপনার অগ্রাধিকার অনুযায়ী ক্রম' : 'Ordered by your priority'}</Text>
          {(data.exploration_order ?? []).map(entry => {
            const option = data.options?.find(item => item.option_id === entry.option_id);
            const basis = entry.basis?.filter(b => b.value != null).map(b => {
              const label = BASIS_LABEL[b.metric_id];
              return label ? `${bn ? label[1] : label[0]}: ${label[2](b.value as number)}` : `${b.metric_id}: ${b.value}`;
            }).join(' · ');
            return <Text key={entry.option_id} style={styles.body}>{entry.position}. {option ? (bn ? option.name_bn : option.name_en) : entry.option_id}{basis ? ` — ${basis}` : ''}</Text>;
          })}
          {(data.unranked_options ?? []).map(item => {
            const option = data.options?.find(o => o.option_id === item.option_id);
            return <Text key={item.option_id} style={styles.note}>{option ? (bn ? option.name_bn : option.name_en) : item.option_id}: {bn ? item.detail_bn : item.detail_en}</Text>;
          })}
          {!!(bn ? data.exploration_note_bn : data.exploration_note_en) && <Text style={styles.note}>{bn ? data.exploration_note_bn : data.exploration_note_en}</Text>}
        </View>}
        {data.options?.map(option => <View key={option.option_id} style={styles.option}>
          <Text style={styles.label}>{option.role === 'baseline' ? (bn ? 'বর্তমান ধারা · ' : 'Baseline · ') : (bn ? 'প্রকাশিত উদাহরণ · ' : 'Published example · ')}{bn ? option.name_bn : option.name_en}</Text>
          {option.steps.map((step, index) => <View key={`${index}-${step.crop_code}`} style={styles.stack}><Text style={styles.body}>{index + 1}. {describeRotationStep(step, language)}</Text>{details && step.calendar_evidence && <CalendarStepDetails evidence={step.calendar_evidence} language={language} stepNumber={index+1} />}</View>)}
          {option.steps.length === 0 && <Text style={styles.body}>{bn ? 'কোনো ফসলের তারিখসহ ইতিহাস নেই।' : 'No dated crop history is recorded.'}</Text>}
          <Text style={styles.body}>{option.eligibility === 'eligible' ? (bn ? 'শর্তের সঙ্গে মেলে' : 'Meets reviewed conditions') : option.eligibility === 'ineligible' ? (bn ? 'প্রকাশিত শর্ত মেলে না' : 'Outside documented conditions') : (bn ? 'আরও যাচাই প্রয়োজন' : 'More evidence needed')}</Text>
          {(bn ? option.reasons_bn : option.reasons_en)?.map((item, index) => <Text key={index} style={styles.body}>{item}</Text>)}
          <Section title={bn ? 'কেন দেখানো হচ্ছে' : 'Why this option'} items={bn ? option.why_bn : option.why_en} />
          <Section title={bn ? 'সম্ভাব্য সুবিধা' : 'Possible benefits'} items={bn ? option.benefits_bn : option.benefits_en} />
          <Section title={bn ? 'ঝুঁকি · স্থানীয় বিশেষজ্ঞের সঙ্গে যাচাই করুন' : 'Risks · check with a local expert'} items={bn ? option.risks_bn : option.risks_en} />
          <Section title={bn ? 'যে তথ্য এখনও নেই' : 'Information still missing'} items={bn ? option.gaps_bn : option.gaps_en} muted />
          {details && <Text style={styles.label}>{bn ? 'তথ্য ও প্রমাণ' : 'Evidence'}</Text>}
          {details && option.metrics?.filter(metric => metric.status !== 'missing').map(metric => <Text key={metric.metric_id} style={styles.note}>
            {metric.metric_id.match(/^step_(\d+)_/) ? `${bn ? 'ধাপ' : 'Step'} ${metric.metric_id.match(/^step_(\d+)_/)?.[1]} · ` : ''}
            {metric.value != null && metric.status !== 'missing' && metric.status !== 'not_applicable' ? `${metric.value.toFixed(1)} ${bn && metric.unit === 'days' ? 'দিন' : metric.unit ?? ''} · ` : ''}{bn ? metric.detail_bn : metric.detail_en}
            {metric.valid_year_count ? ` (${metric.valid_year_count} ${bn ? 'বছর' : 'years'})` : ''}
          </Text>)}
        </View>)}
        {details && (bn ? data.limitations_bn : data.limitations_en)?.map((item, index) => <Text key={index} style={styles.note}>{item}</Text>)}
        {details && data.pilot_observation && <View style={styles.option}>
          <Text style={styles.label}>{bn ? 'IMERG নামে দেওয়া file · এক দিনের পরীক্ষামূলক তথ্য' : 'User-supplied IMERG-labeled file · one-day prototype'}</Text>
          <Text style={styles.body}>{pilotObservationText(data.pilot_observation, language)}</Text>
          <Text style={styles.note}>{bn ? 'তোমার দেওয়া file-এর উৎস স্বাধীনভাবে যাচাই হয়নি। অঞ্চলটি পরীক্ষার আয়তক্ষেত্র, জেলার গড় নয়। তথ্যের পর্যালোচনা বাকি; রোপণের সিদ্ধান্তে ব্যবহার হয়নি।' : 'The user-supplied file origin is not independently verified. This pilot rectangle is not a district average. Data review is pending; it is not used for a planting decision.'}</Text>
          <Text style={styles.note}>{bn ? 'মূল satellite grid' : 'Native satellite grid'}: {data.pilot_observation.native_support} · {data.pilot_observation.source}</Text>
          {data.pilot_observation.terrain && <View style={styles.stack}>
            <Text style={styles.label}>{bn ? 'SRTM · মাঠের অবস্থানের কাছের উচ্চতা নমুনা' : 'SRTM · elevation sample near the field location'}</Text>
            <Text style={styles.body}>{data.pilot_observation.terrain.elevation_m?.toFixed(0)} {bn ? 'মিটার' : 'm'} · {data.pilot_observation.terrain.latitude.toFixed(4)}, {data.pilot_observation.terrain.longitude.toFixed(4)}</Text>
            <Text style={styles.note}>{bn ? '২০০০ সালের প্রদত্ত SRTM tile থেকে profile-এর অবস্থানের সবচেয়ে কাছের ১-arc-second grid node। file-এর উৎস এবং বিন্দুটি স্থল না জল তা যাচাই হয়নি। এটি পুরো জমির survey, বন্যার পূর্বাভাস বা rotation score নয়।' : 'Nearest 1-arc-second grid node to the profile location from a user-supplied February 2000 SRTM tile. File origin and land/water status are unverified. This is not a field survey, flood forecast, or rotation score.'}</Text>
          </View>}
        </View>}
        {data.status !== 'unsupported_region' && <>
          <Button accessibilityRole="button" title={details ? (bn ? 'বিস্তারিত তথ্য বন্ধ করুন' : 'Hide details') : (bn ? 'NASA, ক্যালেন্ডার ও উৎসের বিস্তারিত দেখুন' : 'Show NASA, calendar and source details')} variant="outline" accessibilityState={{ expanded: details }} onPress={() => setDetails(v => !v)} />
          {details && <View style={styles.stack}>
            {data.evidence?.map(e => <View key={e.evidence_id} style={styles.option}>
              <Text style={styles.label}>{e.source}</Text>
              <Text style={styles.note}>{e.coverage_start} {e.coverage_end ? `— ${e.coverage_end}` : ''}</Text>
              <Text style={styles.note}>{e.spatial_support}</Text>
              <Text style={styles.note}>{bn ? 'তথ্যের অবস্থা' : 'Evidence availability'}: {evidenceAvailabilityText(e.cache_status, language)} · {e.scope}</Text>
              <Button accessibilityRole="button" title={bn ? 'মূল উৎস খুলুন' : 'Open source'} variant="outline" onPress={() => { void Linking.openURL(e.url).catch(() => setError(bn ? 'উৎস খোলা যায়নি।' : 'Could not open source.')); }} />
            </View>)}
            {data.products?.map(p => <Text key={p.product_id} style={styles.note}>{p.product_id}: {p.state === 'not_acquired' ? (bn ? 'এখনও তুলনায় যুক্ত নয়' : 'Not yet incorporated') : p.state === 'pilot_unreviewed' ? (bn ? 'পর্যালোচনাধীন এক দিনের নমুনা' : 'One-day sample pending review') : p.state} · {p.role}</Text>)}
          </View>}
          <Text style={styles.note}>{bn ? 'পরবর্তী ধাপ: আগের ফসলের তারিখ নিশ্চিত করুন এবং স্থানীয় ক্যালেন্ডার যাচাই করুন। এই তুলনা থেকে মৌসুম তৈরি হয় না।' : 'Next: confirm your previous crop dates and check local calendars. This comparison does not create a season.'}</Text>
        </>}
      </>}
    </View>
  </Card>;
}

function Section({ title, items, muted }: { title: string; items?: string[]; muted?: boolean }) {
  if (!items?.length) return null;
  return <View style={styles.section}>
    <Text style={styles.label}>{title}</Text>
    {items.map((item, index) => <Text key={index} style={muted ? styles.note : styles.body}>• {item}</Text>)}
  </View>;
}

const styles = StyleSheet.create({
  stack: { gap: SPACING.md }, row: { flexDirection: 'row', flexWrap: 'wrap', gap: SPACING.sm },
  title: { ...TYPOGRAPHY.h3 }, label: { ...TYPOGRAPHY.body, fontWeight: '600' },
  body: { ...TYPOGRAPHY.body, lineHeight: 25 }, note: { ...TYPOGRAPHY.bodySecondary, fontSize: 14, lineHeight: 22 },
  warning: { ...TYPOGRAPHY.body, color: COLORS.error },
  section: { gap: SPACING.xs },
  chips: { flexDirection: 'row', flexWrap: 'wrap', gap: SPACING.sm },
  chip: { paddingVertical: 9, paddingHorizontal: 14, borderRadius: 999, borderWidth: 1.5, borderColor: COLORS.primary, backgroundColor: '#ffffff' },
  chipOn: { backgroundColor: COLORS.primary },
  chipText: { ...TYPOGRAPHY.body, fontSize: 15, color: COLORS.primary, fontWeight: '600' },
  chipTextOn: { color: '#ffffff' },
  banner: { backgroundColor: '#e8f3ec', borderRadius: 10, padding: SPACING.md },
  bannerText: { ...TYPOGRAPHY.body, fontWeight: '600', lineHeight: 24 },
  ranking: { gap: SPACING.sm, padding: SPACING.md, borderRadius: 10, borderWidth: 1, borderColor: COLORS.border },
  option: { paddingTop: SPACING.md, borderTopWidth: 1, borderTopColor: COLORS.border, gap: SPACING.sm },
});
