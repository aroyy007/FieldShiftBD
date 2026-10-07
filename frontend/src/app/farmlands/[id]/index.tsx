import React, { useEffect, useState } from 'react';
import { ImageBackground, Pressable, ScrollView, StyleSheet, Text, View, useWindowDimensions } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Href, useLocalSearchParams, useRouter } from 'expo-router';
import { DashboardIcon } from '../../../components/dashboard-icons';
import { BrandPlantIcon } from '../../../components/icons';
import { FarmBottomNavigation, FarmChromeIcon } from '../../../components/farmland-mobile-ui';
import { FarmProfileIcon, FarmProfileIconName } from '../../../components/farm-profile-icons';
import { FieldIcon } from '../../../components/field-screen-ui';
import { useAppContext } from '../../../context/AppProvider';
import { apiRequest } from '../../../services/api-client';

const PAPER = '#fffdf7';
const GREEN = '#07543a';
const MUTED = '#52677a';
type WeatherAssessment = { alerts: { title: string; message: string; recommended_action: string }[] };

function overviewTaskIcon(title: string): 'fertilizer' | 'weeds' | 'camera' | 'rain' {
  const lower = title.toLowerCase();
  if (/water|irrigat|drain/.test(lower)) return 'rain';
  if (/weed/.test(lower)) return 'weeds';
  if (/photo|scan|check-in|check in/.test(lower)) return 'camera';
  return 'fertilizer';
}

function formatCheckinDate(value: string | undefined): string {
  if (!value) return 'No check-ins recorded';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? 'Recent check-in' : date.toLocaleString([], { dateStyle: 'medium', timeStyle: 'short' });
}

export default function FarmOverview() {
  const params = useLocalSearchParams<{ id?: string | string[] }>();
  const farmId = Array.isArray(params.id) ? params.id[0] : params.id;
  const { farmlands } = useAppContext();
  const farm = farmlands.find(item => item.id === farmId);
  const router = useRouter();
  const { width } = useWindowDimensions();
  const compact = width < 420;
  const narrow = width < 360;
  const smallGrid = width < 370;
  const activeTasks = farm?.tasks.filter(task => task.status === 'pending') ?? [];
  const openProblems = farm?.problems.filter(problem => problem.status === 'open' || problem.status === 'monitoring') ?? [];
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
        <View style={[styles.brandHeader, compact && styles.brandHeaderCompact]}>
          <Pressable accessibilityRole="button" accessibilityLabel="Back to farmlands" onPress={() => router.replace('/farmlands' as Href)} style={styles.headerBack}>
            <FarmChromeIcon name="back" size={22} color={GREEN} />
          </Pressable>
          <BrandPlantIcon size={compact ? 31 : 37} />
          <View style={styles.brandCopy}>
            <Text numberOfLines={1} style={[styles.brandName, compact && styles.brandNameCompact]}>FieldShift BD</Text>
            <Text numberOfLines={1} style={styles.brandSubtitle}>AI Farmer Assistant</Text>
          </View>
          <Pressable accessibilityRole="button" accessibilityLabel="Open alerts" onPress={() => go('alerts')} style={styles.bellButton}>
            <DashboardIcon name="bell" size={25} color={GREEN} />
          </Pressable>
          <Pressable accessibilityRole="button" accessibilityLabel="Open profile" onPress={() => router.push('/farmlands/profile-setup' as Href)} style={styles.avatarButton}>
            <ImageBackground source={require('../../../../assets/images/landing-farmer.png')} resizeMode="cover" style={styles.avatarImage} imageStyle={styles.avatarImageAsset} />
          </Pressable>
        </View>

        <ScrollView style={styles.scroll} contentContainerStyle={[styles.content, compact && styles.contentCompact]} showsVerticalScrollIndicator={false}>
          <View style={styles.pageHeading}>
            <Text style={[styles.pageTitle, compact && styles.pageTitleCompact]}>Farm Overview</Text>
            <Text style={styles.pageSubtitle}>Your farm’s current state, tasks, weather and health at a glance.</Text>
          </View>

          <Pressable accessibilityRole="button" accessibilityLabel="View season plan" onPress={() => go('season-plan')} style={styles.cropCard}>
            <ImageBackground source={require('../../../../assets/images/verification-rice-field.png')} resizeMode="cover" style={[styles.cropPhoto, narrow && styles.cropPhotoNarrow]} imageStyle={styles.cropPhotoAsset}>
              <View style={[styles.cropGradient, narrow && styles.cropGradientNarrow]}>
                <View style={styles.cropEyebrow}><View style={styles.miniLeaf}><FarmProfileIcon name="leaf" size={15} color={GREEN} /></View><Text style={styles.cropEyebrowText}>Current crop</Text></View>
                <Text numberOfLines={1} style={[styles.cropName, compact && styles.cropNameCompact]}>{farm.crop}</Text>
                <Text style={styles.cropStage}>{farm.growthStage}</Text>
                <Text numberOfLines={2} style={styles.cropDescription}>{farm.activeSeasonId ? 'Current crop and growth stage from your active season.' : 'No active season. Start one with Crop Advisor.'}</Text>
                <View style={[styles.cropMetaRow, narrow && styles.cropMetaRowNarrow]}>
                  <View style={styles.metaChip}><DashboardIcon name="location" size={15} color={GREEN} /><Text numberOfLines={1} style={styles.metaChipText}>{farm.location ?? 'Location not set'}</Text></View>
                  <View style={styles.metaChip}><DashboardIcon name="acreage" size={15} color={GREEN} /><Text style={styles.metaChipText}>{farm.acreage.toLocaleString(undefined, { maximumFractionDigits: 2 })} acres</Text></View>
                </View>
              </View>
            </ImageBackground>
            <View style={styles.growthProgress}>
              <Text style={styles.progressCaption}>{farm.seasonProgressPercent == null ? 'No active season' : `Season progress ${farm.seasonProgressPercent}%`}</Text>
              <View style={styles.progressTrack}>
                <View style={styles.progressBase} />
                <View style={[styles.progressDone, { width: `${farm.seasonProgressPercent ?? 0}%` }]} />
                {farm.seasonPlan.map((stage, index) => (
                  <View key={stage.id} style={styles.progressStage}>
                    <View style={[styles.progressDot, stage.status === 'current' && styles.progressDotCurrent]}>{stage.status === 'current' ? <View style={styles.progressDotInner} /> : null}</View>
                    <Text numberOfLines={1} style={[styles.progressLabel, stage.status === 'current' && styles.progressLabelCurrent, compact && styles.progressLabelCompact]}>{stage.name}</Text>
                  </View>
                ))}
              </View>
            </View>
          </Pressable>

          <View style={styles.sectionCard}>
            <View style={styles.sectionHeading}>
              <View style={styles.headingLead}><FarmProfileIcon name="chart" size={21} color={GREEN} /><Text style={[styles.sectionTitle, compact && styles.sectionTitleCompact]}>Farm details</Text></View>
              <Pressable accessibilityRole="button" onPress={() => router.push('/farmlands/manage' as Href)} style={styles.viewDetails}>
                <Text numberOfLines={1} style={styles.viewDetailsText}>View and edit details</Text><DashboardIcon name="chevron" size={16} color={MUTED} />
              </Pressable>
            </View>
            <View style={[styles.detailsGrid, smallGrid && styles.detailsGridCompact]}>
              <DetailTile icon="soil" title="Soil type" value={farm.soilType ?? 'Not set'} compact={compact} />
              <DetailTile icon="drop" title="Irrigation" value={farm.irrigationAvailable == null ? 'Not set' : farm.irrigationAvailable ? 'Available' : 'Unavailable'} compact={compact} />
              <DetailTile icon="water" title="Water source" value={farm.waterSource ?? 'Not set'} compact={compact} />
              <DetailTile icon="clipboard" title="Active tasks" value={`${activeTasks.length} pending`} compact={compact} />
            </View>
          </View>

          <View style={styles.sectionCard}>
            <Pressable accessibilityRole="button" onPress={() => go('tasks')} style={styles.sectionHeading}>
              <View style={styles.headingLead}><DashboardIcon name="tasks" size={21} color={GREEN} /><Text style={[styles.sectionTitle, compact && styles.sectionTitleCompact]}>Today on this farm</Text></View>
              <View style={styles.inlineLink}><Text style={styles.todayCount}>{activeTasks.length} pending tasks</Text><DashboardIcon name="chevron" size={16} color={MUTED} /></View>
            </Pressable>
            <View style={styles.taskRows}>
              {activeTasks.slice(0, 3).map(task => <TaskRow key={task.id} icon={overviewTaskIcon(task.title)} title={task.title} note={task.description ?? `${task.priority} priority · ${task.source.replaceAll('_', ' ')}`} dueLabel={task.dueAt ? new Date(task.dueAt).toLocaleDateString() : 'No due date'} onPress={() => go('tasks')} compact={compact} />)}
              {activeTasks.length === 0 ? <Text style={styles.empty}>{farm.activeSeasonId ? 'No pending tasks for this farm.' : 'Start a season to create crop tasks.'}</Text> : null}
            </View>
          </View>

          <Pressable accessibilityRole="button" accessibilityLabel="View weather forecast" onPress={() => go('alerts')} style={styles.weatherCard}>
            <ImageBackground source={require('../../../../assets/images/assistant-rain-field.png')} resizeMode="cover" style={styles.weatherImage} imageStyle={styles.weatherImageAsset}>
              <View style={styles.weatherShade} />
              <View style={styles.weatherTop}>
                <View style={styles.weatherIcon}><DashboardIcon name="rain" size={29} color="#eaf8ff" /></View>
                <View style={styles.weatherCopy}>
                  <Text numberOfLines={1} style={styles.weatherTitle}>{weather?.alerts[0]?.title ?? (weatherError ? 'Weather assessment unavailable' : 'Weather assessment')}</Text>
                  <Text numberOfLines={2} style={styles.weatherDescription}>{weather?.alerts[0]?.message ?? (weatherError || 'No actionable weather alert is currently returned for this farm.')}</Text>
                </View>
              </View>
              <View style={[styles.weatherBottom, compact && styles.weatherBottomCompact]}>
                <View style={styles.adviceBox}>
                  <View style={styles.bulb}><DashboardIcon name="bulb" size={19} color="#c88b08" /></View>
                  <Text numberOfLines={2} style={styles.adviceText}>{weather?.alerts[0]?.recommended_action ?? 'Open alerts to see weather provider status and any farm-specific risks.'}</Text>
                </View>
                <View style={styles.forecastButton}><Text style={styles.forecastButtonText}>View forecast</Text><View style={styles.forecastArrow}><DashboardIcon name="chevron" size={15} color={GREEN} /></View></View>
              </View>
            </ImageBackground>
          </Pressable>

          {openProblems[0] ? <Pressable accessibilityRole="button" onPress={() => go('problems')} style={styles.issueCard}>
            <View style={styles.issueImage}><DashboardIcon name="warning" size={24} color="#e34b1d" /></View>
            <View style={styles.issueCopy}>
              <View style={styles.issueLabel}><DashboardIcon name="warning" size={15} color="#e34b1d" /><Text style={styles.issueLabelText}>Open issue</Text></View>
              <Text numberOfLines={1} style={styles.issueTitle}>{openProblems[0].category}</Text>
              <Text numberOfLines={1} style={styles.issueDescription}>{openProblems[0].description}</Text>
            </View>
            <View style={styles.issueChevron}><DashboardIcon name="chevron" size={17} color={MUTED} /></View>
          </Pressable> : null}

          <View style={[styles.sectionCard, styles.activityCard]}>
            <View style={styles.sectionHeading}>
              <View style={styles.headingLead}><View style={styles.activityIcon}><FieldIcon name="clock" size={16} color={PAPER} /></View><Text style={[styles.sectionTitle, compact && styles.sectionTitleCompact]}>Recent activity</Text></View>
              <Pressable accessibilityRole="button" onPress={() => go('check-ins')} style={styles.viewDetails}><Text style={styles.viewDetailsText}>View all activity</Text><DashboardIcon name="chevron" size={16} color={MUTED} /></Pressable>
            </View>
            <View style={styles.activityRow}>
              <Pressable accessibilityRole="button" onPress={() => go('check-ins')} style={styles.activityTile}>
                <View style={styles.activityTileIcon}><DashboardIcon name="camera" size={20} color={GREEN} /></View>
                <View style={styles.activityCopy}><Text style={styles.activityTitle}>Last check-in</Text><Text numberOfLines={1} style={styles.activityMeta}>{formatCheckinDate(farm.checkIns[0]?.at)}</Text></View>
              </Pressable>
              <Pressable accessibilityRole="button" onPress={() => go('problems')} style={styles.activityTile}>
                <View style={styles.warningCircle}><DashboardIcon name="warning" size={19} color="#e45a17" /></View>
                <View style={styles.activityCopy}><Text style={styles.activityTitle}>{openProblems.length} open problems</Text><Text style={styles.activityMeta}>{openProblems.length ? 'Needs follow-up' : 'No issues to follow up'}</Text></View>
                <DashboardIcon name="chevron" size={15} color={MUTED} />
              </Pressable>
            </View>
          </View>
        </ScrollView>
        <FarmBottomNavigation active="Home" farmId={farmId} compact />
      </View>
    </SafeAreaView>
  );
}

function DetailTile({ icon, title, value, compact }: { icon: FarmProfileIconName; title: string; value: string; compact: boolean }) {
  return (
    <View style={[styles.detailTile, compact && styles.detailTileCompact]}>
      <View style={[styles.detailIcon, compact && styles.detailIconCompact]}><FarmProfileIcon name={icon} size={compact ? 20 : 22} color={GREEN} /></View>
      <View style={styles.detailCopy}><Text numberOfLines={2} style={styles.detailTitle}>{title}</Text><Text numberOfLines={2} style={styles.detailValue}>{value}</Text></View>
    </View>
  );
}

function TaskRow({ icon, title, note, dueLabel, onPress, compact }: { icon: 'fertilizer' | 'weeds' | 'camera' | 'rain'; title: string; note: string; dueLabel: string; onPress: () => void; compact: boolean }) {
  return (
    <Pressable accessibilityRole="button" onPress={onPress} style={[styles.taskRow, compact && styles.taskRowCompact]}>
      <View style={styles.taskIcon}><DashboardIcon name={icon} size={24} color={GREEN} /></View>
      <View style={styles.taskCopy}><Text numberOfLines={1} style={styles.taskTitle}>{title}</Text><Text numberOfLines={1} style={styles.taskNote}>{note}</Text></View>
      <View style={styles.taskDue}><Text numberOfLines={1} style={styles.taskDueText}>{dueLabel}</Text></View>
      <View style={styles.taskChevron}><DashboardIcon name="chevron" size={17} color={MUTED} /></View>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: PAPER },
  frame: { flex: 1, width: '100%', maxWidth: 500, alignSelf: 'center', backgroundColor: PAPER },
  brandHeader: { minHeight: 56, paddingHorizontal: 12, flexDirection: 'row', alignItems: 'center', gap: 6, borderBottomWidth: 1, borderBottomColor: '#f0ede5' },
  brandHeaderCompact: { minHeight: 51, paddingHorizontal: 8, gap: 4 },
  headerBack: { width: 32, height: 32, flexShrink: 0, alignItems: 'center', justifyContent: 'center', borderRadius: 18, backgroundColor: '#edf2e7' },
  brandCopy: { flex: 1, minWidth: 0 },
  brandName: { color: '#12292f', fontFamily: 'Georgia', fontSize: 18, lineHeight: 22, fontWeight: '700', letterSpacing: -0.3 },
  brandNameCompact: { fontSize: 15.8, lineHeight: 19 },
  brandSubtitle: { color: '#627b9b', fontFamily: 'Arial', fontSize: 10.4, lineHeight: 13 },
  bellButton: { width: 31, height: 34, flexShrink: 0, alignItems: 'center', justifyContent: 'center' },
  avatarButton: { width: 38, height: 38, flexShrink: 0, overflow: 'hidden', borderRadius: 21, borderWidth: 1, borderColor: '#e9e6dc' },
  avatarImage: { width: 38, height: 38, flexShrink: 0, overflow: 'hidden', borderRadius: 21 },
  avatarImageAsset: { width: '100%', height: '100%', borderRadius: 21 },
  scroll: { flex: 1, minHeight: 0 },
  content: { paddingHorizontal: 12, paddingTop: 6, paddingBottom: 4, gap: 4 },
  contentCompact: { paddingHorizontal: 9, gap: 6 },
  pageHeading: { paddingHorizontal: 3, marginBottom: 1 },
  pageTitle: { color: '#09372e', fontFamily: 'Georgia', fontSize: 28, lineHeight: 33, fontWeight: '700', letterSpacing: -0.6 },
  pageTitleCompact: { fontSize: 25, lineHeight: 30 },
  pageSubtitle: { color: '#7085a3', fontFamily: 'Arial', fontSize: 12.4, lineHeight: 16 },
  cropCard: { overflow: 'hidden', borderRadius: 15, borderWidth: 1, borderColor: '#f0ede5', backgroundColor: '#fffefa', boxShadow: '0px 2px 8px rgba(30, 54, 37, 0.07)', elevation: 1 },
  cropPhoto: { height: 117, justifyContent: 'center' },
  cropPhotoNarrow: { height: 132 },
  cropPhotoAsset: { width: '100%', height: '100%' },
  cropGradient: { ...StyleSheet.absoluteFill, width: '56%', paddingLeft: 9, paddingVertical: 7, justifyContent: 'center', borderTopRightRadius: 38, borderBottomRightRadius: 38, backgroundColor: 'rgba(255,253,247,0.96)' },
  cropGradientNarrow: { width: '72%' },
  cropEyebrow: { flexDirection: 'row', alignItems: 'center', gap: 5 },
  miniLeaf: { width: 20, height: 20, alignItems: 'center', justifyContent: 'center', borderRadius: 11, backgroundColor: 'rgba(234,242,226,0.92)' },
  cropEyebrowText: { color: '#597193', fontFamily: 'Arial', fontSize: 10.8, lineHeight: 14 },
  cropName: { marginTop: 1, color: '#0b392f', fontFamily: 'Georgia', fontSize: 25, lineHeight: 28, fontWeight: '700', letterSpacing: -0.5 },
  cropNameCompact: { fontSize: 22, lineHeight: 25 },
  cropStage: { color: '#102e35', fontFamily: 'Georgia', fontSize: 13, lineHeight: 16, fontWeight: '700' },
  cropDescription: { maxWidth: 216, marginTop: 2, color: '#637a99', fontFamily: 'Arial', fontSize: 11.2, lineHeight: 14 },
  cropMetaRow: { marginTop: 5, flexDirection: 'row', gap: 5 },
  cropMetaRowNarrow: { flexWrap: 'wrap', rowGap: 3 },
  metaChip: { minHeight: 24, maxWidth: '68%', paddingHorizontal: 7, flexDirection: 'row', alignItems: 'center', gap: 4, borderWidth: 1, borderColor: '#dfe9db', borderRadius: 10, backgroundColor: 'rgba(250,250,242,0.9)' },
  metaChipText: { color: '#334e61', fontFamily: 'Arial', fontSize: 9.8, lineHeight: 12 },
  growthProgress: { height: 47, paddingHorizontal: 9, paddingTop: 3, backgroundColor: '#fffefa' },
  progressCaption: { color: '#18384d', fontFamily: 'Arial', fontSize: 10.3, lineHeight: 13 },
  progressTrack: { height: 33, marginTop: 0, flexDirection: 'row', justifyContent: 'space-between', position: 'relative' },
  progressBase: { position: 'absolute', top: 9, left: '3%', right: '3%', height: 4, borderRadius: 3, backgroundColor: '#e6e5dd' },
  progressDone: { position: 'absolute', top: 9, left: '3%', width: '32%', height: 4, borderRadius: 3, backgroundColor: GREEN },
  progressStage: { flex: 1, minWidth: 0, alignItems: 'flex-start' },
  progressDot: { zIndex: 1, width: 18, height: 18, alignItems: 'center', justifyContent: 'center', borderWidth: 1, borderColor: '#d5d8cf', borderRadius: 10, backgroundColor: '#fffefa' },
  progressDotCurrent: { alignSelf: 'center', width: 25, height: 25, marginTop: -4, borderWidth: 5, borderColor: '#e7f0df', borderRadius: 14, backgroundColor: GREEN },
  progressDotInner: { width: 8, height: 8, borderRadius: 5, backgroundColor: GREEN },
  progressLabel: { marginTop: 3, color: '#637a99', fontFamily: 'Arial', fontSize: 9.7, lineHeight: 12 },
  progressLabelCurrent: { color: '#143b30', fontWeight: '700', alignSelf: 'center' },
  progressLabelCompact: { fontSize: 8.5 },
  sectionCard: { paddingHorizontal: 8, paddingTop: 5, paddingBottom: 5, borderRadius: 15, borderWidth: 1, borderColor: '#f0eee6', backgroundColor: '#fffefa', boxShadow: '0px 2px 8px rgba(30, 54, 37, 0.06)', elevation: 1 },
  sectionHeading: { minHeight: 23, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 5 },
  headingLead: { flexDirection: 'row', alignItems: 'center', gap: 7, minWidth: 0 },
  sectionTitle: { color: '#112349', fontFamily: 'Georgia', fontSize: 17, lineHeight: 21, fontWeight: '700', letterSpacing: -0.25 },
  sectionTitleCompact: { fontSize: 15, lineHeight: 19 },
  viewDetails: { flexDirection: 'row', alignItems: 'center', gap: 2, minWidth: 0 },
  viewDetailsText: { color: '#627b9b', fontFamily: 'Arial', fontSize: 9.7, lineHeight: 12 },
  detailsGrid: { marginTop: 4, flexDirection: 'row', gap: 4 },
  detailsGridCompact: { flexWrap: 'wrap' },
  detailTile: { flex: 1, minWidth: 0, height: 42, paddingHorizontal: 4, flexDirection: 'row', alignItems: 'center', gap: 4, borderWidth: 1, borderColor: '#f0eee6', borderRadius: 11, backgroundColor: '#fffefa' },
  detailTileCompact: { flexBasis: '48%', height: 52 },
  detailIcon: { width: 30, height: 30, flexShrink: 0, alignItems: 'center', justifyContent: 'center', borderRadius: 16, backgroundColor: '#eaf2e5' },
  detailIconCompact: { width: 34, height: 34 },
  detailCopy: { flex: 1, minWidth: 0 },
  detailTitle: { color: '#183350', fontFamily: 'Arial', fontSize: 8.6, lineHeight: 10.5, fontWeight: '600' },
  detailValue: { color: '#647b98', fontFamily: 'Arial', fontSize: 9.3, lineHeight: 11 },
  inlineLink: { flexDirection: 'row', alignItems: 'center', gap: 2 },
  todayCount: { color: '#203b56', fontFamily: 'Arial', fontSize: 10.2, lineHeight: 13 },
  taskRows: { marginTop: 4, gap: 4 },
  taskRow: { minHeight: 42, paddingHorizontal: 5, flexDirection: 'row', alignItems: 'center', gap: 6, borderWidth: 1, borderColor: '#f0eee6', borderRadius: 13, backgroundColor: '#fffefa' },
  taskRowCompact: { minHeight: 39, paddingHorizontal: 4, gap: 4 },
  taskIcon: { width: 30, height: 30, flexShrink: 0, alignItems: 'center', justifyContent: 'center', borderRadius: 20, backgroundColor: '#eaf2e4' },
  taskCopy: { flex: 1, minWidth: 0 },
  taskTitle: { color: '#112349', fontFamily: 'Georgia', fontSize: 13.6, lineHeight: 16, fontWeight: '700' },
  taskNote: { color: '#6d82a0', fontFamily: 'Arial', fontSize: 10, lineHeight: 13 },
  taskDue: { minWidth: 61, height: 24, paddingHorizontal: 6, alignItems: 'center', justifyContent: 'center', borderRadius: 13, backgroundColor: '#fff0d4' },
  taskDueText: { color: '#c74c1c', fontFamily: 'Arial', fontSize: 9.5, lineHeight: 12 },
  taskChevron: { width: 26, height: 29, alignItems: 'center', justifyContent: 'center', borderRadius: 15, backgroundColor: '#fffefa', boxShadow: '0px 1px 5px rgba(25, 39, 37, 0.08)' },
  weatherCard: { height: 98, overflow: 'hidden', borderRadius: 14, backgroundColor: '#0e433d', boxShadow: '0px 2px 8px rgba(30, 54, 37, 0.08)', elevation: 1 },
  weatherImage: { flex: 1, justifyContent: 'space-between', padding: 7 },
  weatherImageAsset: { width: '100%', height: '100%' },
  weatherShade: { ...StyleSheet.absoluteFill, backgroundColor: 'rgba(4, 45, 42, 0.36)' },
  weatherTop: { flexDirection: 'row', alignItems: 'center', gap: 7 },
  weatherIcon: { width: 35, height: 35, flexShrink: 0, alignItems: 'center', justifyContent: 'center', borderRadius: 25, backgroundColor: 'rgba(234,249,254,0.96)' },
  weatherCopy: { flex: 1, minWidth: 0, paddingRight: 2 },
  weatherTitle: { color: PAPER, fontFamily: 'Georgia', fontSize: 16, lineHeight: 19, fontWeight: '700' },
  weatherDescription: { color: '#f3f7f5', fontFamily: 'Arial', fontSize: 10.8, lineHeight: 13 },
  weatherBottom: { flexDirection: 'row', alignItems: 'center', gap: 6 },
  weatherBottomCompact: { gap: 4 },
  adviceBox: { flex: 1, minWidth: 0, minHeight: 29, paddingHorizontal: 6, flexDirection: 'row', alignItems: 'center', gap: 5, borderRadius: 12, backgroundColor: 'rgba(255,253,247,0.94)' },
  bulb: { width: 23, height: 23, flexShrink: 0, alignItems: 'center', justifyContent: 'center', borderRadius: 17, backgroundColor: '#fff1cc' },
  adviceText: { flex: 1, color: '#18314a', fontFamily: 'Arial', fontSize: 9.8, lineHeight: 12 },
  forecastButton: { width: 103, height: 29, paddingLeft: 6, paddingRight: 3, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', borderWidth: 1, borderColor: '#edf6ef', borderRadius: 18, backgroundColor: '#00563c' },
  forecastButtonText: { color: PAPER, fontFamily: 'Arial', fontSize: 10.6, lineHeight: 13, fontWeight: '600' },
  forecastArrow: { width: 22, height: 22, alignItems: 'center', justifyContent: 'center', borderRadius: 16, backgroundColor: PAPER },
  issueCard: { minHeight: 56, paddingHorizontal: 5, paddingVertical: 3, flexDirection: 'row', alignItems: 'center', gap: 7, borderWidth: 1, borderColor: '#f0eee6', borderRadius: 14, backgroundColor: '#fffefa', boxShadow: '0px 2px 7px rgba(30, 54, 37, 0.05)' },
  issueImage: { width: 50, height: 50, flexShrink: 0, borderRadius: 8 },
  issueCopy: { flex: 1, minWidth: 0 },
  issueLabel: { flexDirection: 'row', alignItems: 'center', gap: 4 },
  issueLabelText: { color: '#de481a', fontFamily: 'Arial', fontSize: 9.8, lineHeight: 12 },
  issueTitle: { color: '#122349', fontFamily: 'Georgia', fontSize: 13.4, lineHeight: 16, fontWeight: '700' },
  issueDescription: { color: '#6d82a0', fontFamily: 'Arial', fontSize: 10, lineHeight: 13 },
  issueChevron: { width: 22, height: 22, alignItems: 'center', justifyContent: 'center', borderRadius: 16, backgroundColor: '#fffefa', boxShadow: '0px 1px 5px rgba(25, 39, 37, 0.08)' },
  activityCard: { paddingTop: 6, paddingBottom: 6 },
  activityIcon: { width: 25, height: 25, alignItems: 'center', justifyContent: 'center', borderRadius: 14, backgroundColor: GREEN },
  activityRow: { marginTop: 4, flexDirection: 'row', gap: 5 },
  activityTile: { flex: 1, minWidth: 0, minHeight: 40, paddingHorizontal: 5, flexDirection: 'row', alignItems: 'center', gap: 5, borderWidth: 1, borderColor: '#eeece4', borderRadius: 12, backgroundColor: '#fffefa' },
  activityTileIcon: { width: 27, height: 27, flexShrink: 0, alignItems: 'center', justifyContent: 'center', borderRadius: 18, backgroundColor: '#eaf2e4' },
  warningCircle: { width: 27, height: 27, flexShrink: 0, alignItems: 'center', justifyContent: 'center', borderRadius: 18, backgroundColor: '#fff0d5' },
  activityCopy: { flex: 1, minWidth: 0 },
  activityTitle: { color: '#183350', fontFamily: 'Arial', fontSize: 9.5, lineHeight: 12, fontWeight: '600' },
  activityMeta: { color: '#657b99', fontFamily: 'Arial', fontSize: 9.3, lineHeight: 12 },
  empty: { color: MUTED, fontFamily: 'Arial', fontSize: 14, textAlign: 'center', padding: 24 },
});
