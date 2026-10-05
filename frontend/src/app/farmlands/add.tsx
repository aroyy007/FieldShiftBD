import React, { useState } from 'react';
import { Text, StyleSheet, Alert, ScrollView } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { Button, Input } from '../../components/ui';
import { useAppContext } from '../../context/AppProvider';
import { COLORS, SPACING, TYPOGRAPHY } from '../../theme/theme';

export default function AddFarmland() {
  const [name, setName] = useState('');
  const [crop, setCrop] = useState('');
  const [acreage, setAcreage] = useState('');
  const router = useRouter();
  const { addFarmland } = useAppContext();

  const handleSave = () => {
    if (!name || !crop || !acreage) {
      Alert.alert('Error', 'Please fill all fields');
      return;
    }
    addFarmland({
      id: Math.random().toString(),
      name, crop,
      acreage: parseFloat(acreage) || 0,
      growthStage: 'Preparation',
      tasks: [], alerts: [], seasonPlan: [],
      cropHealth: { status: 'Unknown', diseaseRisk: 'Low', recentIssues: [] },
    });
    router.back();
  };

  return (
    <SafeAreaView style={styles.safe}>
      <ScrollView contentContainerStyle={styles.container} keyboardShouldPersistTaps="handled">
        <Text style={styles.title}>New Farmland</Text>
        <Input label="Farmland Name" placeholder="e.g. South Field" value={name} onChangeText={setName} />
        <Input label="Crop Type" placeholder="e.g. Rice" value={crop} onChangeText={setCrop} />
        <Input label="Acreage" placeholder="e.g. 50" value={acreage} onChangeText={setAcreage} keyboardType="numeric" />
        <Button title="Save Farmland" onPress={handleSave} style={styles.button} />
        <Button title="Cancel" variant="secondary" onPress={() => router.back()} />
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: COLORS.background },
  container: { flexGrow: 1, padding: SPACING.lg },
  title: { ...TYPOGRAPHY.h2, marginBottom: SPACING.lg, color: COLORS.primary },
  button: { marginBottom: SPACING.md },
});