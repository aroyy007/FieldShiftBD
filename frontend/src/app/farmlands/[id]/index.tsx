import { ENGLISH_FONT_FAMILY } from '@/theme/fonts';
import { Href, useLocalSearchParams, useRouter } from 'expo-router';
import React, { useEffect, useState } from 'react';
import { ImageBackground, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { DashboardIcon, DashboardIconName } from '../../../components/dashboard-icons';
import { FarmProfileIcon } from '../../../components/farm-profile-icons';
import { FarmBottomNavigation, FarmChromeIcon } from '../../../components/farmland-mobile-ui';
import { BrandPlantIcon } from '../../../components/icons';
import { useAppContext } from '../../../context/AppProvider';
import { useHydrationSafeWindowDimensions } from '../../../hooks/useHydrationSafeWindowDimensions';
import { apiRequest } from '../../../services/api-client';

const PAPER = '#fffdf7';
const GREEN = '#07543a';
const INK = '#102b25';
const MUTED = '#52677a';

type WeatherAssessment = {
  alerts: { title: string; message: string; recommended_action: string }[];
};

function overviewTaskIcon(title: string): 'fertilizer' | 'weeds' | 'camera' | 'rain' {
  const lower = title.toLowerCase();
  if (/water|irrigat|drain/.test(lower)) return 'rain';
  if (/weed/.test(lower)) return 'weeds';
  if (/photo|scan|check-in|check in/.test(lower)) return 'camera';
  return 'fertilizer';
}

function formatDueDate(value: string | null): string {
  if (!value) return 'Any time';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return 'Upcoming';
  return date.toLocaleDateString([], { month: 'short', day: 'numeric' });
}

export default function FarmOverview() {
  const params = useLocalSearchParams<{ id?: string | string[] }>();
  const farmId = Array.isArray(params.id) ? params.id[0] : params.id;
  const { farmlands } = useAppContext();
  const farm = farmlands.find(item => item.id === farmId);
  const router = useRouter();
  const { width } = useHydrationSafeWindowDimensions();
  const compact = width < 380;
  const activeTasks = farm?.tasks.filter(task => task.status === 'pending') ?? [];
  const openProblems = farm?.problems.filter(problem => problem.status === 'open' || problem.status === 'monitoring') ?? [];
  const [weather, setWeather] = useState<WeatherAssessment | null>(null);
  const [weatherError, setWeatherError] = useState(false);
  const go = (route: string) => farmId && router.push(`/farmlands/${farmId}/${route}` as Href);

  useEffect(() => {
    if (!farmId) return;
    let active = true;
    apiRequest<WeatherAssessment>(`/weather/assessment/${encodeURIComponent(farmId)}`)
      .then(result => {
        if (active) {
          setWeather(result);
          setWeatherError(false);
        }
      })
      .catch(() => {
        if (active) {
          setWeather(null);
          setWeatherError(true);
        }
      });
    return () => { active = false; };
  }, [farmId]);

  if (!farm || !farmId) {
    return <SafeAreaView style={styles.safe} edges={['bottom', 'left', 'right']}><Text style={styles.empty}>Farm not found.</Text></SafeAreaView>;
  }

  const weatherAlert = weather?.alerts[0];
  const weatherStatus = weatherError ? 'Offline' : weather ? (weatherAlert ? 'Alert' : 'Clear') : 'Checking';
  const nextTask = activeTasks[0];

  return (
    <SafeAreaView style={styles.safe} edges={['bottom', 'left', 'right']}>
      <View style={styles.frame}>
        <View style={[styles.brandHeader, compact && styles.brandHeaderCompact]}>
          <Pressable accessibilityRole="button" accessibilityLabel="Back to farms" onPress={() => router.replace('/farmlands' as Href)} style={styles.headerBack}>
            <FarmChromeIcon name="back" size={22} color={GREEN} />
          </Pressable>
          <BrandPlantIcon size={compact ? 31 : 35} />
          <Text numberOfLines={1} style={styles.brandName}>FieldShift BD</Text>
          <Pressable accessibilityRole="button" accessibilityLabel="Open alerts" onPress={() => go('alerts')} style={styles.headerButton}>
            <DashboardIcon name="bell" size={25} color={GREEN} />
          </Pressable>
          <Pressable accessibilityRole="button" accessibilityLabel="Open profile" onPress={() => router.push('/farmlands/profile-setup' as Href)} style={styles.avatarButton}>
            <ImageBackground source={require('../../../../assets/images/landing-farmer.png')} resizeMode="cover" style={styles.avatarImage} imageStyle={styles.avatarImageAsset} />
          </Pressable>
        </View>

        <ScrollView style={styles.scroll} contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
          <Text numberOfLines={1} style={[styles.pageTitle, compact && styles.pageTitleCompact]}>{farm.name}</Text>

          <Pressable accessibilityRole="button" accessibilityLabel={`Open season plan for ${farm.crop}`} onPress={() => go('season-plan')} style={styles.cropCard}>
            <ImageBackground source={require('../../../../assets/images/verification-rice-field.png')} resizeMode="cover" style={styles.cropPhoto} imageStyle={styles.cropPhotoAsset}>
              <View style={styles.cropShade} />
              <View style={styles.cropTopRow}>
                <View style={styles.cropLabel}>
                  <FarmProfileIcon name="leaf" size={17} color={GREEN} />
                  <Text style={styles.cropLabelText}>Current crop</Text>
                </View>
                <View style={styles.heroArrow}><DashboardIcon name="chevron" size={17} color={GREEN} /></View>
              </View>
              <View style={styles.cropCopy}>
                <Text numberOfLines={1} style={styles.cropName}>{farm.crop}</Text>
                <Text numberOfLines={1} style={styles.cropStage}>{farm.activeSeasonId ? farm.growthStage : 'No active season'}</Text>
              </View>
              <View style={styles.cropMetaRow}>
                <View style={styles.metaChip}><DashboardIcon name="location" size={16} color={GREEN} /><Text numberOfLines={1} style={styles.metaChipText}>{farm.location ?? 'Location not set'}</Text></View>
                <View style={styles.metaChip}><DashboardIcon name="acreage" size={16} color={GREEN} /><Text style={styles.metaChipText}>{farm.acreage.toLocaleString(undefined, { maximumFractionDigits: 2 })} acres</Text></View>
              </View>
            </ImageBackground>
            <View style={styles.progressArea}>
              <View style={styles.progressHeading}>
                <Text style={styles.progressText}>{farm.seasonProgressPercent == null ? 'Start season plan' : `${farm.seasonProgressPercent}% complete`}</Text>
                <Text style={styles.progressLink}>Season plan</Text>
              </View>
              <View style={styles.progressTrack}><View style={[styles.progressDone, { width: `${farm.seasonProgressPercent ?? 0}%` }]} /></View>
            </View>
          </Pressable>

          <View style={styles.statusRow}>
            <StatusButton icon="tasks" value={String(activeTasks.length)} label="Tasks" onPress={() => go('tasks')} />
            <StatusButton icon="rain" value={weatherStatus} label="Weather" tone="sky" onPress={() => go('alerts')} />
            <StatusButton icon="warning" value={String(openProblems.length)} label="Issues" tone={openProblems.length ? 'warning' : 'plain'} onPress={() => go('problems')} />
          </View>

          {nextTask ? (
            <View style={styles.section}>
              <View style={styles.sectionHeading}>
                <Text style={styles.sectionTitle}>Next task</Text>
                {activeTasks.length > 1 ? <Pressable accessibilityRole="button" onPress={() => go('tasks')}><Text style={styles.sectionLink}>See all {activeTasks.length}</Text></Pressable> : null}
              </View>
              <Pressable accessibilityRole="button" onPress={() => go('tasks')} style={styles.taskCard}>
                <View style={styles.taskIcon}><DashboardIcon name={overviewTaskIcon(nextTask.title)} size={27} color={GREEN} /></View>
                <Text numberOfLines={2} style={styles.taskTitle}>{nextTask.title}</Text>
                <View style={styles.dueChip}><Text style={styles.dueText}>{formatDueDate(nextTask.dueAt)}</Text></View>
                <DashboardIcon name="chevron" size={18} color={MUTED} />
              </Pressable>
            </View>
          ) : null}

          {weatherAlert ? (
            <ActionCard
              icon="rain"
              label="Weather advice"
              title={weatherAlert.recommended_action || weatherAlert.title}
              onPress={() => go('alerts')}
              tone="weather"
            />
          ) : null}

          {openProblems[0] ? (
            <ActionCard
              icon="warning"
              label="Crop issue"
              title={openProblems[0].category}
              onPress={() => go('problems')}
              tone="warning"
            />
          ) : null}

          <View style={styles.quickRow}>
            <QuickAction icon="camera" label="Check in" onPress={() => go('check-ins')} />
            <QuickAction icon="grid" label="Farm info" onPress={() => go('resources')} />
          </View>
        </ScrollView>
        <FarmBottomNavigation active="Home" farmId={farmId} compact />
      </View>
    </SafeAreaView>
  );
}

function StatusButton({
  icon,
  value,
  label,
  tone = 'plain',
  onPress,
}: {
  icon: DashboardIconName;
  value: string;
  label: string;
  tone?: 'plain' | 'sky' | 'warning';
  onPress: () => void;
}) {
  const iconColor = tone === 'warning' ? '#d95120' : GREEN;
  return (
    <Pressable accessibilityRole="button" accessibilityLabel={`${label}: ${value}`} onPress={onPress} style={styles.statusCard}>
      <View style={[styles.statusIcon, tone === 'sky' && styles.statusIconSky, tone === 'warning' && styles.statusIconWarning]}>
        <DashboardIcon name={icon} size={24} color={iconColor} />
      </View>
      <Text numberOfLines={1} style={styles.statusValue}>{value}</Text>
      <Text style={styles.statusLabel}>{label}</Text>
    </Pressable>
  );
}

function ActionCard({
  icon,
  label,
  title,
  tone,
  onPress,
}: {
  icon: 'rain' | 'warning';
  label: string;
  title: string;
  tone: 'weather' | 'warning';
  onPress: () => void;
}) {
  return (
    <Pressable accessibilityRole="button" onPress={onPress} style={[styles.actionCard, tone === 'weather' ? styles.actionCardWeather : styles.actionCardWarning]}>
      <View style={[styles.actionIcon, tone === 'weather' ? styles.actionIconWeather : styles.actionIconWarning]}>
        <DashboardIcon name={icon} size={27} color={tone === 'weather' ? GREEN : '#d95120'} />
      </View>
      <View style={styles.actionCopy}>
        <Text style={styles.actionLabel}>{label}</Text>
        <Text numberOfLines={2} style={styles.actionTitle}>{title}</Text>
      </View>
      <View style={styles.actionArrow}><DashboardIcon name="chevron" size={18} color={GREEN} /></View>
    </Pressable>
  );
}

function QuickAction({ icon, label, onPress }: { icon: 'camera' | 'grid'; label: string; onPress: () => void }) {
  return (
    <Pressable accessibilityRole="button" onPress={onPress} style={styles.quickButton}>
      <View style={styles.quickIcon}><DashboardIcon name={icon} size={24} color={GREEN} /></View>
      <Text style={styles.quickText}>{label}</Text>
      <DashboardIcon name="chevron" size={17} color={MUTED} />
    </Pressable>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: PAPER },
  frame: { flex: 1, width: '100%', maxWidth: 500, alignSelf: 'center', backgroundColor: PAPER },
  brandHeader: { minHeight: 58, paddingHorizontal: 12, flexDirection: 'row', alignItems: 'center', gap: 8, borderBottomWidth: 1, borderBottomColor: '#ece9df' },
  brandHeaderCompact: { paddingHorizontal: 9, gap: 6 },
  headerBack: { width: 38, height: 38, flexShrink: 0, alignItems: 'center', justifyContent: 'center', borderRadius: 20, backgroundColor: '#edf2e7' },
  brandName: { flex: 1, color: INK, fontFamily: ENGLISH_FONT_FAMILY, fontSize: 18, lineHeight: 22, fontWeight: '700', letterSpacing: -0.3 },
  headerButton: { width: 36, height: 38, flexShrink: 0, alignItems: 'center', justifyContent: 'center' },
  avatarButton: { width: 40, height: 40, flexShrink: 0, overflow: 'hidden', borderRadius: 22, borderWidth: 1, borderColor: '#e3e0d6' },
  avatarImage: { width: 40, height: 40 },
  avatarImageAsset: { borderRadius: 22 },
  scroll: { flex: 1, minHeight: 0 },
  content: { paddingHorizontal: 14, paddingTop: 14, paddingBottom: 18, gap: 14 },
  pageTitle: { color: INK, fontFamily: ENGLISH_FONT_FAMILY, fontSize: 29, lineHeight: 35, fontWeight: '700', letterSpacing: -0.7 },
  pageTitleCompact: { fontSize: 25, lineHeight: 31 },
  cropCard: { overflow: 'hidden', borderRadius: 22, borderWidth: 1, borderColor: '#e7e4da', backgroundColor: '#fffefa', boxShadow: '0px 4px 12px rgba(30, 54, 37, 0.09)', elevation: 2 },
  cropPhoto: { height: 190, padding: 14, justifyContent: 'space-between' },
  cropPhotoAsset: { borderTopLeftRadius: 21, borderTopRightRadius: 21 },
  cropShade: { ...StyleSheet.absoluteFill, backgroundColor: 'rgba(7, 48, 38, 0.28)' },
  cropTopRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  cropLabel: { minHeight: 34, paddingHorizontal: 10, flexDirection: 'row', alignItems: 'center', gap: 6, borderRadius: 18, backgroundColor: 'rgba(255,253,247,0.94)' },
  cropLabelText: { color: GREEN, fontFamily: ENGLISH_FONT_FAMILY, fontSize: 12, lineHeight: 16, fontWeight: '700' },
  heroArrow: { width: 34, height: 34, alignItems: 'center', justifyContent: 'center', borderRadius: 18, backgroundColor: 'rgba(255,253,247,0.94)' },
  cropCopy: { marginTop: 'auto', marginBottom: 10 },
  cropName: { color: PAPER, fontFamily: ENGLISH_FONT_FAMILY, fontSize: 34, lineHeight: 39, fontWeight: '700', letterSpacing: -0.8 },
  cropStage: { marginTop: 2, color: '#f4f8f4', fontFamily: ENGLISH_FONT_FAMILY, fontSize: 16, lineHeight: 21, fontWeight: '600' },
  cropMetaRow: { flexDirection: 'row', gap: 7 },
  metaChip: { minHeight: 32, maxWidth: '68%', flexShrink: 1, paddingHorizontal: 9, flexDirection: 'row', alignItems: 'center', gap: 5, borderRadius: 16, backgroundColor: 'rgba(255,253,247,0.94)' },
  metaChipText: { flexShrink: 1, color: '#25483f', fontFamily: ENGLISH_FONT_FAMILY, fontSize: 12, lineHeight: 16, fontWeight: '600' },
  progressArea: { paddingHorizontal: 14, paddingVertical: 12 },
  progressHeading: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  progressText: { color: INK, fontFamily: ENGLISH_FONT_FAMILY, fontSize: 14, lineHeight: 18, fontWeight: '700' },
  progressLink: { color: GREEN, fontFamily: ENGLISH_FONT_FAMILY, fontSize: 12, lineHeight: 16, fontWeight: '600' },
  progressTrack: { height: 8, marginTop: 9, overflow: 'hidden', borderRadius: 5, backgroundColor: '#e4e6df' },
  progressDone: { height: '100%', borderRadius: 5, backgroundColor: GREEN },
  statusRow: { flexDirection: 'row', gap: 9 },
  statusCard: { flex: 1, minWidth: 0, minHeight: 112, alignItems: 'center', justifyContent: 'center', paddingHorizontal: 5, borderWidth: 1, borderColor: '#e8e5dc', borderRadius: 18, backgroundColor: '#fffefa' },
  statusIcon: { width: 43, height: 43, alignItems: 'center', justifyContent: 'center', borderRadius: 23, backgroundColor: '#eaf2e5' },
  statusIconSky: { backgroundColor: '#1b6b65' },
  statusIconWarning: { backgroundColor: '#fff0dd' },
  statusValue: { maxWidth: '100%', marginTop: 6, color: INK, fontFamily: ENGLISH_FONT_FAMILY, fontSize: 18, lineHeight: 22, fontWeight: '700', textAlign: 'center' },
  statusLabel: { marginTop: 1, color: MUTED, fontFamily: ENGLISH_FONT_FAMILY, fontSize: 12, lineHeight: 16 },
  section: { gap: 8 },
  sectionHeading: { minHeight: 25, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  sectionTitle: { color: INK, fontFamily: ENGLISH_FONT_FAMILY, fontSize: 20, lineHeight: 25, fontWeight: '700' },
  sectionLink: { color: GREEN, fontFamily: ENGLISH_FONT_FAMILY, fontSize: 13, lineHeight: 17, fontWeight: '700' },
  taskCard: { minHeight: 78, paddingHorizontal: 11, flexDirection: 'row', alignItems: 'center', gap: 9, borderWidth: 1, borderColor: '#e7e4da', borderRadius: 18, backgroundColor: '#fffefa' },
  taskIcon: { width: 48, height: 48, flexShrink: 0, alignItems: 'center', justifyContent: 'center', borderRadius: 25, backgroundColor: '#eaf2e5' },
  taskTitle: { flex: 1, minWidth: 0, color: INK, fontFamily: ENGLISH_FONT_FAMILY, fontSize: 15, lineHeight: 20, fontWeight: '700' },
  dueChip: { minHeight: 30, paddingHorizontal: 9, alignItems: 'center', justifyContent: 'center', borderRadius: 16, backgroundColor: '#fff0d8' },
  dueText: { color: '#b94f20', fontFamily: ENGLISH_FONT_FAMILY, fontSize: 11, lineHeight: 15, fontWeight: '700' },
  actionCard: { minHeight: 86, padding: 12, flexDirection: 'row', alignItems: 'center', gap: 11, borderWidth: 1, borderRadius: 18 },
  actionCardWeather: { borderColor: '#cfe1de', backgroundColor: '#edf6f3' },
  actionCardWarning: { borderColor: '#f0d8c7', backgroundColor: '#fff5e9' },
  actionIcon: { width: 50, height: 50, flexShrink: 0, alignItems: 'center', justifyContent: 'center', borderRadius: 26 },
  actionIconWeather: { backgroundColor: '#1b6b65' },
  actionIconWarning: { backgroundColor: '#ffe5cf' },
  actionCopy: { flex: 1, minWidth: 0 },
  actionLabel: { color: MUTED, fontFamily: ENGLISH_FONT_FAMILY, fontSize: 12, lineHeight: 16, fontWeight: '600' },
  actionTitle: { marginTop: 2, color: INK, fontFamily: ENGLISH_FONT_FAMILY, fontSize: 15, lineHeight: 20, fontWeight: '700' },
  actionArrow: { width: 34, height: 34, flexShrink: 0, alignItems: 'center', justifyContent: 'center', borderRadius: 18, backgroundColor: PAPER },
  quickRow: { flexDirection: 'row', gap: 9 },
  quickButton: { flex: 1, minWidth: 0, minHeight: 62, paddingHorizontal: 10, flexDirection: 'row', alignItems: 'center', gap: 8, borderWidth: 1, borderColor: '#e7e4da', borderRadius: 17, backgroundColor: '#fffefa' },
  quickIcon: { width: 38, height: 38, flexShrink: 0, alignItems: 'center', justifyContent: 'center', borderRadius: 20, backgroundColor: '#eaf2e5' },
  quickText: { flex: 1, color: INK, fontFamily: ENGLISH_FONT_FAMILY, fontSize: 14, lineHeight: 18, fontWeight: '700' },
  empty: { color: MUTED, fontFamily: ENGLISH_FONT_FAMILY, fontSize: 15, textAlign: 'center', padding: 24 },
});
