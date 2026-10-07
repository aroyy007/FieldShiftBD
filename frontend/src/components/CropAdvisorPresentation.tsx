import { useEffect, useRef, useState } from 'react';
import type { ReactNode } from 'react';
import {
  ImageBackground,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
  useWindowDimensions,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { CropAdvisorIcon } from './crop-advisor-icons';
import type { CropAdvisorIconName } from './crop-advisor-icons';

const PAPER = '#fffdf7';
const INK = '#0b342f';
const GREEN = '#155d3c';
const MUTED = '#64758a';
const SERIF = 'Georgia';
const SANS = 'Arial';

type RecommendationReason = { icon: CropAdvisorIconName; title: string; detail: string };
type WatchOut = { icon: 'drop' | 'bug'; title: string; detail: string };
type Tab = 'Home' | 'Tasks' | 'Chat' | 'Scan' | 'Profile';

type Props = {
  cropEyebrow: string;
  cropName: string;
  cropDescription: string;
  location: string;
  landArea: string;
  reasons: RecommendationReason[] | null;
  watchOuts: WatchOut[] | null;
  seasonStages: { name: string; timing: string }[];
  hasRecommendation: boolean;
  toolsOpen: boolean;
  toolsContent: ReactNode;
  onBack: () => void;
  onStartPlan: () => void;
  onOtherCrops: () => void;
  onTabPress: (tab: Tab) => void;
};

const TABS: { label: Tab; icon: CropAdvisorIconName }[] = [
  { label: 'Home', icon: 'home' },
  { label: 'Tasks', icon: 'tasks' },
  { label: 'Chat', icon: 'chat' },
  { label: 'Scan', icon: 'scan' },
  { label: 'Profile', icon: 'profile' },
];

export default function CropAdvisorPresentation({
  cropEyebrow,
  cropName,
  cropDescription,
  location,
  landArea,
  reasons,
  watchOuts,
  seasonStages,
  hasRecommendation,
  toolsOpen,
  toolsContent,
  onBack,
  onStartPlan,
  onOtherCrops,
  onTabPress,
}: Props) {
  const scrollRef = useRef<ScrollView>(null);
  const { width, height } = useWindowDimensions();
  const compact = width < 400 || height < 850;
  const veryCompact = width < 375;
  const visibleReasons = reasons ?? [];
  const visibleWatchOuts = watchOuts ?? [];

  useEffect(() => {
    if (toolsOpen) scrollRef.current?.scrollToEnd({ animated: true });
  }, [toolsOpen]);

  return (
    <SafeAreaView style={styles.safe} edges={['bottom', 'left', 'right']}>
      <View style={styles.page}>
        <View style={[styles.topBar, compact && styles.topBarCompact, veryCompact && styles.topBarVeryCompact]}>
          <Pressable
            accessibilityRole="button"
            accessibilityLabel="Back to farm"
            onPress={onBack}
            style={styles.backButton}
            hitSlop={8}
          >
            <CropAdvisorIcon name="back" size={20} color={INK} />
          </Pressable>
          <View style={styles.titleBlock}>
          <Text style={[styles.pageTitle, compact && styles.pageTitleCompact]}>Crop Advisor</Text>
            <Text style={[styles.pageSubtitle, compact && styles.pageSubtitleCompact]}>
              Recommendations based on your land, season and farm resources.
            </Text>
          </View>
          <View style={styles.headerSpacer} />
        </View>

        <ScrollView
          ref={scrollRef}
          style={styles.scroll}
          contentContainerStyle={[styles.scrollContent, compact && styles.scrollContentCompact, veryCompact && styles.scrollContentVeryCompact]}
          showsVerticalScrollIndicator={false}
          keyboardShouldPersistTaps="handled"
        >
          <View style={[styles.heroCard, compact && styles.heroCardCompact, veryCompact && styles.heroCardVeryCompact]}>
            <ImageBackground
              source={require('../../assets/images/verification-rice-field.png')}
              resizeMode="cover"
              style={styles.heroImage}
              imageStyle={styles.heroImageAsset}
            >
              <View style={[styles.heroWash, styles.nonInteractive]} />
              <View style={[styles.heroWashBandOne, styles.nonInteractive]} />
              <View style={[styles.heroWashBandTwo, styles.nonInteractive]} />
              <View style={[styles.heroWashBandThree, styles.nonInteractive]} />
              <View style={[styles.heroCopy, compact && styles.heroCopyCompact]}>
                <View style={[styles.bestFitPill, compact && styles.bestFitPillCompact]}>
                  <CropAdvisorIcon name="leaf" size={16} color={GREEN} />
                  <Text style={[styles.bestFitText, compact && styles.bestFitTextCompact]}>{cropEyebrow}</Text>
                </View>
                <Text numberOfLines={1} adjustsFontSizeToFit style={[styles.cropName, compact && styles.cropNameCompact]}>
                  {cropName}
                </Text>
                <Text numberOfLines={2} style={[styles.heroDescription, compact && styles.heroDescriptionCompact]}>
                  {cropDescription}
                </Text>
                <View style={[styles.farmChips, compact && styles.farmChipsCompact]}>
                  <View style={[styles.farmChip, compact && styles.farmChipCompact]}>
                    <CropAdvisorIcon name="location" size={compact ? 14 : 16} color={GREEN} />
                    <Text numberOfLines={1} style={[styles.farmChipText, compact && styles.farmChipTextCompact]}>{location}</Text>
                  </View>
                  <View style={[styles.farmChip, compact && styles.farmChipCompact]}>
                    <CropAdvisorIcon name="acreage" size={compact ? 14 : 16} color={GREEN} />
                    <Text numberOfLines={1} style={[styles.farmChipText, compact && styles.farmChipTextCompact]}>{landArea} acres</Text>
                  </View>
                </View>
              </View>
            </ImageBackground>
          </View>

          <SectionCard
            title="Why this works"
            icon="sprout"
            compact={compact}
            veryCompact={veryCompact}
            emptyMessage="Request crop recommendations to see which farm conditions support a match."
            rows={visibleReasons.map(reason => ({ ...reason, tone: 'green' as const }))}
          />

          <SectionCard
            title="Watch-outs"
            icon="warning"
            compact={compact}
            veryCompact={veryCompact}
            emptyMessage="No crop-specific risks are available until an evidence-backed recommendation is returned."
            rows={visibleWatchOuts.map(item => ({ ...item, tone: 'amber' as const }))}
          />

          <SeasonTimeline compact={compact} veryCompact={veryCompact} stages={seasonStages} />

          <View style={[styles.actions, compact && styles.actionsCompact, veryCompact && styles.actionsVeryCompact]}>
            <Pressable
              accessibilityRole="button"
              onPress={onStartPlan}
              style={[styles.primaryAction, compact && styles.primaryActionCompact, veryCompact && styles.primaryActionVeryCompact]}
            >
              <CropAdvisorIcon name="leaf" size={19} color="#fffdf7" />
              <Text style={[styles.primaryActionText, compact && styles.primaryActionTextCompact]}>
                {hasRecommendation ? 'Start this season plan' : 'Find suitable crops'}
              </Text>
              <View style={styles.primaryArrow}>
                <CropAdvisorIcon name="arrow" size={18} color={INK} />
              </View>
            </Pressable>
            <Pressable
              accessibilityRole="button"
              onPress={onOtherCrops}
              style={[styles.secondaryAction, compact && styles.secondaryActionCompact, veryCompact && styles.secondaryActionVeryCompact]}
            >
              <CropAdvisorIcon name="grid" size={18} color={GREEN} />
              <Text style={[styles.secondaryActionText, compact && styles.secondaryActionTextCompact]}>View other crop options</Text>
            </Pressable>
          </View>

          {toolsOpen ? (
            <View style={styles.toolsPanel}>
              <View style={styles.toolsHeading}>
                <CropAdvisorIcon name="field" size={20} color={GREEN} />
                <Text style={styles.toolsTitle}>Farm details and season tools</Text>
              </View>
              {toolsContent}
            </View>
          ) : null}
        </ScrollView>

        <View style={styles.tabBar}>
          {TABS.map(tab => {
            const active = tab.label === 'Home';
            return (
              <Pressable
                key={tab.label}
                accessibilityRole="button"
                accessibilityLabel={tab.label}
                accessibilityState={{ selected: active }}
                onPress={() => onTabPress(tab.label)}
                style={styles.tabButton}
              >
                <View style={[styles.tabContent, active && styles.tabContentActive]}>
                  <CropAdvisorIcon name={tab.icon} size={18} color={active ? GREEN : '#778291'} />
                  <Text style={[styles.tabLabel, active && styles.tabLabelActive]}>{tab.label}</Text>
                </View>
              </Pressable>
            );
          })}
        </View>
      </View>
    </SafeAreaView>
  );
}

function SectionCard({
  title,
  icon,
  rows,
  emptyMessage,
  compact,
  veryCompact,
}: {
  title: string;
  icon: CropAdvisorIconName;
  rows: { icon: CropAdvisorIconName; title: string; detail: string; tone: 'green' | 'amber' }[];
  emptyMessage: string;
  compact: boolean;
  veryCompact: boolean;
}) {
  const [expanded, setExpanded] = useState(true);

  return (
    <View style={[styles.sectionCard, compact && styles.sectionCardCompact]}>
      <Pressable
        accessibilityRole="button"
        accessibilityLabel={`${expanded ? 'Collapse' : 'Expand'} ${title}`}
        accessibilityState={{ expanded }}
        onPress={() => setExpanded(open => !open)}
        style={[styles.sectionHeader, compact && styles.sectionHeaderCompact]}
      >
        <View style={[styles.sectionIcon, compact && styles.sectionIconCompact, title === 'Watch-outs' && styles.sectionIconWarning]}>
          <CropAdvisorIcon name={icon} size={19} color={title === 'Watch-outs' ? '#fffdf7' : '#fffdf7'} />
        </View>
        <Text style={[styles.sectionTitle, compact && styles.sectionTitleCompact]}>{title}</Text>
        <View style={[styles.collapseButton, compact && styles.collapseButtonCompact]}>
          <CropAdvisorIcon name={expanded ? 'chevron-up' : 'chevron-down'} size={compact ? 13 : 15} color={INK} />
        </View>
      </Pressable>
      {expanded && (
        <View style={[styles.reasonRows, compact && styles.reasonRowsCompact]}>
          {rows.length === 0 ? (
            <Text style={styles.emptyReason}>{emptyMessage}</Text>
          ) : rows.map((row, index) => (
            <View key={`${title}-${row.title}`} style={[styles.reasonRow, compact && styles.reasonRowCompact, veryCompact && styles.reasonRowVeryCompact, index === 0 && styles.firstReasonRow]}>
              <View style={[styles.reasonIcon, compact && styles.reasonIconCompact, row.tone === 'amber' && styles.reasonIconAmber]}>
                <CropAdvisorIcon
                  name={row.icon}
                  size={compact ? 24 : 28}
                  color={row.tone === 'amber' ? '#d97614' : GREEN}
                />
              </View>
              <View style={styles.reasonCopy}>
                <Text style={[styles.reasonTitle, compact && styles.reasonTitleCompact]}>{row.title}</Text>
                <Text style={[styles.reasonDetail, compact && styles.reasonDetailCompact]}>{row.detail}</Text>
              </View>
              <View style={[styles.reasonArrow, compact && styles.reasonArrowCompact]}>
                <CropAdvisorIcon name="arrow" size={compact ? 13 : 15} color="#29445b" />
              </View>
            </View>
          ))}
        </View>
      )}
    </View>
  );
}

function SeasonTimeline({
  compact,
  veryCompact,
  stages,
}: {
  compact: boolean;
  veryCompact: boolean;
  stages?: { name: string; timing: string }[];
}) {
  const seasonStages = Array.isArray(stages) ? stages : [];
  const iconForStage = (name: string, index: number): CropAdvisorIconName => {
    const normalized = name.toLowerCase();
    if (/sow|plant|prepar/.test(normalized)) return 'sowing';
    if (/vegetat|growth/.test(normalized)) return 'vegetative';
    if (/reproduct|flower|heading/.test(normalized)) return 'reproductive';
    if (/matur|harvest|ripen/.test(normalized)) return 'maturity';
    return index === 0 ? 'sowing' : 'vegetative';
  };

  return (
    <View style={[styles.timelineCard, compact && styles.timelineCardCompact, veryCompact && styles.timelineCardVeryCompact]}>
      <View style={[styles.timelineHeading, compact && styles.timelineHeadingCompact]}>
        <CropAdvisorIcon name="chart" size={compact ? 18 : 20} color={GREEN} />
        <Text style={[styles.timelineTitle, compact && styles.timelineTitleCompact]}>Season timeline</Text>
      </View>
      {seasonStages.length === 0 ? (
        <Text style={styles.emptyReason}>A saved season plan will show its real growth stages here.</Text>
      ) : (
        <View style={[styles.stages, compact && styles.stagesCompact]}>
          <View style={[styles.timelineLine, compact && styles.timelineLineCompact, styles.nonInteractive]} />
          {seasonStages.map((stage, index) => (
            <View key={`${stage.name}-${index}`} style={styles.stage}>
              <View style={[styles.stageIcon, compact && styles.stageIconCompact, index === 0 && styles.stageIconCurrent]}>
                <CropAdvisorIcon name={iconForStage(stage.name, index)} size={compact ? 17 : (index === 0 ? 22 : 20)} color={index === 0 ? '#fffdf7' : GREEN} />
              </View>
              <Text numberOfLines={1} style={[styles.stageName, compact && styles.stageNameCompact]}>{stage.name}</Text>
              <Text numberOfLines={1} style={[styles.stageMonths, compact && styles.stageMonthsCompact]}>{stage.timing}</Text>
            </View>
          ))}
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: PAPER },
  page: { flex: 1, minHeight: 0, overflow: 'hidden', width: '100%', maxWidth: 480, alignSelf: 'center', backgroundColor: PAPER },
  topBar: { minHeight: 94, paddingTop: 16, paddingHorizontal: 20, paddingBottom: 8, flexDirection: 'row', alignItems: 'flex-start', justifyContent: 'space-between' },
  topBarCompact: { paddingHorizontal: 16, paddingTop: 16, paddingBottom: 8, minHeight: 94 },
  topBarVeryCompact: { paddingTop: 14, paddingBottom: 4, minHeight: 86 },
  backButton: { width: 32, height: 32, borderRadius: 17, backgroundColor: '#eef3e8', alignItems: 'center', justifyContent: 'center', marginTop: 1 },
  titleBlock: { flex: 1, alignItems: 'center', paddingHorizontal: 4 },
  headerSpacer: { width: 32, height: 32 },
  pageTitle: { color: INK, fontFamily: SERIF, fontSize: 22, lineHeight: 26, fontWeight: '700', textAlign: 'center', letterSpacing: -0.5 },
  pageTitleCompact: { fontSize: 20, lineHeight: 24 },
  pageSubtitle: { maxWidth: 290, marginTop: 1, color: MUTED, fontFamily: SANS, fontSize: 12, lineHeight: 16, textAlign: 'center' },
  pageSubtitleCompact: { maxWidth: 270, fontSize: 11, lineHeight: 14 },
  scroll: { flex: 1, minHeight: 0 },
  scrollContent: { paddingHorizontal: 20, paddingTop: 0, paddingBottom: 9, gap: 7 },
  scrollContentCompact: { paddingHorizontal: 16, paddingBottom: 5, gap: 6 },
  scrollContentVeryCompact: { paddingHorizontal: 14, gap: 5 },
  heroCard: { height: 139, overflow: 'hidden', borderRadius: 14, borderWidth: 1, borderColor: '#f2eee5', backgroundColor: '#fffdf7', boxShadow: '0px 3px 11px rgba(30, 54, 37, 0.08)', elevation: 2 },
  heroCardCompact: { height: 136 },
  heroCardVeryCompact: { height: 128 },
  heroImage: { width: '100%', height: '100%', overflow: 'hidden', justifyContent: 'center' },
  nonInteractive: { pointerEvents: 'none' },
  heroImageAsset: { opacity: 0.98, transform: [{ translateX: 72 }] },
  heroWash: { position: 'absolute', left: 0, top: 0, bottom: 0, width: '42%', backgroundColor: 'rgba(255,253,247,0.99)' },
  heroWashBandOne: { position: 'absolute', left: '38%', top: 0, bottom: 0, width: '10%', backgroundColor: 'rgba(255,253,247,0.91)' },
  heroWashBandTwo: { position: 'absolute', left: '47%', top: 0, bottom: 0, width: '10%', backgroundColor: 'rgba(255,253,247,0.62)' },
  heroWashBandThree: { position: 'absolute', left: '56%', top: 0, bottom: 0, width: '10%', backgroundColor: 'rgba(255,253,247,0.28)' },
  heroCopy: { width: '100%', paddingHorizontal: 12, paddingVertical: 8, alignSelf: 'stretch' },
  heroCopyCompact: { paddingHorizontal: 10, paddingVertical: 5 },
  bestFitPill: { height: 22, alignSelf: 'flex-start', flexDirection: 'row', alignItems: 'center', gap: 7, paddingHorizontal: 8, borderRadius: 14, backgroundColor: 'rgba(232,241,226,0.96)' },
  bestFitPillCompact: { height: 20, gap: 5, paddingHorizontal: 7 },
  bestFitText: { color: '#174d35', fontFamily: SANS, fontSize: 11.5, lineHeight: 15 },
  bestFitTextCompact: { fontSize: 10.5, lineHeight: 13 },
  cropName: { maxWidth: '90%', marginTop: 4, color: INK, fontFamily: SERIF, fontWeight: '700', fontSize: 29, lineHeight: 33, letterSpacing: -0.8 },
  cropNameCompact: { fontSize: 25, lineHeight: 28, marginTop: 3 },
  heroDescription: { maxWidth: 220, color: MUTED, fontFamily: SANS, fontSize: 12.5, lineHeight: 16 },
  heroDescriptionCompact: { maxWidth: 200, fontSize: 11, lineHeight: 14 },
  farmChips: { flexDirection: 'row', flexWrap: 'wrap', alignItems: 'center', gap: 5, marginTop: 6 },
  farmChipsCompact: { gap: 4, marginTop: 4 },
  farmChip: { height: 28, maxWidth: '58%', paddingHorizontal: 8, flexDirection: 'row', alignItems: 'center', gap: 5, borderRadius: 16, borderWidth: 1, borderColor: '#e8e7db', backgroundColor: 'rgba(255,253,247,0.96)' },
  farmChipCompact: { height: 24, gap: 4, paddingHorizontal: 6 },
  farmChipText: { color: '#4c6077', fontFamily: SANS, fontSize: 10.8, lineHeight: 14 },
  farmChipTextCompact: { fontSize: 9.8, lineHeight: 12 },
  sectionCard: { paddingHorizontal: 6, paddingTop: 6, paddingBottom: 6, borderRadius: 18, borderWidth: 1, borderColor: '#f1eee6', backgroundColor: '#fffefa', boxShadow: '0px 3px 11px rgba(30, 54, 37, 0.065)', elevation: 1 },
  sectionCardCompact: { paddingHorizontal: 5, paddingTop: 4, paddingBottom: 4, borderRadius: 16 },
  sectionHeader: { height: 27, paddingHorizontal: 5, flexDirection: 'row', alignItems: 'center', gap: 9 },
  sectionHeaderCompact: { height: 24, paddingHorizontal: 4, gap: 7 },
  sectionIcon: { width: 22, height: 22, borderRadius: 5, backgroundColor: '#287342', alignItems: 'center', justifyContent: 'center' },
  sectionIconCompact: { width: 20, height: 20, borderRadius: 5 },
  sectionIconWarning: { backgroundColor: 'transparent' },
  sectionTitle: { flex: 1, color: INK, fontFamily: SERIF, fontSize: 19, lineHeight: 23, fontWeight: '700', letterSpacing: -0.45 },
  sectionTitleCompact: { fontSize: 17, lineHeight: 20 },
  collapseButton: { width: 28, height: 28, borderRadius: 15, backgroundColor: '#fbfaf5', alignItems: 'center', justifyContent: 'center' },
  collapseButtonCompact: { width: 24, height: 24 },
  reasonRows: { gap: 3 },
  reasonRowsCompact: { gap: 2 },
  emptyReason: { paddingHorizontal: 10, paddingVertical: 12, color: MUTED, fontFamily: SANS, fontSize: 12, lineHeight: 16 },
  reasonRow: { minHeight: 41, paddingHorizontal: 8, paddingVertical: 3, flexDirection: 'row', alignItems: 'center', gap: 8, borderRadius: 14, borderWidth: 1, borderColor: '#f0eee7', backgroundColor: '#fffefa', boxShadow: '0px 2px 6px rgba(30, 54, 37, 0.04)', elevation: 1 },
  reasonRowCompact: { minHeight: 40, paddingHorizontal: 6, paddingVertical: 2, gap: 6, borderRadius: 12 },
  reasonRowVeryCompact: { minHeight: 37, paddingVertical: 1 },
  firstReasonRow: { marginTop: 1 },
  reasonIcon: { width: 45, height: 32, flexShrink: 0, borderRadius: 13, backgroundColor: '#edf3e8', alignItems: 'center', justifyContent: 'center' },
  reasonIconCompact: { width: 40, height: 28, borderRadius: 12 },
  reasonIconAmber: { backgroundColor: '#fff1d6' },
  reasonCopy: { flex: 1, minWidth: 0, paddingLeft: 3 },
  reasonTitle: { color: '#142b4a', fontFamily: SERIF, fontSize: 15.5, lineHeight: 19, fontWeight: '700', letterSpacing: -0.2 },
  reasonTitleCompact: { fontSize: 14, lineHeight: 17 },
  reasonDetail: { color: MUTED, fontFamily: SANS, fontSize: 11.5, lineHeight: 14.5 },
  reasonDetailCompact: { fontSize: 10.5, lineHeight: 13 },
  reasonArrow: { width: 31, height: 31, flexShrink: 0, borderRadius: 17, borderWidth: 1, borderColor: '#f0eee7', backgroundColor: '#fffefa', alignItems: 'center', justifyContent: 'center', boxShadow: '0px 2px 5px rgba(30, 54, 37, 0.04)' },
  reasonArrowCompact: { width: 27, height: 27 },
  timelineCard: { minHeight: 91, paddingHorizontal: 10, paddingTop: 7, paddingBottom: 5, borderRadius: 18, borderWidth: 1, borderColor: '#f1eee6', backgroundColor: '#fffefa', boxShadow: '0px 3px 11px rgba(30, 54, 37, 0.065)', elevation: 1 },
  timelineCardCompact: { minHeight: 90, paddingHorizontal: 7, paddingTop: 5, paddingBottom: 3, borderRadius: 16 },
  timelineCardVeryCompact: { minHeight: 85 },
  timelineHeading: { height: 23, flexDirection: 'row', alignItems: 'center', gap: 8 },
  timelineHeadingCompact: { height: 20, gap: 6 },
  timelineTitle: { color: INK, fontFamily: SERIF, fontWeight: '700', fontSize: 19, lineHeight: 23, letterSpacing: -0.4 },
  timelineTitleCompact: { fontSize: 17, lineHeight: 20 },
  stages: { flex: 1, minHeight: 54, paddingTop: 4, flexDirection: 'row', justifyContent: 'space-between', position: 'relative' },
  stagesCompact: { minHeight: 47, paddingTop: 3 },
  timelineLine: { position: 'absolute', left: '12.5%', right: '12.5%', top: 18, height: 2, borderRadius: 2, backgroundColor: '#72ab78' },
  timelineLineCompact: { top: 16 },
  stage: { flex: 1, minWidth: 0, alignItems: 'center' },
  stageIcon: { width: 31, height: 31, borderRadius: 17, backgroundColor: '#edf3e8', alignItems: 'center', justifyContent: 'center', borderWidth: 1, borderColor: '#e9ecdd' },
  stageIconCompact: { width: 27, height: 27, borderRadius: 15 },
  stageIconCurrent: { backgroundColor: '#155d3c', borderColor: '#155d3c' },
  stageName: { maxWidth: '100%', marginTop: 1, color: '#18323b', fontFamily: SANS, fontSize: 10.5, lineHeight: 13, textAlign: 'center' },
  stageNameCompact: { fontSize: 9, lineHeight: 11 },
  stageMonths: { maxWidth: '100%', color: MUTED, fontFamily: SANS, fontSize: 10, lineHeight: 13, textAlign: 'center' },
  stageMonthsCompact: { fontSize: 8.5, lineHeight: 11 },
  actions: { gap: 4, marginTop: 0 },
  actionsCompact: { gap: 3 },
  actionsVeryCompact: { gap: 2 },
  primaryAction: { height: 28, paddingLeft: 9, paddingRight: 4, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 10, borderRadius: 18, borderWidth: 1, borderColor: '#1f6c4e', backgroundColor: '#1d6046' },
  primaryActionCompact: { height: 27 },
  primaryActionVeryCompact: { height: 25 },
  primaryActionText: { color: '#fffdf7', fontFamily: SERIF, fontSize: 15.5, lineHeight: 19, fontWeight: '700', letterSpacing: -0.2 },
  primaryActionTextCompact: { fontSize: 14, lineHeight: 17 },
  primaryArrow: { position: 'absolute', right: 4, width: 24, height: 24, borderRadius: 13, backgroundColor: '#fffdf7', alignItems: 'center', justifyContent: 'center' },
  secondaryAction: { height: 27, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 11, borderRadius: 17, borderWidth: 1, borderColor: '#246746', backgroundColor: 'rgba(255,253,247,0.55)' },
  secondaryActionCompact: { height: 26, gap: 8 },
  secondaryActionVeryCompact: { height: 23, gap: 7 },
  secondaryActionText: { color: INK, fontFamily: SERIF, fontSize: 14.5, lineHeight: 18, fontWeight: '700' },
  secondaryActionTextCompact: { fontSize: 13, lineHeight: 16 },
  toolsPanel: { marginTop: 8, padding: 10, gap: 8, borderRadius: 18, borderWidth: 1, borderColor: '#ece9df', backgroundColor: '#fffefa' },
  toolsHeading: { minHeight: 28, flexDirection: 'row', alignItems: 'center', gap: 8 },
  toolsTitle: { color: INK, fontFamily: SERIF, fontSize: 18, lineHeight: 22, fontWeight: '700' },
  tabBar: { minHeight: 42, paddingHorizontal: 8, paddingTop: 3, paddingBottom: 2, flexDirection: 'row', alignItems: 'center', backgroundColor: 'rgba(255,254,250,0.98)', borderTopLeftRadius: 24, borderTopRightRadius: 24, borderWidth: 1, borderBottomWidth: 0, borderColor: '#f1eee7', boxShadow: '0px -2px 10px rgba(48, 55, 44, 0.065)', elevation: 4 },
  tabButton: { flex: 1, alignItems: 'stretch', justifyContent: 'center' },
  tabContent: { minHeight: 37, borderRadius: 14, alignItems: 'center', justifyContent: 'center', gap: 0 },
  tabContentActive: { backgroundColor: '#edf3e8' },
  tabLabel: { color: '#748195', fontFamily: SANS, fontSize: 9, lineHeight: 11 },
  tabLabelActive: { color: INK, fontWeight: '600' },
});
