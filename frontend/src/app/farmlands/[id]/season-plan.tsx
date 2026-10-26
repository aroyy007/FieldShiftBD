import React, { useEffect, useState } from 'react';
import { ImageBackground, Pressable, ScrollView, StyleSheet, Text, View, useWindowDimensions } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Href, useLocalSearchParams, useRouter } from 'expo-router';
import { DashboardIcon, DashboardIconName } from '../../../components/dashboard-icons';
import { FarmBottomNavigation, FarmChromeIcon } from '../../../components/farmland-mobile-ui';
import { FarmProfileIcon, FarmProfileIconName } from '../../../components/farm-profile-icons';
import { useAppContext } from '../../../context/AppProvider';
import { apiRequest } from '../../../services/api-client';
import { formatDhakaDate, getTaskScheduleState } from '../../../utils/task-dates';

const PAPER = '#fffdf7';
const INK = '#111916';
const GREEN = '#07543a';
const MUTED = '#52677a';

type PlanGlyphName = DashboardIconName | FarmProfileIconName;

type WeatherAssessment = { alerts: { title: string; message: string; recommended_action: string }[] };

function taskGlyph(title: string): PlanGlyphName {
  const lower = title.toLowerCase();
  if (/water|irrigat|drain/.test(lower)) return 'drop';
  if (/weed/.test(lower)) return 'weeds';
  if (/fertili|urea|nitrogen/.test(lower)) return 'fertilizer';
  if (/scan|photo|check-in|check in/.test(lower)) return 'camera';
  return 'tasks';
}

export default function SeasonPlan() {
  const params = useLocalSearchParams<{ id?: string | string[] }>();
  const farmId = Array.isArray(params.id) ? params.id[0] : params.id;
  const { farmlands } = useAppContext();
  const farm = farmlands.find(item => item.id === farmId);
  const router = useRouter();
  const { width } = useWindowDimensions();
  const compact = width < 420;
  const weeklyPlan = farm?.tasks.filter(task => task.status === 'pending').slice(0, 3) ?? [];
  const milestones = [
    ...(farm?.problems.filter(problem => problem.status === 'open' || problem.status === 'monitoring').map(problem => ({
      id: problem.id, title: problem.category, note: problem.description, icon: 'leaf' as PlanGlyphName,
      date: new Date(problem.createdAt).toLocaleDateString(), urgent: problem.severity === 'high' || problem.severity === 'critical',
      linked: `${problem.severity} · ${problem.status}`, route: 'problems',
    })) ?? []),
    ...(farm?.tasks.filter(task => task.status === 'pending').slice(3).map(task => ({
      id: task.id, title: task.title, note: task.description ?? 'Scheduled farm task', icon: taskGlyph(task.title),
      date: task.dueAt ? formatDhakaDate(task.dueAt) : 'No due date', urgent: task.priority === 'high' || task.priority === 'urgent',
      linked: undefined, route: 'tasks',
    })) ?? []),
  ].slice(0, 3);
  const [weather, setWeather] = useState<WeatherAssessment | null>(null);
  const [weatherError, setWeatherError] = useState('');
  const go = (route: string) => farmId && router.push(`/farmlands/${farmId}/${route}` as Href);

  useEffect(() => {
    if (!farmId) return;
    let active = true;
    apiRequest<WeatherAssessment>(`/weather/assessment/${encodeURIComponent(farmId)}`)
      .then(result => { if (active) { setWeather(result); setWeatherError(''); } })
      .catch(error => { if (active) { setWeather(null); setWeatherError(error instanceof Error ? error.message : 'Weather assessment is unavailable.'); } });
    return () => { active = false; };
  }, [farmId]);

  if (!farm || !farmId) {
    return <SafeAreaView style={styles.safe} edges={['bottom', 'left', 'right']}><Text style={styles.empty}>Farm not found.</Text></SafeAreaView>;
  }

  return (
    <SafeAreaView style={styles.safe} edges={['bottom', 'left', 'right']}>
      <View style={styles.frame}>
        <View style={[styles.header, compact && styles.headerCompact]}>
          <Pressable accessibilityRole="button" accessibilityLabel="Back to farm overview" onPress={() => router.replace(`/farmlands/${farmId}` as Href)} style={styles.headerButton}>
            <FarmChromeIcon name="back" size={23} color={GREEN} />
          </Pressable>
          <View style={styles.headerCopy}>
            <Text style={styles.headerTitle}>Season Plan</Text>
            <Text numberOfLines={1} style={[styles.headerSubtitle, compact && styles.headerSubtitleCompact]}>{farm.crop} · {farm.growthStage} · {farm.location}</Text>
          </View>
          <Pressable accessibilityRole="button" accessibilityLabel="Open calendar and tasks" onPress={() => go('tasks')} style={[styles.headerButton, styles.calendarButton]}>
            <DashboardIcon name="calendar" size={21} color={GREEN} />
          </Pressable>
        </View>

        <ScrollView style={styles.scroll} contentContainerStyle={[styles.content, compact && styles.contentCompact]} showsVerticalScrollIndicator={false}>
          <View style={[styles.hero, compact && styles.heroCompact]}>
            <ImageBackground source={require('../../../../assets/images/verification-rice-field.png')} resizeMode="cover" style={styles.heroPhoto} imageStyle={styles.heroImage}>
              <View style={styles.heroCopy}>
                <View style={styles.activePill}><FarmProfileIcon name="leaf" size={17} color={GREEN} /><Text style={styles.activeText}>{farm.activeSeasonId ? 'Active plan' : 'No active season'}</Text></View>
                <Text numberOfLines={1} style={[styles.cropName, compact && styles.cropNameCompact]}>{farm.crop}</Text>
                <Text style={styles.cropSubtitle}>{farm.growthStage}</Text>
                <View style={styles.locationRow}>
                  <DashboardIcon name="location" size={16} color={GREEN} />
                  <Text numberOfLines={1} style={styles.locationText}>{farm.location}</Text>
                  <View style={styles.metaDivider} />
                  <DashboardIcon name="acreage" size={17} color={GREEN} />
                  <Text style={styles.locationText}>{farm.acreage.toFixed(1)} acres</Text>
                </View>
                <Text style={styles.focusText}><Text style={styles.focusStrong}>Current focus: </Text>{farm.activeSeasonId ? `${weeklyPlan.length} pending tasks · ${farm.problems.filter(problem => problem.status === 'open' || problem.status === 'monitoring').length} open issues.` : 'Choose a crop in Crop Advisor to start a season.'}</Text>
              </View>
            </ImageBackground>
          </View>

          <View style={styles.sectionCard}>
            <View style={styles.sectionHeading}>
              <Text style={[styles.sectionTitle, compact && styles.sectionTitleCompact]}>Season timeline</Text>
              <Text style={styles.weekCounter}>{farm.daysSincePlanting == null ? 'Season timeline' : `Week ${Math.floor(farm.daysSincePlanting / 7) + 1} · ${farm.seasonProgressPercent ?? 0}%`}</Text>
            </View>
            <View style={styles.stageTrack}>
              <View style={styles.trackLine} />
              <View style={styles.trackProgress} />
              {farm.seasonPlan.map((stage, index) => (
                <View key={stage.id} style={styles.stageColumn}>
                  <View style={[styles.stageIconCircle, compact && styles.stageIconCompact]}>
                    <PlanGlyph name={stage.name.toLowerCase().includes('harvest') ? 'chart' : taskGlyph(stage.name)} size={compact ? 20 : 22} color={GREEN} />
                  </View>
                  <View style={[styles.stageDot, stage.status === 'current' && styles.stageDotCurrent, stage.status === 'completed' && styles.stageDotCurrent]} />
                  <Text numberOfLines={1} style={[styles.stageName, stage.status === 'current' && styles.stageNameCurrent, compact && styles.stageNameCompact]}>{stage.name}</Text>
                  <Text numberOfLines={1} style={[styles.stageDate, compact && styles.stageDateCompact]}>{stage.dateRange}</Text>
                  {stage.status === 'current' ? <View style={styles.currentPill}><Text style={styles.currentPillText}>Active</Text></View> : <View style={styles.currentPillSpacer} />}
                </View>
              ))}
              {farm.seasonPlan.length === 0 ? <Text style={styles.empty}>No growth stages are available for this farm.</Text> : null}
            </View>
          </View>

          <View style={styles.sectionCard}>
            <Text style={[styles.sectionTitle, styles.cardTitle, compact && styles.sectionTitleCompact]}>This week’s plan</Text>
            {weeklyPlan.map((item, index) => (
              <Pressable key={item.id} accessibilityRole="button" onPress={() => go('tasks')} style={[styles.planRow, index === weeklyPlan.length - 1 && styles.lastRow]}>
                <View style={styles.rowIconCircle}><PlanGlyph name={taskGlyph(item.title)} size={21} color={GREEN} /></View>
                <View style={styles.rowCopy}>
                  <Text numberOfLines={1} style={styles.rowTitle}>{item.title}</Text>
                  <Text numberOfLines={1} style={[styles.rowNote, compact && styles.rowNoteCompact]}>{item.description ?? 'Scheduled farm task'}</Text>
                </View>
                <View style={[styles.statusPill, item.priority === 'high' || item.priority === 'urgent' ? styles.duePill : styles.plannedPill]}><Text numberOfLines={1} style={[styles.statusText, item.priority === 'high' || item.priority === 'urgent' ? styles.dueText : styles.plannedText]}>{getTaskScheduleState(item, new Date())}</Text></View>
                <DashboardIcon name="chevron" size={18} color={MUTED} />
              </Pressable>
            ))}
            {weeklyPlan.length === 0 ? <Text style={styles.empty}>No pending tasks in this season.</Text> : null}
          </View>

          <Pressable accessibilityRole="button" accessibilityLabel="View weather forecast" onPress={() => go('alerts')} style={[styles.weatherCard, compact && styles.weatherCompact]}>
            <ImageBackground source={require('../../../../assets/images/assistant-rain-field.png')} resizeMode="cover" style={styles.weatherImage} imageStyle={styles.weatherImageStyle}>
              <View style={styles.weatherWash} />
              <DashboardIcon name="rain" size={38} color="#21648c" />
              <View style={styles.weatherCopy}>
                <Text style={styles.weatherTitle}>{weather?.alerts[0]?.title ?? (weatherError ? 'Weather assessment unavailable' : 'Weather update')}</Text>
                <Text numberOfLines={3} style={styles.weatherDescription}>{weather?.alerts[0] ? `${weather.alerts[0].message} ${weather.alerts[0].recommended_action}` : weatherError || 'No actionable weather adjustment is currently returned for this farm.'}</Text>
              </View>
              <View style={styles.weatherAction}><Text style={styles.weatherActionText}>View forecast</Text><DashboardIcon name="chevron" size={16} color={PAPER} /></View>
            </ImageBackground>
          </Pressable>

          <View style={styles.sectionCard}>
            <Text style={[styles.sectionTitle, styles.cardTitle, compact && styles.sectionTitleCompact]}>Upcoming milestones</Text>
            {milestones.map((item, index) => (
              <Pressable key={item.id} accessibilityRole="button" onPress={() => go(item.route)} style={[styles.milestoneRow, index === milestones.length - 1 && styles.lastRow]}>
                <View style={styles.milestoneIconCircle}><PlanGlyph name={item.icon} size={20} color={GREEN} /></View>
                <View style={styles.milestoneCopy}>
                  <Text numberOfLines={1} style={[styles.rowTitle, compact && styles.milestoneTitleCompact]}>{item.title}</Text>
                  <Text numberOfLines={1} style={styles.milestoneNote}>{item.note}</Text>
                  {item.linked ? <Text style={styles.linkedNote}>{item.linked}</Text> : null}
                </View>
                <View style={styles.milestoneTrailing}>
                  <View style={[styles.milestoneDatePill, item.urgent ? styles.duePill : styles.plannedPill]}>
                    <DashboardIcon name="calendar" size={14} color={item.urgent ? '#d7441c' : GREEN} />
                    <Text numberOfLines={1} style={[styles.milestoneDateText, item.urgent ? styles.dueText : styles.plannedText]}>{item.date}</Text>
                  </View>
                </View>
                <DashboardIcon name="chevron" size={17} color={MUTED} />
              </Pressable>
            ))}
          </View>

          <View style={[styles.sectionCard, styles.resourcesCard]}>
            <Text style={[styles.sectionTitle, styles.resourcesTitle, compact && styles.sectionTitleCompact]}>Inputs &amp; resources</Text>
            <View style={styles.resourcesRow}>
                <ResourceTile icon="soil" label="Soil" value={farm.soilType ?? 'Not set'} tone="soilTone" compact={compact} />
              <ResourceTile icon="drop" label="Irrigation" value={farm.irrigationAvailable == null ? 'Not set' : farm.irrigationAvailable ? 'Available' : 'Unavailable'} tone="waterTone" compact={compact} />
              <ResourceTile icon="water" label="Water source" value={farm.waterSource ?? 'Not set'} tone="sourceTone" compact={compact} />
            </View>
          </View>
        </ScrollView>

        <View style={[styles.actionsBar, compact && styles.actionsBarCompact]}>
          <Pressable accessibilityRole="button" onPress={() => go('tasks')} style={styles.outlineAction}>
            <DashboardIcon name="calendar" size={19} color={GREEN} /><Text style={[styles.outlineActionText, compact && styles.actionTextCompact]}>Calendar view</Text>
          </Pressable>
          <Pressable accessibilityRole="button" onPress={() => go('crop-advisor')} style={styles.primaryAction}>
            <FarmChromeIcon name="filters" size={20} color={PAPER} /><Text style={[styles.primaryActionText, compact && styles.actionTextCompact]}>Adjust plan</Text>
          </Pressable>
        </View>
        <FarmBottomNavigation active="Home" farmId={farmId} compact />
      </View>
    </SafeAreaView>
  );
}

function PlanGlyph({ name, size, color }: { name: PlanGlyphName; size: number; color: string }) {
  if (name === 'soil' || name === 'drop' || name === 'water' || name === 'leaf' || name === 'edit' || name === 'check' || name === 'clipboard' || name === 'field' || name === 'location' || name === 'person' || name === 'coins' || name === 'chart') {
    return <FarmProfileIcon name={name as FarmProfileIconName} size={size} color={color} />;
  }
  return <DashboardIcon name={name as DashboardIconName} size={size} color={color} />;
}

function ResourceTile({ icon, label, value, tone, compact }: { icon: 'soil' | 'drop' | 'water'; label: string; value: string; tone: 'soilTone' | 'waterTone' | 'sourceTone'; compact: boolean }) {
  return (
    <View style={[styles.resourceTile, styles[tone], compact && styles.resourceTileCompact]}>
      <FarmProfileIcon name={icon} size={compact ? 20 : 23} color={icon === 'soil' ? '#65432d' : icon === 'water' ? '#16857d' : GREEN} />
      <View style={styles.resourceCopy}><Text numberOfLines={1} style={styles.resourceLabel}>{label}</Text><Text numberOfLines={1} style={[styles.resourceValue, compact && styles.resourceValueCompact]}>{value}</Text></View>
    </View>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: PAPER },
  frame: { flex: 1, width: '100%', maxWidth: 480, alignSelf: 'center', backgroundColor: PAPER },
  header: { height: 60, paddingHorizontal: 12, flexDirection: 'row', alignItems: 'center', gap: 8, borderBottomWidth: 1, borderBottomColor: '#eeece3' },
  headerCompact: { height: 57, paddingHorizontal: 9, gap: 6 },
  headerButton: { width: 34, height: 34, flexShrink: 0, alignItems: 'center', justifyContent: 'center', borderRadius: 18, backgroundColor: '#edf2e7' },
  calendarButton: { backgroundColor: '#e8f1e4' },
  headerCopy: { flex: 1, minWidth: 0, alignItems: 'center' },
  headerTitle: { color: '#101820', fontFamily: 'Georgia', fontSize: 21, lineHeight: 24, fontWeight: '700' },
  headerSubtitle: { color: MUTED, fontFamily: 'Arial', fontSize: 11.2, lineHeight: 14, marginTop: 1, textAlign: 'center' },
  headerSubtitleCompact: { fontSize: 9.5 },
  scroll: { flex: 1, minHeight: 0 },
  content: { paddingHorizontal: 12, paddingTop: 6, paddingBottom: 4, gap: 4 },
  contentCompact: { paddingHorizontal: 9, gap: 4 },
  hero: { height: 128, overflow: 'hidden', borderRadius: 15, borderWidth: 1, borderColor: '#eeece3', backgroundColor: '#f8f5e9' },
  heroCompact: { height: 124 },
  heroPhoto: { flex: 1, justifyContent: 'center' },
  heroImage: { width: '100%', height: '100%', borderRadius: 15 },
  heroCopy: { width: '60%', height: '100%', justifyContent: 'center', paddingLeft: 9, paddingRight: 8, backgroundColor: 'rgba(255,253,247,0.97)', borderTopRightRadius: 39, borderBottomRightRadius: 39 },
  activePill: { height: 22, minWidth: 96, alignSelf: 'flex-start', paddingHorizontal: 8, flexDirection: 'row', alignItems: 'center', gap: 5, borderRadius: 14, backgroundColor: '#eaf2e2' },
  activeText: { color: GREEN, fontFamily: 'Arial', fontSize: 11, lineHeight: 14, fontWeight: '600' },
  cropName: { marginTop: 2, color: '#101820', fontFamily: 'Georgia', fontSize: 27, lineHeight: 30, fontWeight: '700', letterSpacing: -0.7 },
  cropNameCompact: { fontSize: 24, lineHeight: 27 },
  cropSubtitle: { color: '#364c5f', fontFamily: 'Arial', fontSize: 11.6, lineHeight: 15 },
  locationRow: { marginTop: 4, flexDirection: 'row', alignItems: 'center', gap: 3 },
  locationText: { color: '#344c5e', fontFamily: 'Arial', fontSize: 9.6, lineHeight: 12, flexShrink: 1 },
  metaDivider: { width: 1, height: 14, marginHorizontal: 3, backgroundColor: '#d8d5cb' },
  focusText: { marginTop: 5, color: '#425a70', fontFamily: 'Arial', fontSize: 10, lineHeight: 13, maxWidth: 232 },
  focusStrong: { color: INK, fontWeight: '700' },
  sectionCard: { paddingHorizontal: 9, paddingTop: 6, paddingBottom: 4, borderRadius: 14, borderWidth: 1, borderColor: '#f0eee6', backgroundColor: '#fffefa', boxShadow: '0px 2px 7px rgba(30, 54, 37, 0.06)', elevation: 1 },
  sectionHeading: { minHeight: 21, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  sectionTitle: { color: '#111916', fontFamily: 'Georgia', fontSize: 17, lineHeight: 21, fontWeight: '700', letterSpacing: -0.3 },
  sectionTitleCompact: { fontSize: 15.5, lineHeight: 19 },
  weekCounter: { color: '#304a60', fontFamily: 'Arial', fontSize: 10.8, lineHeight: 14 },
  stageTrack: { height: 70, marginTop: 3, flexDirection: 'row', justifyContent: 'space-between', position: 'relative' },
  trackLine: { position: 'absolute', top: 32, left: '12%', right: '12%', height: 1.5, backgroundColor: '#a8ada7' },
  trackProgress: { position: 'absolute', top: 32, left: '12%', width: '25.3%', height: 2, backgroundColor: GREEN },
  stageColumn: { flex: 1, minWidth: 0, alignItems: 'center' },
  stageIconCircle: { width: 36, height: 36, alignItems: 'center', justifyContent: 'center', borderRadius: 20, backgroundColor: '#eaf2e4' },
  stageIconCompact: { width: 32, height: 32 },
  stageDot: { zIndex: 1, width: 10, height: 10, marginTop: -1, borderWidth: 1.5, borderColor: '#a1a79f', borderRadius: 6, backgroundColor: PAPER },
  stageDotCurrent: { width: 12, height: 12, marginTop: -2, borderWidth: 2, borderColor: GREEN, backgroundColor: GREEN },
  stageName: { marginTop: 3, color: '#11191b', fontFamily: 'Arial', fontSize: 10.4, lineHeight: 13, fontWeight: '600' },
  stageNameCurrent: { color: GREEN, fontWeight: '700' },
  stageNameCompact: { fontSize: 9.3 },
  stageDate: { color: MUTED, fontFamily: 'Arial', fontSize: 9.6, lineHeight: 12 },
  stageDateCompact: { fontSize: 8.8 },
  currentPill: { height: 14, minWidth: 48, marginTop: 1, paddingHorizontal: 8, alignItems: 'center', justifyContent: 'center', borderRadius: 9, backgroundColor: GREEN },
  currentPillText: { color: PAPER, fontFamily: 'Arial', fontSize: 8, lineHeight: 11 },
  currentPillSpacer: { height: 15 },
  cardTitle: { marginBottom: 2 },
  planRow: { minHeight: 38, flexDirection: 'row', alignItems: 'center', gap: 6, borderBottomWidth: 1, borderBottomColor: '#eeeae1' },
  lastRow: { borderBottomWidth: 0 },
  rowIconCircle: { width: 29, height: 29, flexShrink: 0, alignItems: 'center', justifyContent: 'center', borderRadius: 18, backgroundColor: '#eaf2e4' },
  rowCopy: { flex: 1, minWidth: 0 },
  rowTitle: { color: '#11191a', fontFamily: 'Arial', fontSize: 12.2, lineHeight: 15, fontWeight: '700' },
  rowNote: { color: '#52677a', fontFamily: 'Arial', fontSize: 9.8, lineHeight: 12.5 },
  rowNoteCompact: { fontSize: 8.8 },
  statusPill: { minWidth: 61, minHeight: 24, paddingHorizontal: 6, alignItems: 'center', justifyContent: 'center', borderRadius: 12 },
  duePill: { backgroundColor: '#fff0dc' },
  plannedPill: { backgroundColor: '#eaf2e5' },
  statusText: { fontFamily: 'Arial', fontSize: 9.6, lineHeight: 12, fontWeight: '600' },
  dueText: { color: '#d1431d' },
  plannedText: { color: GREEN },
  weatherCard: { height: 76, overflow: 'hidden', borderRadius: 14, backgroundColor: '#b7d6e7' },
  weatherCompact: { height: 74 },
  weatherImage: { flex: 1, flexDirection: 'row', alignItems: 'center', gap: 7, paddingHorizontal: 9 },
  weatherImageStyle: { width: '100%', height: '100%' },
  weatherWash: { ...StyleSheet.absoluteFill, backgroundColor: 'rgba(193,222,240,0.75)' },
  weatherCopy: { flex: 1, minWidth: 0, paddingRight: 88 },
  weatherTitle: { color: '#11191a', fontFamily: 'Georgia', fontSize: 15.5, lineHeight: 19, fontWeight: '700' },
  weatherDescription: { color: '#2e536e', fontFamily: 'Arial', fontSize: 10.4, lineHeight: 13.5 },
  weatherAction: { position: 'absolute', right: 8, bottom: 8, height: 27, minWidth: 100, paddingHorizontal: 8, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', borderRadius: 16, backgroundColor: GREEN },
  weatherActionText: { color: PAPER, fontFamily: 'Arial', fontSize: 10, lineHeight: 13, fontWeight: '600' },
  milestoneRow: { minHeight: 36, flexDirection: 'row', alignItems: 'center', gap: 6, borderBottomWidth: 1, borderBottomColor: '#eeeae1' },
  milestoneIconCircle: { width: 28, height: 28, flexShrink: 0, alignItems: 'center', justifyContent: 'center', borderRadius: 18, backgroundColor: '#eaf2e4' },
  milestoneCopy: { flex: 1, minWidth: 0 },
  milestoneTitleCompact: { fontSize: 10.6 },
  milestoneNote: { color: MUTED, fontFamily: 'Arial', fontSize: 9.2, lineHeight: 12 },
  linkedNote: { color: MUTED, fontFamily: 'Arial', fontSize: 8, lineHeight: 10 },
  milestoneTrailing: { alignItems: 'flex-end', justifyContent: 'center' },
  milestoneDatePill: { minHeight: 23, maxWidth: 116, paddingHorizontal: 6, flexDirection: 'row', alignItems: 'center', gap: 3, borderRadius: 13 },
  milestoneDateText: { fontFamily: 'Arial', fontSize: 8.8, lineHeight: 11 },
  resourcesCard: { paddingTop: 6, paddingHorizontal: 7, paddingBottom: 6 },
  resourcesTitle: { marginBottom: 4 },
  resourcesRow: { flexDirection: 'row', gap: 5 },
  resourceTile: { flex: 1, minWidth: 0, height: 32, paddingHorizontal: 5, flexDirection: 'row', alignItems: 'center', gap: 4, borderRadius: 9 },
  resourceTileCompact: { height: 31, paddingHorizontal: 3, gap: 2 },
  soilTone: { backgroundColor: '#fbefdf' },
  waterTone: { backgroundColor: '#edf4e8' },
  sourceTone: { backgroundColor: '#e6f0e8' },
  resourceCopy: { flex: 1, minWidth: 0 },
  resourceLabel: { color: '#405668', fontFamily: 'Arial', fontSize: 8.2, lineHeight: 10 },
  resourceValue: { color: INK, fontFamily: 'Arial', fontSize: 10, lineHeight: 12, fontWeight: '600' },
  resourceValueCompact: { fontSize: 8.8 },
  actionsBar: { height: 45, paddingHorizontal: 12, flexDirection: 'row', gap: 6, alignItems: 'center', borderTopWidth: 1, borderTopColor: '#ece9df', backgroundColor: PAPER },
  actionsBarCompact: { height: 43, paddingHorizontal: 9 },
  outlineAction: { flex: 1, height: 34, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 7, borderWidth: 1, borderColor: GREEN, borderRadius: 10, backgroundColor: '#fffefa' },
  primaryAction: { flex: 1, height: 34, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 7, borderRadius: 10, backgroundColor: '#004b35' },
  outlineActionText: { color: GREEN, fontFamily: 'Arial', fontSize: 11.5, lineHeight: 15, fontWeight: '600' },
  primaryActionText: { color: PAPER, fontFamily: 'Arial', fontSize: 11.5, lineHeight: 15, fontWeight: '600' },
  actionTextCompact: { fontSize: 10.2 },
  empty: { color: MUTED, fontFamily: 'Arial', fontSize: 14, textAlign: 'center', padding: 24 },
});
