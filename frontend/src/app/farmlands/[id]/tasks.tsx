import React, { useState } from 'react';
import { ScrollView, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useLocalSearchParams } from 'expo-router';
import { Button, Card, Input } from '../../../components/ui';
import { useAppContext } from '../../../context/AppProvider';
import { TaskScheduleState } from '../../../data/demo';
import {
  formatDhakaDate,
  getTaskScheduleState,
  taskDueAtForDhakaDate,
} from '../../../utils/task-dates';
import { BORDER_RADIUS, COLORS, SPACING, TYPOGRAPHY } from '../../../theme/theme';

type Filter = 'all' | 'due' | 'overdue' | 'upcoming' | 'completed' | 'skipped';
const FILTERS: { id: Filter; label: string }[] = [
  { id: 'all', label: 'All' },
  { id: 'due', label: 'Due today' },
  { id: 'overdue', label: 'Overdue' },
  { id: 'upcoming', label: 'Upcoming' },
  { id: 'completed', label: 'Completed' },
  { id: 'skipped', label: 'Skipped' },
];

function taskStateLabel(state: TaskScheduleState) {
  if (state === 'due') return 'Due today';
  if (state === 'upcoming') return 'Upcoming';
  if (state === 'overdue') return 'Overdue';
  if (state === 'unscheduled') return 'No due date';
  return state[0].toUpperCase() + state.slice(1);
}

export default function Tasks() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const farmId = Array.isArray(id) ? id[0] : id;
  const { farmlands, addTask, updateTaskStatus } = useAppContext();
  const farm = farmlands.find(item => item.id === farmId);
  const [filter, setFilter] = useState<Filter>('all');
  const [title, setTitle] = useState('');
  const [dueDate, setDueDate] = useState('');
  const [formError, setFormError] = useState('');
  const tasks = farm?.tasks ?? [];
  const asOf = new Date();

  const visibleTasks = tasks
    .filter(task => {
      const state = getTaskScheduleState(task, asOf);
      if (filter === 'all') return true;
      if (filter === 'skipped') return state === 'skipped' || state === 'cancelled';
      return state === filter;
    })
    .sort((a, b) => {
      const order: Record<TaskScheduleState, number> = {
        overdue: 0,
        due: 1,
        upcoming: 2,
        unscheduled: 3,
        pending: 4,
        completed: 5,
        skipped: 6,
        cancelled: 7,
      };
      const stateDifference = order[getTaskScheduleState(a, asOf)] - order[getTaskScheduleState(b, asOf)];
      if (stateDifference !== 0) return stateDifference;
      return (a.dueAt ?? '').localeCompare(b.dueAt ?? '');
    });

  if (!farm || !farmId) {
    return <SafeAreaView style={styles.safe}><Text style={styles.empty}>Farm not found.</Text></SafeAreaView>;
  }

  const dueTodayCount = tasks.filter(task => getTaskScheduleState(task, asOf) === 'due').length;
  const overdueCount = tasks.filter(task => getTaskScheduleState(task, asOf) === 'overdue').length;
  const completedCount = tasks.filter(task => task.status === 'completed').length;

  const createTask = () => {
    const cleanTitle = title.trim();
    if (!cleanTitle) {
      setFormError('Add a task name before saving.');
      return;
    }

    let dueAt: string | null = null;
    if (dueDate.trim()) {
      const dateText = dueDate.trim();
      dueAt = taskDueAtForDhakaDate(dateText);
      if (!dueAt) {
        setFormError('Enter a valid due date.');
        return;
      }
    }

    addTask(farmId, cleanTitle, dueAt);
    setTitle('');
    setDueDate('');
    setFormError('');
  };

  return (
    <SafeAreaView style={styles.safe} edges={['bottom', 'left', 'right']}>
      <ScrollView contentContainerStyle={styles.container} keyboardShouldPersistTaps="handled">
        <View style={styles.heading}>
          <Text style={styles.eyebrow}>FARM BRAIN</Text>
          <Text style={styles.title}>Tasks</Text>
          <Text style={styles.subtitle}>Stay on top of what needs doing in {farm.name}.</Text>
        </View>

        <View style={styles.statsRow}>
          <Card style={styles.statCard}>
            <Text style={styles.statNumber}>{dueTodayCount}</Text>
            <Text style={styles.statLabel}>Due today</Text>
          </Card>
          <Card style={[styles.statCard, overdueCount > 0 && styles.overdueStat]}>
            <Text style={[styles.statNumber, overdueCount > 0 && styles.overdueText]}>{overdueCount}</Text>
            <Text style={styles.statLabel}>Overdue</Text>
          </Card>
          <Card style={styles.statCard}>
            <Text style={styles.statNumber}>{completedCount}</Text>
            <Text style={styles.statLabel}>Completed</Text>
          </Card>
        </View>

        <Card style={styles.addCard}>
          <Text style={styles.cardTitle}>Add a task</Text>
          <Input
            label="Task"
            placeholder="e.g. Check irrigation channels"
            value={title}
            onChangeText={setTitle}
            returnKeyType="done"
          />
          <Input
            label="Due date (optional)"
            placeholder="YYYY-MM-DD"
            value={dueDate}
            onChangeText={setDueDate}
            keyboardType="numbers-and-punctuation"
          />
          {formError ? <Text accessibilityRole="alert" style={styles.error}>{formError}</Text> : null}
          <Button title="Add task" onPress={createTask} />
        </Card>

        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.filters}>
          {FILTERS.map(option => (
            <TouchableOpacity
              key={option.id}
              accessibilityRole="button"
              accessibilityState={{ selected: filter === option.id }}
              onPress={() => setFilter(option.id)}
              style={[styles.filterChip, filter === option.id && styles.filterChipActive]}
            >
              <Text style={[styles.filterText, filter === option.id && styles.filterTextActive]}>
                {option.label}
              </Text>
            </TouchableOpacity>
          ))}
        </ScrollView>

        <View style={styles.listHeading}>
          <Text style={styles.cardTitle}>{filter === 'all' ? 'Your tasks' : FILTERS.find(item => item.id === filter)?.label}</Text>
          <Text style={styles.count}>{visibleTasks.length}</Text>
        </View>
        {visibleTasks.length === 0 ? (
          <Card><Text style={styles.empty}>No tasks in this view.</Text></Card>
        ) : visibleTasks.map(task => {
          const state = getTaskScheduleState(task, asOf);
          const isTerminal = task.status === 'completed' || task.status === 'skipped' || task.status === 'cancelled';
          return (
            <Card key={task.id} style={[styles.taskCard, state === 'overdue' && styles.overdueCard]}>
              <View style={styles.taskTopRow}>
                <View style={styles.taskCopy}>
                  <Text style={[styles.taskTitle, task.status === 'completed' && styles.completedTitle]}>
                    {task.title}
                  </Text>
                  {task.description ? <Text style={styles.description}>{task.description}</Text> : null}
                </View>
                <View style={[styles.statePill, state === 'overdue' && styles.overduePill, state === 'completed' && styles.completedPill]}>
                  <Text style={[styles.stateText, state === 'overdue' && styles.overdueText]}>{taskStateLabel(state)}</Text>
                </View>
              </View>
              <View style={styles.metadataRow}>
                <Text style={styles.metadata}>{formatDhakaDate(task.dueAt)}</Text>
                <Text style={styles.metadata}>{task.priority} priority · {task.source.replace('_', ' ')}</Text>
              </View>
              <View style={styles.actions}>
                {!isTerminal ? (
                  <>
                    <Button
                      title="Mark complete"
                      onPress={() => updateTaskStatus(farmId, task.id, 'completed')}
                      style={styles.actionButton}
                    />
                    <Button
                      title="Skip"
                      variant="outline"
                      onPress={() => updateTaskStatus(farmId, task.id, 'skipped')}
                      style={styles.actionButton}
                    />
                  </>
                ) : (
                  <Button
                    title="Reopen task"
                    variant="outline"
                    onPress={() => updateTaskStatus(farmId, task.id, 'pending')}
                    style={styles.actionButton}
                  />
                )}
              </View>
            </Card>
          );
        })}
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
  statsRow: { flexDirection: 'row', gap: SPACING.sm, marginBottom: SPACING.sm },
  statCard: { flex: 1, marginBottom: 0, paddingVertical: SPACING.md },
  overdueStat: { borderColor: '#f0caca', borderWidth: 1 },
  statNumber: { ...TYPOGRAPHY.h2, color: COLORS.primaryDark },
  statLabel: { ...TYPOGRAPHY.caption, marginTop: SPACING.xs },
  addCard: { marginTop: SPACING.md },
  cardTitle: { ...TYPOGRAPHY.h3 },
  filters: { gap: SPACING.xs, paddingVertical: SPACING.sm },
  filterChip: { minHeight: 38, justifyContent: 'center', paddingHorizontal: SPACING.md, borderWidth: 1, borderColor: COLORS.border, borderRadius: BORDER_RADIUS.round, backgroundColor: COLORS.surface },
  filterChipActive: { backgroundColor: COLORS.primary, borderColor: COLORS.primary },
  filterText: { ...TYPOGRAPHY.caption, color: COLORS.text, fontWeight: '600' },
  filterTextActive: { color: COLORS.surface },
  listHeading: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginVertical: SPACING.sm },
  count: { ...TYPOGRAPHY.caption, fontWeight: '700' },
  taskCard: { borderWidth: 1, borderColor: 'transparent' },
  overdueCard: { borderColor: '#edc2bd' },
  taskTopRow: { flexDirection: 'row', alignItems: 'flex-start', justifyContent: 'space-between', gap: SPACING.sm },
  taskCopy: { flex: 1 },
  taskTitle: { ...TYPOGRAPHY.h3 },
  completedTitle: { textDecorationLine: 'line-through', color: COLORS.textSecondary },
  description: { ...TYPOGRAPHY.bodySecondary, marginTop: SPACING.xs, lineHeight: 22 },
  statePill: { paddingHorizontal: SPACING.sm, paddingVertical: 5, borderRadius: BORDER_RADIUS.round, backgroundColor: '#e9f0e8' },
  overduePill: { backgroundColor: '#fae7e4' },
  completedPill: { backgroundColor: '#e8f2e8' },
  stateText: { ...TYPOGRAPHY.caption, color: COLORS.primaryDark, fontWeight: '700', textTransform: 'capitalize' },
  overdueText: { color: COLORS.error },
  metadataRow: { flexDirection: 'row', justifyContent: 'space-between', gap: SPACING.sm, marginTop: SPACING.md },
  metadata: { ...TYPOGRAPHY.caption, textTransform: 'capitalize' },
  actions: { flexDirection: 'row', gap: SPACING.sm, marginTop: SPACING.md },
  actionButton: { flex: 1, minHeight: 42 },
  error: { ...TYPOGRAPHY.caption, color: COLORS.error, marginBottom: SPACING.sm },
  empty: { ...TYPOGRAPHY.bodySecondary, textAlign: 'center', padding: SPACING.lg },
});
