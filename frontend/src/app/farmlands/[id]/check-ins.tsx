import React, { useState } from 'react';
import { ScrollView, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useLocalSearchParams } from 'expo-router';
import { Button, Card, Input } from '../../../components/ui';
import { useAppContext } from '../../../context/AppProvider';
import { formatDhakaDate } from '../../../utils/task-dates';
import { BORDER_RADIUS, COLORS, SPACING, TYPOGRAPHY } from '../../../theme/theme';

export default function CheckIns() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const farmId = Array.isArray(id) ? id[0] : id;
  const { farmlands, addCheckIn } = useAppContext();
  const farm = farmlands.find(item => item.id === farmId);
  const [notes, setNotes] = useState('');
  const [cropCondition, setCropCondition] = useState('');
  const [waterCondition, setWaterCondition] = useState('');
  const [pestObserved, setPestObserved] = useState(false);
  const [diseaseObserved, setDiseaseObserved] = useState(false);
  const [error, setError] = useState('');

  if (!farm || !farmId) {
    return <SafeAreaView style={styles.safe}><Text style={styles.empty}>Farm not found.</Text></SafeAreaView>;
  }

  const saveCheckIn = () => {
    const cleanNotes = notes.trim();
    if (!cleanNotes && !cropCondition.trim() && !waterCondition.trim() && !pestObserved && !diseaseObserved) {
      setError('Add a note or observation before saving.');
      return;
    }
    addCheckIn(farmId, cleanNotes || 'Field observations recorded.', {
      cropCondition: cropCondition.trim() || undefined,
      waterCondition: waterCondition.trim() || undefined,
      pestObserved,
      diseaseObserved,
    });
    setNotes('');
    setCropCondition('');
    setWaterCondition('');
    setPestObserved(false);
    setDiseaseObserved(false);
    setError('');
  };

  const toggle = (value: boolean, setter: (value: boolean) => void) => (
    <TouchableOpacity
      accessibilityRole="checkbox"
      accessibilityState={{ checked: value }}
      onPress={() => setter(!value)}
      style={[styles.toggle, value && styles.toggleActive]}
    >
      <View style={[styles.toggleMark, value && styles.toggleMarkActive]} />
      <Text style={[styles.toggleText, value && styles.toggleTextActive]}>{value ? 'Observed' : 'Not observed'}</Text>
    </TouchableOpacity>
  );

  return (
    <SafeAreaView style={styles.safe} edges={['bottom', 'left', 'right']}>
      <ScrollView contentContainerStyle={styles.container} keyboardShouldPersistTaps="handled">
        <View style={styles.heading}>
          <Text style={styles.eyebrow}>FARM BRAIN</Text>
          <Text style={styles.title}>Field check-in</Text>
          <Text style={styles.subtitle}>Record what you see so the farm history stays useful.</Text>
        </View>

        <Card>
          <Text style={styles.cardTitle}>Today at {farm.name}</Text>
          <Text style={styles.stage}>Current stage · {farm.growthStage || 'Not set'}</Text>
          <Input
            label="Crop condition"
            placeholder="e.g. Leaves look healthy"
            value={cropCondition}
            onChangeText={setCropCondition}
          />
          <Input
            label="Water condition"
            placeholder="e.g. Soil is moist near the roots"
            value={waterCondition}
            onChangeText={setWaterCondition}
          />
          <View style={styles.observationRow}>
            <Text style={styles.inputLabel}>Pests seen</Text>
            {toggle(pestObserved, setPestObserved)}
          </View>
          <View style={styles.observationRow}>
            <Text style={styles.inputLabel}>Disease symptoms seen</Text>
            {toggle(diseaseObserved, setDiseaseObserved)}
          </View>
          <Input
            label="Notes"
            placeholder="Anything else you noticed today?"
            value={notes}
            onChangeText={setNotes}
            multiline
            numberOfLines={4}
            textAlignVertical="top"
            style={styles.notesInput}
          />
          {error ? <Text accessibilityRole="alert" style={styles.error}>{error}</Text> : null}
          <Button title="Save check-in" onPress={saveCheckIn} />
        </Card>

        <View style={styles.listHeading}>
          <Text style={styles.cardTitle}>Recent check-ins</Text>
          <Text style={styles.count}>{farm.checkIns.length}</Text>
        </View>
        {farm.checkIns.length === 0 ? (
          <Card><Text style={styles.empty}>No check-ins recorded yet.</Text></Card>
        ) : farm.checkIns.map(checkIn => (
          <Card key={checkIn.id}>
            <View style={styles.historyTop}>
              <Text style={styles.historyStage}>{checkIn.stageName}</Text>
              <Text style={styles.date}>{formatDhakaDate(checkIn.at)}</Text>
            </View>
            <Text style={styles.historyNotes}>{checkIn.notes}</Text>
            <View style={styles.observations}>
              {checkIn.observations.cropCondition ? <Text style={styles.observationText}>Crop · {checkIn.observations.cropCondition}</Text> : null}
              {checkIn.observations.waterCondition ? <Text style={styles.observationText}>Water · {checkIn.observations.waterCondition}</Text> : null}
              {checkIn.observations.pestObserved ? <Text style={styles.observationText}>Pests observed</Text> : null}
              {checkIn.observations.diseaseObserved ? <Text style={styles.observationText}>Disease symptoms observed</Text> : null}
            </View>
          </Card>
        ))}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: COLORS.background },
  container: { flexGrow: 1, width: '100%', maxWidth: 920, alignSelf: 'center', padding: SPACING.md },
  heading: { marginBottom: SPACING.md },
  eyebrow: { ...TYPOGRAPHY.caption, fontWeight: '700', letterSpacing: 1.2, color: COLORS.primary },
  title: { ...TYPOGRAPHY.h1, marginTop: SPACING.xs },
  subtitle: { ...TYPOGRAPHY.bodySecondary, marginTop: SPACING.xs, lineHeight: 23 },
  cardTitle: { ...TYPOGRAPHY.h3 },
  stage: { ...TYPOGRAPHY.caption, marginTop: SPACING.xs, marginBottom: SPACING.md },
  inputLabel: { ...TYPOGRAPHY.caption, color: COLORS.text, flex: 1 },
  observationRow: { minHeight: 52, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: SPACING.md, borderTopWidth: 1, borderTopColor: COLORS.border },
  toggle: { minHeight: 38, flexDirection: 'row', alignItems: 'center', gap: SPACING.xs, paddingHorizontal: SPACING.sm, borderRadius: BORDER_RADIUS.round, backgroundColor: '#f0f2ef' },
  toggleActive: { backgroundColor: '#e5f1e3' },
  toggleMark: { width: 10, height: 10, borderRadius: 5, backgroundColor: COLORS.border },
  toggleMarkActive: { backgroundColor: COLORS.success },
  toggleText: { ...TYPOGRAPHY.caption, fontWeight: '600' },
  toggleTextActive: { color: COLORS.primaryDark },
  notesInput: { minHeight: 100 },
  error: { ...TYPOGRAPHY.caption, color: COLORS.error, marginBottom: SPACING.sm },
  listHeading: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginTop: SPACING.lg, marginBottom: SPACING.sm },
  count: { ...TYPOGRAPHY.caption, fontWeight: '700' },
  historyTop: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: SPACING.md },
  historyStage: { ...TYPOGRAPHY.body, fontWeight: '600', flex: 1 },
  date: { ...TYPOGRAPHY.caption },
  historyNotes: { ...TYPOGRAPHY.bodySecondary, marginTop: SPACING.sm, lineHeight: 23 },
  observations: { gap: SPACING.xs, marginTop: SPACING.md },
  observationText: { ...TYPOGRAPHY.caption, color: COLORS.primaryDark },
  empty: { ...TYPOGRAPHY.bodySecondary, textAlign: 'center', padding: SPACING.lg },
});
