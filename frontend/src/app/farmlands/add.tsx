import React, { useMemo, useState } from 'react';
import { Modal, Platform, Pressable, ScrollView, StyleSheet, Text, TextInput, View, useWindowDimensions } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { FarmBottomNavigation, FarmChromeIcon, FarmPageHeader } from '../../components/farmland-mobile-ui';
import { FarmProfileIcon, FarmProfileIconName } from '../../components/farm-profile-icons';
import { useAppContext } from '../../context/AppProvider';

const PAPER = '#fffdf7';
const GREEN = '#07543a';
const INK = '#102b25';
const MUTED = '#52677a';
const BORDER = '#e5e2d8';
const MAX_LAND_AREA_SQM = 99_999_999_999.999;
const SQUARE_METRES_PER_ACRE = 4046.8564224;
const MAX_ACREAGE = 24_710_538.14;
type FieldKey = 'location' | 'soil' | 'irrigation' | 'waterSource';
type FormValues = Record<FieldKey, string>;

const fieldOptions: Record<FieldKey, string[]> = {
  location: ['Gazipur, Dhaka Division', 'Dhaka, Dhaka Division', 'Mymensingh, Mymensingh Division', 'Rajshahi, Rajshahi Division'],
  soil: ['Clay loam', 'Sandy loam', 'Silt', 'Clay'],
  irrigation: ['Available', 'Not available'],
  waterSource: ['Tube well', 'Canal', 'River', 'Rain-fed'],
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
  const [values, setValues] = useState<FormValues>(() => ({
    location: '', soil: '', irrigation: '', waterSource: '',
  }));
  const [picker, setPicker] = useState<FieldKey | null>(null);
  const [error, setError] = useState('');
  const [locationNotice, setLocationNotice] = useState('');
  const [coordinates, setCoordinates] = useState<{ latitude: number; longitude: number } | null>(null);
  const [saving, setSaving] = useState(false);
  const selectedOptions = useMemo(() => picker ? fieldOptions[picker] : [], [picker]);

  const updateValue = (key: FieldKey, value: string) => {
    setValues(current => ({ ...current, [key]: value }));
    if (key === 'location') setCoordinates(null);
    setError('');
  };

  const useCurrentLocation = () => {
    setLocationNotice('');
    if (Platform.OS === 'web' && typeof navigator !== 'undefined' && navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        ({ coords: current }) => {
          setCoordinates({ latitude: current.latitude, longitude: current.longitude });
          setLocationNotice('Current coordinates added.');
        },
        () => setLocationNotice('Location is unavailable. Choose a location above or enter it manually.'),
        { enableHighAccuracy: false, timeout: 10000, maximumAge: 60000 },
      );
      return;
    }
    setLocationNotice('Choose a location above or enter it manually on this device.');
  };

  const saveFarmland = async () => {
    const parsedAcreage = Number(acreage.trim());
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
    if (!values.location.trim() && !coordinates) {
      setError('Choose a district or add your current location.');
      return;
    }
    const [district, division] = values.location.split(',').map(part => part.trim());
    setSaving(true);
    try {
      await createFarmland({
        name: name.trim(),
        land_area_sqm: parsedAcreage * SQUARE_METRES_PER_ACRE,
        land_area_display_unit: 'acre',
        division: coordinates ? undefined : division,
        district: coordinates ? undefined : district,
        latitude: coordinates?.latitude,
        longitude: coordinates?.longitude,
        soil_type: values.soil || undefined,
        irrigation_available: values.irrigation ? values.irrigation !== 'Not available' : undefined,
        water_source: values.waterSource || undefined,
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
            {renderSelectRow('location', 'District / division', 'location')}
            {renderTextRow('field', 'Land area', acreage, value => { setAcreage(value); setError(''); }, true)}
          </View>

          <View style={styles.groupCard}>
            <Text style={styles.groupTitle}>Farm profile</Text>
            {renderSelectRow('soil', 'Soil type', 'soil')}
            {renderSelectRow('drop', 'Irrigation', 'irrigation')}
            {renderSelectRow('water', 'Water source', 'waterSource')}
          </View>

          <View style={styles.adviceBanner}>
            <View style={styles.adviceIcon}><FarmProfileIcon name="leaf" size={27} color={GREEN} /></View>
            <Text style={styles.adviceText}>This profile is saved to your account. Choose a crop later in Crop Advisor to start a season.</Text>
          </View>
          {error ? <Text accessibilityRole="alert" style={styles.error}>{error}</Text> : null}
        </ScrollView>

        <View style={styles.actionBar}>
          <Pressable accessibilityRole="button" onPress={useCurrentLocation} style={styles.locationButton}>
            <FarmProfileIcon name="location" size={21} color={GREEN} />
            <Text style={styles.locationButtonText}>Use current location</Text>
          </Pressable>
          <Pressable accessibilityRole="button" disabled={saving} onPress={() => void saveFarmland()} style={[styles.saveButton, saving && styles.savingButton]}>
            <View style={styles.saveCheck}><FarmProfileIcon name="check" size={17} color={GREEN} /></View>
            <Text style={styles.saveButtonText}>{saving ? 'Saving…' : 'Save farmland'}</Text>
          </Pressable>
        </View>
        {locationNotice ? <Text accessibilityLiveRegion="polite" style={styles.locationNotice}>{locationNotice}</Text> : null}
        <FarmBottomNavigation active="Home" />

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
  rowIcon: { width: 28, height: 28, flexShrink: 0, alignItems: 'center', justifyContent: 'center', borderRadius: 18, backgroundColor: '#e9f1e3' },
  rowLabel: { flexShrink: 0, color: '#182941', fontSize: 11, lineHeight: 14 },
  rowInput: { flex: 1, minWidth: 0, height: 27, paddingHorizontal: 8, paddingVertical: 0, color: '#182941', fontSize: 11, lineHeight: 15, borderWidth: 1, borderColor: '#e2e0d8', borderRadius: 7, backgroundColor: '#f8f7f2' },
  rowValue: { flex: 1, minWidth: 0, height: 27, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 4, paddingHorizontal: 8, borderWidth: 1, borderColor: '#e2e0d8', borderRadius: 7, backgroundColor: '#f8f7f2' },
  valueText: { flex: 1, minWidth: 0, color: '#182941', fontSize: 11, lineHeight: 15 },
  infoBanner: { minHeight: 30, flexDirection: 'row', alignItems: 'center', gap: 7, paddingHorizontal: 8, marginTop: 4, borderRadius: 9, backgroundColor: '#eef3e8' },
  infoText: { flex: 1, color: '#36546a', fontSize: 10, lineHeight: 14 },
  adviceBanner: { minHeight: 56, flexDirection: 'row', alignItems: 'center', gap: 8, paddingHorizontal: 10, borderRadius: 13, overflow: 'hidden', backgroundColor: '#eef3e8' },
  adviceIcon: { width: 38, height: 38, flexShrink: 0, borderRadius: 22, alignItems: 'center', justifyContent: 'center', backgroundColor: '#dfead7' },
  adviceText: { flex: 1, color: INK, fontFamily: 'Georgia', fontSize: 12, lineHeight: 16, fontWeight: '700' },
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
