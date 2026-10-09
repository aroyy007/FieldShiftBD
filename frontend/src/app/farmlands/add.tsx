import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { Modal, Pressable, ScrollView, StyleSheet, Text, TextInput, View, useWindowDimensions } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { FarmBottomNavigation, FarmChromeIcon, FarmPageHeader } from '../../components/farmland-mobile-ui';
import { FarmProfileIcon, FarmProfileIconName } from '../../components/farm-profile-icons';
import { useAppContext } from '../../context/AppProvider';
import OptionPickerModal, { PickerOption } from '../../components/OptionPickerModal';
import { DivisionRef, ProfileVocabulary, loadLocations, loadProfileVocabulary } from '../../services/m1-reference';
import { captureCurrentFarmLocation } from '../../services/farm-location';

const PAPER = '#fffdf7';
const GREEN = '#07543a';
const INK = '#102b25';
const MUTED = '#52677a';
const BORDER = '#e5e2d8';
const MAX_LAND_AREA_SQM = 99_999_999_999.999;
const SQUARE_METRES_PER_ACRE = 4046.8564224;
const MAX_ACREAGE = 24_710_538.14;
type FieldKey = 'irrigation' | 'waterSource';
type FormValues = Record<FieldKey, string>;

type ReferenceKey = 'division' | 'district' | 'upazila' | 'soil' | 'landType';

const fieldOptions: Record<FieldKey, string[]> = {
  irrigation: ['Available', 'Not available'],
  waterSource: ['Tube well', 'Canal', 'River', 'Pond', 'Rain-fed', 'Other'],
};

export default function AddFarmland() {
  const router = useRouter();
  const params = useLocalSearchParams<{ name?: string | string[]; acreage?: string | string[] }>();
  const { width } = useWindowDimensions();
  const labelWidth = Math.max(78, Math.min(106, width * 0.25));
  const { createFarmland } = useAppContext();
  const readParam = (value: string | string[] | undefined, fallback: string) => Array.isArray(value) ? value[0] ?? fallback : value ?? fallback;
  const [name, setName] = useState(() => readParam(params.name, ''));
  const [acreage, setAcreage] = useState(() => readParam(params.acreage, ''));
  const [village, setVillage] = useState('');
  const [equipmentText, setEquipmentText] = useState('');
  const [budgetText, setBudgetText] = useState('');
  const [values, setValues] = useState<FormValues>(() => ({ irrigation: '', waterSource: '' }));
  const [picker, setPicker] = useState<FieldKey | null>(null);
  const [referencePicker, setReferencePicker] = useState<ReferenceKey | null>(null);
  const [divisions, setDivisions] = useState<DivisionRef[] | null>(null);
  const [vocabulary, setVocabulary] = useState<ProfileVocabulary | null>(null);
  const [referenceError, setReferenceError] = useState('');
  const [divisionCode, setDivisionCode] = useState<string | null>(null);
  const [districtCode, setDistrictCode] = useState<string | null>(null);
  const [upazilaCode, setUpazilaCode] = useState<string | null>(null);
  const [soilCode, setSoilCode] = useState<string | null>(null);
  const [landType, setLandType] = useState<string | null>(null);
  const [error, setError] = useState('');
  const [locationNotice, setLocationNotice] = useState('');
  const [coordinates, setCoordinates] = useState<{ latitude: number; longitude: number } | null>(null);
  const [locationLoading, setLocationLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const selectedOptions = useMemo(() => picker ? fieldOptions[picker] : [], [picker]);

  const fetchReference = useCallback(() => Promise.all([loadLocations(), loadProfileVocabulary()])
    .then(([locationTree, profileVocabulary]) => {
      setDivisions(locationTree);
      setVocabulary(profileVocabulary);
      setReferenceError('');
    })
    .catch(requestError => setReferenceError(requestError instanceof Error ? requestError.message : 'Could not load location and soil lists.')), []);
  useEffect(() => { void fetchReference(); }, [fetchReference]);
  const loadReference = () => {
    setReferenceError('');
    void fetchReference();
  };

  const division = divisions?.find(item => item.code === divisionCode);
  const district = division?.districts.find(item => item.code === districtCode);
  const upazila = district?.upazilas.find(item => item.code === upazilaCode);
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
  const referenceTitles: Record<ReferenceKey, string> = {
    division: 'Division', district: 'District', upazila: 'Upazila', soil: 'Soil type', landType: 'Land type',
  };
  const selectReference = (value: string | null) => {
    if (referencePicker === 'division') { setDivisionCode(value); setDistrictCode(null); setUpazilaCode(null); }
    if (referencePicker === 'district') { setDistrictCode(value); setUpazilaCode(null); }
    if (referencePicker === 'upazila') setUpazilaCode(value);
    if (referencePicker === 'soil') setSoilCode(value);
    if (referencePicker === 'landType') setLandType(value);
    setReferencePicker(null);
    setError('');
  };
  const openReference = (key: ReferenceKey) => {
    if (!divisions || !vocabulary) { loadReference(); return; }
    if (key === 'district' && !division) { setError('Choose a division first.'); return; }
    if (key === 'upazila' && !district) { setError('Choose a district first.'); return; }
    setReferencePicker(key);
  };

  const updateValue = (key: FieldKey, value: string) => {
    setValues(current => ({ ...current, [key]: value }));
    setError('');
  };

  const requestCurrentLocation = async () => {
    setLocationNotice('');
    setLocationLoading(true);
    try {
      const result = await captureCurrentFarmLocation();
      setCoordinates({ latitude: result.latitude, longitude: result.longitude });
      if (result.divisionCode) setDivisionCode(result.divisionCode);
      if (result.districtCode) setDistrictCode(result.districtCode);
      if (result.upazilaCode) setUpazilaCode(result.upazilaCode);
      setLocationNotice(result.notice);
    } catch (locationError) {
      setLocationNotice(locationError instanceof Error ? locationError.message : 'Could not get your current location. Enter it manually.');
    } finally {
      setLocationLoading(false);
    }
  };

  const saveFarmland = async () => {
    if (locationLoading) {
      setError('Wait for the location request to finish before saving.');
      return;
    }
    const parsedAcreage = Number(acreage.trim());
    const parsedBudget = budgetText.trim() ? Number(budgetText.trim()) : undefined;
    if (!name.trim()) {
      setError('Enter a farmland name.');
      return;
    }
    if (!Number.isFinite(parsedAcreage) || parsedAcreage <= 0) {
      setError('Enter a valid land area greater than zero.');
      return;
    }
    if (parsedAcreage > MAX_ACREAGE || parsedAcreage * SQUARE_METRES_PER_ACRE > MAX_LAND_AREA_SQM) {
      setError('This land area is larger than the maximum the system can save.');
      return;
    }
    if (!district) {
      setError('Choose the division and district of this farmland.');
      return;
    }
    if (parsedBudget !== undefined && (!Number.isFinite(parsedBudget) || parsedBudget < 0)) {
      setError('Enter a valid non-negative farm budget.');
      return;
    }
    setSaving(true);
    try {
      await createFarmland({
        name: name.trim(),
        land_area_sqm: parsedAcreage * SQUARE_METRES_PER_ACRE,
        land_area_display_unit: 'acre',
        division: division?.name,
        district: district.name,
        upazila: upazila?.name,
        village_or_locality: village.trim() || undefined,
        latitude: coordinates?.latitude,
        longitude: coordinates?.longitude,
        soil_type: soil?.label_en,
        land_type: land?.code,
        irrigation_available: values.irrigation ? values.irrigation !== 'Not available' : undefined,
        water_source: values.waterSource || undefined,
        equipment: equipmentText.split(/[\n,]/).map(item => item.trim()).filter(Boolean),
        budget_amount: parsedBudget,
        budget_currency: 'BDT',
      });
      setError('');
      if (router.canGoBack()) router.back();
      else router.replace('/farmlands/manage');
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Could not save the farmland. Please try again.');
    } finally {
      setSaving(false);
    }
  };

  const renderTextRow = (icon: FarmProfileIconName, label: string, value: string, setValue: (next: string) => void, numeric = false) => (
    <View style={styles.formRow}>
      <View style={styles.rowIcon}><FarmProfileIcon name={icon} size={20} color={GREEN} /></View>
      <Text style={[styles.rowLabel, { width: labelWidth }]} numberOfLines={1}>{label}</Text>
      <TextInput
        accessibilityLabel={label}
        value={value}
        onChangeText={setValue}
        keyboardType={numeric ? 'decimal-pad' : 'default'}
        placeholder={label}
        placeholderTextColor="#82909a"
        style={styles.rowInput}
        selectTextOnFocus
      />
    </View>
  );

  const renderReferenceRow = (icon: FarmProfileIconName, label: string, key: ReferenceKey, value: string | undefined) => (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={`${label}: ${value ?? 'not chosen'}`}
      onPress={() => openReference(key)}
      style={styles.formRow}
    >
      <View style={styles.rowIcon}><FarmProfileIcon name={icon} size={20} color={GREEN} /></View>
      <Text style={[styles.rowLabel, { width: labelWidth }]} numberOfLines={1}>{label}</Text>
      <View style={styles.rowValue}><Text numberOfLines={1} style={[styles.valueText, !value && styles.placeholderText]}>{value ?? 'Choose'}</Text><FarmChromeIcon name="chevron" size={16} color={MUTED} /></View>
    </Pressable>
  );

  const renderSelectRow = (icon: FarmProfileIconName, label: string, key: FieldKey) => (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={`${label}: ${values[key]}`}
      onPress={() => setPicker(key)}
      style={styles.formRow}
    >
      <View style={styles.rowIcon}><FarmProfileIcon name={icon} size={20} color={GREEN} /></View>
      <Text style={[styles.rowLabel, { width: labelWidth }]} numberOfLines={1}>{label}</Text>
      <View style={styles.rowValue}><Text numberOfLines={1} style={styles.valueText}>{values[key]}</Text><FarmChromeIcon name="chevron" size={16} color={MUTED} /></View>
    </Pressable>
  );

  return (
    <SafeAreaView style={styles.safe} edges={['top', 'bottom']}>
      <View style={styles.screen}>
        <FarmPageHeader
          title="Add Farmland"
          subtitle="Create a land profile to track crops, tasks, and seasonal advice."
          subtitleLines={2}
          actionLabel="Save farmland"
          actionIcon="save"
          onAction={() => void saveFarmland()}
        />
        <ScrollView contentContainerStyle={styles.scrollContent} keyboardShouldPersistTaps="handled" showsVerticalScrollIndicator={false}>
          <View style={styles.groupCard}>
            <Text style={styles.groupTitle}>Land details</Text>
            {renderTextRow('leaf', 'Farmland name', name, value => { setName(value); setError(''); })}
            {renderReferenceRow('location', 'Division', 'division', division?.name)}
            {renderReferenceRow('location', 'District', 'district', district?.name)}
            {renderReferenceRow('location', 'Upazila', 'upazila', upazila?.name)}
            {renderTextRow('location', 'Village/locality', village, value => { setVillage(value); setError(''); })}
            {renderTextRow('field', 'Land area', acreage, value => { setAcreage(value); setError(''); }, true)}
          </View>

          <View style={styles.groupCard}>
            <Text style={styles.groupTitle}>Farm profile</Text>
            {renderReferenceRow('soil', 'Soil type', 'soil', soil?.label_en)}
            {renderReferenceRow('field', 'Land type', 'landType', land?.label_en)}
            {renderSelectRow('drop', 'Irrigation', 'irrigation')}
            {renderSelectRow('water', 'Water source', 'waterSource')}
            {renderTextRow('coins', 'Budget (BDT)', budgetText, value => { setBudgetText(value); setError(''); }, true)}
            <View style={styles.multilineRow}>
              <View style={styles.rowIcon}><FarmProfileIcon name="field" size={20} color={GREEN} /></View>
              <Text style={[styles.rowLabel, { width: labelWidth }]}>Equipment</Text>
              <TextInput
                accessibilityLabel="Available equipment"
                value={equipmentText}
                onChangeText={setEquipmentText}
                placeholder="Pump, tractor, tools…"
                placeholderTextColor="#82909a"
                style={styles.multilineInput}
                multiline
              />
            </View>
          </View>

          <View style={styles.adviceBanner}>
            <View style={styles.adviceIcon}><FarmProfileIcon name="leaf" size={27} color={GREEN} /></View>
            <Text style={styles.adviceText}>This profile is saved to your account. Choose a crop later in Crop Advisor to start a season.</Text>
          </View>
          <Text style={styles.helpText}>Land type and soil type are used to check published crop conditions. Leave them empty if you are not sure.</Text>
          {referenceError ? (
            <Pressable accessibilityRole="button" onPress={loadReference}>
              <Text accessibilityRole="alert" style={styles.error}>{referenceError} Tap to retry.</Text>
            </Pressable>
          ) : null}
          {error ? <Text accessibilityRole="alert" style={styles.error}>{error}</Text> : null}
        </ScrollView>

        <View style={styles.actionBar}>
          <Pressable accessibilityRole="button" disabled={locationLoading} onPress={() => void requestCurrentLocation()} style={[styles.locationButton, locationLoading && styles.savingButton]}>
            <FarmProfileIcon name="location" size={21} color={GREEN} />
            <Text style={styles.locationButtonText}>{locationLoading ? 'Getting location…' : 'Use current location'}</Text>
          </Pressable>
          <Pressable accessibilityRole="button" disabled={saving} onPress={() => void saveFarmland()} style={[styles.saveButton, saving && styles.savingButton]}>
            <View style={styles.saveCheck}><FarmProfileIcon name="check" size={17} color={GREEN} /></View>
            <Text style={styles.saveButtonText}>{saving ? 'Saving…' : 'Save farmland'}</Text>
          </Pressable>
        </View>
        {locationNotice ? <Text accessibilityLiveRegion="polite" style={styles.locationNotice}>{locationNotice}</Text> : null}
        <FarmBottomNavigation active="Home" />

        <OptionPickerModal
          visible={referencePicker !== null}
          title={referencePicker ? referenceTitles[referencePicker] : ''}
          options={referenceOptions}
          selected={referencePicker === 'division' ? divisionCode : referencePicker === 'district' ? districtCode : referencePicker === 'upazila' ? upazilaCode : referencePicker === 'soil' ? soilCode : landType}
          allowClear={referencePicker === 'upazila' || referencePicker === 'soil' || referencePicker === 'landType'}
          onSelect={selectReference}
          onClose={() => setReferencePicker(null)}
        />
        <Modal visible={picker !== null} transparent animationType="fade" onRequestClose={() => setPicker(null)}>
          <Pressable style={styles.modalBackdrop} onPress={() => setPicker(null)}>
            <View style={styles.optionSheet}>
              <Text style={styles.optionTitle}>{picker ? picker === 'waterSource' ? 'Water source' : picker[0].toUpperCase() + picker.slice(1) : ''}</Text>
              {selectedOptions.map(option => (
                <Pressable key={option} accessibilityRole="button" accessibilityState={{ selected: picker ? values[picker] === option : false }} onPress={() => { if (picker) updateValue(picker, option); setPicker(null); }} style={styles.optionRow}>
                  <Text style={styles.optionText}>{option}</Text>
                  {picker && values[picker] === option ? <FarmProfileIcon name="check" size={19} color={GREEN} /> : <View style={styles.optionRadio} />}
                </Pressable>
              ))}
              <Pressable accessibilityRole="button" onPress={() => setPicker(null)} style={styles.cancelOption}><Text style={styles.cancelOptionText}>Cancel</Text></Pressable>
            </View>
          </Pressable>
        </Modal>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: PAPER },
  screen: { flex: 1, backgroundColor: PAPER },
  scrollContent: { paddingHorizontal: 12, paddingTop: 8, paddingBottom: 8, gap: 7 },
  photoCard: { height: 104, borderRadius: 15, overflow: 'hidden', backgroundColor: '#e9eee0', borderWidth: 1, borderColor: '#edeae1' },
  photoBackground: { flex: 1, justifyContent: 'center' },
  photoImage: { borderRadius: 15, top: -18 },
  photoCopy: { width: '56%', height: '100%', justifyContent: 'center', paddingHorizontal: 10, backgroundColor: 'rgba(255,253,247,0.96)', borderTopRightRadius: 36, borderBottomRightRadius: 38 },
  photoTitle: { color: INK, fontFamily: 'Georgia', fontSize: 19, lineHeight: 23, fontWeight: '700' },
  photoDescription: { color: MUTED, fontSize: 11, lineHeight: 14, marginTop: 1 },
  uploadButton: { height: 31, minWidth: 112, alignSelf: 'flex-start', flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 6, paddingHorizontal: 10, marginTop: 7, borderRadius: 10, backgroundColor: '#e9f0e3' },
  uploadText: { color: GREEN, fontSize: 11, fontWeight: '600' },
  groupCard: { paddingHorizontal: 9, paddingTop: 6, paddingBottom: 5, borderRadius: 14, backgroundColor: '#fffefa', borderWidth: 1, borderColor: '#eeece3' },
  groupTitle: { marginBottom: 2, color: INK, fontFamily: 'Georgia', fontSize: 18, lineHeight: 23, fontWeight: '700' },
  formRow: { minHeight: 31, flexDirection: 'row', alignItems: 'center', gap: 6, borderBottomWidth: 1, borderBottomColor: '#eeece5' },
  multilineRow: { minHeight: 51, flexDirection: 'row', alignItems: 'center', gap: 6, borderBottomWidth: 1, borderBottomColor: '#eeece5' },
  rowIcon: { width: 28, height: 28, flexShrink: 0, alignItems: 'center', justifyContent: 'center', borderRadius: 18, backgroundColor: '#e9f1e3' },
  rowLabel: { flexShrink: 0, color: '#182941', fontSize: 11, lineHeight: 14 },
  rowInput: { flex: 1, minWidth: 0, height: 27, paddingHorizontal: 8, paddingVertical: 0, color: '#182941', fontSize: 11, lineHeight: 15, borderWidth: 1, borderColor: '#e2e0d8', borderRadius: 7, backgroundColor: '#f8f7f2' },
  multilineInput: { flex: 1, minWidth: 0, minHeight: 40, maxHeight: 76, paddingHorizontal: 8, paddingVertical: 5, color: '#182941', fontSize: 11, lineHeight: 15, borderWidth: 1, borderColor: '#e2e0d8', borderRadius: 7, backgroundColor: '#f8f7f2' },
  rowValue: { flex: 1, minWidth: 0, height: 27, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 4, paddingHorizontal: 8, borderWidth: 1, borderColor: '#e2e0d8', borderRadius: 7, backgroundColor: '#f8f7f2' },
  valueText: { flex: 1, minWidth: 0, color: '#182941', fontSize: 11, lineHeight: 15 },
  infoBanner: { minHeight: 30, flexDirection: 'row', alignItems: 'center', gap: 7, paddingHorizontal: 8, marginTop: 4, borderRadius: 9, backgroundColor: '#eef3e8' },
  infoText: { flex: 1, color: '#36546a', fontSize: 10, lineHeight: 14 },
  adviceBanner: { minHeight: 56, flexDirection: 'row', alignItems: 'center', gap: 8, paddingHorizontal: 10, borderRadius: 13, overflow: 'hidden', backgroundColor: '#eef3e8' },
  adviceIcon: { width: 38, height: 38, flexShrink: 0, borderRadius: 22, alignItems: 'center', justifyContent: 'center', backgroundColor: '#dfead7' },
  adviceText: { flex: 1, color: INK, fontFamily: 'Georgia', fontSize: 12, lineHeight: 16, fontWeight: '700' },
  placeholderText: { color: '#82909a' },
  helpText: { color: MUTED, fontSize: 11, lineHeight: 15, paddingHorizontal: 5 },
  error: { color: '#bb2e19', fontSize: 12, lineHeight: 16, paddingHorizontal: 5 },
  actionBar: { flexDirection: 'row', gap: 7, paddingHorizontal: 10, paddingTop: 7, paddingBottom: 6, backgroundColor: PAPER, borderTopWidth: 1, borderTopColor: '#efede5' },
  locationButton: { flex: 1, minHeight: 43, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 6, paddingHorizontal: 6, borderWidth: 1.4, borderColor: GREEN, borderRadius: 10, backgroundColor: PAPER },
  locationButtonText: { color: GREEN, fontSize: 11, fontWeight: '700' },
  saveButton: { flex: 1, minHeight: 43, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 7, paddingHorizontal: 6, borderRadius: 10, backgroundColor: GREEN },
  savingButton: { opacity: 0.65 },
  saveCheck: { width: 22, height: 22, borderRadius: 12, alignItems: 'center', justifyContent: 'center', backgroundColor: PAPER },
  saveButtonText: { color: PAPER, fontSize: 12, fontWeight: '700' },
  locationNotice: { paddingHorizontal: 12, paddingBottom: 4, color: MUTED, fontSize: 10, lineHeight: 13, textAlign: 'center', backgroundColor: PAPER },
  modalBackdrop: { flex: 1, justifyContent: 'flex-end', paddingHorizontal: 12, paddingBottom: 18, backgroundColor: 'rgba(16, 24, 32, 0.38)' },
  optionSheet: { padding: 14, borderRadius: 18, backgroundColor: PAPER },
  optionTitle: { color: INK, fontFamily: 'Georgia', fontSize: 19, lineHeight: 24, fontWeight: '700', marginBottom: 8 },
  optionRow: { minHeight: 46, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', borderBottomWidth: 1, borderBottomColor: BORDER },
  optionText: { color: INK, fontSize: 14 },
  optionRadio: { width: 18, height: 18, borderRadius: 10, borderWidth: 1.5, borderColor: '#abb6ad' },
  cancelOption: { minHeight: 44, alignItems: 'center', justifyContent: 'center', marginTop: 6, borderRadius: 9, backgroundColor: '#edf2e8' },
  cancelOptionText: { color: GREEN, fontSize: 14, fontWeight: '700' },
});
