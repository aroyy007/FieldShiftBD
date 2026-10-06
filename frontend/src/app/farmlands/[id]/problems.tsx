import React, { useState } from 'react';
import { ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useLocalSearchParams } from 'expo-router';
import { Button, Card, Input } from '../../../components/ui';
import { useAppContext } from '../../../context/AppProvider';
import { ProblemStatus } from '../../../data/demo';
import { formatDhakaDate } from '../../../utils/task-dates';
import { COLORS, SPACING, TYPOGRAPHY } from '../../../theme/theme';

function nextStatusActions(status: ProblemStatus) {
  if (status === 'open') return [
    { status: 'monitoring' as const, label: 'Monitor' },
    { status: 'resolved' as const, label: 'Resolve' },
    { status: 'dismissed' as const, label: 'Dismiss' },
  ];
  if (status === 'monitoring') return [
    { status: 'resolved' as const, label: 'Resolve' },
    { status: 'open' as const, label: 'Reopen' },
  ];
  return [{ status: 'open' as const, label: 'Reopen' }];
}

export default function FarmProblems() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const farmId = Array.isArray(id) ? id[0] : id;
  const { farmlands, addProblem, updateProblemStatus } = useAppContext();
  const farm = farmlands.find(item => item.id === farmId);
  const [description, setDescription] = useState('');
  const [error, setError] = useState('');

  if (!farm || !farmId) {
    return <SafeAreaView style={styles.safe}><Text style={styles.empty}>Farm not found.</Text></SafeAreaView>;
  }

  const reportProblem = () => {
    if (!description.trim()) {
      setError('Describe what you noticed before reporting it.');
      return;
    }
    addProblem(farmId, description);
    setDescription('');
    setError('');
  };

  const activeCount = farm.problems.filter(problem => problem.status === 'open' || problem.status === 'monitoring').length;
  const problems = [...farm.problems].sort((a, b) => b.createdAt.localeCompare(a.createdAt));

  return (
    <SafeAreaView style={styles.safe} edges={['bottom', 'left', 'right']}>
      <ScrollView contentContainerStyle={styles.container} keyboardShouldPersistTaps="handled">
        <View style={styles.heading}>
          <Text style={styles.eyebrow}>FARM BRAIN</Text>
          <Text style={styles.title}>Farm problems</Text>
          <Text style={styles.subtitle}>Keep issues visible until they are resolved or dismissed.</Text>
        </View>

        <View style={styles.summary}>
          <Text style={styles.summaryNumber}>{activeCount}</Text>
          <View style={styles.summaryCopy}>
            <Text style={styles.summaryTitle}>Open problems</Text>
            <Text style={styles.summaryText}>Monitoring and open issues for this farm.</Text>
          </View>
        </View>

        <Card>
          <Text style={styles.cardTitle}>Report a problem</Text>
          <Text style={styles.formHint}>Add a short description. You can update its status as you follow up.</Text>
          <Input
            label="What did you notice?"
            placeholder="Describe the issue in the field"
            value={description}
            onChangeText={setDescription}
            multiline
            numberOfLines={3}
            textAlignVertical="top"
            style={styles.descriptionInput}
          />
          {error ? <Text accessibilityRole="alert" style={styles.error}>{error}</Text> : null}
          <Button title="Report problem" onPress={reportProblem} />
        </Card>

        <View style={styles.listHeader}>
          <Text style={styles.cardTitle}>Problem history</Text>
          <Text style={styles.count}>{problems.length}</Text>
        </View>
        {problems.length === 0 ? (
          <Card><Text style={styles.empty}>No farm problems have been reported.</Text></Card>
        ) : problems.map(problem => (
          <Card key={problem.id} style={styles.problemCard}>
            <View style={styles.problemHeading}>
              <View style={styles.problemCopy}>
                <Text style={styles.category}>{problem.category}</Text>
                <Text style={styles.meta}>{problem.source.replace('_', ' ')} · {formatDhakaDate(problem.createdAt)}</Text>
              </View>
              <Text style={[styles.status, problem.status === 'resolved' && styles.resolved]}>
                {problem.status}
              </Text>
            </View>
            <Text style={styles.description}>{problem.description}</Text>
            <View style={styles.severityRow}>
              <Text style={styles.meta}>Severity</Text>
              <Text style={styles.severity}>{problem.severity}</Text>
            </View>
            <View style={styles.actions}>
              {nextStatusActions(problem.status).map(action => (
                <Button
                  key={action.status}
                  title={action.label}
                  variant={action.status === 'resolved' ? 'primary' : 'outline'}
                  onPress={() => updateProblemStatus(farmId, problem.id, action.status)}
                  style={styles.actionButton}
                />
              ))}
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
  summary: { flexDirection: 'row', alignItems: 'center', padding: SPACING.md, marginBottom: SPACING.md, borderRadius: 12, backgroundColor: '#e9f0e8' },
  summaryNumber: { ...TYPOGRAPHY.h1, color: COLORS.primaryDark, marginRight: SPACING.md },
  summaryCopy: { flex: 1 },
  summaryTitle: { ...TYPOGRAPHY.body, fontWeight: '700' },
  summaryText: { ...TYPOGRAPHY.caption, marginTop: 2 },
  cardTitle: { ...TYPOGRAPHY.h3 },
  formHint: { ...TYPOGRAPHY.caption, marginTop: SPACING.xs, marginBottom: SPACING.md, lineHeight: 19 },
  descriptionInput: { minHeight: 86 },
  error: { ...TYPOGRAPHY.caption, color: COLORS.error, marginBottom: SPACING.sm },
  listHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginTop: SPACING.lg, marginBottom: SPACING.sm },
  count: { ...TYPOGRAPHY.caption, fontWeight: '700' },
  problemCard: { borderLeftWidth: 4, borderLeftColor: COLORS.warning },
  problemHeading: { flexDirection: 'row', alignItems: 'flex-start', gap: SPACING.sm },
  problemCopy: { flex: 1 },
  category: { ...TYPOGRAPHY.h3 },
  meta: { ...TYPOGRAPHY.caption, textTransform: 'capitalize' },
  status: { ...TYPOGRAPHY.caption, color: COLORS.warning, fontWeight: '700', textTransform: 'capitalize' },
  resolved: { color: COLORS.success },
  description: { ...TYPOGRAPHY.bodySecondary, marginTop: SPACING.md, lineHeight: 23 },
  severityRow: { flexDirection: 'row', justifyContent: 'space-between', marginTop: SPACING.md },
  severity: { ...TYPOGRAPHY.caption, textTransform: 'capitalize', fontWeight: '700' },
  actions: { flexDirection: 'row', flexWrap: 'wrap', gap: SPACING.xs, marginTop: SPACING.md },
  actionButton: { minHeight: 40, paddingHorizontal: SPACING.md },
  empty: { ...TYPOGRAPHY.bodySecondary, textAlign: 'center', padding: SPACING.lg },
});
