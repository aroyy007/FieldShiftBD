import React from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useLocalSearchParams } from 'expo-router';
import { useAppContext } from '../../../context/AppProvider';
import { Card } from '../../../components/ui';
import { COLORS, SPACING, TYPOGRAPHY } from '../../../theme/theme';

export default function SeasonPlan() {
  const { id } = useLocalSearchParams();
  const farmId = Array.isArray(id) ? id[0] : id;
  const { farmlands, updateGrowthStage } = useAppContext();
  const farm = farmlands.find(f => f.id === farmId);

  if (!farm || !farmId) return null;

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
              <TouchableOpacity
                accessibilityRole="button"
                disabled={stage.status === 'current'}
                onPress={() => updateGrowthStage(farmId, stage.id)}
                style={[styles.stageButton, stage.status === 'current' && styles.stageButtonCurrent]}
              >
                <Text style={[styles.stageButtonText, stage.status === 'current' && styles.stageButtonTextCurrent]}>
                  {stage.status === 'current' ? 'Current stage' : 'Set as current'}
                </Text>
              </TouchableOpacity>
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
  stageButton: { alignSelf: 'flex-start', marginTop: SPACING.sm, paddingHorizontal: SPACING.md, paddingVertical: SPACING.sm, borderWidth: 1, borderColor: COLORS.primary, borderRadius: 8 },
  stageButtonCurrent: { borderColor: COLORS.border, backgroundColor: '#f5f7f5' },
  stageButtonText: { ...TYPOGRAPHY.caption, color: COLORS.primary, fontWeight: '700' },
  stageButtonTextCurrent: { color: COLORS.textSecondary },
});
