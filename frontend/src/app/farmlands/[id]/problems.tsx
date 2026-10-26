import React, { useState } from 'react';
import {
  ImageBackground,
  Modal,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
  useWindowDimensions,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Href, useLocalSearchParams, useRouter } from 'expo-router';
import { FieldBottomNav, FieldIcon, FieldScreenHeader } from '../../../components/field-screen-ui';
import type { FieldIconName } from '../../../components/field-screen-ui';
import { useAppContext } from '../../../context/AppProvider';
import type { FarmProblem, ProblemStatus } from '../../../data/demo';

const PAPER = '#fffdf7';
const CARD = '#fffefa';
const GREEN = '#07543a';
const GREEN_DARK = '#064832';
const INK = '#111a23';
const MUTED = '#52677a';
const BORDER = '#e9e7df';
type Filter = 'all' | 'open' | 'monitoring' | 'resolved';
type ProblemAction = 'diagnosis' | 'forecast' | 'tasks' | null;
type ProblemBadgeTone = 'green' | 'yellow' | 'orange' | 'blue';
type ProblemBadge = { label: string; icon: FieldIconName; tone: ProblemBadgeTone };
type ProblemCardModel = {
  id: string;
  title: string;
  description: string;
  status: ProblemStatus;
  severity: string;
  category: string;
  sourceText: string;
  sourceIcon: FieldIconName;
  badges: [ProblemBadge, ProblemBadge];
  action: ProblemAction;
  actionLabel?: string;
  actualId?: string;
  completedLabel?: string;
};

function isClosedProblem(status: ProblemStatus) {
  return status === 'resolved' || status === 'dismissed';
}

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
  return <FarmProblemsScreen key={farmId ?? 'missing'} farmId={farmId} />;
}

function FarmProblemsScreen({ farmId }: { farmId: string | undefined }) {
  const router = useRouter();
  const { width } = useWindowDimensions();
  const compact = width < 350;
  const { farmlands, addProblem, updateProblemStatus } = useAppContext();
  const farm = farmlands.find(item => item.id === farmId);
  const [filter, setFilter] = useState<Filter>('all');
  const [filterModalOpen, setFilterModalOpen] = useState(false);
  const [reportOpen, setReportOpen] = useState(false);
  const [reportDescription, setReportDescription] = useState('');
  const [reportError, setReportError] = useState('');
  const [savingReport, setSavingReport] = useState(false);
  const [savingStatus, setSavingStatus] = useState(false);
  const [statusError, setStatusError] = useState('');
  const [focusedProblemId, setFocusedProblemId] = useState<string | null>(null);

  if (!farm || !farmId) {
    return <SafeAreaView style={styles.safe} edges={['bottom', 'left', 'right']}><Text style={styles.empty}>Farm not found.</Text></SafeAreaView>;
  }

  const cards = farm.problems.map(problem => mapActualProblem(problem, problem.status));
  const counts = {
    all: cards.length,
    open: cards.filter(problem => problem.status === 'open').length,
    monitoring: cards.filter(problem => problem.status === 'monitoring').length,
    resolved: cards.filter(problem => isClosedProblem(problem.status)).length,
  };
  const visibleCards = filter === 'all'
    ? cards
    : filter === 'resolved'
      ? cards.filter(problem => isClosedProblem(problem.status))
      : cards.filter(problem => problem.status === filter);
  const focusedProblem = cards.find(problem => problem.id === focusedProblemId) ?? null;

  const navigate = (action: ProblemAction) => {
    if (!action) return;
    const route = action === 'diagnosis' ? 'crop-health' : action === 'forecast' ? 'alerts' : 'tasks';
    router.push(`/farmlands/${farmId}/${route}` as Href);
  };

  const submitReport = async () => {
    if (!reportDescription.trim()) {
      setReportError('Add a short description before submitting.');
      return;
    }
    setSavingReport(true);
    try {
      await addProblem(farmId, reportDescription.trim());
      setReportDescription('');
      setReportError('');
      setReportOpen(false);
      setFilter('all');
    } catch (error) {
      setReportError(error instanceof Error ? error.message : 'Could not save the report. Try again.');
    } finally {
      setSavingReport(false);
    }
  };

  const changeStatus = async (problem: ProblemCardModel, status: ProblemStatus) => {
    if (!problem.actualId) return;
    setSavingStatus(true);
    setStatusError('');
    try {
      await updateProblemStatus(farmId, problem.actualId, status);
      setFocusedProblemId(null);
    } catch (error) {
      setStatusError(error instanceof Error ? error.message : 'Could not update the problem. Try again.');
    } finally {
      setSavingStatus(false);
    }
  };

  return (
    <SafeAreaView style={styles.safe} edges={['bottom', 'left', 'right']}>
      <View style={styles.frame}>
        <FieldScreenHeader
          title="Farm Problems"
          subtitle={`${farm.crop} · ${farm.growthStage} · ${farm.location ?? 'Location not set'}`}
          backHref={`/farmlands/${farmId}` as Href}
          actionLabel="Filter farm problems"
          actionIcon="filters"
          onAction={() => setFilterModalOpen(true)}
        />

        <ScrollView style={styles.scroll} contentContainerStyle={styles.content} showsVerticalScrollIndicator={false} keyboardShouldPersistTaps="handled">
          <View style={[styles.hero, compact && styles.heroCompact]}>
            <ImageBackground
              source={require('../../../../assets/images/verification-rice-field.png')}
              resizeMode="cover"
              style={StyleSheet.absoluteFill}
              imageStyle={styles.heroImage}
            >
              <View style={styles.heroShade} />
            </ImageBackground>
            <View style={[styles.heroCopy, compact && styles.heroCopyCompact]}>
              <Text style={[styles.heroTitle, compact && styles.heroTitleCompact]}>{farm.name}</Text>
              <Text numberOfLines={1} style={styles.heroCrop}>{farm.crop} · {farm.growthStage}</Text>
              <View style={styles.heroMeta}>
                <FieldIcon name="location" size={17} color={GREEN} />
                <Text numberOfLines={1} style={styles.metaText}>{farm.location}</Text>
                <View style={styles.metaDivider} />
                <FieldIcon name="rice" size={18} color={GREEN} />
                <Text style={styles.metaText}>{farm.acreage.toLocaleString(undefined, { maximumFractionDigits: 2 })} acres</Text>
              </View>
              <Text style={[styles.heroDescription, compact && styles.heroDescriptionCompact]}>Track disease, drainage, and field issues that need attention.</Text>
              <View style={styles.statsRow}>
                <StatTile icon="warning" value={String(counts.open)} label="open" tone="orange" compact={compact} />
                <StatTile icon="clock" value={String(counts.monitoring)} label="monitoring" tone="yellow" compact={compact} />
                <StatTile icon="check" value={String(counts.resolved)} label="resolved" tone="green" compact={compact} />
              </View>
            </View>
          </View>

          <View style={[styles.filters, compact && styles.filtersCompact]} accessibilityRole="tablist">
            <FilterTab label="All" count={counts.all} selected={filter === 'all'} compact={compact} onPress={() => setFilter('all')} />
            <FilterTab label="Open" count={counts.open} selected={filter === 'open'} compact={compact} onPress={() => setFilter('open')} />
            <FilterTab label="Monitoring" count={counts.monitoring} selected={filter === 'monitoring'} compact={compact} onPress={() => setFilter('monitoring')} />
            <FilterTab label="Resolved" count={counts.resolved} selected={filter === 'resolved'} compact={compact} onPress={() => setFilter('resolved')} />
          </View>

          <View style={styles.problemList}>
            {visibleCards.map(problem => (
              <ProblemCard
                key={problem.id}
                problem={problem}
                compact={compact}
                onPress={() => setFocusedProblemId(problem.id)}
                onAction={() => navigate(problem.action)}
              />
            ))}
            {visibleCards.length === 0 ? <View style={styles.emptyCard}><Text style={styles.empty}>No problems in this filter.</Text></View> : null}
          </View>

          <Text style={[styles.recommendTitle, compact && styles.recommendTitleCompact]}>Recommended actions</Text>
          <View style={styles.recommendedRow}>
            <Pressable accessibilityRole="button" onPress={() => navigate('diagnosis')} style={[styles.recommendedCard, compact && styles.recommendedCardCompact, styles.recommendedScan]}>
              <FieldIcon name="camera" size={compact ? 20 : 25} color="#fffdf7" />
              <View style={styles.recommendedCopy}><Text numberOfLines={1} style={styles.recommendedLabel}>Scan new problem</Text><Text numberOfLines={2} style={styles.recommendedHint}>Detect issues from a plant photo</Text></View>
            </Pressable>
            <Pressable accessibilityRole="button" onPress={() => setReportOpen(true)} style={[styles.recommendedCard, compact && styles.recommendedCardCompact, styles.recommendedReport]}>
              <FieldIcon name="note" size={compact ? 20 : 25} color="#fffdf7" />
              <View style={styles.recommendedCopy}><Text numberOfLines={1} style={styles.recommendedLabel}>Add manual report</Text><Text numberOfLines={2} style={styles.recommendedHint}>Record a field issue or observation</Text></View>
            </Pressable>
          </View>
        </ScrollView>
        <FieldBottomNav active="Scan" farmId={farmId} />
      </View>

      <Modal visible={filterModalOpen} transparent animationType="fade" onRequestClose={() => setFilterModalOpen(false)}>
        <View style={styles.modalBackdrop}>
          <View style={styles.modalCard}>
            <ModalHeading title="Filter problems" onClose={() => setFilterModalOpen(false)} />
            {(['all', 'open', 'monitoring', 'resolved'] as Filter[]).map(value => (
              <Pressable key={value} accessibilityRole="button" accessibilityState={{ selected: filter === value }} onPress={() => { setFilter(value); setFilterModalOpen(false); }} style={styles.modalFilterRow}>
                <Text style={styles.modalFilterText}>{value[0].toUpperCase() + value.slice(1)}</Text>
                <Text style={styles.modalFilterCount}>{counts[value]}</Text>
                {filter === value ? <FieldIcon name="check" size={18} color={GREEN} /> : <View style={styles.filterSpacer} />}
              </Pressable>
            ))}
          </View>
        </View>
      </Modal>

      <Modal visible={reportOpen} transparent animationType="fade" onRequestClose={() => setReportOpen(false)}>
        <View style={styles.modalBackdrop}>
          <View style={styles.modalCard}>
            <ModalHeading title="Add manual report" onClose={() => setReportOpen(false)} />
            <Text style={styles.inputLabel}>What did you notice?</Text>
            <TextInput
              accessibilityLabel="Problem description"
              value={reportDescription}
                onChangeText={value => { setReportDescription(value.slice(0, 1000)); setReportError(''); }}
              placeholder="Describe the issue in the field"
              placeholderTextColor="#7a8790"
              multiline
              maxLength={1000}
              textAlignVertical="top"
              style={styles.reportInput}
            />
            {reportError ? <Text accessibilityRole="alert" style={styles.reportError}>{reportError}</Text> : null}
            <Pressable accessibilityRole="button" disabled={savingReport} onPress={() => void submitReport()} style={[styles.submitReport, savingReport && styles.submitReportDisabled]}><Text style={styles.submitReportText}>{savingReport ? 'Saving…' : 'Save report'}</Text></Pressable>
          </View>
        </View>
      </Modal>

      <Modal visible={Boolean(focusedProblem)} transparent animationType="fade" onRequestClose={() => setFocusedProblemId(null)}>
        <View style={styles.modalBackdrop}>
          {focusedProblem ? (
            <View style={styles.modalCard}>
              <ModalHeading title={focusedProblem.title} onClose={() => setFocusedProblemId(null)} />
              <Text style={styles.detailDescription}>{focusedProblem.description}</Text>
              <View style={styles.detailStatus}><Text style={styles.inputLabel}>Current status</Text><StatusPill status={focusedProblem.status} /></View>
              <Text style={[styles.inputLabel, styles.updateStatusLabel]}>Update status</Text>
              <View style={styles.statusActions}>
                {nextStatusActions(focusedProblem.status).map(action => (
                  <Pressable key={action.status} accessibilityRole="button" disabled={savingStatus} onPress={() => void changeStatus(focusedProblem, action.status)} style={[styles.statusAction, action.status === 'resolved' && styles.statusActionPrimary, savingStatus && styles.submitReportDisabled]}>
                    <Text style={[styles.statusActionText, action.status === 'resolved' && styles.statusActionPrimaryText]}>{action.label}</Text>
                  </Pressable>
                ))}
              </View>
              {statusError ? <Text accessibilityRole="alert" style={styles.reportError}>{statusError}</Text> : null}
              {focusedProblem.action ? <Pressable accessibilityRole="button" onPress={() => navigate(focusedProblem.action)} style={[styles.submitReport, styles.detailAction]}><Text style={styles.submitReportText}>{focusedProblem.actionLabel ?? 'Open linked record'}</Text></Pressable> : null}
            </View>
          ) : null}
        </View>
      </Modal>
    </SafeAreaView>
  );
}

function mapActualProblem(problem: FarmProblem, status: ProblemStatus): ProblemCardModel {
  const problemStatusLabel = status === 'open' ? 'Open issue' : status[0].toUpperCase() + status.slice(1);
  const severityTone: ProblemBadgeTone = problem.severity === 'low' ? 'green' : problem.severity === 'moderate' ? 'yellow' : 'orange';
  const closed = isClosedProblem(status);
  const statusTone: ProblemBadgeTone = status === 'monitoring' ? 'yellow' : closed ? 'green' : 'orange';
  const category = problem.source === 'weather'
    ? 'Weather'
    : problem.source === 'disease_detection'
      ? 'Crop health'
      : problem.source === 'farmer'
        ? 'Farmer report'
        : 'Farm system';
  const action = problem.source === 'weather' ? 'forecast' : problem.source === 'disease_detection' ? 'diagnosis' : null;
  return {
    id: `actual-${problem.id}`,
    actualId: problem.id,
    title: problem.category || category,
    description: problem.description,
    status,
    severity: problem.severity[0].toUpperCase() + problem.severity.slice(1),
    category,
    sourceText: problem.source.replaceAll('_', ' '),
    sourceIcon: problem.source === 'weather' ? 'cloudRain' : problem.source === 'farmer' ? 'note' : 'camera',
    badges: [
      { label: problem.severity[0].toUpperCase() + problem.severity.slice(1), icon: 'warning', tone: severityTone },
      { label: problemStatusLabel, icon: status === 'monitoring' ? 'clock' : closed ? 'check' : 'warning', tone: statusTone },
    ],
    action,
    actionLabel: action === 'forecast' ? 'View forecast' : action === 'diagnosis' ? 'View diagnosis' : undefined,
    completedLabel: status === 'dismissed' ? 'Dismissed' : 'Resolved',
  };
}

function StatTile({ icon, value, label, tone, compact }: { icon: FieldIconName; value: string; label: string; tone: 'orange' | 'yellow' | 'green'; compact: boolean }) {
  return (
    <View style={[styles.statTile, compact && styles.statTileCompact, tone === 'orange' ? styles.statOrange : tone === 'yellow' ? styles.statYellow : styles.statGreen]}>
      <View style={[styles.statIcon, tone === 'orange' ? styles.statIconOrange : tone === 'yellow' ? styles.statIconYellow : styles.statIconGreen]}><FieldIcon name={icon} size={22} color={tone === 'orange' ? '#d94323' : tone === 'yellow' ? '#de810b' : GREEN} /></View>
      <View style={styles.statCopy}><Text style={[styles.statValue, compact && styles.statValueCompact]}>{value}</Text><Text style={[styles.statLabel, compact && styles.statLabelCompact]}>{label}</Text></View>
    </View>
  );
}

function FilterTab({ label, count, selected, compact, onPress }: { label: string; count: number; selected: boolean; compact: boolean; onPress: () => void }) {
  return (
    <Pressable accessibilityRole="tab" accessibilityState={{ selected }} onPress={onPress} style={[styles.filterTab, compact && styles.filterTabCompact, selected && styles.filterTabSelected]}>
      <Text numberOfLines={1} style={[styles.filterText, compact && styles.filterTextCompact, selected && styles.filterTextSelected]}>{label} ({count})</Text>
    </Pressable>
  );
}

function ProblemCard({ problem, compact, onPress, onAction }: { problem: ProblemCardModel; compact: boolean; onPress: () => void; onAction: () => void }) {
  const resolved = isClosedProblem(problem.status);
  if (resolved) {
    return (
      <Pressable accessibilityRole="button" onPress={onPress} style={[styles.resolvedCard, compact && styles.resolvedCardCompact]}>
        <View style={[styles.resolvedCheck, compact && styles.resolvedCheckCompact]}><FieldIcon name="check" size={compact ? 30 : 42} color={GREEN} /></View>
        <View style={styles.resolvedCopy}>
          <View style={styles.problemTitleRow}><Text style={[styles.problemTitle, compact && styles.problemTitleCompact]}>{problem.title}</Text><FieldIcon name="chevron" size={19} color="#314d61" /></View>
          <Text numberOfLines={compact ? 2 : undefined} style={[styles.problemDescription, compact && styles.problemDescriptionCompact]}>{problem.description}</Text>
          <View style={styles.resolvedMeta}><View style={styles.resolvedTag}><FieldIcon name={problem.sourceIcon} size={15} color={GREEN} /><Text style={styles.resolvedTagText}>{problem.category}</Text></View><View style={styles.resolvedTag}><FieldIcon name="check" size={15} color={GREEN} /><Text style={styles.resolvedTagText}>Resolved</Text></View><Text style={styles.completedDate}>{problem.completedLabel ?? 'Completed'}</Text></View>
        </View>
      </Pressable>
    );
  }

  return (
    <View style={[styles.problemCard, compact && styles.problemCardCompact]}>
      <View style={styles.problemCopy}>
        <Pressable accessibilityRole="button" accessibilityLabel={`View ${problem.title} details`} onPress={onPress} style={styles.problemTitleRow}>
          <Text numberOfLines={2} style={[styles.problemTitle, compact && styles.problemTitleCompact]}>{problem.title}</Text><FieldIcon name="chevron" size={18} color="#314d61" />
        </Pressable>
        <Text numberOfLines={compact ? 2 : 3} style={[styles.problemDescription, compact && styles.problemDescriptionCompact]}>{problem.description}</Text>
        <View style={styles.badgesRow}>
          <Tag compact={compact} icon={problem.category === 'Weather' ? 'droplet' : problem.category === 'Crop health' ? (problem.id.includes('weed') ? 'weeds' : 'leaf') : 'note'} label={problem.category} tone={problem.category === 'Weather' ? 'blue' : 'green'} />
          <Tag compact={compact} icon={problem.badges[0].icon} label={problem.badges[0].label} tone={problem.badges[0].tone} />
          <Tag compact={compact} icon={problem.badges[1].icon} label={problem.badges[1].label} tone={problem.badges[1].tone} />
        </View>
        <View style={styles.cardFooter}>
          <View style={styles.sourceRow}><FieldIcon name={problem.sourceIcon} size={compact ? 13 : 16} color="#3b5368" /><Text numberOfLines={2} style={[styles.sourceText, compact && styles.sourceTextCompact]}>{problem.sourceText}</Text></View>
          {problem.action ? <Pressable accessibilityRole="button" accessibilityLabel={problem.actionLabel ?? 'Open linked record'} onPress={onAction} style={[styles.cardAction, compact && styles.cardActionCompact]}><Text style={[styles.cardActionText, compact && styles.cardActionTextCompact]}>{problem.actionLabel ?? 'Open'}</Text><FieldIcon name="chevron" size={14} color="#fffdf7" /></Pressable> : null}
        </View>
      </View>
    </View>
  );
}

function Tag({ icon, label, tone, compact }: { icon: FieldIconName; label: string; tone: 'green' | 'yellow' | 'orange' | 'blue'; compact: boolean }) {
  const toneStyle = tone === 'green' ? styles.tagGreen : tone === 'yellow' ? styles.tagYellow : tone === 'blue' ? styles.tagBlue : styles.tagOrange;
  const iconColor = tone === 'green' ? GREEN : tone === 'yellow' ? '#d27a06' : tone === 'blue' ? '#0873c6' : '#db3d25';
  return <View style={[styles.tag, compact && styles.tagCompact, toneStyle]}><FieldIcon name={icon} size={compact ? 11 : 14} color={iconColor} /><Text numberOfLines={1} style={[styles.tagText, compact && styles.tagTextCompact, tone === 'green' ? styles.tagTextGreen : tone === 'yellow' ? styles.tagTextYellow : tone === 'blue' ? styles.tagTextBlue : styles.tagTextOrange]}>{label}</Text></View>;
}

function StatusPill({ status }: { status: ProblemStatus }) {
  return <View style={[styles.statusPill, isClosedProblem(status) ? styles.statusResolved : status === 'monitoring' ? styles.statusMonitoring : styles.statusOpen]}><Text style={styles.statusPillText}>{status}</Text></View>;
}

function ModalHeading({ title, onClose }: { title: string; onClose: () => void }) {
  return <View style={styles.modalHeading}><Text style={styles.modalTitle}>{title}</Text><Pressable accessibilityRole="button" accessibilityLabel="Close" onPress={onClose} style={styles.closeButton}><FieldIcon name="close" size={20} color={INK} /></Pressable></View>;
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: PAPER },
  frame: { flex: 1, width: '100%', maxWidth: 520, alignSelf: 'center', backgroundColor: PAPER },
  scroll: { flex: 1 },
  content: { paddingHorizontal: 12, paddingTop: 6, paddingBottom: 6 },
  hero: { height: 190, overflow: 'hidden', borderWidth: 1, borderColor: BORDER, borderRadius: 19, marginBottom: 9, backgroundColor: '#e9f0e3' },
  heroCompact: { height: 158 },
  heroImage: { width: '100%', height: '100%' },
  heroShade: { ...StyleSheet.absoluteFill, backgroundColor: 'rgba(19,45,27,.07)' },
  heroCopy: { position: 'absolute', top: 0, bottom: 0, left: 0, width: '75%', paddingHorizontal: 10, paddingTop: 8, backgroundColor: PAPER, borderTopRightRadius: 43, borderBottomRightRadius: 39 },
  heroCopyCompact: { width: '78%', paddingHorizontal: 8 },
  heroTitle: { color: INK, fontFamily: 'Georgia', fontSize: 26, lineHeight: 31, fontWeight: '700' },
  heroTitleCompact: { fontSize: 20, lineHeight: 24 },
  heroCrop: { color: INK, fontSize: 13, lineHeight: 16, fontWeight: '600' },
  heroMeta: { flexDirection: 'row', alignItems: 'center', gap: 5, marginTop: 5 },
  metaText: { color: MUTED, fontSize: 10, flexShrink: 1 },
  metaDivider: { width: 1, height: 13, marginHorizontal: 1, backgroundColor: BORDER },
  heroDescription: { width: '90%', color: MUTED, fontSize: 11.5, lineHeight: 15, marginTop: 6 },
  heroDescriptionCompact: { fontSize: 9.5, lineHeight: 12 },
  statsRow: { width: '108%', flexDirection: 'row', gap: 6, marginTop: 8 },
  statTile: { flex: 1, minWidth: 0, height: 54, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 5, paddingHorizontal: 5, borderRadius: 13 },
  statTileCompact: { height: 44, gap: 2, paddingHorizontal: 2 },
  statOrange: { backgroundColor: '#fff0e6' },
  statYellow: { backgroundColor: '#fff6e3' },
  statGreen: { backgroundColor: '#edf4e9' },
  statIcon: { width: 29, height: 29, flexShrink: 0, alignItems: 'center', justifyContent: 'center', borderRadius: 16 },
  statIconOrange: { backgroundColor: '#ffe1d2' },
  statIconYellow: { backgroundColor: '#ffedc7' },
  statIconGreen: { backgroundColor: '#dfeedd' },
  statCopy: { alignItems: 'center', minWidth: 0 },
  statValue: { color: INK, fontFamily: 'Georgia', fontSize: 18, lineHeight: 22, fontWeight: '700' },
  statValueCompact: { fontSize: 15 },
  statLabel: { color: GREEN, fontSize: 10, lineHeight: 13 },
  statLabelCompact: { fontSize: 8 },
  filters: { minHeight: 40, flexDirection: 'row', alignItems: 'stretch', padding: 2, marginBottom: 8, borderWidth: 1, borderColor: BORDER, borderRadius: 18, backgroundColor: '#f8f7f1' },
  filtersCompact: { minHeight: 32 },
  filterTab: { flex: 1, minWidth: 0, alignItems: 'center', justifyContent: 'center', paddingHorizontal: 2, borderRadius: 15 },
  filterTabCompact: { paddingHorizontal: 1 },
  filterTabSelected: { backgroundColor: GREEN },
  filterText: { color: '#30465a', fontSize: 11, textAlign: 'center' },
  filterTextCompact: { fontSize: 8.5 },
  filterTextSelected: { color: '#fffdf7', fontWeight: '600' },
  problemList: { gap: 9 },
  problemCard: { minHeight: 142, flexDirection: 'row', gap: 9, padding: 9, borderWidth: 1, borderColor: BORDER, borderRadius: 18, backgroundColor: CARD, boxShadow: '0px 1px 5px rgba(79, 80, 55, 0.045)' },
  problemCardCompact: { minHeight: 108, gap: 6, padding: 6 },
  problemImage: { width: 74, height: 82, flexShrink: 0, borderRadius: 11, backgroundColor: '#e7eadf' },
  problemImageCompact: { width: 58, height: 66 },
  problemCopy: { flex: 1, minWidth: 0 },
  problemTitleRow: { flexDirection: 'row', alignItems: 'flex-start', gap: 3 },
  problemTitle: { flex: 1, color: INK, fontFamily: 'Georgia', fontSize: 15.5, lineHeight: 19, fontWeight: '700' },
  problemTitleCompact: { fontSize: 13.5, lineHeight: 16 },
  problemDescription: { color: MUTED, fontSize: 11, lineHeight: 15, marginTop: 3 },
  problemDescriptionCompact: { fontSize: 9.5, lineHeight: 12 },
  badgesRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 4, marginTop: 6 },
  tag: { minHeight: 24, maxWidth: '100%', flexDirection: 'row', alignItems: 'center', gap: 4, paddingHorizontal: 6, paddingVertical: 3, borderRadius: 13 },
  tagCompact: { minHeight: 20, gap: 3, paddingHorizontal: 5, paddingVertical: 2 },
  tagGreen: { backgroundColor: '#eaf3e7' },
  tagYellow: { backgroundColor: '#fff4dc' },
  tagOrange: { backgroundColor: '#ffebe4' },
  tagBlue: { backgroundColor: '#e4f2fb' },
  tagText: { maxWidth: 95, fontSize: 9.5, lineHeight: 12 },
  tagTextCompact: { fontSize: 8.5, lineHeight: 10 },
  tagTextGreen: { color: GREEN },
  tagTextYellow: { color: '#bd7103' },
  tagTextOrange: { color: '#c9381e' },
  tagTextBlue: { color: '#0870bb' },
  cardFooter: { minHeight: 32, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 4, marginTop: 4 },
  sourceRow: { flex: 1, minWidth: 0, flexDirection: 'row', alignItems: 'center', gap: 5 },
  sourceText: { flex: 1, color: '#3c5368', fontSize: 9.5, lineHeight: 12 },
  sourceTextCompact: { fontSize: 8, lineHeight: 10 },
  cardAction: { minHeight: 31, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 3, paddingHorizontal: 8, borderRadius: 16, backgroundColor: GREEN },
  cardActionCompact: { minHeight: 22, paddingHorizontal: 5 },
  cardActionText: { color: '#fffdf7', fontSize: 10, fontWeight: '600' },
  cardActionTextCompact: { fontSize: 8 },
  resolvedCard: { minHeight: 124, flexDirection: 'row', alignItems: 'center', gap: 10, padding: 10, borderWidth: 1, borderColor: '#e3ebdc', borderRadius: 18, backgroundColor: '#f0f6ec' },
  resolvedCardCompact: { minHeight: 82, gap: 6, padding: 6 },
  resolvedCheck: { width: 52, height: 52, flexShrink: 0, alignItems: 'center', justifyContent: 'center', borderRadius: 34, backgroundColor: '#dcebd7' },
  resolvedCheckCompact: { width: 40, height: 40 },
  resolvedCopy: { flex: 1, minWidth: 0 },
  resolvedMeta: { flexDirection: 'row', flexWrap: 'wrap', alignItems: 'center', gap: 4, marginTop: 5 },
  resolvedTag: { minHeight: 24, flexDirection: 'row', alignItems: 'center', gap: 3, paddingHorizontal: 7, borderRadius: 13, backgroundColor: '#e0efdc' },
  resolvedTagText: { color: GREEN, fontSize: 9.5 },
  completedDate: { flex: 1, color: MUTED, fontSize: 9.5, textAlign: 'right' },
  recommendTitle: { color: INK, fontFamily: 'Georgia', fontSize: 19, lineHeight: 24, fontWeight: '700', marginTop: 12, marginBottom: 7 },
  recommendTitleCompact: { fontSize: 15, lineHeight: 18 },
  recommendedRow: { flexDirection: 'row', gap: 8, marginBottom: 4 },
  recommendedCard: { flex: 1, minWidth: 0, minHeight: 77, flexDirection: 'row', alignItems: 'center', gap: 7, paddingHorizontal: 8, borderRadius: 14 },
  recommendedCardCompact: { minHeight: 54, paddingHorizontal: 5, gap: 4 },
  recommendedScan: { backgroundColor: GREEN },
  recommendedReport: { backgroundColor: '#497220' },
  recommendedCopy: { flex: 1, minWidth: 0 },
  recommendedLabel: { color: '#fffdf7', fontSize: 11, lineHeight: 15, fontWeight: '600' },
  recommendedHint: { color: '#edf2e6', fontSize: 9, lineHeight: 12, marginTop: 3 },
  emptyCard: { borderRadius: 16, backgroundColor: CARD, borderWidth: 1, borderColor: BORDER },
  empty: { padding: 22, color: MUTED, fontSize: 13, textAlign: 'center' },
  modalBackdrop: { flex: 1, justifyContent: 'center', paddingHorizontal: 20, backgroundColor: 'rgba(18,33,27,.42)' },
  modalCard: { width: '100%', maxWidth: 460, alignSelf: 'center', padding: 18, borderRadius: 20, backgroundColor: PAPER },
  modalHeading: { flexDirection: 'row', alignItems: 'flex-start', justifyContent: 'space-between', gap: 10, marginBottom: 10 },
  modalTitle: { flex: 1, color: INK, fontFamily: 'Georgia', fontSize: 20, lineHeight: 26, fontWeight: '700' },
  closeButton: { width: 36, height: 36, alignItems: 'center', justifyContent: 'center', borderRadius: 18, backgroundColor: '#efeee7' },
  modalFilterRow: { minHeight: 48, flexDirection: 'row', alignItems: 'center', gap: 12, borderTopWidth: 1, borderTopColor: BORDER },
  modalFilterText: { flex: 1, color: INK, fontSize: 14 },
  modalFilterCount: { color: MUTED, fontSize: 13 },
  filterSpacer: { width: 18 },
  inputLabel: { color: INK, fontSize: 12, fontWeight: '600' },
  reportInput: { minHeight: 112, padding: 12, marginTop: 7, borderWidth: 1, borderColor: BORDER, borderRadius: 12, color: INK, fontSize: 14, lineHeight: 20, backgroundColor: '#fffefa', outlineStyle: 'none' as never },
  reportError: { color: '#bc381d', fontSize: 11, marginTop: 7 },
  submitReport: { minHeight: 46, alignItems: 'center', justifyContent: 'center', marginTop: 12, borderRadius: 12, backgroundColor: GREEN },
  submitReportDisabled: { opacity: 0.6 },
  submitReportText: { color: '#fffdf7', fontSize: 14, fontWeight: '600' },
  detailDescription: { color: MUTED, fontSize: 13, lineHeight: 20, marginBottom: 14 },
  detailStatus: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingVertical: 10, borderTopWidth: 1, borderTopColor: BORDER },
  statusPill: { minHeight: 27, alignItems: 'center', justifyContent: 'center', paddingHorizontal: 10, borderRadius: 14 },
  statusOpen: { backgroundColor: '#ffebe4' },
  statusMonitoring: { backgroundColor: '#fff2d8' },
  statusResolved: { backgroundColor: '#e2efdd' },
  statusPillText: { color: GREEN_DARK, fontSize: 11, fontWeight: '600', textTransform: 'capitalize' },
  updateStatusLabel: { marginTop: 7, marginBottom: 8 },
  statusActions: { flexDirection: 'row', flexWrap: 'wrap', gap: 7 },
  statusAction: { minHeight: 38, alignItems: 'center', justifyContent: 'center', paddingHorizontal: 12, borderWidth: 1, borderColor: '#b7c9bb', borderRadius: 11 },
  statusActionPrimary: { borderColor: GREEN, backgroundColor: GREEN },
  statusActionText: { color: GREEN_DARK, fontSize: 12, fontWeight: '600' },
  statusActionPrimaryText: { color: '#fffdf7' },
  detailAction: { marginTop: 14 },
});
