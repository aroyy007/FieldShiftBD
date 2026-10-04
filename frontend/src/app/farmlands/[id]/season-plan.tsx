import React from 'react';
import { View, Text, StyleSheet, ScrollView } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useLocalSearchParams } from 'expo-router';
import { useAppContext } from '../../../context/AppProvider';
import { Card } from '../../../components/ui';
import { COLORS, SPACING, TYPOGRAPHY } from '../../../theme/theme';

export default function SeasonPlan() {
  const { id } = useLocalSearchParams();
  const { farmlands } = useAppContext();
  const farm = farmlands.find(f => f.id === id);

  if (!farm) return null;

  return (
    <SafeAreaView style={styles.safe} edges={['bottom', 'left', 'right']}>
      <ScrollView contentContainerStyle={styles.container}>
        <Text style={styles.header}>Season Plan: {farm.crop}</Text>
        {farm.seasonPlan.length === 0 && <Text style={styles.empty}>No plan available.</Text>}
        {farm.seasonPlan.map((stage) => (
          <View key={stage.id} style={styles.timelineItem}>
            <View style={styles.dotCol}>
              <View style={[
                styles.dot,
                stage.status === 'completed' && styles.dotCompleted,
                stage.status === 'current' && styles.dotCurrent,
              ]} />
              <View style={styles.line} />
            </View>
            <Card style={styles.card}>
              <Text style={styles.stageName}>{stage.name}</Text>
              <Text style={styles.dateRange}>{stage.dateRange}</Text>
              <Text style={[styles.status, { color: stage.status === 'current' ? COLORS.primary : COLORS.textSecondary }]}>
                {stage.status.toUpperCase()}
              </Text>
            </Card>
          </View>
        ))}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: COLORS.background },
  container: { flexGrow: 1, padding: SPACING.md },
  header: { ...TYPOGRAPHY.h2, color: COLORS.primary, marginBottom: SPACING.lg, textAlign: 'center' },
  timelineItem: { flexDirection: 'row', marginBottom: SPACING.sm },
  dotCol: { alignItems: 'center', marginRight: SPACING.md, marginTop: SPACING.md },
  dot: { width: 20, height: 20, borderRadius: 10, backgroundColor: COLORS.border },
  dotCompleted: { backgroundColor: COLORS.success },
  dotCurrent: { backgroundColor: COLORS.primary, borderWidth: 3, borderColor: COLORS.primaryLight },
  line: { width: 2, flex: 1, backgroundColor: COLORS.border, marginTop: 4 },
  card: { flex: 1, marginBottom: 0 },
  stageName: { ...TYPOGRAPHY.h3 },
  dateRange: { ...TYPOGRAPHY.body, color: COLORS.textSecondary, marginVertical: SPACING.xs },
  status: { ...TYPOGRAPHY.caption, fontWeight: 'bold' },
  empty: { textAlign: 'center', ...TYPOGRAPHY.bodySecondary },
});