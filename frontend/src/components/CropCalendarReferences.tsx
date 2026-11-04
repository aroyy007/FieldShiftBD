import { useEffect, useState } from 'react';
import { ActivityIndicator, Pressable, StyleSheet, Text, View } from 'react-native';
import { Card, Button } from './ui';
import { m2Request, VarietyCalendarReference } from '../services/m2-advisor';
import { COLORS, SPACING, TYPOGRAPHY } from '../theme/theme';

type Language = 'bn' | 'en';
const seasonNames: Record<string, string> = { Aman: 'আমন', Boro: 'বোরো', Aus: 'আউশ' };

function monthDay(value: string, language: Language) {
  const [month, day] = value.split('-').map(Number);
  return new Intl.DateTimeFormat(language === 'bn' ? 'bn-BD' : 'en-BD', {
    day: 'numeric', month: 'short', timeZone: 'UTC',
  }).format(new Date(Date.UTC(2000, month - 1, day)));
}

export function PublishedCalendarDetails({ reference, language }: { reference: VarietyCalendarReference; language: Language }) {
  const bn = language === 'bn';
  const dates = (window: { start: string; end: string }) => `${monthDay(window.start, language)} – ${monthDay(window.end, language)}`;
  return (
    <View style={styles.details}>
      <Text style={styles.heading}>{bn ? reference.variety_name_bn ?? reference.variety_name : reference.variety_name} · {bn ? seasonNames[reference.season] ?? reference.season : reference.season}</Text>
      <Text style={styles.warning}>{bn ? 'প্রকাশিত তথ্য যাচাই করা হয়েছে; কৃষিবিদের পর্যালোচনা বাকি।' : 'Published source checked; agronomic review pending.'}</Text>
      {reference.seedbed_window ? <Text style={styles.body}>{bn ? 'বীজতলায় বপন' : 'Seedbed sowing'}: {dates(reference.seedbed_window)}</Text> : null}
      {reference.seedling_age_days ? <Text style={styles.body}>{bn ? 'চারার বয়স' : 'Seedling age'}: {reference.seedling_age_days.min}–{reference.seedling_age_days.max} {bn ? 'দিন' : 'days'}</Text> : null}
      <Text style={styles.body}>{bn ? 'চারা রোপণ' : 'Transplanting'}: {dates(reference.transplanting_window)}</Text>
      <Text style={styles.body}>{bn ? 'প্রকাশিত ফসল কাটার সময়' : 'Published harvest period'}: {dates(reference.harvest_window)}</Text>
      <Text style={styles.helper}>{bn ? `প্রকাশিত জীবনকাল ${reference.reported_life_duration_days} দিন। এই দিন গণনার শুরুর ধাপ উৎসে স্পষ্ট নয়; রোপণের তারিখের সঙ্গে যোগ করে কাটার দিন নির্ধারণ করবেন না।` : `Reported life duration: ${reference.reported_life_duration_days} days. Its starting event is unspecified; do not add it to a transplanting date to predict harvest.`}</Text>
      <Text style={styles.helper}>{bn ? reference.geographic_scope_bn : reference.geographic_scope_en}</Text>
      <Text style={styles.label}>{bn ? 'পরিচর্যার প্রকাশিত তথ্য' : 'Published care references'}</Text>
      {(reference.care_references ?? []).map((care, index) => (
        <View key={`${care.kind}-${index}`} style={styles.care}>
          <Text style={styles.body}>{bn ? care.detail_bn ?? care.detail_en : care.detail_en}</Text>
          {care.day_range ? <Text style={styles.helper}>{bn ? 'রোপণের পর' : 'After transplanting'}: {care.day_range.min}–{care.day_range.max} {bn ? 'দিন' : 'days'}</Text> : null}
          <Text style={styles.helper}>{bn ? care.condition_bn ?? care.condition_en : care.condition_en}</Text>
        </View>
      ))}
      <Text style={styles.warning}>{bn ? 'এই জাতের যাচাইকৃত GDD মান ও সম্পূর্ণ বৃদ্ধির ধাপের সময়সূচি নেই। তাই এই তথ্য থেকে স্বয়ংক্রিয় সেচ, কাজ বা কাটার তারিখ নির্ধারণ করা হয়নি।' : 'Validated cultivar GDD parameters and a complete stage timeline are unavailable. These references do not schedule irrigation, tasks or harvest.'}</Text>
      <Text selectable style={styles.helper}>{reference.source_name} · {reference.source_accessed}{'\n'}{reference.source_url}</Text>
      {(bn ? reference.limitations_bn ?? [] : reference.limitations_en ?? []).map((item, index) => <Text key={index} style={styles.helper}>{item}</Text>)}
    </View>
  );
}

export default function CropCalendarReferences({ language, season }: { language: Language; season?: string }) {
  const [references, setReferences] = useState<VarietyCalendarReference[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [failed, setFailed] = useState(false);
  const [reload, setReload] = useState(0);
  const bn = language === 'bn';
  useEffect(() => {
    let current = true;
    void Promise.resolve().then(() => {
      if (current) { setLoading(true); setFailed(false); }
      return m2Request<VarietyCalendarReference[]>(`/advisor/calendar-references?crop=rice${season ? `&season=${encodeURIComponent(season)}` : ''}`);
    })
      .then(value => { if (current) { setReferences(value); setFailed(false); } })
      .catch(() => { if (current) setFailed(true); })
      .finally(() => { if (current) setLoading(false); });
    return () => { current = false; };
  }, [reload, season]);
  const visibleReferences = season ? references.filter(item => item.season.toLowerCase() === season.toLowerCase()) : references;
  const selected = visibleReferences.find(item => item.profile_id === selectedId) ?? visibleReferences[0];
  return (
    <Card>
      <Text style={styles.heading}>{bn ? 'ধানের জাতের প্রকাশিত ক্যালেন্ডার' : 'Published rice variety calendars'}</Text>
      <Text style={styles.helper}>{bn ? 'জাতভেদে বপন, রোপণ ও পরিচর্যার তথ্য দেখুন। জাত বেছে দেখলে আপনার মৌসুম বদলাবে না।' : 'Explore variety-specific sowing, transplanting and care references. Browsing does not select a crop or change your season.'}</Text>
      {loading ? <ActivityIndicator accessibilityLabel={bn ? 'ক্যালেন্ডার লোড হচ্ছে' : 'Loading calendars'} color={COLORS.primary} /> : null}
      {failed ? <><Text accessibilityRole="alert" style={styles.warning}>{bn ? 'ক্যালেন্ডার লোড হয়নি। আবার চেষ্টা করুন।' : 'Could not load calendars. Try again.'}</Text><Button accessibilityRole="button" title={bn ? 'আবার চেষ্টা করুন' : 'Try again'} variant="outline" onPress={() => { setLoading(true); setReload(value => value + 1); }} /></> : null}
      <View style={styles.options}>
        {visibleReferences.map(item => <Pressable key={item.profile_id ?? `${item.season}-${item.variety_name}`} accessibilityRole="button" accessibilityState={{ selected: item.profile_id === selected?.profile_id }} onPress={() => setSelectedId(item.profile_id ?? null)} style={[styles.option, item.profile_id === selected?.profile_id && styles.selected]}><Text style={styles.body}>{bn ? item.variety_name_bn ?? item.variety_name : item.variety_name} · {bn ? seasonNames[item.season] ?? item.season : item.season}</Text></Pressable>)}
      </View>
      {selected && !failed ? <PublishedCalendarDetails reference={selected} language={language} /> : null}
    </Card>
  );
}

const styles = StyleSheet.create({
  heading: { ...TYPOGRAPHY.h3, marginBottom: SPACING.sm },
  body: { ...TYPOGRAPHY.body, lineHeight: 24 },
  helper: { ...TYPOGRAPHY.caption, color: COLORS.textSecondary, lineHeight: 20 },
  label: { ...TYPOGRAPHY.body, fontWeight: '600', marginTop: SPACING.sm },
  details: { gap: SPACING.sm, paddingTop: SPACING.sm },
  warning: { ...TYPOGRAPHY.body, color: '#79460b', backgroundColor: '#fff8ea', padding: SPACING.sm, borderRadius: 8, lineHeight: 24 },
  care: { borderLeftWidth: 3, borderLeftColor: COLORS.border, paddingLeft: SPACING.sm, gap: SPACING.xs },
  options: { gap: SPACING.sm, paddingVertical: SPACING.sm },
  option: { minHeight: 56, justifyContent: 'center', padding: SPACING.sm, borderWidth: 1, borderColor: COLORS.border, borderRadius: 8 },
  selected: { borderColor: COLORS.primary, backgroundColor: '#edf5ec' },
});
