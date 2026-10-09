import React, { useEffect, useMemo, useState } from 'react';
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Href, useLocalSearchParams, useRouter } from 'expo-router';
import OptionPickerModal, { PickerOption } from '../../../components/OptionPickerModal';
import { FarmBottomNavigation, FarmChromeIcon, FarmPageHeader } from '../../../components/farmland-mobile-ui';
import { FarmProfileIcon, FarmProfileIconName } from '../../../components/farm-profile-icons';
import { useAppContext } from '../../../context/AppProvider';
import type { Farmland } from '../../../data/demo';
import { captureCurrentFarmLocation } from '../../../services/farm-location';
import { DivisionRef, ProfileVocabulary, loadLocations, loadProfileVocabulary } from '../../../services/m1-reference';

const PAPER = '#fffdf7';
const GREEN = '#07543a';
const INK = '#102b25';
const MUTED = '#52677a';
type ReferenceKey = 'division' | 'district' | 'upazila' | 'soil' | 'landType' | 'irrigation';
type LocationReferenceKey = Exclude<ReferenceKey, 'irrigation'>;

export default function FarmResources() {
  const params = useLocalSearchParams<{ id?: string | string[] }>();
  const farmId = Array.isArray(params.id) ? params.id[0] : params.id;
  const { farmlands } = useAppContext();
  const farm = farmlands.find(item => item.id === farmId);

  if (!farm) {
    return <SafeAreaView style={styles.safe}><Text style={styles.error}>Farm not found.</Text></SafeAreaView>;
  }
  return <FarmResourcesForm key={farm.id} farm={farm} />;
}

function FarmResourcesForm({ farm }: { farm: Farmland }) {
  const { updateFarmland } = useAppContext();
  const farmId = farm.id;
  const router = useRouter();
  const [divisions, setDivisions] = useState<DivisionRef[] | null>(null);
  const [vocabulary, setVocabulary] = useState<ProfileVocabulary | null>(null);
  const [referencePicker, setReferencePicker] = useState<ReferenceKey | null>(null);
  const [divisionCode, setDivisionCode] = useState<string | null>(farm.divisionCode ?? null);
  const [districtCode, setDistrictCode] = useState<string | null>(farm.districtCode ?? null);
  const [upazilaCode, setUpazilaCode] = useState<string | null>(farm.upazilaCode ?? null);
  const [soilCodeOverride, setSoilCodeOverride] = useState<string | null | undefined>(undefined);
  const [landTypeOverride, setLandTypeOverride] = useState<string | null | undefined>(undefined);
  const [village, setVillage] = useState(farm.villageOrLocality ?? '');
  const [irrigation, setIrrigation] = useState(farm.irrigationAvailable == null ? '' : farm.irrigationAvailable ? 'Available' : 'Not available');
  const [waterSource, setWaterSource] = useState(farm.waterSource ?? '');
  const [equipmentText, setEquipmentText] = useState((farm.equipment ?? []).join(', '));
  const [budgetText, setBudgetText] = useState(farm.budgetAmount == null ? '' : String(farm.budgetAmount));
  const [coordinates, setCoordinates] = useState<{ latitude: number | null; longitude: number | null }>({ latitude: farm.latitude ?? null, longitude: farm.longitude ?? null });
  const [locationNotice, setLocationNotice] = useState('');
  const [locationSelectionTouched, setLocationSelectionTouched] = useState(false);
  const [error, setError] = useState('');
  const [referenceError, setReferenceError] = useState('');
  const [locationLoading, setLocationLoading] = useState(false);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    let active = true;
    Promise.all([loadLocations(), loadProfileVocabulary()]).then(([locationData, profileData]) => {
      if (!active) return;
      setDivisions(locationData);
      setVocabulary(profileData);
      setReferenceError('');
    }).catch(requestError => {
      if (active) setReferenceError(requestError instanceof Error ? requestError.message : 'Could not load farm reference data.');
    });
    return () => { active = false; };
  }, []);

  const division = divisions?.find(item => item.code === divisionCode);
  const district = division?.districts.find(item => item.code === districtCode);
  const upazila = district?.upazilas.find(item => item.code === upazilaCode);
  const soilCode = soilCodeOverride === undefined
    ? vocabulary?.soil_textures.find(item => item.label_en === farm.soilType)?.code ?? null
    : soilCodeOverride;
  const landType = landTypeOverride === undefined
    ? vocabulary?.land_types.find(item => item.code === farm.landType || item.label_en === farm.landType)?.code ?? null
    : landTypeOverride;
  const soil = vocabulary?.soil_textures.find(item => item.code === soilCode);
  const land = vocabulary?.land_types.find(item => item.code === landType);
  const referenceOptions: PickerOption[] = useMemo(() => {
    if (referencePicker === 'division') return (divisions ?? []).map(item => ({ value: item.code, label: item.name, detail: item.name_bn }));
    if (referencePicker === 'district') return (division?.districts ?? []).map(item => ({ value: item.code, label: item.name, detail: item.name_bn }));
    if (referencePicker === 'upazila') return (district?.upazilas ?? []).map(item => ({ value: item.code, label: item.name, detail: item.name_bn }));
    if (referencePicker === 'soil') return (vocabulary?.soil_textures ?? []).map(item => ({ value: item.code, label: item.label_en, detail: item.label_bn }));
    if (referencePicker === 'landType') return (vocabulary?.land_types ?? []).map(item => ({ value: item.code, label: item.label_en, detail: item.label_bn }));
    return [];
  }, [referencePicker, divisions, division, district, vocabulary]);
  const referenceTitles: Record<LocationReferenceKey, string> = { division: 'Division', district: 'District', upazila: 'Upazila', soil: 'Soil type', landType: 'Land type' };

  const selectReference = (value: string | null) => {
    if (referencePicker === 'irrigation') {
      setIrrigation(value ?? '');
      setReferencePicker(null);
      setError('');
      return;
    }
    if (referencePicker === 'division') { setDivisionCode(value); setDistrictCode(null); setUpazilaCode(null); setLocationSelectionTouched(true); }
    if (referencePicker === 'district') { setDistrictCode(value); setUpazilaCode(null); setLocationSelectionTouched(true); }
    if (referencePicker === 'upazila') setLocationSelectionTouched(true);
    if (referencePicker === 'upazila') setUpazilaCode(value);
    if (referencePicker === 'soil') setSoilCodeOverride(value);
    if (referencePicker === 'landType') setLandTypeOverride(value);
    setReferencePicker(null);
    setError('');
  };

  const openReference = (key: LocationReferenceKey) => {
    if (!divisions || !vocabulary) { setReferenceError('Location or farm resource choices are still loading.'); return; }
    if (key === 'district' && !division) { setError('Choose a division first.'); return; }
    if (key === 'upazila' && !district) { setError('Choose a district first.'); return; }
    setReferencePicker(key);
  };

  const requestCurrentLocation = async () => {
    setLocationNotice('');
    setLocationLoading(true);
    try {
      const result = await captureCurrentFarmLocation();
      setCoordinates({ latitude: result.latitude, longitude: result.longitude });
      if (result.divisionCode) {
        setDivisionCode(result.divisionCode);
        if (result.divisionCode !== divisionCode) {
          setDistrictCode(null);
          setUpazilaCode(null);
          setLocationSelectionTouched(true);
        }
      }
      if (result.districtCode) {
        setDistrictCode(result.districtCode);
        if (result.districtCode !== districtCode) {
          setUpazilaCode(null);
          setLocationSelectionTouched(true);
        }
      }
      if (result.upazilaCode) setUpazilaCode(result.upazilaCode);
      setLocationNotice(result.notice);
    } catch (locationError) {
      setLocationNotice(locationError instanceof Error ? locationError.message : 'Could not get your current location. Enter it manually.');
    } finally {
      setLocationLoading(false);
    }
  };

  const save = async () => {
    if (saving || locationLoading) return;
    const budget = budgetText.trim() ? Number(budgetText.trim()) : null;
    if (budget !== null && (!Number.isFinite(budget) || budget < 0)) {
      setError('Enter a valid non-negative farm budget.');
      return;
    }
    if ((coordinates.latitude === null) !== (coordinates.longitude === null)) {
      setError('Both coordinates are required. Use current location or clear them in the location settings.');
      return;
    }
    setSaving(true);
    setError('');
    try {
      await updateFarmland(farmId, {
        division: division?.name ?? (locationSelectionTouched ? null : farm.division ?? null),
        district: district?.name ?? (locationSelectionTouched ? null : farm.district ?? null),
        upazila: upazila?.name ?? (locationSelectionTouched ? null : farm.upazila ?? null),
        village_or_locality: village.trim() || null,
        latitude: coordinates.latitude,
        longitude: coordinates.longitude,
        soil_type: soil?.label_en ?? farm.soilType ?? null,
        land_type: land?.code ?? farm.landType ?? null,
        irrigation_available: irrigation === 'Available' ? true : irrigation === 'Not available' ? false : null,
        water_source: waterSource.trim() || null,
        equipment: Array.from(new Set(equipmentText.split(/[\n,]/).map(item => item.trim()).filter(Boolean))),
        budget_amount: budget,
        budget_currency: 'BDT',
      });
      if (router.canGoBack()) router.back();
      else router.replace(`/farmlands/${farmId}` as Href);
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : 'Could not save this farm profile. Try again.');
    } finally {
      setSaving(false);
    }
  };

  const renderText = (icon: FarmProfileIconName, label: string, value: string, onChange: (next: string) => void, numeric = false) => (
    <View style={styles.formRow}>
      <View style={styles.rowIcon}><FarmProfileIcon name={icon} size={19} color={GREEN} /></View>
      <Text style={styles.rowLabel}>{label}</Text>
      <TextInput accessibilityLabel={label} value={value} onChangeText={onChange} keyboardType={numeric ? 'decimal-pad' : 'default'} placeholder={label} placeholderTextColor="#82909a" style={styles.input} />
    </View>
  );

  const renderChoice = (icon: FarmProfileIconName, label: string, key: LocationReferenceKey, value: string | undefined) => (
    <Pressable accessibilityRole="button" accessibilityLabel={`${label}: ${value ?? 'not chosen'}`} onPress={() => openReference(key)} style={styles.formRow}>
      <View style={styles.rowIcon}><FarmProfileIcon name={icon} size={19} color={GREEN} /></View>
      <Text style={styles.rowLabel}>{label}</Text>
      <View style={styles.valueBox}><Text numberOfLines={1} style={[styles.valueText, !value && styles.placeholder]}>{value ?? 'Choose'}</Text><FarmChromeIcon name="chevron" size={16} color={MUTED} /></View>
    </Pressable>
  );

  return (
    <SafeAreaView style={styles.safe} edges={['top', 'bottom']}>
      <View style={styles.screen}>
        <FarmPageHeader title="Farm Profile & Resources" subtitle={`Edit the location and resources for ${farm.name}.`} subtitleLines={2} actionLabel="Save" actionIcon="save" onAction={() => void save()} />
        <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled" showsVerticalScrollIndicator={false}>
          <View style={styles.card}>
            <Text style={styles.cardTitle}>Location</Text>
            {renderChoice('location', 'Division', 'division', division?.name)}
            {renderChoice('location', 'District', 'district', district?.name)}
            {renderChoice('location', 'Upazila', 'upazila', upazila?.name)}
            {renderText('location', 'Village/locality', village, setVillage)}
            <View style={styles.coordinateRow}>
              <Text style={styles.coordinateText}>{coordinates.latitude == null ? 'Coordinates not saved' : `${coordinates.latitude.toFixed(5)}, ${coordinates.longitude?.toFixed(5)}`}</Text>
              <Pressable accessibilityRole="button" disabled={locationLoading} onPress={() => void requestCurrentLocation()} style={[styles.locationButton, locationLoading && styles.disabled]}>
                {locationLoading ? <ActivityIndicator color={GREEN} size="small" /> : <FarmProfileIcon name="location" size={18} color={GREEN} />}
                <Text style={styles.locationButtonText}>{locationLoading ? 'Getting location…' : 'Use current location'}</Text>
              </Pressable>
            </View>
            {locationNotice ? <Text accessibilityLiveRegion="polite" style={styles.notice}>{locationNotice}</Text> : null}
          </View>

          <View style={styles.card}>
            <Text style={styles.cardTitle}>Resources</Text>
            {renderChoice('soil', 'Soil type', 'soil', soil?.label_en ?? farm.soilType ?? undefined)}
            {renderChoice('field', 'Land type', 'landType', land?.label_en ?? farm.landType ?? undefined)}
            <Pressable accessibilityRole="button" onPress={() => setReferencePicker('irrigation')} style={styles.formRow}>
              <View style={styles.rowIcon}><FarmProfileIcon name="drop" size={19} color={GREEN} /></View>
              <Text style={styles.rowLabel}>Irrigation</Text>
              <View style={styles.valueBox}><Text style={[styles.valueText, !irrigation && styles.placeholder]}>{irrigation || 'Choose'}</Text><FarmChromeIcon name="chevron" size={16} color={MUTED} /></View>
            </Pressable>
            {renderText('water', 'Water source', waterSource, setWaterSource)}
            {renderText('coins', 'Budget (BDT)', budgetText, setBudgetText, true)}
            <View style={styles.multilineRow}>
              <View style={styles.rowIcon}><FarmProfileIcon name="field" size={19} color={GREEN} /></View>
              <Text style={styles.rowLabel}>Equipment</Text>
              <TextInput accessibilityLabel="Available equipment" value={equipmentText} onChangeText={setEquipmentText} placeholder="Pump, tractor, tools…" placeholderTextColor="#82909a" style={styles.multilineInput} multiline />
            </View>
          </View>
          {referenceError ? <Text accessibilityRole="alert" style={styles.error}>{referenceError}</Text> : null}
          {error ? <Text accessibilityRole="alert" style={styles.error}>{error}</Text> : null}
          <Pressable accessibilityRole="button" disabled={saving} onPress={() => void save()} style={[styles.saveButton, saving && styles.disabled]}>
            <Text style={styles.saveText}>{saving ? 'Saving…' : 'Save farm profile'}</Text>
          </Pressable>
        </ScrollView>
        <FarmBottomNavigation active="Home" farmId={farmId} />
        <OptionPickerModal
          visible={referencePicker !== null && referencePicker !== 'irrigation'}
          title={referencePicker && referencePicker !== 'irrigation' ? referenceTitles[referencePicker] : ''}
          options={referenceOptions}
          selected={referencePicker === 'division' ? divisionCode : referencePicker === 'district' ? districtCode : referencePicker === 'upazila' ? upazilaCode : referencePicker === 'soil' ? soilCode : referencePicker === 'landType' ? landType : irrigation}
          allowClear={referencePicker === 'upazila' || referencePicker === 'soil' || referencePicker === 'landType'}
          onSelect={selectReference}
          onClose={() => setReferencePicker(null)}
        />
        {referencePicker === 'irrigation' ? (
          <OptionPickerModal visible title="Irrigation" options={['Available', 'Not available'].map(value => ({ value, label: value }))} selected={irrigation || null} allowClear onSelect={selectReference} onClose={() => setReferencePicker(null)} />
        ) : null}
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: PAPER },
  screen: { flex: 1, backgroundColor: PAPER },
  content: { paddingHorizontal: 12, paddingTop: 8, paddingBottom: 18, gap: 10 },
  card: { paddingHorizontal: 10, paddingTop: 8, paddingBottom: 6, borderRadius: 15, backgroundColor: '#fffefa', borderWidth: 1, borderColor: '#eeece3' },
  cardTitle: { marginBottom: 4, color: INK, fontFamily: 'Georgia', fontSize: 18, lineHeight: 23, fontWeight: '700' },
  formRow: { minHeight: 42, flexDirection: 'row', alignItems: 'center', gap: 8, borderBottomWidth: 1, borderBottomColor: '#eeece5' },
  multilineRow: { minHeight: 62, flexDirection: 'row', alignItems: 'center', gap: 8, borderBottomWidth: 1, borderBottomColor: '#eeece5' },
  rowIcon: { width: 29, height: 29, flexShrink: 0, alignItems: 'center', justifyContent: 'center', borderRadius: 18, backgroundColor: '#e9f1e3' },
  rowLabel: { width: 104, flexShrink: 0, color: '#182941', fontSize: 12, lineHeight: 16 },
  input: { flex: 1, minWidth: 0, height: 34, paddingHorizontal: 9, color: '#182941', fontSize: 12, borderWidth: 1, borderColor: '#e2e0d8', borderRadius: 8, backgroundColor: '#f8f7f2' },
  multilineInput: { flex: 1, minWidth: 0, minHeight: 50, maxHeight: 80, paddingHorizontal: 9, paddingVertical: 7, color: '#182941', fontSize: 12, borderWidth: 1, borderColor: '#e2e0d8', borderRadius: 8, backgroundColor: '#f8f7f2' },
  valueBox: { flex: 1, minWidth: 0, height: 34, paddingHorizontal: 9, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 4, borderWidth: 1, borderColor: '#e2e0d8', borderRadius: 8, backgroundColor: '#f8f7f2' },
  valueText: { flex: 1, minWidth: 0, color: '#182941', fontSize: 12 },
  placeholder: { color: '#82909a' },
  coordinateRow: { minHeight: 44, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 8 },
  coordinateText: { flex: 1, color: MUTED, fontSize: 11 },
  locationButton: { minHeight: 36, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 5, paddingHorizontal: 8, borderWidth: 1, borderColor: GREEN, borderRadius: 9 },
  locationButtonText: { color: GREEN, fontSize: 11, fontWeight: '700' },
  notice: { paddingBottom: 4, color: MUTED, fontSize: 11, lineHeight: 15 },
  error: { paddingHorizontal: 4, color: '#bb2e19', fontSize: 12, lineHeight: 17 },
  saveButton: { minHeight: 46, alignItems: 'center', justifyContent: 'center', borderRadius: 12, backgroundColor: GREEN },
  saveText: { color: PAPER, fontSize: 14, fontWeight: '700' },
  disabled: { opacity: 0.62 },
});
