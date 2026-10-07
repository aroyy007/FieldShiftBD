import { useEffect, useState } from 'react';
import {
  Image,
  ImageBackground,
  Modal,
  Platform,
  Pressable,
  RefreshControl,
  ScrollView,
  StyleSheet,
  Text,
  View,
  useWindowDimensions,
} from 'react-native';
import Svg, { Path } from 'react-native-svg';
import { Href, useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { BrandPlantIcon } from '../../components/icons';
import { DashboardIcon, DashboardIconName, LeafSpotIllustration } from '../../components/dashboard-icons';
import { useAppContext } from '../../context/AppProvider';
import { apiRequest } from '../../services/api-client';
import { getTaskScheduleState } from '../../utils/task-dates';

const PAPER = '#fffdf7';
const INK = '#0a392f';
const GREEN = '#145f3b';
const MUTED = '#647581';
const SERIF = 'Georgia';
const SANS = 'Arial';

type Tab = { title: string; icon: DashboardIconName; route?: string };
const TABS: Tab[] = [
  { title: 'Home', icon: 'home' },
  { title: 'Tasks', icon: 'tasks', route: 'tasks' },
  { title: 'Chat', icon: 'chat', route: 'chat' },
  { title: 'Scan', icon: 'scan', route: 'crop-health' },
  { title: 'Profile', icon: 'profile' },
];

type WeatherAlert = { title: string; message: string; recommended_action: string; severity: string };
type WeatherAssessment = { alerts: WeatherAlert[] };

function taskIcon(title: string): DashboardIconName {
  const lower = title.toLowerCase();
  if (/water|irrigat|drain/.test(lower)) return 'rain';
  if (/weed/.test(lower)) return 'weeds';
  if (/fertili|urea|nitrogen/.test(lower)) return 'fertilizer';
  if (/photo|scan|check-in/.test(lower)) return 'camera';
  return 'tasks';
}

export default function AllFarmlands() {
  const { user, farmlands, logout, authLoading, dataLoading, refreshProfile } = useAppContext();
  const router = useRouter();
  const { width } = useWindowDimensions();
  const compact = width < 380;
  const [profileOpen, setProfileOpen] = useState(false);
  const farm = farmlands[0];
  const ScreenContainer = Platform.OS === 'web' ? View : SafeAreaView;
  const [weather, setWeather] = useState<WeatherAssessment | null>(null);
  const [weatherError, setWeatherError] = useState('');
  const now = new Date();
  const dueTasks = farm?.tasks.filter(task => {
    const state = getTaskScheduleState(task, now);
    return state === 'due' || state === 'overdue' || state === 'unscheduled';
  }) ?? [];
  const openProblem = farm?.problems.find(problem => problem.status === 'open' || problem.status === 'monitoring');

  useEffect(() => {
    if (!authLoading && !user) router.replace('/auth/login' as Href);
  }, [authLoading, router, user]);

  useEffect(() => {
    if (!farm?.id) return;
    let active = true;
    apiRequest<WeatherAssessment>(`/weather/assessment/${encodeURIComponent(farm.id)}`)
      .then(result => { if (active) setWeather(result); })
      .catch(error => {
        if (active) {
          setWeather(null);
          setWeatherError(error instanceof Error ? error.message : 'Weather assessment is unavailable.');
        }
      });
    return () => { active = false; };
  }, [farm?.id]);

  const refresh = () => { void refreshProfile().catch(() => undefined); };

  const openFarmSection = (section: string) => {
    if (!farm) {
      router.push('/farmlands/add' as Href);
      return;
    }
    router.push(`/farmlands/${farm.id}/${section}` as Href);
  };

  const onTabPress = (tab: Tab) => {
    if (tab.title === 'Profile') {
      setProfileOpen(true);
    } else if (tab.route) {
      openFarmSection(tab.route);
    } else {
      router.push('/farmlands' as Href);
    }
  };

  if (!user) return null;

  return (
    <ScreenContainer style={styles.safe}>
      <View style={styles.page}>
        <View style={styles.header}>
          <View style={styles.brand}>
            <BrandPlantIcon size={31} />
            <View>
              <Text style={styles.brandName}>FieldShift BD</Text>
              <Text style={styles.brandTagline}>AI Farmer Assistant</Text>
            </View>
          </View>
          <View style={styles.headerActions}>
            <Pressable
              accessibilityRole="button"
              accessibilityLabel="View notifications"
              onPress={() => openFarmSection('alerts')}
              style={styles.bellButton}
            >
              <DashboardIcon name="bell" size={25} color={GREEN} />
            </Pressable>
            <Pressable
              accessibilityRole="button"
              accessibilityLabel="Open profile"
              onPress={() => setProfileOpen(true)}
              style={styles.avatarButton}
            >
              <Image source={require('../../../assets/images/landing-farmer.png')} style={styles.avatar} />
            </Pressable>
          </View>
        </View>

        <View style={styles.intro}>
          <Text numberOfLines={1} adjustsFontSizeToFit style={styles.greeting}>Good morning, {user.name.split(' ')[0]}</Text>
          <Text numberOfLines={1} adjustsFontSizeToFit style={styles.subtitle}>Here’s what needs attention on your farm today.</Text>
        </View>

        <ScrollView
          style={styles.scroll}
          contentContainerStyle={styles.scrollContent}
          showsVerticalScrollIndicator={false}
          bounces={false}
          refreshControl={<RefreshControl refreshing={dataLoading} onRefresh={refresh} tintColor={GREEN} />}
        >
          {!farm ? (
            <View style={styles.noFarmCard}>
              <BrandPlantIcon size={38} />
              <Text style={styles.noFarmTitle}>{dataLoading ? 'Loading your farms…' : 'No farmland saved yet'}</Text>
              <Text style={styles.noFarmText}>Add a farmland to get crop advice, tasks, and field records from your account.</Text>
              <Pressable accessibilityRole="button" onPress={() => router.push('/farmlands/add' as Href)} style={styles.noFarmButton}>
                <Text style={styles.noFarmButtonText}>Add farmland</Text>
              </Pressable>
            </View>
          ) : <>
          <Pressable
            accessibilityRole="button"
            accessibilityLabel="Open current season plan"
            onPress={() => openFarmSection('season-plan')}
            style={styles.seasonCard}
          >
            <ImageBackground
              source={require('../../../assets/images/verification-rice-field.png')}
              style={styles.seasonImage}
              imageStyle={styles.seasonImageAsset}
            >
              <View pointerEvents="none" style={styles.seasonWash} />
              <View pointerEvents="none" style={styles.seasonWashBandOne} />
              <View pointerEvents="none" style={styles.seasonWashBandTwo} />
              <View pointerEvents="none" style={styles.seasonWashBandThree} />
              <View style={styles.seasonCopy}>
                <View style={styles.seasonEyebrow}>
                  <View style={styles.seasonLeaf}>
                    <BrandPlantIcon size={17} />
                  </View>
                  <Text style={styles.seasonLabel}>Current season</Text>
                </View>
                <Text numberOfLines={1} style={styles.cropName}>{farm.crop}</Text>
                <Text numberOfLines={1} style={styles.growthLine}>{farm.growthStage}</Text>
                <Text numberOfLines={2} style={styles.seasonDescription}>
                  {farm.activeSeasonId ? `${farm.crop} season is active on this farmland.` : 'No active crop season. Choose a crop in Crop Advisor to begin.'}
                </Text>
                <View style={styles.farmDetails}>
                  <View style={styles.detailChip}>
                    <DashboardIcon name="location" size={15} color={GREEN} />
                    <Text numberOfLines={1} style={styles.detailText}>{farm.location ?? 'Location not set'}</Text>
                  </View>
                  <View style={styles.detailChip}>
                    <DashboardIcon name="acreage" size={15} color={GREEN} />
                    <Text style={styles.detailText}>{farm.acreage.toLocaleString(undefined, { maximumFractionDigits: 2 })} acres</Text>
                  </View>
                </View>
              </View>
            </ImageBackground>
            <View style={styles.timeline}>
              <Text style={styles.weekLabel}>
                {farm.seasonProgressPercent == null ? 'No active season' : `Season progress ${farm.seasonProgressPercent}%`}
              </Text>
              <View style={styles.phaseTrack}>
                <View style={styles.trackBase} />
                <View style={[styles.trackComplete, { width: `${farm.seasonProgressPercent ?? 0}%` }]} />
                {farm.seasonPlan.map(stage => (
                  <View key={stage.id} style={styles.phase}>
                    <View style={[styles.phaseDot, stage.status === 'current' && styles.phaseDotCurrent]}>
                      {stage.status === 'current' ? <View style={styles.phaseDotCenter} /> : null}
                    </View>
                    <Text numberOfLines={1} style={[styles.phaseText, stage.status === 'current' && styles.phaseTextCurrent]}>{stage.name}</Text>
                  </View>
                ))}
              </View>
            </View>
          </Pressable>

          <View style={styles.priorityCard}>
            <View style={styles.priorityHeader}>
              <View style={styles.priorityTitleGroup}>
                <DashboardIcon name="tasks" size={20} color={GREEN} />
                <Text style={[styles.sectionTitle, compact && styles.sectionTitleCompact]}>Today’s priorities</Text>
              </View>
              <Pressable accessibilityRole="button" onPress={() => openFarmSection('tasks')} style={styles.taskCount}>
                <Text style={[styles.taskCountText, compact && styles.taskCountTextCompact]}>{dueTasks.length} tasks to review</Text>
                <DashboardIcon name="chevron" size={15} color="#41566a" />
              </Pressable>
            </View>
            <View style={styles.priorityRows}>
              {dueTasks.slice(0, 3).map((task) => (
                <Pressable
                  key={task.id}
                  accessibilityRole="button"
                  onPress={() => openFarmSection('tasks')}
                  style={[styles.priorityRow, compact && styles.priorityRowCompact]}
                >
                  <View style={styles.priorityIconCircle}>
                    <DashboardIcon name={taskIcon(task.title)} size={23} color={GREEN} />
                  </View>
                  <View style={styles.priorityCopy}>
                    <Text numberOfLines={1} style={styles.priorityTaskTitle}>{task.title}</Text>
                    <Text numberOfLines={compact ? 2 : 1} style={styles.priorityTaskSubtitle}>{task.description || task.priority}</Text>
                  </View>
                  <View style={styles.duePill}><Text style={styles.dueText}>{getTaskScheduleState(task, now)}</Text></View>
                  <View style={styles.priorityChevron}><DashboardIcon name="chevron" size={15} color="#50647a" /></View>
                </Pressable>
              ))}
              {dueTasks.length === 0 ? <Text style={styles.emptyTaskText}>No tasks are due or overdue.</Text> : null}
            </View>
          </View>

          <Pressable
            accessibilityRole="button"
            accessibilityLabel="View weather forecast"
            onPress={() => openFarmSection('alerts')}
            style={[styles.weatherCard, compact && styles.weatherCardCompact]}
          >
            <ImageBackground
              source={require('../../../assets/images/verification-rice-field.png')}
              style={styles.weatherImage}
              imageStyle={styles.weatherImageAsset}
            >
                <View style={styles.weatherShade} />
                <Svg width="100%" height="100%" viewBox="0 0 360 110" preserveAspectRatio="none" style={styles.rainOverlay}>
                  {Array.from({ length: 24 }, (_, index) => {
                    const x = (index * 47) % 360;
                    const y = (index * 29) % 100;
                    return <Path key={index} d={`M${x} ${y}l-7 13`} stroke="#d9edf0" strokeOpacity="0.32" strokeWidth="1" strokeLinecap="round" />;
                  })}
                </Svg>
              <View style={styles.weatherTop}>
                <View style={styles.weatherIconCircle}><DashboardIcon name="rain" size={26} color="#f6ffff" /></View>
                <View style={styles.weatherTextBlock}>
                  <Text numberOfLines={1} style={styles.weatherTitle}>{weather?.alerts[0]?.title ?? (weatherError ? 'Weather assessment unavailable' : 'Weather assessment')}</Text>
                  <Text numberOfLines={2} style={styles.weatherDescription}>{weather?.alerts[0]?.message ?? (weatherError || 'No actionable weather warning is currently returned for this farm.')}</Text>
                </View>
              </View>
              <View style={[styles.weatherBottom, compact && styles.weatherBottomCompact]}>
                <View style={styles.adviceBox}>
                  <View style={styles.bulbCircle}><DashboardIcon name="bulb" size={21} color="#c88b08" /></View>
                  <Text numberOfLines={compact ? 3 : 2} style={styles.adviceText}>{weather?.alerts[0]?.recommended_action ?? 'Open weather details to review provider availability and farm-specific alerts.'}</Text>
                </View>
                <View style={[styles.forecastButton, compact && styles.forecastButtonCompact]}>
                  <Text style={styles.forecastText}>View forecast</Text>
                  <View style={styles.forecastArrow}><DashboardIcon name="chevron" size={16} color={GREEN} /></View>
                </View>
              </View>
            </ImageBackground>
          </Pressable>

          <View style={styles.quickSection}>
            <View style={styles.quickHeading}>
              <DashboardIcon name="grid" size={19} color={GREEN} />
              <Text style={[styles.sectionTitle, compact && styles.sectionTitleCompact]}>Quick actions</Text>
            </View>
            <View style={styles.quickActions}>
              <QuickAction compact={compact} icon="assistant" title="Ask Assistant" subtitle="Get expert advice" onPress={() => openFarmSection('chat')} />
              <QuickAction compact={compact} icon="scan" title="Scan Leaf" subtitle="Detect problems" onPress={() => openFarmSection('crop-health')} accent="gold" />
              <QuickAction compact={compact} icon="calendar" title="Season Plan" subtitle="View your plan" onPress={() => openFarmSection('season-plan')} />
            </View>
          </View>

          {openProblem ? <Pressable
            accessibilityRole="button"
            accessibilityLabel="View open farm problem"
            onPress={() => openFarmSection('problems')}
            style={[styles.issueCard, compact && styles.issueCardCompact]}
          >
            <View style={styles.leafImage}><LeafSpotIllustration /></View>
            <View style={styles.issueCopy}>
              <View style={styles.issueEyebrow}>
                <DashboardIcon name="warning" size={14} color="#e26616" />
              <Text style={styles.issueLabel}>{openProblem.status === 'monitoring' ? 'Monitoring' : 'Open issue'}</Text>
              </View>
            <Text numberOfLines={1} style={styles.issueTitle}>{openProblem.category}</Text>
            <Text numberOfLines={compact ? 2 : 1} style={styles.issueDescription}>{openProblem.description}</Text>
            </View>
            <View style={styles.issueArrow}><DashboardIcon name="chevron" size={15} color="#50647a" /></View>
          </Pressable> : null}
          </>}
        </ScrollView>

        <View style={styles.tabBar}>
          {TABS.map((tab) => {
            const active = tab.title === 'Home';
            return (
              <Pressable
                key={tab.title}
                accessibilityRole="button"
                accessibilityLabel={tab.title}
                accessibilityState={{ selected: active }}
                onPress={() => onTabPress(tab)}
                style={styles.tabButton}
              >
                <View style={[styles.tabActive, active && styles.tabActiveSelected]}>
                  <DashboardIcon name={tab.icon} size={21} color={active ? GREEN : '#758293'} />
                  <Text style={[styles.tabLabel, active && styles.tabLabelActive]}>{tab.title}</Text>
                </View>
              </Pressable>
            );
          })}
        </View>
      </View>

      <Modal
        visible={profileOpen}
        transparent
        animationType="fade"
        onRequestClose={() => setProfileOpen(false)}
      >
        <Pressable style={styles.modalBackdrop} onPress={() => setProfileOpen(false)}>
          <View style={styles.profileCard}>
            <Text style={styles.profileTitle}>{user.name}</Text>
            <Text style={styles.profilePhone}>{user.phone}</Text>
            <Pressable
              accessibilityRole="button"
              onPress={() => {
                setProfileOpen(false);
                router.push('/farmlands/profile-setup' as Href);
              }}
              style={styles.manageButton}
            >
              <Text style={styles.manageText}>Map your farm</Text>
            </Pressable>
            <Pressable
              accessibilityRole="button"
              onPress={() => {
                setProfileOpen(false);
                router.push('/farmlands/manage' as Href);
              }}
              style={styles.manageButton}
            >
              <Text style={styles.manageText}>My farmlands</Text>
            </Pressable>
            <Pressable
              accessibilityRole="button"
              onPress={() => {
                setProfileOpen(false);
                logout();
                router.replace('/auth/login' as Href);
              }}
              style={styles.logoutButton}
            >
              <Text style={styles.logoutText}>Log out</Text>
            </Pressable>
          </View>
        </Pressable>
      </Modal>
    </ScreenContainer>
  );
}

function QuickAction({
  icon,
  title,
  subtitle,
  onPress,
  accent = 'green',
  compact = false,
}: {
  icon: DashboardIconName;
  title: string;
  subtitle: string;
  onPress: () => void;
  accent?: 'green' | 'gold';
  compact?: boolean;
}) {
  return (
    <Pressable
      accessibilityRole="button"
      onPress={onPress}
      style={[styles.quickActionCard, compact && styles.quickActionCardCompact, accent === 'gold' && styles.quickActionGold]}
    >
      <View style={[styles.quickIconBox, accent === 'gold' && styles.quickIconGold]}>
        <DashboardIcon name={icon} size={23} color={accent === 'gold' ? '#165e3a' : GREEN} />
      </View>
      <View style={styles.quickCopy}>
        <Text numberOfLines={2} style={styles.quickTitle}>{title}</Text>
        <Text numberOfLines={2} style={styles.quickSubtitle}>{subtitle}</Text>
      </View>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: PAPER },
  page: { flex: 1, minHeight: 0, overflow: 'hidden', width: '100%', maxWidth: 480, alignSelf: 'center', backgroundColor: PAPER },
  header: {
    minHeight: 42,
    marginTop: 5,
    paddingHorizontal: 20,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  brand: { flexDirection: 'row', alignItems: 'center', gap: 6 },
  brandName: { color: INK, fontFamily: SERIF, fontWeight: '700', fontSize: 17, lineHeight: 20, letterSpacing: -0.4 },
  brandTagline: { color: MUTED, fontFamily: SANS, fontSize: 11.5, lineHeight: 14 },
  headerActions: { flexDirection: 'row', alignItems: 'center', gap: 12 },
  bellButton: { width: 30, height: 36, alignItems: 'center', justifyContent: 'center' },
  avatarButton: { width: 38, height: 38, borderRadius: 20, padding: 2, backgroundColor: '#fff', borderWidth: 1, borderColor: '#e9e6d8' },
  avatar: { width: '100%', height: '100%', borderRadius: 18 },
  intro: { marginTop: 10, marginBottom: 9, paddingHorizontal: 21 },
  noFarmCard: { minHeight: 245, padding: 22, alignItems: 'center', justifyContent: 'center', gap: 10, borderRadius: 18, borderWidth: 1, borderColor: '#e9e7df', backgroundColor: '#fffefa' },
  noFarmTitle: { color: INK, fontFamily: SERIF, fontSize: 21, fontWeight: '700', textAlign: 'center' },
  noFarmText: { maxWidth: 290, color: MUTED, fontFamily: SANS, fontSize: 13, lineHeight: 18, textAlign: 'center' },
  noFarmButton: { minHeight: 40, marginTop: 3, paddingHorizontal: 22, justifyContent: 'center', borderRadius: 22, backgroundColor: GREEN },
  noFarmButtonText: { color: PAPER, fontFamily: SANS, fontSize: 14, fontWeight: '600' },
  greeting: { color: '#073c32', fontFamily: SERIF, fontSize: 26, fontWeight: '700', lineHeight: 31, letterSpacing: -0.8 },
  subtitle: { color: MUTED, fontFamily: SANS, fontSize: 14, lineHeight: 19, letterSpacing: -0.1 },
  scroll: { flex: 1, minHeight: 0 },
  scrollContent: { paddingHorizontal: 16, paddingTop: 1, paddingBottom: 7, gap: 7 },
  seasonCard: {
    overflow: 'hidden',
    borderRadius: 15,
    borderWidth: 1,
    borderColor: '#fff',
    backgroundColor: '#fffefa',
    boxShadow: '0px 3px 11px rgba(30, 54, 37, 0.08)',
    elevation: 2,
  },
  seasonImage: { height: 116, overflow: 'hidden', justifyContent: 'center' },
  seasonImageAsset: { resizeMode: 'cover', opacity: 0.98 },
  seasonWash: { position: 'absolute', left: 0, top: 0, bottom: 0, width: '48%', backgroundColor: 'rgba(255,253,247,0.98)' },
  seasonWashBandOne: { position: 'absolute', left: '45%', top: 0, bottom: 0, width: '10%', backgroundColor: 'rgba(255,253,247,0.88)' },
  seasonWashBandTwo: { position: 'absolute', left: '54%', top: 0, bottom: 0, width: '10%', backgroundColor: 'rgba(255,253,247,0.62)' },
  seasonWashBandThree: { position: 'absolute', left: '63%', top: 0, bottom: 0, width: '10%', backgroundColor: 'rgba(255,253,247,0.28)' },
  seasonCopy: { paddingHorizontal: 10, paddingVertical: 4, alignSelf: 'stretch' },
  seasonEyebrow: { height: 19, flexDirection: 'row', alignItems: 'center', gap: 5 },
  seasonLeaf: { width: 18, height: 18, borderRadius: 9, backgroundColor: 'rgba(239,245,232,0.9)', alignItems: 'center', justifyContent: 'center' },
  seasonLabel: { color: '#52647e', fontFamily: SANS, fontSize: 11.5, lineHeight: 15 },
  cropName: { color: INK, fontFamily: SERIF, fontSize: 24, fontWeight: '700', lineHeight: 27, letterSpacing: -0.7 },
  growthLine: { color: INK, fontFamily: SERIF, fontSize: 13.5, fontWeight: '700', lineHeight: 16, letterSpacing: -0.25 },
  dot: { color: GREEN, fontSize: 14 },
  seasonDescription: { width: 177, color: MUTED, fontFamily: SANS, fontSize: 11.5, lineHeight: 14 },
  farmDetails: { flexDirection: 'row', alignItems: 'center', gap: 6, marginTop: 2 },
  detailChip: { height: 23, paddingHorizontal: 7, flexDirection: 'row', alignItems: 'center', gap: 4, borderRadius: 10, borderWidth: 1, borderColor: '#e2e9d9', backgroundColor: 'rgba(246,248,240,0.93)' },
  detailText: { color: '#435b6d', fontFamily: SANS, fontSize: 10.7, lineHeight: 14 },
  timeline: { height: 45, paddingHorizontal: 10, paddingTop: 3, backgroundColor: '#fffefa' },
  weekLabel: { color: '#152c2d', fontFamily: SANS, fontWeight: '600', fontSize: 10.5, lineHeight: 13 },
  phaseTrack: { height: 28, flexDirection: 'row', justifyContent: 'space-between', position: 'relative' },
  trackBase: { position: 'absolute', left: 7, right: 7, top: 5, height: 3, borderRadius: 2, backgroundColor: '#e4e5db' },
  trackComplete: { position: 'absolute', left: 7, top: 5, width: '36%', height: 3, borderRadius: 2, backgroundColor: '#4c9467' },
  phase: { flex: 1, alignItems: 'center', zIndex: 1 },
  phaseDot: { width: 12, height: 12, borderRadius: 8, borderWidth: 1, borderColor: '#ece8da', backgroundColor: '#faf8ee', alignItems: 'center', justifyContent: 'center' },
  phaseDotCurrent: { width: 18, height: 18, marginTop: -3, borderWidth: 3, borderColor: GREEN, backgroundColor: '#fffefa' },
  phaseDotCenter: { width: 6, height: 6, borderRadius: 4, backgroundColor: GREEN },
  phaseText: { position: 'absolute', top: 13, left: 0, right: 0, textAlign: 'center', color: '#52647e', fontFamily: SANS, fontSize: 9.3, lineHeight: 12 },
  phaseTextCurrent: { top: 13, color: INK, fontWeight: '600' },
  priorityCard: { paddingHorizontal: 7, paddingTop: 6, paddingBottom: 7, borderRadius: 15, backgroundColor: '#fffefa', borderWidth: 1, borderColor: '#fff', boxShadow: '0px 3px 11px rgba(30, 54, 37, 0.08)', elevation: 2 },
  priorityHeader: { minHeight: 23, paddingHorizontal: 3, marginBottom: 3, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 4 },
  priorityTitleGroup: { flexDirection: 'row', alignItems: 'center', gap: 7, flexShrink: 1 },
  sectionTitle: { color: INK, fontFamily: SERIF, fontSize: 17.5, lineHeight: 22, fontWeight: '700', letterSpacing: -0.35 },
  sectionTitleCompact: { fontSize: 15.5, lineHeight: 19 },
  taskCount: { flexDirection: 'row', alignItems: 'center', gap: 3, paddingVertical: 3, paddingLeft: 3 },
  taskCountText: { color: '#182e41', fontFamily: SANS, fontSize: 10.5, lineHeight: 14 },
  taskCountTextCompact: { fontSize: 9.4, lineHeight: 12 },
  priorityRows: { gap: 3 },
  emptyTaskText: { paddingVertical: 12, color: MUTED, fontFamily: SANS, fontSize: 12, textAlign: 'center' },
  priorityRow: { minHeight: 35, flexDirection: 'row', alignItems: 'center', paddingHorizontal: 5, gap: 6, borderRadius: 13, borderWidth: 1, borderColor: '#f1eee5', backgroundColor: '#fffefa' },
  priorityRowCompact: { minHeight: 39 },
  priorityIconCircle: { width: 30, height: 30, borderRadius: 16, backgroundColor: '#edf3e8', alignItems: 'center', justifyContent: 'center' },
  priorityCopy: { flex: 1, minWidth: 0 },
  priorityTaskTitle: { color: '#172c35', fontFamily: SERIF, fontSize: 13.5, lineHeight: 16, fontWeight: '700', letterSpacing: -0.2 },
  priorityTaskSubtitle: { color: '#52647e', fontFamily: SANS, fontSize: 10.4, lineHeight: 13 },
  duePill: { paddingHorizontal: 7, height: 23, borderRadius: 14, backgroundColor: '#ffedca', alignItems: 'center', justifyContent: 'center' },
  dueText: { color: '#ad510e', fontFamily: SANS, fontSize: 10.3, lineHeight: 13 },
  priorityChevron: { width: 22, height: 22, borderRadius: 12, backgroundColor: '#fff', borderWidth: 1, borderColor: '#f2efe7', alignItems: 'center', justifyContent: 'center' },
  weatherCard: { height: 105, overflow: 'hidden', borderRadius: 14, borderWidth: 1, borderColor: '#fff', boxShadow: '0px 3px 11px rgba(30, 54, 37, 0.08)', elevation: 2 },
  weatherCardCompact: { height: 116 },
  weatherImage: { flex: 1, paddingHorizontal: 8, paddingVertical: 7, justifyContent: 'space-between' },
  weatherImageAsset: { resizeMode: 'cover', opacity: 0.78 },
  weatherShade: { ...StyleSheet.absoluteFill, backgroundColor: 'rgba(8, 49, 62, 0.64)' },
  rainOverlay: { position: 'absolute', left: 0, top: 0 },
  weatherTop: { flexDirection: 'row', alignItems: 'center', gap: 8, minHeight: 45 },
  weatherIconCircle: { width: 39, height: 39, borderRadius: 22, backgroundColor: '#e9f6f6', alignItems: 'center', justifyContent: 'center' },
  weatherTextBlock: { flex: 1, minWidth: 0 },
  weatherTitle: { color: '#fffdf7', fontFamily: SERIF, fontSize: 15.5, lineHeight: 18, fontWeight: '700', letterSpacing: -0.3 },
  weatherDescription: { color: '#f5fbfb', fontFamily: SANS, fontSize: 10.7, lineHeight: 13 },
  weatherBottom: { height: 34, flexDirection: 'row', alignItems: 'center', gap: 6 },
  weatherBottomCompact: { height: 40 },
  adviceBox: { flex: 1, minWidth: 0, height: 34, flexDirection: 'row', alignItems: 'center', gap: 6, paddingHorizontal: 5, borderRadius: 10, backgroundColor: 'rgba(255,253,247,0.97)' },
  bulbCircle: { width: 27, height: 27, borderRadius: 15, backgroundColor: '#fff0bb', alignItems: 'center', justifyContent: 'center' },
  adviceText: { flex: 1, color: '#18303b', fontFamily: SANS, fontSize: 9.5, lineHeight: 11.5 },
  forecastButton: { width: 107, height: 33, paddingLeft: 9, paddingRight: 3, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', borderWidth: 1, borderColor: '#fff', borderRadius: 18, backgroundColor: 'rgba(10,71,52,0.92)' },
  forecastButtonCompact: { width: 94 },
  forecastText: { color: '#fffdf7', fontFamily: SANS, fontSize: 10.6, lineHeight: 14 },
  forecastArrow: { width: 27, height: 27, borderRadius: 14, backgroundColor: '#fffefa', alignItems: 'center', justifyContent: 'center' },
  quickSection: { gap: 4 },
  quickHeading: { height: 20, paddingHorizontal: 3, flexDirection: 'row', alignItems: 'center', gap: 7 },
  quickActions: { flexDirection: 'row', gap: 5 },
  quickActionCard: { flex: 1, minWidth: 0, height: 42, paddingHorizontal: 5, flexDirection: 'row', alignItems: 'center', gap: 5, borderRadius: 12, borderWidth: 1, borderColor: '#e1e9dc', backgroundColor: '#f5f7ed' },
  quickActionCardCompact: { height: 48, paddingHorizontal: 4, gap: 3 },
  quickActionGold: { borderColor: '#efe4c9', backgroundColor: '#fff9ec' },
  quickIconBox: { width: 30, height: 32, borderRadius: 10, backgroundColor: '#e2ecdc', alignItems: 'center', justifyContent: 'center' },
  quickIconGold: { backgroundColor: '#fff0d1' },
  quickCopy: { flex: 1, minWidth: 0 },
  quickTitle: { color: '#172c35', fontFamily: SERIF, fontWeight: '700', fontSize: 10.4, lineHeight: 12 },
  quickSubtitle: { color: '#52647e', fontFamily: SANS, fontSize: 9.1, lineHeight: 11 },
  issueCard: { minHeight: 46, paddingHorizontal: 6, paddingVertical: 4, flexDirection: 'row', alignItems: 'center', gap: 8, borderRadius: 13, borderWidth: 1, borderColor: '#f1eee5', backgroundColor: '#fffefa', boxShadow: '0px 2px 8px rgba(30, 54, 37, 0.07)', elevation: 1 },
  issueCardCompact: { minHeight: 56 },
  leafImage: { width: 58, height: 36, borderRadius: 8, overflow: 'hidden', alignItems: 'center', justifyContent: 'center', backgroundColor: '#e5edcf' },
  issueCopy: { flex: 1, minWidth: 0 },
  issueEyebrow: { height: 14, flexDirection: 'row', alignItems: 'center', gap: 4 },
  issueLabel: { color: '#c25012', fontFamily: SANS, fontSize: 10.5, lineHeight: 13 },
  issueTitle: { color: '#172c35', fontFamily: SERIF, fontSize: 13.5, fontWeight: '700', lineHeight: 16, letterSpacing: -0.2 },
  issueDescription: { color: '#52647e', fontFamily: SANS, fontSize: 10.2, lineHeight: 13 },
  issueArrow: { width: 26, height: 26, borderRadius: 14, borderWidth: 1, borderColor: '#f1eee5', backgroundColor: '#fff', alignItems: 'center', justifyContent: 'center' },
  tabBar: { minHeight: 47, marginHorizontal: 8, marginBottom: 2, paddingHorizontal: 6, flexDirection: 'row', alignItems: 'center', backgroundColor: 'rgba(255,254,250,0.97)', borderRadius: 18, borderWidth: 1, borderColor: '#fff', boxShadow: '0px -2px 12px rgba(48, 55, 44, 0.08)', elevation: 4 },
  tabButton: { flex: 1, alignItems: 'stretch', justifyContent: 'center' },
  tabActive: { height: 40, borderRadius: 14, alignItems: 'center', justifyContent: 'center', gap: 0 },
  tabActiveSelected: { backgroundColor: '#edf3e8' },
  tabLabel: { color: '#53637b', fontFamily: SANS, fontSize: 9.8, lineHeight: 12 },
  tabLabelActive: { color: INK, fontWeight: '600' },
  modalBackdrop: { flex: 1, justifyContent: 'flex-start', alignItems: 'flex-end', paddingTop: 60, paddingHorizontal: 16, backgroundColor: 'rgba(11, 28, 22, 0.22)' },
  profileCard: { width: 210, padding: 16, borderRadius: 16, backgroundColor: PAPER, boxShadow: '0px 5px 16px rgba(0, 0, 0, 0.18)', elevation: 8 },
  profileTitle: { color: INK, fontFamily: SERIF, fontSize: 17, fontWeight: '700' },
  profilePhone: { color: MUTED, fontFamily: SANS, fontSize: 12, marginTop: 3 },
  manageButton: { marginTop: 14, height: 38, borderRadius: 12, alignItems: 'center', justifyContent: 'center', borderWidth: 1, borderColor: '#dce6d8' },
  manageText: { color: GREEN, fontFamily: SANS, fontSize: 14, fontWeight: '600' },
  logoutButton: { marginTop: 14, height: 38, borderRadius: 12, alignItems: 'center', justifyContent: 'center', backgroundColor: '#eaf1e7' },
  logoutText: { color: GREEN, fontFamily: SANS, fontSize: 14, fontWeight: '600' },
});
