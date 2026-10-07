import React, { useState } from 'react';
import {
  ImageBackground,
  KeyboardAvoidingView,
  Modal,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
  useWindowDimensions,
} from 'react-native';
import Svg, { Circle, Path, Rect } from 'react-native-svg';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Href, useLocalSearchParams, useRouter } from 'expo-router';
import { DashboardIcon } from '../../../components/dashboard-icons';
import { useAppContext } from '../../../context/AppProvider';
import type { Task, TaskScheduleState } from '../../../data/demo';
import { formatDhakaDate, getTaskScheduleState, taskDueAtForDhakaDate } from '../../../utils/task-dates';

const PAPER = '#fffdf7';
const INK = '#102b25';
const GREEN = '#07543a';
const MUTED = '#52677a';

type TaskTab = 'today' | 'upcoming' | 'completed';
type PreviewIcon = 'fertilizer' | 'weeds' | 'camera' | 'droplet' | 'leaf';

const NAV_ITEMS: { label: string }[] = [
  { label: 'Home' },
  { label: 'Tasks' },
  { label: 'Chat' },
  { label: 'Scan' },
  { label: 'Profile' },
];

function TaskGlyph({
  name,
  size = 20,
  color = GREEN,
}: {
  name: 'back' | 'calendar' | 'calendar-check' | 'check' | 'clock' | 'chevron' | 'droplet' | 'list-check' | 'plus' | 'alert' | 'chart' | 'info' | 'rain' | 'rice' | 'leaf' | 'home' | 'chat' | 'scan' | 'profile';
  size?: number;
  color?: string;
}) {
  const stroke = { fill: 'none', stroke: color, strokeWidth: 1.9, strokeLinecap: 'round' as const, strokeLinejoin: 'round' as const };

  return (
    <Svg width={size} height={size} viewBox="0 0 24 24" aria-hidden>
      {name === 'back' ? <Path d="m15 18-6-6 6-6" {...stroke} strokeWidth="2.1" /> : null}
      {name === 'chevron' ? <Path d="m9 5 7 7-7 7" {...stroke} strokeWidth="2.1" /> : null}
      {name === 'calendar' || name === 'calendar-check' ? <>
        <Rect x="3.5" y="5" width="17" height="16" rx="2.5" {...stroke} />
        <Path d="M7.5 3v4M16.5 3v4M4 9h16" {...stroke} />
        {name === 'calendar-check' ? <Path d="m9 14 2 2 4-4" {...stroke} strokeWidth="2.2" /> : null}
      </> : null}
      {name === 'list-check' ? <>
        <Path d="m3 7 1.5 1.5L7 6M10 7h11M3 16l1.5 1.5L7 15M10 16h11" {...stroke} />
      </> : null}
      {name === 'clock' ? <>
        <Circle cx="12" cy="12" r="9" {...stroke} />
        <Path d="M12 7v5l3.5 2" {...stroke} strokeWidth="2.1" />
      </> : null}
      {name === 'check' ? <Path d="m5 12.5 4.4 4.3L19.5 7" {...stroke} strokeWidth="2.8" /> : null}
      {name === 'droplet' ? <Path d="M12 3C9 7.3 5.7 10.5 5.7 14.3a6.3 6.3 0 0 0 12.6 0C18.3 10.5 15 7.3 12 3Z" {...stroke} /> : null}
      {name === 'rain' ? <>
        <Path d="M6.2 14.5h11.5a4.1 4.1 0 0 0 .2-8.2 6.1 6.1 0 0 0-11.5 1.1 3.6 3.6 0 0 0-.2 7.1Z" fill="#d8eef7" stroke={color} strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
        <Path d="m8 17.2-1 2.3m5-2.3-1 2.3m5-2.3-1 2.3" fill="none" stroke="#1776b5" strokeWidth="1.8" strokeLinecap="round" />
      </> : null}
      {name === 'rice' ? <Path d="M4 21h17M7 20c.4-7.3 2.1-11.8 6-16m-1.6 16c.8-7.7 3.2-12.5 7.6-16m-3.2 16c1.2-6.6 3.4-10.5 6.2-13" {...stroke} strokeWidth="2.4" /> : null}
      {name === 'leaf' ? <>
        <Path d="M5 20C6 9.5 12.5 4.5 20 4c-.5 7.8-5.8 14-15 16Z" fill={color} stroke={color} strokeWidth="1.1" strokeLinejoin="round" />
        <Path d="M6.2 19c3.5-3.6 7.2-7.5 12.3-12.3" fill="none" stroke="#eaf2e4" strokeWidth="1.2" strokeLinecap="round" />
      </> : null}
      {name === 'home' ? <Path d="m3 10 9-7 9 7v10a1 1 0 0 1-1 1h-5v-7h-6v7H4a1 1 0 0 1-1-1Z" {...stroke} strokeWidth="1.8" /> : null}
      {name === 'chat' ? <Path d="M5 5h14a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2h-8l-6 3v-5H5a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2Z" {...stroke} /> : null}
      {name === 'scan' ? <Path d="M8 3H5a2 2 0 0 0-2 2v3m13-5h3a2 2 0 0 1 2 2v3M3 16v3a2 2 0 0 0 2 2h3m8 0h3a2 2 0 0 0 2-2v-3" {...stroke} strokeWidth="2.4" /> : null}
      {name === 'profile' ? <>
        <Circle cx="12" cy="7.5" r="4" {...stroke} />
        <Path d="M4 21v-2a8 8 0 0 1 16 0v2Z" {...stroke} />
      </> : null}
      {name === 'plus' ? <Path d="M12 5v14M5 12h14" {...stroke} strokeWidth="2.2" /> : null}
      {name === 'alert' ? <>
        <Circle cx="12" cy="12" r="9" {...stroke} />
        <Path d="M12 7.5v5M12 16.5v.1" {...stroke} strokeWidth="2.2" />
      </> : null}
      {name === 'chart' ? <>
        <Path d="M4 20h17" {...stroke} />
        <Rect x="5" y="12" width="3" height="7" rx=".5" fill={color} />
        <Rect x="10.5" y="8" width="3" height="11" rx=".5" fill={color} />
        <Rect x="16" y="4" width="3" height="15" rx=".5" fill={color} />
      </> : null}
      {name === 'info' ? <>
        <Circle cx="12" cy="12" r="9" {...stroke} />
        <Path d="M12 11v5M12 8h.1" {...stroke} strokeWidth="2.2" />
      </> : null}
    </Svg>
  );
}

function taskIcon(title: string): PreviewIcon {
  const normalized = title.toLowerCase();
  if (/weed/.test(normalized)) return 'weeds';
  if (/photo|scan|check.?in|inspect/.test(normalized)) return 'camera';
  if (/water|irrigat|drain/.test(normalized)) return 'droplet';
  if (/disease|leaf|pest/.test(normalized)) return 'leaf';
  return 'fertilizer';
}

function isFinished(task: Task) {
  return task.status === 'completed' || task.status === 'skipped' || task.status === 'cancelled';
}

function getTaskStatusLabel(state: TaskScheduleState) {
  if (state === 'due') return 'Due today';
  if (state === 'upcoming') return 'Upcoming';
  if (state === 'overdue') return 'Overdue';
  if (state === 'unscheduled') return 'No due date';
  return state[0].toUpperCase() + state.slice(1);
}

export default function Tasks() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const farmId = Array.isArray(id) ? id[0] : id;
  const router = useRouter();
  const { width } = useWindowDimensions();
  const compact = width < 370;
  const { farmlands, addTask, updateTaskStatus } = useAppContext();
  const farm = farmlands.find(item => item.id === farmId);
  const [tab, setTab] = useState<TaskTab>('today');
  const [formOpen, setFormOpen] = useState(false);
  const [title, setTitle] = useState('');
  const [dueDate, setDueDate] = useState('');
  const [formError, setFormError] = useState('');
  const [taskError, setTaskError] = useState('');
  const [saving, setSaving] = useState(false);
  const now = new Date();
  const farmTasks = farm?.tasks ?? [];
  const todayTasks = farmTasks.filter(task => {
    const state = getTaskScheduleState(task, now);
    return task.status === 'pending' && (state === 'due' || state === 'overdue' || state === 'unscheduled');
  });
  const upcomingTasks = farmTasks.filter(task => task.status === 'pending' && getTaskScheduleState(task, now) === 'upcoming');
  const completedTasks = farmTasks.filter(isFinished);
  const todayCount = todayTasks.length;
  const upcomingCount = upcomingTasks.length;
  const completedCount = completedTasks.length;
  const visibleTasks = tab === 'today' ? todayTasks : tab === 'upcoming' ? upcomingTasks : completedTasks;

  const changeTaskStatus = async (task: Task, status: Task['status']) => {
    if (!farmId) return;
    setTaskError('');
    try {
      await updateTaskStatus(farmId, task.id, status);
    } catch (error) {
      setTaskError(error instanceof Error ? error.message : 'Could not update this task.');
    }
  };

  const createTask = async () => {
    const cleanTitle = title.trim();
    if (!cleanTitle) {
      setFormError('Add a task name before saving.');
      return;
    }
    if (!farm?.activeSeasonId) {
      setFormError('Start an active season in Crop Advisor before adding tasks.');
      return;
    }
    let dueAt: string | null = null;
    if (dueDate.trim()) {
      dueAt = taskDueAtForDhakaDate(dueDate.trim());
      if (!dueAt) {
        setFormError('Enter a valid due date.');
        return;
      }
    }

    setSaving(true);
    try {
      await addTask(farmId, cleanTitle, dueAt);
      const draft = { id: 'draft', title: cleanTitle, status: 'pending' as const, dueAt, priority: 'normal' as const, source: 'farmer' as const };
      setTab(getTaskScheduleState(draft, now) === 'upcoming' ? 'upcoming' : 'today');
      setFormOpen(false);
      setTitle('');
      setDueDate('');
      setFormError('');
    } catch (error) {
      setFormError(error instanceof Error ? error.message : 'Could not save this task.');
    } finally {
      setSaving(false);
    }
  };

  const navigateTo = (route: string) => {
    if (route === 'home') {
      router.replace('/farmlands' as Href);
      return;
    }
    if (route === 'profile') {
      router.push('/farmlands/profile-setup' as Href);
      return;
    }
    if (route === 'scan') route = 'crop-health';
    if (farmId) router.push(`/farmlands/${farmId}/${route}` as Href);
  };

  if (!farm || !farmId) {
    return <SafeAreaView style={styles.safe} edges={['bottom', 'left', 'right']}><Text style={styles.empty}>Farm not found.</Text></SafeAreaView>;
  }

  return (
    <SafeAreaView style={styles.safe} edges={['bottom', 'left', 'right']}>
      <View style={styles.frame}>
        <View style={[
          styles.header,
          Platform.OS === 'web' ? (compact ? styles.headerWebCompact : styles.headerWeb) : compact && styles.headerCompact,
        ]}>
          <Pressable
            accessibilityRole="button"
            accessibilityLabel="Back to farmland"
            onPress={() => router.replace(`/farmlands/${farmId}` as Href)}
            style={styles.headerButton}
          >
            <TaskGlyph name="back" size={23} color={GREEN} />
          </Pressable>
          <View style={styles.headerCopy}>
            <Text style={[styles.headerTitle, compact && styles.headerTitleCompact]}>Tasks</Text>
            <Text numberOfLines={1} style={[styles.headerSubtitle, compact && styles.headerSubtitleCompact]}>
              {farm.crop} · {farm.growthStage} · {farm.location ?? 'Location not set'}
            </Text>
          </View>
          <Pressable
            accessibilityRole="button"
            accessibilityLabel="Open season calendar"
            onPress={() => router.push(`/farmlands/${farmId}/season-plan` as Href)}
            style={styles.headerButton}
          >
            <TaskGlyph name="calendar-check" size={21} color={GREEN} />
          </Pressable>
        </View>

        <ScrollView
          style={styles.scroll}
          contentContainerStyle={[styles.content, compact && styles.contentCompact]}
          showsVerticalScrollIndicator={false}
          keyboardShouldPersistTaps="handled"
        >
          <View style={styles.summaryCard}>
            <View style={[styles.cropHero, compact && styles.cropHeroCompact]}>
              <ImageBackground
                source={require('../../../../assets/images/verification-rice-field.png')}
                resizeMode="cover"
                style={styles.cropPhoto}
                imageStyle={styles.cropPhotoAsset}
              >
                  <View style={[styles.cropCopy, compact && styles.cropCopyCompact]}>
                  <Text numberOfLines={1} style={[styles.cropName, compact && styles.cropNameCompact]}>{farm.crop}</Text>
                  <Text numberOfLines={1} style={[styles.growthStage, compact && styles.growthStageCompact]}>{farm.growthStage}</Text>
                  <View style={styles.farmMeta}>
                    <View style={styles.metaItem}>
                      <DashboardIcon name="location" size={15} color={GREEN} />
                      <Text numberOfLines={1} style={[styles.metaText, compact && styles.metaTextCompact]}>{farm.location ?? 'Location not set'}</Text>
                    </View>
                    <View style={styles.riceMark}><TaskGlyph name="rice" size={21} color={GREEN} /></View>
                    <Text style={[styles.metaText, compact && styles.metaTextCompact]}>{farm.acreage.toLocaleString(undefined, { maximumFractionDigits: 2 })} acres</Text>
                  </View>
                </View>
              </ImageBackground>
            </View>

            <View style={[styles.statsRow, compact && styles.statsRowCompact]}>
              <StatTile compact={compact} color="orange" icon="list-check" value={String(todayCount)} label="due today" />
              <StatTile compact={compact} color="green" icon="clock" value={String(upcomingCount)} label="upcoming" />
              <StatTile compact={compact} color="green" icon="check" value={String(completedCount)} label="completed" />
            </View>

          </View>

          <View style={[styles.segmented, compact && styles.segmentedCompact]} accessibilityRole="tablist">
            <SegmentButton title="Today" count={todayCount} selected={tab === 'today'} onPress={() => setTab('today')} />
            <SegmentButton title="Upcoming" count={upcomingCount} selected={tab === 'upcoming'} onPress={() => setTab('upcoming')} />
            <SegmentButton title="Completed" count={completedCount} selected={tab === 'completed'} onPress={() => setTab('completed')} />
          </View>

          <View style={styles.taskList}>
            {visibleTasks.map(task => (
              <TaskCard
                key={task.id}
                task={task}
                checked={isFinished(task)}
                compact={compact}
                onToggle={() => void changeTaskStatus(task, task.status === 'completed' ? 'pending' : 'completed')}
                onOpen={() => setTab(tab === 'today' ? 'upcoming' : tab)}
              />
            ))}
            {visibleTasks.length === 0 ? (
              <View style={styles.emptyCard}><Text style={styles.empty}>No tasks in this view.</Text></View>
            ) : null}
            {taskError ? <Text accessibilityRole="alert" style={styles.formError}>{taskError}</Text> : null}
          </View>

          {tab === 'today' ? (
            <View style={styles.upcomingSection}>
              <View style={styles.sectionHeading}>
                <Text style={[styles.sectionTitle, compact && styles.sectionTitleCompact]}>Upcoming tasks ({upcomingCount})</Text>
                <Pressable accessibilityRole="button" onPress={() => setTab('upcoming')} style={styles.seeAll}>
                  <Text style={styles.seeAllText}>See all</Text>
                  <TaskGlyph name="chevron" size={16} color="#314d61" />
                </Pressable>
              </View>
              {upcomingTasks.map(task => <UpcomingRow key={task.id} task={task} compact={compact} />)}
              {upcomingTasks.length === 0 ? <Text style={styles.empty}>No upcoming tasks.</Text> : null}
            </View>
          ) : null}

          <View style={styles.actionsRow}>
            <Pressable
              accessibilityRole="button"
              onPress={() => router.push(`/farmlands/${farmId}/season-plan` as Href)}
              style={[styles.actionButton, styles.calendarAction]}
            >
              <TaskGlyph name="calendar-check" size={22} color={GREEN} />
              <Text style={[styles.actionLabel, styles.calendarActionLabel, compact && styles.actionLabelCompact]}>Calendar view</Text>
            </Pressable>
            <Pressable accessibilityRole="button" onPress={() => setFormOpen(true)} style={[styles.actionButton, styles.addAction]}>
              <View style={styles.addCircle}><TaskGlyph name="plus" size={22} color="#fffdf7" /></View>
              <Text style={[styles.actionLabel, styles.addActionLabel, compact && styles.actionLabelCompact]}>Add task</Text>
            </Pressable>
          </View>
        </ScrollView>

        <View style={styles.bottomNav}>
          {NAV_ITEMS.map(item => {
            const selected = item.label === 'Tasks';
            return (
              <Pressable
                key={item.label}
                accessibilityRole="button"
                accessibilityLabel={item.label}
                accessibilityState={{ selected }}
                onPress={() => item.label === 'Tasks' ? setTab('today') : navigateTo(item.label.toLowerCase())}
                style={styles.navButton}
              >
                <View style={[styles.navIconWrap, selected && styles.navIconWrapSelected]}>
                  <TaskGlyph
                    name={item.label === 'Tasks' ? 'check' : item.label.toLowerCase() as 'home' | 'chat' | 'scan' | 'profile'}
                    size={selected ? 18 : 20}
                    color={selected ? '#fffdf7' : '#52677a'}
                  />
                </View>
                <Text style={[styles.navLabel, selected && styles.navLabelSelected]}>{item.label}</Text>
              </Pressable>
            );
          })}
        </View>
      </View>

      <Modal visible={formOpen} transparent animationType="fade" onRequestClose={() => setFormOpen(false)}>
        <KeyboardAvoidingView style={styles.modalBackdrop} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
          <View style={styles.formCard}>
            <View style={styles.formHeading}>
              <Text style={styles.formTitle}>Add a task</Text>
              <Pressable accessibilityRole="button" accessibilityLabel="Close" onPress={() => setFormOpen(false)} style={styles.closeButton}>
                <Text style={styles.closeText}>×</Text>
              </Pressable>
            </View>
            <Text style={styles.inputLabel}>Task name</Text>
            <TextInput
              accessibilityLabel="Task name"
              value={title}
              onChangeText={setTitle}
              placeholder="e.g. Check irrigation channels"
              placeholderTextColor="#89949c"
              returnKeyType="done"
              style={styles.input}
            />
            <Text style={styles.inputLabel}>Due date (optional)</Text>
            <TextInput
              accessibilityLabel="Due date"
              value={dueDate}
              onChangeText={setDueDate}
              placeholder="YYYY-MM-DD"
              placeholderTextColor="#89949c"
              keyboardType="numbers-and-punctuation"
              style={styles.input}
            />
            {formError ? <Text accessibilityRole="alert" style={styles.formError}>{formError}</Text> : null}
            <Pressable accessibilityRole="button" disabled={saving} onPress={() => void createTask()} style={[styles.saveButton, saving && styles.saveButtonDisabled]}>
              <Text style={styles.saveButtonText}>{saving ? 'Saving…' : 'Save task'}</Text>
            </Pressable>
          </View>
        </KeyboardAvoidingView>
      </Modal>
    </SafeAreaView>
  );
}

function StatTile({
  color,
  icon,
  value,
  label,
  compact,
}: {
  color: 'orange' | 'green';
  icon: 'list-check' | 'clock' | 'check';
  value: string;
  label: string;
  compact: boolean;
}) {
  const orange = color === 'orange';
  return (
    <View style={[styles.statTile, compact && styles.statTileCompact, orange ? styles.statOrange : styles.statGreen]}>
      <View style={[styles.statIconCircle, orange ? styles.statIconOrange : styles.statIconGreen]}>
        <TaskGlyph name={icon} size={23} color={orange ? '#d85900' : GREEN} />
      </View>
      <View style={styles.statCopy}>
        <Text style={[styles.statValue, orange && styles.statValueOrange]}>{value}</Text>
        <Text style={[styles.statLabel, orange && styles.statLabelOrange]}>{label}</Text>
      </View>
    </View>
  );
}

function SegmentButton({
  title,
  count,
  selected,
  onPress,
}: {
  title: string;
  count: number;
  selected: boolean;
  onPress: () => void;
}) {
  return (
    <Pressable
      accessibilityRole="tab"
      accessibilityState={{ selected }}
      onPress={onPress}
      style={[styles.segment, selected && styles.segmentSelected]}
    >
      <Text style={[styles.segmentText, selected && styles.segmentTextSelected]}>{title} ({count})</Text>
    </Pressable>
  );
}

function TaskCard({
  task,
  checked,
  compact,
  onToggle,
  onOpen,
}: {
  task: Task;
  checked: boolean;
  compact: boolean;
  onToggle: () => void;
  onOpen: () => void;
}) {
  const priority = task.priority === 'high' || task.priority === 'urgent'
    ? { background: '#ffe3e3', foreground: '#cf1b17', icon: 'alert' as const }
    : task.priority === 'normal'
      ? { background: '#fff0d2', foreground: '#d67700', icon: 'chart' as const }
      : { background: '#e3f2fc', foreground: '#1765ca', icon: 'info' as const };
  const state = getTaskScheduleState(task, new Date());
  const icon = taskIcon(task.title);
  return (
    <View style={[styles.taskCard, compact && styles.taskCardCompact]}>
      <View style={styles.taskIconCircle}>
        {icon === 'droplet' || icon === 'leaf'
          ? <TaskGlyph name={icon} size={22} color={GREEN} />
          : <DashboardIcon name={icon} size={23} color={GREEN} />}
      </View>
      <View style={styles.taskBody}>
        <Text numberOfLines={1} style={[styles.taskTitle, compact && styles.taskTitleCompact]}>{task.title}</Text>
        {task.description ? <Text numberOfLines={2} style={[styles.taskDescription, compact && styles.taskDescriptionCompact]}>{task.description}</Text> : null}
        <View style={styles.badgesRow}>
          <View style={[styles.badge, { backgroundColor: priority.background }]}>
            <TaskGlyph name={priority.icon} size={14} color={priority.foreground} />
            <Text style={[styles.badgeText, { color: priority.foreground }]}>{task.priority} priority</Text>
          </View>
          <View style={styles.dueBadge}>
            <TaskGlyph name="calendar-check" size={14} color="#d43919" />
            <Text style={styles.dueBadgeText}>{getTaskStatusLabel(state)}</Text>
          </View>
        </View>
      </View>
      <View style={styles.taskActions}>
        <Pressable
          accessibilityRole="checkbox"
          accessibilityLabel={`Mark ${task.title} ${checked ? 'incomplete' : 'complete'}`}
          accessibilityState={{ checked }}
          onPress={onToggle}
          style={[styles.checkbox, checked && styles.checkboxChecked]}
        >
          {checked ? <TaskGlyph name="check" size={17} color="#fffdf7" /> : null}
        </Pressable>
        <Pressable accessibilityRole="button" accessibilityLabel={`Open ${task.title}`} onPress={onOpen} style={styles.chevronButton}>
          <TaskGlyph name="chevron" size={18} color="#435b6d" />
        </Pressable>
      </View>
    </View>
  );
}

function UpcomingRow({ task, compact }: { task: Task; compact: boolean }) {
  const icon = taskIcon(task.title);
  return (
    <Pressable accessibilityRole="button" style={[styles.upcomingRow, compact && styles.upcomingRowCompact]}>
      <View style={styles.upcomingIconCircle}>{icon === 'leaf' || icon === 'droplet' ? <TaskGlyph name={icon} size={20} color={GREEN} /> : <DashboardIcon name={icon} size={20} color={GREEN} />}</View>
      <View style={styles.upcomingCopy}>
        <Text numberOfLines={1} style={styles.upcomingTitle}>{task.title}</Text>
        <Text numberOfLines={1} style={styles.upcomingDescription}>{task.description ?? 'Scheduled farm task'}</Text>
      </View>
      <View style={styles.upcomingTrailing}>
        <View style={[styles.upcomingDate, compact && styles.upcomingDateCompact]}>
          <TaskGlyph name="calendar-check" size={13} color="#d43919" />
          <Text numberOfLines={1} style={styles.upcomingDateText}>{formatDhakaDate(task.dueAt)}</Text>
        </View>
      </View>
      <TaskGlyph name="chevron" size={16} color="#435b6d" />
    </Pressable>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: PAPER },
  frame: { flex: 1, width: '100%', maxWidth: 480, alignSelf: 'center', backgroundColor: PAPER },
  header: { height: 62, paddingHorizontal: 12, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 8 },
  headerWeb: { height: 82, paddingTop: 20 },
  headerCompact: { height: 58, paddingHorizontal: 9, gap: 6 },
  headerWebCompact: { height: 78, paddingTop: 20, paddingHorizontal: 9, gap: 6 },
  headerButton: { width: 34, height: 34, flexShrink: 0, borderRadius: 18, backgroundColor: '#edf2e7', alignItems: 'center', justifyContent: 'center' },
  headerCopy: { flex: 1, minWidth: 0, alignItems: 'center', justifyContent: 'center' },
  headerTitle: { color: '#080f0e', fontFamily: 'Georgia', fontWeight: '700', fontSize: 22, lineHeight: 25, letterSpacing: -0.5 },
  headerTitleCompact: { fontSize: 20, lineHeight: 23 },
  headerSubtitle: { marginTop: 2, color: MUTED, fontFamily: 'Arial', fontSize: 11.7, lineHeight: 15, textAlign: 'center' },
  headerSubtitleCompact: { fontSize: 9.8, lineHeight: 12 },
  scroll: { flex: 1, minHeight: 0 },
  content: { paddingHorizontal: 10, paddingTop: 1, paddingBottom: 5, gap: 7 },
  contentCompact: { paddingHorizontal: 8, gap: 6 },
  summaryCard: { overflow: 'hidden', paddingBottom: 5, borderRadius: 17, borderWidth: 1, borderColor: '#f2efe7', backgroundColor: '#fffefa', boxShadow: '0px 3px 10px rgba(30, 54, 37, 0.08)', elevation: 2 },
  cropHero: { height: 78, overflow: 'hidden' },
  cropHeroCompact: { height: 74 },
  cropPhoto: { flex: 1, justifyContent: 'center' },
  cropPhotoAsset: { width: '100%', height: '100%' },
  cropCopy: { position: 'absolute', left: 0, top: 0, bottom: 0, width: '54%', paddingLeft: 8, paddingVertical: 6, justifyContent: 'center', borderTopRightRadius: 30, borderBottomRightRadius: 28, backgroundColor: 'rgba(255,253,247,0.97)' },
  cropCopyCompact: { width: '64%' },
  cropName: { color: '#111418', fontFamily: 'Georgia', fontSize: 27, lineHeight: 30, fontWeight: '700', letterSpacing: -0.8 },
  cropNameCompact: { fontSize: 23, lineHeight: 26 },
  growthStage: { color: '#111b1e', fontFamily: 'Georgia', fontSize: 13.5, lineHeight: 16, fontWeight: '700', letterSpacing: -0.2 },
  growthStageCompact: { fontSize: 11.7, lineHeight: 14 },
  farmMeta: { flexDirection: 'row', alignItems: 'center', gap: 4, marginTop: 2 },
  metaItem: { flexDirection: 'row', alignItems: 'center', gap: 3 },
  metaText: { color: '#31475a', fontFamily: 'Arial', fontSize: 10.5, lineHeight: 13 },
  metaTextCompact: { fontSize: 9.4, lineHeight: 12 },
  riceMark: { width: 19, height: 19, alignItems: 'center', justifyContent: 'center', marginLeft: 3 },
  statsRow: { flexDirection: 'row', gap: 5, marginHorizontal: 5, marginTop: 4 },
  statsRowCompact: { gap: 4, marginHorizontal: 4 },
  statTile: { flex: 1, height: 46, minWidth: 0, flexDirection: 'row', alignItems: 'center', gap: 5, paddingHorizontal: 6, borderRadius: 11 },
  statTileCompact: { height: 42 },
  statOrange: { backgroundColor: '#fff0dc' },
  statGreen: { backgroundColor: '#eff4e9' },
  statIconCircle: { width: 34, height: 34, flexShrink: 0, borderRadius: 18, alignItems: 'center', justifyContent: 'center' },
  statIconOrange: { backgroundColor: '#ffead0' },
  statIconGreen: { backgroundColor: '#e5efde' },
  statCopy: { flex: 1, minWidth: 0 },
  statValue: { color: '#111916', fontFamily: 'Georgia', fontWeight: '700', fontSize: 20, lineHeight: 21 },
  statValueOrange: { color: '#131512' },
  statLabel: { color: '#355268', fontFamily: 'Arial', fontSize: 10, lineHeight: 12 },
  statLabelOrange: { color: '#c94218' },
  rainNotice: { height: 27, marginHorizontal: 5, marginTop: 5, paddingHorizontal: 7, flexDirection: 'row', alignItems: 'center', gap: 7, borderRadius: 11, backgroundColor: '#d9edf8' },
  rainNoticeText: { flex: 1, color: '#2e5977', fontFamily: 'Arial', fontSize: 11.5, lineHeight: 15 },
  rainNoticeTextCompact: { fontSize: 10.5 },
  segmented: { height: 28, padding: 1.5, flexDirection: 'row', alignItems: 'stretch', borderWidth: 1, borderColor: '#e4e3db', borderRadius: 16, backgroundColor: '#fffefa' },
  segmentedCompact: { height: 29 },
  segment: { flex: 1, alignItems: 'center', justifyContent: 'center', borderRadius: 15 },
  segmentSelected: { backgroundColor: '#004a34' },
  segmentText: { color: '#344f64', fontFamily: 'Arial', fontSize: 11.7, lineHeight: 15 },
  segmentTextSelected: { color: '#fffdf7', fontWeight: '600' },
  taskList: { gap: 5 },
  taskCard: { minHeight: 80, paddingHorizontal: 6, paddingVertical: 5, flexDirection: 'row', alignItems: 'center', gap: 9, borderRadius: 15, borderWidth: 1, borderColor: '#f0eee6', backgroundColor: '#fffefa', boxShadow: '0px 2px 8px rgba(30, 54, 37, 0.06)', elevation: 1 },
  taskCardCompact: { minHeight: 76, paddingHorizontal: 5, gap: 6 },
  taskIconCircle: { width: 40, height: 40, flexShrink: 0, borderRadius: 22, alignItems: 'center', justifyContent: 'center', backgroundColor: '#eaf2e4' },
  taskBody: { flex: 1, minWidth: 0, justifyContent: 'center' },
  taskTitle: { color: '#11191a', fontFamily: 'Arial', fontWeight: '700', fontSize: 14.2, lineHeight: 18 },
  taskTitleCompact: { fontSize: 12.6, lineHeight: 16 },
  taskDescription: { color: '#4d6277', fontFamily: 'Arial', fontSize: 11.3, lineHeight: 14 },
  taskDescriptionCompact: { fontSize: 10.3, lineHeight: 12.5 },
  badgesRow: { flexDirection: 'row', alignItems: 'center', gap: 6, marginTop: 3 },
  badge: { minHeight: 20, paddingHorizontal: 6, flexDirection: 'row', alignItems: 'center', gap: 4, borderRadius: 12 },
  badgeText: { fontFamily: 'Arial', fontSize: 10, lineHeight: 13, fontWeight: '600' },
  dueBadge: { minHeight: 20, paddingHorizontal: 6, flexDirection: 'row', alignItems: 'center', gap: 4, borderRadius: 12, backgroundColor: '#fff0dc' },
  dueBadgeText: { color: '#c8401c', fontFamily: 'Arial', fontSize: 10, lineHeight: 13 },
  taskActions: { width: 27, height: 57, flexShrink: 0, alignItems: 'center', justifyContent: 'space-between', paddingVertical: 2 },
  checkbox: { width: 17, height: 17, alignItems: 'center', justifyContent: 'center', borderWidth: 1.5, borderColor: '#536d82', borderRadius: 4, backgroundColor: '#fffefa' },
  checkboxChecked: { borderColor: GREEN, backgroundColor: GREEN },
  chevronButton: { width: 20, height: 23, alignItems: 'center', justifyContent: 'center' },
  actualDate: { color: MUTED, fontFamily: 'Arial', fontSize: 9.5, lineHeight: 12, marginTop: 2 },
  weatherCard: { height: 74, overflow: 'hidden', borderRadius: 14, backgroundColor: '#b9dceb', boxShadow: '0px 2px 8px rgba(30, 54, 37, 0.07)', elevation: 1 },
  weatherCardCompact: { height: 68 },
  weatherImage: { flex: 1, flexDirection: 'row', alignItems: 'center', paddingHorizontal: 8, gap: 6 },
  weatherImageAsset: { width: '100%', height: '100%', opacity: 0.92 },
  weatherWash: { ...StyleSheet.absoluteFill, backgroundColor: 'rgba(180, 220, 238, 0.46)' },
  weatherCopy: { flex: 1, minWidth: 0, alignSelf: 'stretch', justifyContent: 'center', paddingRight: 96, paddingBottom: 3 },
  weatherTitle: { color: '#11191a', fontFamily: 'Arial', fontWeight: '700', fontSize: 13.1, lineHeight: 17 },
  weatherDescription: { color: '#274b63', fontFamily: 'Arial', fontSize: 10.6, lineHeight: 14, paddingRight: 2 },
  forecastButton: { position: 'absolute', right: 8, bottom: 9, minWidth: 108, height: 29, paddingHorizontal: 8, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 3, borderRadius: 17, backgroundColor: '#004b35' },
  forecastButtonCompact: { minWidth: 94, right: 6, paddingHorizontal: 7 },
  forecastLabel: { color: '#fffdf7', fontFamily: 'Arial', fontSize: 10.5, lineHeight: 13, fontWeight: '600' },
  forecastLabelCompact: { fontSize: 9.7 },
  upcomingSection: { gap: 4 },
  sectionHeading: { minHeight: 20, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  sectionTitle: { color: '#131817', fontFamily: 'Arial', fontWeight: '700', fontSize: 14.5, lineHeight: 19 },
  sectionTitleCompact: { fontSize: 13 },
  seeAll: { flexDirection: 'row', alignItems: 'center', gap: 2 },
  seeAllText: { color: '#223e52', fontFamily: 'Arial', fontSize: 11.5, lineHeight: 15 },
  upcomingRow: { minHeight: 37, paddingHorizontal: 5, flexDirection: 'row', alignItems: 'center', gap: 6, borderRadius: 14, borderWidth: 1, borderColor: '#f0eee6', backgroundColor: '#fffefa', boxShadow: '0px 2px 7px rgba(30, 54, 37, 0.05)', elevation: 1 },
  upcomingRowCompact: { minHeight: 36, gap: 4, paddingHorizontal: 4 },
  upcomingIconCircle: { width: 31, height: 31, flexShrink: 0, borderRadius: 18, alignItems: 'center', justifyContent: 'center', backgroundColor: '#eaf2e4' },
  upcomingCopy: { flex: 1, minWidth: 0 },
  upcomingTitle: { color: '#11191a', fontFamily: 'Arial', fontWeight: '700', fontSize: 11.8, lineHeight: 14 },
  upcomingDescription: { color: '#52677a', fontFamily: 'Arial', fontSize: 9.6, lineHeight: 12 },
  upcomingTrailing: { alignItems: 'flex-end', justifyContent: 'center', gap: 1 },
  upcomingDate: { minHeight: 23, maxWidth: 125, paddingHorizontal: 6, flexDirection: 'row', alignItems: 'center', gap: 4, borderRadius: 13, backgroundColor: '#fff0dc' },
  upcomingDateCompact: { maxWidth: 100, paddingHorizontal: 4, gap: 2 },
  upcomingDateText: { color: '#c8401c', fontFamily: 'Arial', fontSize: 9.5, lineHeight: 12 },
  linkedIssue: { color: '#50647a', fontFamily: 'Arial', fontSize: 8.8, lineHeight: 11 },
  actionsRow: { minHeight: 36, flexDirection: 'row', gap: 6, marginTop: 1 },
  actionButton: { flex: 1, height: 36, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 7, borderRadius: 12 },
  calendarAction: { borderWidth: 1, borderColor: GREEN, backgroundColor: '#fffefa' },
  calendarActionLabel: { color: GREEN },
  addAction: { backgroundColor: '#004b35' },
  addCircle: { width: 23, height: 23, alignItems: 'center', justifyContent: 'center', borderWidth: 1.5, borderColor: '#fffdf7', borderRadius: 13 },
  actionLabel: { fontFamily: 'Arial', fontSize: 13.2, lineHeight: 17, fontWeight: '600' },
  actionLabelCompact: { fontSize: 11.5 },
  addActionLabel: { color: '#fffdf7' },
  bottomNav: { height: 52, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-around', borderTopWidth: 1, borderTopColor: '#ece9df', backgroundColor: 'rgba(255,254,250,0.98)' },
  navButton: { flex: 1, height: 48, alignItems: 'center', justifyContent: 'center', gap: 1 },
  navIconWrap: { minWidth: 30, height: 26, paddingHorizontal: 5, borderRadius: 7, alignItems: 'center', justifyContent: 'center' },
  navIconWrapSelected: { backgroundColor: GREEN },
  navLabel: { color: '#52677a', fontFamily: 'Arial', fontSize: 9.3, lineHeight: 12 },
  navLabelSelected: { color: INK, fontWeight: '700' },
  empty: { color: MUTED, fontFamily: 'Arial', fontSize: 14, textAlign: 'center', padding: 24 },
  emptyCard: { borderRadius: 13, backgroundColor: '#fffefa' },
  modalBackdrop: { flex: 1, justifyContent: 'center', paddingHorizontal: 18, backgroundColor: 'rgba(12, 30, 23, 0.42)' },
  formCard: { width: '100%', maxWidth: 420, alignSelf: 'center', padding: 18, borderRadius: 18, backgroundColor: PAPER, boxShadow: '0px 8px 24px rgba(0, 0, 0, 0.2)', elevation: 8 },
  formHeading: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginBottom: 11 },
  formTitle: { color: INK, fontFamily: 'Georgia', fontSize: 20, lineHeight: 24, fontWeight: '700' },
  closeButton: { width: 30, height: 30, alignItems: 'center', justifyContent: 'center', borderRadius: 16, backgroundColor: '#edf2e7' },
  closeText: { color: GREEN, fontFamily: 'Arial', fontSize: 23, lineHeight: 25 },
  inputLabel: { color: INK, fontFamily: 'Arial', fontSize: 12, lineHeight: 15, fontWeight: '600', marginTop: 8, marginBottom: 5 },
  input: { height: 42, paddingHorizontal: 11, borderWidth: 1, borderColor: '#dfe6dc', borderRadius: 10, backgroundColor: '#fffefa', color: INK, fontFamily: 'Arial', fontSize: 14 },
  formError: { color: '#b42318', fontFamily: 'Arial', fontSize: 12, marginTop: 7 },
  saveButton: { height: 42, alignItems: 'center', justifyContent: 'center', marginTop: 15, borderRadius: 12, backgroundColor: GREEN },
  saveButtonDisabled: { opacity: 0.65 },
  saveButtonText: { color: '#fffdf7', fontFamily: 'Arial', fontSize: 14, fontWeight: '700' },
});
