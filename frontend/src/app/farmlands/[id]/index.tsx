import React from 'react';
import { View, Text, StyleSheet, ScrollView } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { useAppContext } from '../../../context/AppProvider';
import { Button, Card } from '../../../components/ui';
import { COLORS, SPACING, TYPOGRAPHY } from '../../../theme/theme';

export default function FarmDashboard() {
  const { id } = useLocalSearchParams();
  const router = useRouter();
  const { farmlands } = useAppContext();
  const farm = farmlands.find(f => f.id === id);

  if (!farm) return <Text style={styles.errorText}>Farm not found</Text>;

  return (
    <SafeAreaView style={styles.safe} edges={['bottom', 'left', 'right']}>
      <ScrollView contentContainerStyle={styles.container}>
        <View style={styles.header}>
          <Text style={styles.title}>{farm.name}</Text>
          <Text style={styles.subtitle}>{farm.crop} - {farm.acreage} acres</Text>
          <Text style={styles.stage}>Stage: {farm.growthStage}</Text>
        </View>
        <Card style={styles.summaryCard}>
          <Text style={styles.summaryTitle}>Quick Summary</Text>
          <Text style={styles.summaryText}>Tasks: {farm.tasks.length} total, {farm.tasks.filter(t => !t.completed).length} pending</Text>
          <Text style={styles.summaryText}>Alerts: {farm.alerts.length} active</Text>
          <Text style={styles.summaryText}>Crop Health: {farm.cropHealth.status}</Text>
        </Card>
        <Button title="Chat with Assistant" onPress={() => router.push(`/farmlands/${id}/chat` as any)} style={styles.button} />
        <Button title="View Alerts" onPress={() => router.push(`/farmlands/${id}/alerts` as any)} style={styles.button} />
        <Button title="Daily Tasks" onPress={() => router.push(`/farmlands/${id}/tasks` as any)} style={styles.button} />
        <Button title="Season Plan" onPress={() => router.push(`/farmlands/${id}/season-plan` as any)} style={styles.button} />
        <Button title="Crop Health" onPress={() => router.push(`/farmlands/${id}/crop-health` as any)} style={styles.button} />
        <Button title="Back to All Farmlands" variant="outline" onPress={() => router.push('/farmlands' as any)} />
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: COLORS.background },
  container: { flexGrow: 1, padding: SPACING.md },
  errorText: { ...TYPOGRAPHY.h3, color: COLORS.error, textAlign: 'center', marginTop: SPACING.xl },
  header: { marginBottom: SPACING.lg, alignItems: 'center' },
  title: { ...TYPOGRAPHY.h1, color: COLORS.primary, marginBottom: SPACING.xs },
  subtitle: { ...TYPOGRAPHY.h3, color: COLORS.textSecondary },
  stage: { ...TYPOGRAPHY.body, color: COLORS.success, marginTop: SPACING.sm, fontWeight: 'bold' },
  summaryCard: { marginBottom: SPACING.lg, backgroundColor: COLORS.primaryLight },
  summaryTitle: { ...TYPOGRAPHY.h3, color: COLORS.surface, marginBottom: SPACING.sm },
  summaryText: { ...TYPOGRAPHY.body, color: COLORS.surface, marginBottom: SPACING.xs },
  button: { marginBottom: SPACING.md },
});