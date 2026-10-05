import React from 'react';
import { View, Text, StyleSheet, ScrollView } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useLocalSearchParams } from 'expo-router';
import { useAppContext } from '../../../context/AppProvider';
import { Card } from '../../../components/ui';
import { COLORS, SPACING, TYPOGRAPHY } from '../../../theme/theme';

export default function CropHealth() {
  const { id } = useLocalSearchParams();
  const { farmlands } = useAppContext();
  const farm = farmlands.find(f => f.id === id);

  if (!farm) return null;

  const isGood = farm.cropHealth.status === 'Good' || farm.cropHealth.status === 'Excellent';

  return (
    <SafeAreaView style={styles.safe} edges={['bottom', 'left', 'right']}>
      <ScrollView contentContainerStyle={styles.container}>
        <Card style={styles.mainCard}>
          <Text style={styles.cardLabel}>Overall Status</Text>
          <Text style={[styles.statusValue, isGood ? styles.good : styles.warning]}>
            {farm.cropHealth.status}
          </Text>
        </Card>
        <Card>
          <Text style={styles.sectionTitle}>Disease Risk</Text>
          <Text style={styles.bodyText}>{farm.cropHealth.diseaseRisk}</Text>
        </Card>
        <Card>
          <Text style={styles.sectionTitle}>Recent Issues</Text>
          {farm.cropHealth.recentIssues.length > 0 ? (
            farm.cropHealth.recentIssues.map((issue, idx) => (
              <Text key={idx} style={styles.issueText}>- {issue}</Text>
            ))
          ) : (
            <Text style={styles.bodyText}>No recent issues reported.</Text>
          )}
        </Card>
        <View style={styles.placeholder}>
          <Text style={styles.placeholderText}>Disease Detection Placeholder</Text>
          <Text style={styles.placeholderSub}>Upload photos in future updates to see analysis here.</Text>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: COLORS.background },
  container: { flexGrow: 1, padding: SPACING.md },
  mainCard: { alignItems: 'center', paddingVertical: SPACING.xl },
  cardLabel: { ...TYPOGRAPHY.h2, marginBottom: SPACING.sm },
  statusValue: { ...TYPOGRAPHY.h1 },
  good: { color: COLORS.success },
  warning: { color: COLORS.warning },
  sectionTitle: { ...TYPOGRAPHY.h3, color: COLORS.primary, marginBottom: SPACING.sm },
  bodyText: { ...TYPOGRAPHY.body, color: COLORS.textSecondary },
  issueText: { ...TYPOGRAPHY.body, marginBottom: SPACING.xs },
  placeholder: { marginTop: SPACING.xl, padding: SPACING.xl, borderWidth: 2, borderStyle: 'dashed', borderColor: COLORS.border, borderRadius: SPACING.sm, alignItems: 'center' },
  placeholderText: { ...TYPOGRAPHY.h3, color: COLORS.textSecondary, marginBottom: SPACING.xs },
  placeholderSub: { ...TYPOGRAPHY.caption, textAlign: 'center' },
});