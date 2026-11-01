import { useEffect, useState } from 'react';
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { Button, Card } from '../components/ui';
import OptionPickerModal from '../components/OptionPickerModal';
import ClimateEvidenceCharts from '../components/ClimateEvidenceCharts';
import CropCalendarReferences from '../components/CropCalendarReferences';
import { loadLocations, DistrictRef } from '../services/m1-reference';
import { loadPublicAdvisory, loadDistrictCacheInventory, PublicAdvisory } from '../services/climate-advisory';
import { buildDistrictOptions, cacheStatusLabel } from '../services/climate-inventory';
import type { DistrictCacheInventory } from '../modules/shared/contracts.generated';
import { COLORS, SPACING, TYPOGRAPHY } from '../theme/theme';

export default function PublicAdvisoryScreen() {
  const params = useLocalSearchParams<{ district?: string; language?: string }>();
  const router = useRouter();
  const [language, setLanguage] = useState<'bn' | 'en'>('bn');
  const [districts, setDistricts] = useState<DistrictRef[]>([]);
  const [district, setDistrict] = useState('');
  const [season, setSeason] = useState('aman');
  const [pickerOpen, setPickerOpen] = useState(false);
  const [referenceFailed, setReferenceFailed] = useState(false);
  const [inventory, setInventory] = useState<DistrictCacheInventory | null>(null);
  const [inventoryFailed, setInventoryFailed] = useState(false);
  const [result, setResult] = useState<PublicAdvisory | null>(null);
  const [loading, setLoading] = useState(false);
  const [failed, setFailed] = useState(false);
  const [reload, setReload] = useState(0);
  const bn = language === 'bn';
  const routeDistrict = Array.isArray(params.district) ? params.district[0] : params.district;
  const routeLanguage = Array.isArray(params.language) ? params.language[0] : params.language;
  useEffect(() => {
    let current = true;
    void Promise.resolve().then(() => {
      if (!current) return;
      if (routeDistrict) setDistrict(routeDistrict);
      if (routeLanguage === 'bn' || routeLanguage === 'en') setLanguage(routeLanguage);
    });
    return () => { current = false; };
  }, [routeDistrict, routeLanguage]);
  useEffect(() => {
    let current = true;
    void loadLocations().then(value => { if (current) { setDistricts(value.flatMap(item => item.districts)); setReferenceFailed(false); } })
      .catch(() => { if (current) setReferenceFailed(true); });
    return () => { current = false; };
  }, [reload]);
  useEffect(() => {
    let current = true;
    void loadDistrictCacheInventory()
      .then(value => { if (current) { setInventory(value); setInventoryFailed(false); } })
      .catch(() => { if (current) { setInventory(null); setInventoryFailed(true); } });
    return () => { current = false; };
  }, [reload]);
  useEffect(() => {
    if (!district) return;
    let current = true;
    void Promise.resolve().then(() => {
      if (current) { setLoading(true); setFailed(false); setResult(null); }
      return loadPublicAdvisory(district, season);
    }).then(value => { if (current) setResult(value); })
      .catch(() => { if (current) setFailed(true); })
      .finally(() => { if (current) setLoading(false); });
    return () => { current = false; };
  }, [district, season, reload]);
  const selected = districts.find(item => item.code === district || item.name === district);
  const seasons = [{ code: 'aman', bn: 'আমন', en: 'Aman' }, { code: 'aus', bn: 'আউশ', en: 'Aus' }, { code: 'boro', bn: 'বোরো', en: 'Boro' }];
  const provenance = result?.data_provenance;
  const selectedCacheStatus = inventory?.districts.find(item => item.district_code === selected?.code)?.status;
  return (
    <SafeAreaView style={styles.page}>
      <ScrollView contentContainerStyle={styles.content}>
        <View style={styles.header}>
          <Button accessibilityRole="button" title={bn ? 'ফিরে যান' : 'Back'} variant="outline" onPress={() => router.canGoBack() ? router.back() : router.replace('/')} />
          <Button accessibilityRole="button" title={bn ? 'English' : 'বাংলা'} variant="outline" onPress={() => setLanguage(bn ? 'en' : 'bn')} />
        </View>
        <Text style={styles.title}>{bn ? 'আপনার এলাকার বৃষ্টির ইতিহাস ও ধানের ক্যালেন্ডার' : 'Your area’s rainfall history and rice calendars'}</Text>
        <Text style={styles.body}>{bn ? 'জেলা ও মৌসুম বেছে তুলনা দেখুন। এই অংশে কোনো ব্যক্তিগত খামারের তথ্য ব্যবহার করা হয় না।' : 'Choose a district and season to explore the evidence. This view uses no private farm records.'}</Text>
        <Card>
          <Text style={styles.label}>{bn ? 'ফসল: ধান' : 'Crop: Rice'}</Text>
          <Pressable accessibilityRole="button" onPress={() => setPickerOpen(true)} style={styles.option}>
            <Text style={styles.body}>{selected ? (bn ? selected.name_bn : selected.name) : district || (bn ? 'জেলা বেছে নিন' : 'Choose district')}</Text>
          </Pressable>
          {referenceFailed ? <Text accessibilityRole="alert" style={styles.warning}>{bn ? 'জেলার তালিকা লোড হয়নি। নিচের বোতামে আবার চেষ্টা করুন।' : 'Could not load district names. Retry below.'}</Text> : null}
          <View style={styles.seasons}>{seasons.map(item => <Pressable key={item.code} accessibilityRole="button" accessibilityState={{ selected: season === item.code }} onPress={() => setSeason(item.code)} style={[styles.season, season === item.code && styles.selected]}><Text style={styles.body}>{bn ? item.bn : item.en}</Text></Pressable>)}</View>
          {inventory ? <Text style={styles.helper}>{bn
            ? `${inventory.districts.length}টি জেলার মধ্যে ${inventory.cached_count}টির সংরক্ষিত তথ্য আছে। খোলার সময় তথ্য যাচাই করা হবে।`
            : `Saved data is present for ${inventory.cached_count} of ${inventory.districts.length} districts. Data is validated when opened.`}</Text> : null}
          {inventoryFailed ? <Text style={styles.helper}>{bn ? 'কোন জেলার তথ্য আছে তা যাচাই করা যায়নি। জেলা বেছে চেষ্টা করুন।' : 'Could not check which districts have saved data. Choose a district to try.'}</Text> : null}
          {selected && inventory ? <Text style={styles.helper}>{cacheStatusLabel(selectedCacheStatus, language)}. {bn ? 'যেকোনো জেলার জন্য নিচে প্রকাশিত জাতের ক্যালেন্ডার দেখতে পারবেন।' : 'Published variety calendars remain available below for any district.'}</Text> : null}
          <Text style={styles.helper}>{bn ? 'জেলার তালিকা ও জলবায়ু ক্যাশের কভারেজ আলাদা; প্রতিটি জেলার ডেটা এখনও প্রস্তুত নয়।' : 'District selection and climate-cache coverage differ; data is not yet prepared for every district.'}</Text>
          {district || referenceFailed ? <Button accessibilityRole="button" title={bn ? 'আবার যাচাই করুন' : 'Refresh evidence'} variant="outline" disabled={loading} onPress={() => setReload(value => value + 1)} /> : null}
        </Card>
        {loading ? <ActivityIndicator color={COLORS.primary} accessibilityLabel={bn ? 'ক্যাশের তথ্য যাচাই হচ্ছে' : 'Checking cached evidence'} /> : null}
        {failed ? <Card><Text accessibilityRole="alert" style={styles.warning}>{bn ? 'এই জেলার জলবায়ু ক্যাশ এখন পাওয়া যায়নি। নিচে প্রকাশিত জাতের ক্যালেন্ডার দেখা যাবে।' : 'District climate cache is unavailable. Published variety calendars are available below.'}</Text></Card> : null}
        {result ? <Card>
          <Text style={styles.body}>{bn ? result.message_bn : result.message_en}</Text>
          <Text style={styles.warning}>{bn ? 'পরীক্ষামূলক তুলনা: কৃষিবিদের পর্যালোচনা বাকি। রোপণের তারিখ বদলের সুপারিশ দেওয়া হয়নি।' : 'Exploratory comparison: agronomic review is pending. A planting-date adjustment has not been recommended.'}</Text>
          <ClimateEvidenceCharts comparison={result.annual_comparison} gdd={result.gdd_summary} language={language} />
          {result.annual_comparison ? <Text style={styles.body}>{bn ? 'বৃষ্টির মধ্যম শুরুর পর্যবেক্ষিত পার্থক্য' : 'Observed median rainfall-onset difference'}: {result.annual_comparison.observed_shift_days ?? '—'} {bn ? 'দিন' : 'days'}</Text> : null}
          {(bn ? result.limitations_bn : result.limitations_en).map((item, index) => <Text key={index} style={styles.helper}>{item}</Text>)}
          {provenance ? <View style={styles.sources}>
            <Text style={styles.label}>{bn ? 'উৎস ও কভারেজ' : 'Source and coverage'}</Text>
            <Text style={styles.helper}>{provenance.source} · {provenance.temporal_start} – {provenance.temporal_end}</Text>
            <Text style={styles.helper}>{bn ? 'ক্যাশ থেকে পড়া হয়েছে; সংগ্রহের সময়' : 'Read from cache; retrieved'}: {provenance.retrieved_at ?? '—'}</Text>
            <Text style={styles.helper}>{bn ? 'এটি জেলার একটি প্রকাশিত নির্দেশক বিন্দুর এলাকার grid; জেলা-গড় বা জমির সরাসরি পরিমাপ নয়।' : provenance.spatial_scale}</Text>
            <Text selectable style={styles.helper}>{provenance.source_url}</Text>
            {provenance.sampling_point ? <Text selectable style={styles.helper}>{String(provenance.sampling_point.description)} · {String(provenance.sampling_point.latitude)}, {String(provenance.sampling_point.longitude)}{'\n'}{String(provenance.sampling_point.source_url)}</Text> : null}
          </View> : null}
          <Text style={styles.label}>{bn ? 'সংক্ষিপ্ত বার্তা' : 'Short summary'}</Text>
          <Text selectable style={styles.body}>{bn ? result.sms_bn : result.sms_en}</Text>
        </Card> : null}
        <CropCalendarReferences language={language} season={season} />
      </ScrollView>
      <OptionPickerModal visible={pickerOpen} title={bn ? 'জেলা' : 'District'} language={language} options={buildDistrictOptions(districts, inventory, language)} selected={selected?.code} onSelect={value => { if (value) setDistrict(value); setPickerOpen(false); }} onClose={() => setPickerOpen(false)} />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  page: { flex: 1, backgroundColor: COLORS.background },
  content: { padding: SPACING.md, gap: SPACING.md, width: '100%', maxWidth: 720, alignSelf: 'center' },
  header: { flexDirection: 'row', justifyContent: 'space-between', gap: SPACING.sm },
  title: { ...TYPOGRAPHY.h2, lineHeight: 34 },
  body: { ...TYPOGRAPHY.body, lineHeight: 24 },
  label: { ...TYPOGRAPHY.body, fontWeight: '600', marginVertical: SPACING.sm },
  helper: { ...TYPOGRAPHY.caption, color: COLORS.textSecondary, lineHeight: 20, marginVertical: 4 },
  option: { minHeight: 56, justifyContent: 'center', borderWidth: 1, borderColor: COLORS.border, borderRadius: 8, padding: SPACING.sm },
  seasons: { flexDirection: 'row', gap: SPACING.sm, marginTop: SPACING.sm, flexWrap: 'wrap' },
  season: { minHeight: 56, padding: SPACING.sm, justifyContent: 'center', borderWidth: 1, borderColor: COLORS.border, borderRadius: 8 },
  selected: { backgroundColor: '#edf5ec', borderColor: COLORS.primary },
  warning: { ...TYPOGRAPHY.body, lineHeight: 24, color: '#79460b', backgroundColor: '#fff8ea', padding: SPACING.sm, marginVertical: SPACING.sm, borderRadius: 8 },
  sources: { borderTopWidth: 1, borderTopColor: COLORS.border, marginTop: SPACING.sm },
});
