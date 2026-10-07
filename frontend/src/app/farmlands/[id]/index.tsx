import React from 'react';
import { ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Href, useLocalSearchParams, useRouter } from 'expo-router';
import { Button, Card } from '../../../components/ui';
import { useAppContext } from '../../../context/AppProvider';
import { formatDhakaDate, getTaskScheduleState } from '../../../utils/task-dates';
import { COLORS, SPACING, TYPOGRAPHY } from '../../../theme/theme';

export default function FarmOverview() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const farmId = Array.isArray(id) ? id[0] : id;
  const { farmlands } = useAppContext();
  const farm = farmlands.find(item => item.id === farmId);
  const router = useRouter();

  if (!farm || !farmId) {
    return <SafeAreaView style={styles.safe}><Text style={styles.empty}>Farm not found.</Text></SafeAreaView>;
  }

  const now = new Date();
  const dueToday = farm.tasks.filter(task => getTaskScheduleState(task, now) === 'due').length;
  const overdue = farm.tasks.filter(task => getTaskScheduleState(task, now) === 'overdue').length;
  const openProblems = farm.problems.filter(problem => problem.status === 'open' || problem.status === 'monitoring');
  const nextTasks = farm.tasks
    .filter(task => task.status === 'pending')
    .sort((a, b) => (a.dueAt ?? '9999').localeCompare(b.dueAt ?? '9999'))
    .slice(0, 3);
  const latestCheckIn = [...farm.checkIns].sort((a, b) => b.at.localeCompare(a.at))[0];
  const openSection = (section: string) => router.push(`/farmlands/${farmId}/${section}` as Href);

  return (
    <SafeAreaView style={styles.safe} edges={['bottom', 'left', 'right']}>
      <ScrollView contentContainerStyle={styles.container}>
        <View style={styles.heading}>
          <Text style={styles.eyebrow}>FARM BRAIN</Text>
          <Text style={styles.title}>Farm overview</Text>
          <Text style={styles.subtitle}>{farm.crop} · {farm.acreage} acres</Text>
        </View>

        <Card style={styles.stageCard}>
          <View style={styles.stageTop}>
            <View style={styles.stageCopy}>
              <Text style={styles.cardEyebrow}>CURRENT GROWTH STAGE</Text>
              <Text style={styles.stageName}>{farm.growthStage || 'Not set'}</Text>
            </View>
            <View style={styles.liveDot} />
          </View>
          <View style={styles.stageTrack}>
            {farm.seasonPlan.map(stage => (
              <View key={stage.id} style={styles.stageTrackItem}>
                <View style={[
                  styles.stageMark,
                  stage.status === 'completed' && styles.stageMarkComplete,
                  stage.status === 'current' && styles.stageMarkCurrent,
                ]} />
                <Text numberOfLines={1} style={[styles.stageLabel, stage.status === 'current' && styles.stageLabelCurrent]}>
                  {stage.name}
                </Text>
              </View>
            ))}
          </View>
          <Button title="View season plan" variant="outline" onPress={() => openSection('season-plan')} />
        </Card>

        <Button
          title="ফসলের পরামর্শ নিন"
          onPress={() => router.push(`/farmlands/${farmId}/crop-advisor` as Href)}
          style={styles.advisorButton}
        />

        <View style={styles.metrics}>
          <Card style={styles.metricCard}>
            <Text style={styles.metricValue}>{dueToday}</Text>
            <Text style={styles.metricLabel}>Due today</Text>
          </Card>
          <Card style={[styles.metricCard, overdue > 0 && styles.overdueCard]}>
            <Text style={[styles.metricValue, overdue > 0 && styles.overdueText]}>{overdue}</Text>
            <Text style={styles.metricLabel}>Overdue</Text>
          </Card>
          <Card style={styles.metricCard}>
            <Text style={styles.metricValue}>{openProblems.length}</Text>
            <Text style={styles.metricLabel}>Open problems</Text>
          </Card>
        </View>

        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>Next actions</Text>
          <Text onPress={() => openSection('tasks')} style={styles.link}>See all</Text>
        </View>
        {nextTasks.length === 0 ? (
          <Card><Text style={styles.emptyCardText}>No pending tasks. Your farm is up to date.</Text></Card>
        ) : nextTasks.map(task => (
          <Card key={task.id} style={styles.nextTaskCard}>
            <View style={styles.taskMark} />
            <View style={styles.taskDetails}>
              <Text style={styles.taskTitle}>{task.title}</Text>
              <Text style={styles.taskMeta}>{formatDhakaDate(task.dueAt)} · {task.priority} priority</Text>
            </View>
          </Card>
        ))}

        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>Farm problems</Text>
          <Text onPress={() => openSection('problems')} style={styles.link}>Review</Text>
        </View>
        {openProblems.length === 0 ? (
          <Card><Text style={styles.emptyCardText}>No open farm problems.</Text></Card>
        ) : openProblems.slice(0, 2).map(problem => (
          <Card key={problem.id} style={styles.problemCard}>
            <View style={styles.problemLine} />
            <View style={styles.taskDetails}>
              <Text style={styles.taskTitle}>{problem.category}</Text>
              <Text style={styles.problemDescription}>{problem.description}</Text>
              <Text style={styles.taskMeta}>{problem.severity} severity · {problem.status}</Text>
            </View>
          </Card>
        ))}

        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>Latest check-in</Text>
          <Text onPress={() => openSection('check-ins')} style={styles.link}>Log check-in</Text>
        </View>
        <Card>
          {latestCheckIn ? (
            <>
              <Text style={styles.checkinStage}>{latestCheckIn.stageName} · {formatDhakaDate(latestCheckIn.at)}</Text>
              <Text style={styles.checkinNotes}>{latestCheckIn.notes}</Text>
            </>
          ) : <Text style={styles.emptyCardText}>No check-ins recorded yet.</Text>}
        </Card>

        <View style={styles.quickActions}>
          <Button title="Log a check-in" onPress={() => openSection('check-ins')} style={styles.quickButton} />
          <Button title="Report a problem" variant="outline" onPress={() => openSection('problems')} style={styles.quickButton} />
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: COLORS.background },
  container: { flexGrow: 1, width: '100%', maxWidth: 920, alignSelf: 'center', padding: SPACING.md, paddingBottom: SPACING.xxl },
  heading: { marginBottom: SPACING.md },
  eyebrow: { ...TYPOGRAPHY.caption, fontWeight: '700', letterSpacing: 1.2, color: COLORS.primary },
  title: { ...TYPOGRAPHY.h1, marginTop: SPACING.xs },
  subtitle: { ...TYPOGRAPHY.bodySecondary, marginTop: SPACING.xs },
  stageCard: { padding: SPACING.lg },
  stageTop: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  stageCopy: { flex: 1 },
  cardEyebrow: { ...TYPOGRAPHY.caption, fontWeight: '700', letterSpacing: 0.8 },
  stageName: { ...TYPOGRAPHY.h2, color: COLORS.primaryDark, marginTop: SPACING.xs },
  liveDot: { width: 12, height: 12, borderRadius: 6, backgroundColor: COLORS.success, marginLeft: SPACING.md },
  stageTrack: { flexDirection: 'row', gap: SPACING.sm, marginVertical: SPACING.lg },
  stageTrackItem: { flex: 1, minWidth: 0 },
  stageMark: { height: 5, borderRadius: 3, backgroundColor: COLORS.border, marginBottom: SPACING.xs },
  stageMarkComplete: { backgroundColor: COLORS.success },
  stageMarkCurrent: { backgroundColor: COLORS.primary },
  stageLabel: { ...TYPOGRAPHY.caption, fontSize: 11 },
  stageLabelCurrent: { color: COLORS.primaryDark, fontWeight: '700' },
  metrics: { flexDirection: 'row', gap: SPACING.sm, marginTop: SPACING.sm },
  metricCard: { flex: 1, marginBottom: 0 },
  overdueCard: { borderWidth: 1, borderColor: '#edc2bd' },
  metricValue: { ...TYPOGRAPHY.h2, color: COLORS.primaryDark },
  metricLabel: { ...TYPOGRAPHY.caption, marginTop: SPACING.xs },
  overdueText: { color: COLORS.error },
  sectionHeader: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginTop: SPACING.lg, marginBottom: SPACING.xs },
  sectionTitle: { ...TYPOGRAPHY.h3 },
  link: { ...TYPOGRAPHY.caption, color: COLORS.primary, fontWeight: '700', padding: SPACING.xs },
  nextTaskCard: { flexDirection: 'row', alignItems: 'center', gap: SPACING.md },
  taskMark: { width: 10, height: 10, borderRadius: 5, backgroundColor: COLORS.primary },
  taskDetails: { flex: 1 },
  taskTitle: { ...TYPOGRAPHY.body, fontWeight: '600' },
  taskMeta: { ...TYPOGRAPHY.caption, marginTop: SPACING.xs, textTransform: 'capitalize' },
  problemCard: { flexDirection: 'row', gap: SPACING.md },
  problemLine: { width: 4, borderRadius: 3, backgroundColor: COLORS.warning },
  problemDescription: { ...TYPOGRAPHY.bodySecondary, marginTop: SPACING.xs, lineHeight: 21 },
  checkinStage: { ...TYPOGRAPHY.caption, fontWeight: '700' },
  checkinNotes: { ...TYPOGRAPHY.body, marginTop: SPACING.sm, lineHeight: 23 },
  emptyCardText: { ...TYPOGRAPHY.bodySecondary, lineHeight: 23 },
  quickActions: { flexDirection: 'row', gap: SPACING.sm, marginTop: SPACING.md },
  quickButton: { flex: 1, minHeight: 44 },
  advisorButton: { marginBottom: SPACING.md },
  empty: { ...TYPOGRAPHY.bodySecondary, textAlign: 'center', padding: SPACING.lg },
});
