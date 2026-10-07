import React, { useState } from 'react';
import { Image, ImageSourcePropType, Modal, Pressable, RefreshControl, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Href, useRouter } from 'expo-router';
import { DashboardIcon } from '../../components/dashboard-icons';
import { FarmBottomNavigation, FarmChromeIcon, FarmPageHeader } from '../../components/farmland-mobile-ui';
import { FarmProfileIcon } from '../../components/farm-profile-icons';
import { FieldIcon } from '../../components/field-screen-ui';
import { useAppContext } from '../../context/AppProvider';

const PAPER = '#fffdf7';
const INK = '#101820';
const GREEN = '#07543a';
const MUTED = '#52677a';
type FarmFilter = 'All' | 'Active' | 'Needs attention';
type FarmCardData = {
  id: string;
  farmId: string | null;
  name: string;
  location: string;
  acreage: string;
  crop: string;
  stage: string;
  status: string;
  image: ImageSourcePropType;
  issue?: string;
  task?: string;
  progress?: number;
  stages: { id: string; name: string; status: 'completed' | 'current' | 'upcoming' }[];
  needsAttention: boolean;
};

export default function ManageFarmlands() {
  const { farmlands, dataLoading, refreshProfile } = useAppContext();
  const router = useRouter();
  const [search, setSearch] = useState('');
  const [filter, setFilter] = useState<FarmFilter>('All');
  const [showFilters, setShowFilters] = useState(false);
  const [notice, setNotice] = useState('');
  const cards: FarmCardData[] = farmlands.map(farm => {
    const openProblem = farm.problems.find(problem => problem.status === 'open' || problem.status === 'monitoring');
    const pendingTasks = farm.tasks.filter(task => task.status === 'pending');
    return {
      id: farm.id,
      farmId: farm.id,
      name: farm.name,
      location: farm.location ?? 'Location not set',
      acreage: `${farm.acreage.toLocaleString(undefined, { maximumFractionDigits: 2 })} acres`,
      crop: farm.crop,
      stage: farm.activeSeasonId ? farm.growthStage : 'No active season',
      status: farm.activeSeasonId ? 'Active' : 'No season',
      image: require('../../../assets/images/verification-rice-field.png'),
      task: `${pendingTasks.length} open tasks`,
      issue: openProblem?.category,
      progress: farm.seasonProgressPercent ?? undefined,
      stages: farm.seasonPlan,
      needsAttention: Boolean(openProblem) || pendingTasks.some(task => task.priority === 'high' || task.priority === 'urgent'),
    };
  });
  const visibleCards = cards.filter(card => {
    const matchesSearch = `${card.name} ${card.location} ${card.crop}`.toLowerCase().includes(search.trim().toLowerCase());
    const matchesFilter = filter === 'All' || (filter === 'Needs attention' ? card.needsAttention : card.status !== 'Idle');
    return matchesSearch && matchesFilter;
  });
  const totalAcres = farmlands.reduce((sum, farm) => sum + farm.acreage, 0);
  const attentionCount = cards.filter(card => card.needsAttention).length;
  const refresh = () => { void refreshProfile().catch(error => setNotice(error instanceof Error ? error.message : 'Could not refresh farmland data.')); };

  const addFarm = (name?: string, acreage?: string) => {
    const query = name ? `?name=${encodeURIComponent(name)}&acreage=${encodeURIComponent(acreage ?? '')}&crop=` : '';
    router.push(`/farmlands/add${query}` as Href);
  };

  const openFarm = (farmId: string | null, name: string, acreage: string) => {
    if (farmId) router.push(`/farmlands/${farmId}` as Href);
    else addFarm(name, acreage.replace(' acres', ''));
  };

  return (
    <SafeAreaView style={styles.safe} edges={['top', 'bottom']}>
      <View style={styles.screen}>
        <FarmPageHeader
          title="My Farmlands"
          subtitle="Manage your land profiles and seasonal activity."
          actionLabel="Add farmland"
          actionIcon="plus"
          onAction={() => addFarm()}
        />
        <ScrollView contentContainerStyle={styles.scrollContent} keyboardShouldPersistTaps="handled" showsVerticalScrollIndicator={false} refreshControl={<RefreshControl refreshing={dataLoading} onRefresh={refresh} tintColor={GREEN} />}>
          <View style={styles.summaryCard}>
            <View style={styles.summaryItem}>
              <View style={styles.summaryIcon}><FieldIcon name="leaf" size={25} color={GREEN} /></View>
              <View><Text style={styles.summaryNumber}>{farmlands.length}</Text><Text style={styles.summaryLabel}>farmlands</Text></View>
            </View>
            <View style={styles.summaryDivider} />
            <View style={styles.summaryItem}>
              <View style={styles.summaryIcon}><FarmProfileIcon name="field" size={24} color={GREEN} /></View>
              <View><Text style={styles.summaryNumber}>{totalAcres.toFixed(1)}</Text><Text style={styles.summaryLabel}>acres total</Text></View>
            </View>
            <View style={styles.summaryDivider} />
            <View style={styles.summaryItem}>
              <View style={[styles.summaryIcon, styles.attentionIcon]}><FieldIcon name="warning" size={21} color="#df4216" /></View>
              <View><Text style={styles.summaryNumber}>{attentionCount}</Text><Text style={styles.summaryLabel}>needs attention</Text></View>
            </View>
          </View>

          <View style={styles.searchRow}>
            <View style={styles.searchBox}>
              <FarmChromeIcon name="search" size={20} color={MUTED} />
              <TextInput accessibilityLabel="Search farmland" value={search} onChangeText={setSearch} placeholder="Search farmland" placeholderTextColor={MUTED} style={styles.searchInput} returnKeyType="search" />
              {search.length > 0 && <Pressable accessibilityRole="button" accessibilityLabel="Clear search" onPress={() => setSearch('')} hitSlop={8}><FarmChromeIcon name="close" size={17} color={MUTED} /></Pressable>}
            </View>
            <Pressable accessibilityRole="button" accessibilityLabel="Filter farmlands" onPress={() => setShowFilters(true)} style={styles.filterButton}><FarmChromeIcon name="filters" size={22} color={INK} /></Pressable>
          </View>

          <View style={styles.segment} accessibilityRole="tablist">
            {(['All', 'Active', 'Needs attention'] as const).map((item, index) => {
              const selected = filter === item;
              const count = item === 'All' ? cards.length : item === 'Active' ? cards.filter(farm => farm.status === 'Active').length : cards.filter(farm => farm.needsAttention).length;
              return (
                <Pressable key={item} accessibilityRole="tab" accessibilityState={{ selected }} onPress={() => setFilter(item)} style={[styles.segmentButton, selected && styles.segmentSelected, index > 0 && styles.segmentDivider]}>
                  <Text numberOfLines={1} style={[styles.segmentText, selected && styles.segmentTextSelected]}>{item} ({count})</Text>
                </Pressable>
              );
            })}
          </View>

          <View style={styles.farmCards}>
            {visibleCards.map((farm, index) => (
              <Pressable key={farm.id} accessibilityRole="button" accessibilityLabel={`Open ${farm.name}`} onPress={() => openFarm(farm.farmId, farm.name, farm.acreage)} style={[styles.farmCard, index === 0 && styles.featuredCard]}>
                <Image source={farm.image} resizeMode="cover" style={[styles.farmImage, index === 0 && styles.featuredImage]} />
                <View style={styles.farmInfo}>
                  <View style={styles.farmTitleRow}>
                    <Text numberOfLines={1} style={styles.farmName}>{farm.name}</Text>
                    <Text style={[styles.statusPill, farm.status === 'Idle' ? styles.idlePill : farm.status === 'Active' ? styles.activePill : styles.trackPill]}>{farm.status}</Text>
                  </View>
                  <View style={styles.detailRow}><DashboardIcon name="location" size={15} color={GREEN} /><Text numberOfLines={1} style={styles.detailText}>{farm.location}</Text></View>
                  <View style={styles.detailRow}>
                    <FarmProfileIcon name="field" size={15} color={GREEN} /><Text style={styles.detailText}>{farm.acreage}</Text>
                    <View style={styles.cropIcon}><FieldIcon name="leaf" size={14} color={GREEN} /></View><Text numberOfLines={1} style={[styles.detailText, styles.cropText]}>{farm.crop}</Text>
                  </View>
                  <View style={styles.detailRow}><FieldIcon name={farm.status === 'Idle' ? 'checkCircle' : 'sprout'} size={15} color={GREEN} /><Text numberOfLines={1} style={styles.detailText}>{farm.stage}</Text></View>
                  {farm.progress !== undefined && farm.stages.length > 0 && <View style={styles.progressWrap}>
                    <View style={styles.progressLine}><View style={styles.progressTrack} /><View style={[styles.progressFill, { width: `${farm.progress}%` }]} />{farm.stages.map(stage => <View key={stage.id} style={[styles.progressDot, (stage.status === 'current' || stage.status === 'completed') && styles.progressDotActive]} />)}</View>
                    <View style={styles.progressLabels}>{farm.stages.map(stage => <Text key={stage.id} numberOfLines={1} style={[styles.progressLabel, { width: `${100 / farm.stages.length}%` }, stage.status === 'current' && styles.progressActiveLabel]}>{stage.name}</Text>)}</View>
                  </View>}
                  {farm.issue && <View style={styles.cardTags}>
                    <View style={[styles.taskTag, styles.issueTag]}><FieldIcon name="leaf" size={15} color="#df4216" /><Text style={[styles.taskTagText, styles.issueText]}>{farm.issue}</Text></View>
                    <View style={styles.taskTag}><FieldIcon name="calendar" size={15} color="#cf5818" /><Text style={[styles.taskTagText, styles.dueText]}>{farm.task}</Text></View>
                  </View>}
                  {!farm.issue && farm.task && <View style={[styles.taskTag, farm.status === 'Idle' && styles.idleTaskTag]}><FieldIcon name="calendar" size={15} color={farm.status === 'Idle' ? GREEN : '#176bb3'} /><Text style={[styles.taskTagText, farm.status === 'Idle' ? styles.greenTagText : styles.blueTagText]}>{farm.task}</Text></View>}
                </View>
                <View style={styles.farmChevron}><FieldIcon name="chevron" size={19} color={INK} /></View>
              </Pressable>
            ))}
            {visibleCards.length === 0 && <Text style={styles.emptyText}>No farmlands match your search.</Text>}
          </View>

          <Text style={styles.quickTitle}>Quick actions</Text>
          <View style={styles.quickActions}>
            <Pressable accessibilityRole="button" onPress={() => addFarm()} style={styles.quickCard}>
              <View style={styles.quickIcon}><FarmChromeIcon name="plus" size={25} color={GREEN} /></View>
              <View style={styles.quickCopy}><Text style={styles.quickName}>Add farmland</Text><Text style={styles.quickSub}>Create a new land profile</Text></View>
            </Pressable>
            <Pressable accessibilityRole="button" onPress={() => setNotice('Import from a file or map is not available yet.')} style={styles.quickCard}>
              <View style={styles.quickIcon}><FieldIcon name="note" size={24} color={GREEN} /></View>
              <View style={styles.quickCopy}><Text style={styles.quickName}>Import land details</Text><Text style={styles.quickSub}>Import from a file or map</Text></View>
            </Pressable>
          </View>
          {notice ? <Text accessibilityLiveRegion="polite" style={styles.notice}>{notice}</Text> : null}
          <Pressable accessibilityRole="button" onPress={() => addFarm()} style={styles.addButton}>
            <FarmChromeIcon name="plus" size={23} color={PAPER} /><Text style={styles.addButtonText}>Add new farmland</Text>
          </Pressable>
        </ScrollView>
        <FarmBottomNavigation active="Home" />

        <Modal visible={showFilters} transparent animationType="fade" onRequestClose={() => setShowFilters(false)}>
          <Pressable style={styles.modalBackdrop} onPress={() => setShowFilters(false)}>
            <View style={styles.filterSheet}>
              <Text style={styles.filterTitle}>Filter farmlands</Text>
              {(['All', 'Active', 'Needs attention'] as const).map(item => (
                <Pressable key={item} accessibilityRole="button" accessibilityState={{ selected: filter === item }} onPress={() => { setFilter(item); setShowFilters(false); }} style={styles.filterOption}>
                  <Text style={styles.filterOptionText}>{item}</Text>
                  {filter === item ? <FieldIcon name="checkCircle" size={19} color={GREEN} /> : <View style={styles.radio} />}
                </Pressable>
              ))}
              <Pressable accessibilityRole="button" onPress={() => setShowFilters(false)} style={styles.filterCancel}><Text style={styles.filterCancelText}>Close</Text></Pressable>
            </View>
          </Pressable>
        </Modal>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: PAPER },
  screen: { flex: 1, backgroundColor: PAPER },
  scrollContent: { paddingHorizontal: 12, paddingTop: 8, paddingBottom: 10 },
  summaryCard: { minHeight: 58, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingHorizontal: 7, borderRadius: 14, backgroundColor: '#fffefa', borderWidth: 1, borderColor: '#eeece3' },
  summaryItem: { flex: 1, minWidth: 0, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 5 },
  summaryIcon: { width: 38, height: 38, flexShrink: 0, borderRadius: 22, alignItems: 'center', justifyContent: 'center', backgroundColor: '#e9f2e5' },
  attentionIcon: { backgroundColor: '#fff0dc' },
  summaryNumber: { color: INK, fontFamily: 'Georgia', fontSize: 23, lineHeight: 26, fontWeight: '700' },
  summaryLabel: { color: MUTED, fontSize: 9, lineHeight: 12 },
  summaryDivider: { width: 1, height: 39, backgroundColor: '#dedbd2' },
  searchRow: { flexDirection: 'row', gap: 7, marginTop: 7 },
  searchBox: { flex: 1, height: 39, flexDirection: 'row', alignItems: 'center', gap: 8, paddingHorizontal: 10, borderWidth: 1, borderColor: '#deddd5', borderRadius: 14, backgroundColor: '#fffefa' },
  searchInput: { flex: 1, minWidth: 0, padding: 0, color: INK, fontSize: 13, lineHeight: 17 },
  filterButton: { width: 42, height: 39, alignItems: 'center', justifyContent: 'center', borderWidth: 1, borderColor: '#eeece3', borderRadius: 14, backgroundColor: '#fffefa' },
  segment: { minHeight: 34, flexDirection: 'row', alignItems: 'stretch', marginTop: 7, marginBottom: 7, borderRadius: 20, borderWidth: 1, borderColor: '#deddd5', overflow: 'hidden', backgroundColor: '#fbfaf5' },
  segmentButton: { flex: 1, minHeight: 34, alignItems: 'center', justifyContent: 'center', paddingHorizontal: 3 },
  segmentDivider: { borderLeftWidth: 1, borderColor: '#e4e1d9' },
  segmentSelected: { borderRadius: 20, borderLeftWidth: 0, backgroundColor: GREEN },
  segmentText: { color: MUTED, fontSize: 11, lineHeight: 14, textAlign: 'center' },
  segmentTextSelected: { color: PAPER, fontWeight: '600' },
  farmCards: { gap: 7 },
  farmCard: { minHeight: 118, flexDirection: 'row', alignItems: 'stretch', gap: 8, padding: 7, borderRadius: 14, backgroundColor: '#fffefa', borderWidth: 1, borderColor: '#eeece3' },
  featuredCard: { minHeight: 146 },
  farmImage: { width: 102, height: 104, alignSelf: 'center', flexShrink: 0, borderRadius: 9, backgroundColor: '#e8e6dd' },
  featuredImage: { width: 110, height: 132 },
  farmInfo: { flex: 1, minWidth: 0, paddingTop: 1, paddingBottom: 1 },
  farmTitleRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 4, marginBottom: 3 },
  farmName: { flex: 1, minWidth: 0, color: INK, fontFamily: 'Georgia', fontSize: 19, lineHeight: 23, fontWeight: '700' },
  statusPill: { overflow: 'hidden', minWidth: 49, paddingHorizontal: 8, paddingVertical: 4, borderRadius: 12, textAlign: 'center', fontSize: 10, lineHeight: 13, fontWeight: '600' },
  activePill: { color: GREEN, backgroundColor: '#e8f1e4' },
  trackPill: { color: GREEN, backgroundColor: '#e8f1e4' },
  idlePill: { color: INK, backgroundColor: '#eff0f1' },
  detailRow: { minHeight: 18, flexDirection: 'row', alignItems: 'center', gap: 5 },
  detailText: { color: MUTED, fontSize: 10, lineHeight: 13, flexShrink: 1 },
  cropIcon: { width: 22, height: 22, alignItems: 'center', justifyContent: 'center', borderRadius: 12, backgroundColor: '#e9f2e5' },
  cropText: { flexShrink: 1 },
  progressWrap: { marginTop: 4 },
  progressLine: { height: 12, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', position: 'relative', paddingHorizontal: 4 },
  progressTrack: { position: 'absolute', left: 7, right: 7, top: 5, height: 2, backgroundColor: '#b8b7b1' },
  progressFill: { position: 'absolute', left: 7, top: 5, height: 2, backgroundColor: GREEN },
  progressDot: { width: 10, height: 10, borderRadius: 6, borderWidth: 1.5, borderColor: '#aaa9a2', backgroundColor: PAPER },
  progressDotActive: { width: 13, height: 13, borderColor: GREEN, backgroundColor: GREEN },
  progressLabels: { flexDirection: 'row', justifyContent: 'space-between', marginTop: 2 },
  progressLabel: { width: '25%', color: MUTED, fontSize: 8, lineHeight: 10, textAlign: 'center' },
  progressActiveLabel: { color: GREEN, fontWeight: '600' },
  cardTags: { flexDirection: 'row', gap: 5, marginTop: 5 },
  taskTag: { minHeight: 22, maxWidth: '100%', flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 4, paddingHorizontal: 7, borderRadius: 9, backgroundColor: '#e9f2fa' },
  issueTag: { flex: 1, justifyContent: 'flex-start', backgroundColor: '#fff0df' },
  idleTaskTag: { backgroundColor: '#e9f2e5' },
  taskTagText: { color: GREEN, fontSize: 10, lineHeight: 13, fontWeight: '600' },
  issueText: { color: '#df4216' },
  dueText: { color: '#cf5818' },
  blueTagText: { color: '#176bb3' },
  greenTagText: { color: GREEN },
  farmChevron: { width: 13, flexShrink: 0, alignItems: 'center', justifyContent: 'center' },
  emptyText: { paddingVertical: 24, color: MUTED, fontSize: 13, textAlign: 'center' },
  quickTitle: { color: INK, fontFamily: 'Georgia', fontSize: 22, lineHeight: 27, fontWeight: '700', marginTop: 7, marginBottom: 4 },
  quickActions: { flexDirection: 'row', gap: 7 },
  quickCard: { flex: 1, minWidth: 0, minHeight: 50, flexDirection: 'row', alignItems: 'center', gap: 6, paddingHorizontal: 7, borderRadius: 13, backgroundColor: '#fffefa', borderWidth: 1, borderColor: '#eeece3' },
  quickIcon: { width: 34, height: 34, flexShrink: 0, alignItems: 'center', justifyContent: 'center', borderRadius: 22, backgroundColor: '#e9f2e5' },
  quickCopy: { flex: 1, minWidth: 0 },
  quickName: { color: INK, fontSize: 12, lineHeight: 15, fontWeight: '700' },
  quickSub: { color: MUTED, fontSize: 9, lineHeight: 12, marginTop: 2 },
  notice: { marginTop: 4, color: MUTED, fontSize: 11, lineHeight: 15 },
  addButton: { minHeight: 39, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8, marginTop: 6, marginBottom: 3, borderRadius: 13, backgroundColor: GREEN },
  addButtonText: { color: PAPER, fontSize: 14, lineHeight: 18, fontWeight: '700' },
  modalBackdrop: { flex: 1, justifyContent: 'flex-end', paddingHorizontal: 12, paddingBottom: 18, backgroundColor: 'rgba(16, 24, 32, 0.38)' },
  filterSheet: { padding: 14, borderRadius: 18, backgroundColor: PAPER },
  filterTitle: { marginBottom: 7, color: INK, fontFamily: 'Georgia', fontSize: 19, lineHeight: 24, fontWeight: '700' },
  filterOption: { minHeight: 46, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', borderBottomWidth: 1, borderBottomColor: '#e5e2d8' },
  filterOptionText: { color: INK, fontSize: 14 },
  radio: { width: 18, height: 18, borderRadius: 10, borderWidth: 1.5, borderColor: '#abb6ad' },
  filterCancel: { minHeight: 44, alignItems: 'center', justifyContent: 'center', marginTop: 6, borderRadius: 9, backgroundColor: '#edf2e8' },
  filterCancelText: { color: GREEN, fontSize: 14, fontWeight: '700' },
});
