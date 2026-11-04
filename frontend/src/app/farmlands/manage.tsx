import { ENGLISH_FONT_FAMILY } from '@/theme/fonts';
import { Href, useRouter } from 'expo-router';
import React, { useState } from 'react';
import { Image, ImageSourcePropType, Modal, Pressable, RefreshControl, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { DashboardIcon } from '../../components/dashboard-icons';
import { FarmBottomNavigation, FarmChromeIcon, FarmPageHeader } from '../../components/farmland-mobile-ui';
import { FarmProfileIcon } from '../../components/farm-profile-icons';
import { FieldIcon } from '../../components/field-screen-ui';
import { useAppContext } from '../../context/AppProvider';

const PAPER = '#fffdf7';
const INK = '#101820';
const GREEN = '#07543a';
const MUTED = '#52677a';

type FarmFilter = 'All' | 'Active' | 'Alerts';
type FarmCardData = {
  id: string;
  name: string;
  location: string;
  acreage: string;
  crop: string;
  stage: string;
  status: 'Active' | 'No season';
  image: ImageSourcePropType;
  issue?: string;
  taskCount: number;
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
      name: farm.name,
      location: farm.location ?? 'Location not set',
      acreage: `${farm.acreage.toLocaleString(undefined, { maximumFractionDigits: 2 })} acres`,
      crop: farm.crop,
      stage: farm.activeSeasonId ? farm.growthStage : 'No season yet',
      status: farm.activeSeasonId ? 'Active' : 'No season',
      image: require('../../../assets/images/verification-rice-field.png'),
      taskCount: pendingTasks.length,
      issue: openProblem?.category,
      needsAttention: Boolean(openProblem) || pendingTasks.some(task => task.priority === 'high' || task.priority === 'urgent'),
    };
  });

  const visibleCards = cards.filter(card => {
    const matchesSearch = `${card.name} ${card.location} ${card.crop}`.toLowerCase().includes(search.trim().toLowerCase());
    const matchesFilter = filter === 'All' || (filter === 'Alerts' ? card.needsAttention : card.status === 'Active');
    return matchesSearch && matchesFilter;
  });
  const totalAcres = farmlands.reduce((sum, farm) => sum + farm.acreage, 0);
  const attentionCount = cards.filter(card => card.needsAttention).length;
  const showListTools = cards.length > 3;

  const refresh = () => {
    setNotice('');
    void refreshProfile().catch(error => setNotice(error instanceof Error ? error.message : 'Could not refresh farms.'));
  };
  const addFarm = () => router.push('/farmlands/add' as Href);
  const openFarm = (farmId: string) => router.push(`/farmlands/${farmId}` as Href);

  return (
    <SafeAreaView style={styles.safe} edges={['top', 'bottom']}>
      <View style={styles.screen}>
        <FarmPageHeader
          title="My Farms"
          subtitle={farmlands.length ? 'Choose a farm' : 'Add your first farm'}
          actionLabel="Add farm"
          actionIcon="plus"
          onAction={addFarm}
        />
        <ScrollView
          contentContainerStyle={styles.scrollContent}
          keyboardShouldPersistTaps="handled"
          showsVerticalScrollIndicator={false}
          refreshControl={<RefreshControl refreshing={dataLoading} onRefresh={refresh} tintColor={GREEN} />}
        >
          <View style={styles.summaryCard}>
            <SummaryItem icon="farms" value={String(farmlands.length)} label="Farms" />
            <View style={styles.summaryDivider} />
            <SummaryItem icon="acres" value={totalAcres.toLocaleString(undefined, { maximumFractionDigits: 1 })} label="Acres" />
            <View style={styles.summaryDivider} />
            <SummaryItem icon="alerts" value={String(attentionCount)} label="Alerts" warning={attentionCount > 0} />
          </View>

          {showListTools ? (
            <>
              <View style={styles.searchRow}>
                <View style={styles.searchBox}>
                  <FarmChromeIcon name="search" size={20} color={MUTED} />
                  <TextInput accessibilityLabel="Search farms" value={search} onChangeText={setSearch} placeholder="Find a farm" placeholderTextColor={MUTED} style={styles.searchInput} returnKeyType="search" />
                  {search.length > 0 ? <Pressable accessibilityRole="button" accessibilityLabel="Clear search" onPress={() => setSearch('')} hitSlop={8}><FarmChromeIcon name="close" size={17} color={MUTED} /></Pressable> : null}
                </View>
                <Pressable accessibilityRole="button" accessibilityLabel="Filter farms" onPress={() => setShowFilters(true)} style={styles.filterButton}><FarmChromeIcon name="filters" size={22} color={INK} /></Pressable>
              </View>

              <View style={styles.segment} accessibilityRole="tablist">
                {(['All', 'Active', 'Alerts'] as const).map((item, index) => {
                  const selected = filter === item;
                  const count = item === 'All' ? cards.length : item === 'Active' ? cards.filter(farm => farm.status === 'Active').length : attentionCount;
                  return (
                    <Pressable key={item} accessibilityRole="tab" accessibilityState={{ selected }} onPress={() => setFilter(item)} style={[styles.segmentButton, selected && styles.segmentSelected, index > 0 && styles.segmentDivider]}>
                      <Text style={[styles.segmentText, selected && styles.segmentTextSelected]}>{item} {count}</Text>
                    </Pressable>
                  );
                })}
              </View>
            </>
          ) : null}

          <View style={styles.farmCards}>
            {visibleCards.map(farm => (
              <Pressable key={farm.id} accessibilityRole="button" accessibilityLabel={`Open ${farm.name}`} onPress={() => openFarm(farm.id)} style={styles.farmCard}>
                <Image source={farm.image} resizeMode="cover" style={styles.farmImage} />
                <View style={styles.farmInfo}>
                  <View style={styles.farmTitleRow}>
                    <Text numberOfLines={1} style={styles.farmName}>{farm.name}</Text>
                    <Text style={[styles.statusPill, farm.status === 'Active' ? styles.activePill : styles.idlePill]}>{farm.status}</Text>
                  </View>
                  <View style={styles.mainDetail}>
                    <FieldIcon name="leaf" size={18} color={GREEN} />
                    <Text numberOfLines={1} style={styles.mainDetailText}>{farm.crop} · {farm.stage}</Text>
                  </View>
                  <View style={styles.detailRow}>
                    <DashboardIcon name="location" size={16} color={GREEN} />
                    <Text numberOfLines={1} style={styles.detailText}>{farm.location} · {farm.acreage}</Text>
                  </View>
                  <View style={[styles.signalRow, farm.issue && styles.signalRowWarning]}>
                    <DashboardIcon name={farm.issue ? 'warning' : 'tasks'} size={18} color={farm.issue ? '#d95120' : GREEN} />
                    <Text numberOfLines={1} style={[styles.signalText, farm.issue && styles.signalTextWarning]}>{farm.issue ?? `${farm.taskCount} tasks`}</Text>
                  </View>
                </View>
                <View style={styles.farmChevron}><DashboardIcon name="chevron" size={19} color={INK} /></View>
              </Pressable>
            ))}

            {visibleCards.length === 0 ? (
              <View style={styles.emptyCard}>
                <View style={styles.emptyIcon}><FarmProfileIcon name="field" size={34} color={GREEN} /></View>
                <Text style={styles.emptyTitle}>{cards.length ? 'No matching farms' : 'No farms yet'}</Text>
                <Text style={styles.emptyText}>{cards.length ? 'Try another search or filter.' : 'Add a farm to get started.'}</Text>
                {!cards.length ? <Pressable accessibilityRole="button" onPress={addFarm} style={styles.addButton}><FarmChromeIcon name="plus" size={22} color={PAPER} /><Text style={styles.addButtonText}>Add farm</Text></Pressable> : null}
              </View>
            ) : null}
          </View>

          {notice ? <Text accessibilityLiveRegion="polite" style={styles.notice}>{notice}</Text> : null}
        </ScrollView>
        <FarmBottomNavigation active="Home" />

        <Modal visible={showFilters} transparent animationType="fade" onRequestClose={() => setShowFilters(false)}>
          <Pressable style={styles.modalBackdrop} onPress={() => setShowFilters(false)}>
            <View style={styles.filterSheet}>
              <Text style={styles.filterTitle}>Show farms</Text>
              {(['All', 'Active', 'Alerts'] as const).map(item => (
                <Pressable key={item} accessibilityRole="button" accessibilityState={{ selected: filter === item }} onPress={() => { setFilter(item); setShowFilters(false); }} style={styles.filterOption}>
                  <Text style={styles.filterOptionText}>{item}</Text>
                  {filter === item ? <FieldIcon name="checkCircle" size={20} color={GREEN} /> : <View style={styles.radio} />}
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

function SummaryItem({ icon, value, label, warning = false }: { icon: 'farms' | 'acres' | 'alerts'; value: string; label: string; warning?: boolean }) {
  return (
    <View style={styles.summaryItem}>
      <View style={[styles.summaryIcon, warning && styles.summaryIconWarning]}>
        {icon === 'farms' ? <FieldIcon name="leaf" size={24} color={GREEN} /> : null}
        {icon === 'acres' ? <FarmProfileIcon name="field" size={24} color={GREEN} /> : null}
        {icon === 'alerts' ? <DashboardIcon name="warning" size={23} color={warning ? '#d95120' : GREEN} /> : null}
      </View>
      <Text numberOfLines={1} style={styles.summaryNumber}>{value}</Text>
      <Text style={styles.summaryLabel}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: PAPER },
  screen: { flex: 1, width: '100%', maxWidth: 500, alignSelf: 'center', backgroundColor: PAPER },
  scrollContent: { paddingHorizontal: 14, paddingTop: 12, paddingBottom: 18, gap: 12 },
  summaryCard: { minHeight: 100, flexDirection: 'row', alignItems: 'center', paddingHorizontal: 8, borderRadius: 20, backgroundColor: '#fffefa', borderWidth: 1, borderColor: '#e8e5dc' },
  summaryItem: { flex: 1, minWidth: 0, alignItems: 'center', justifyContent: 'center' },
  summaryIcon: { width: 39, height: 39, alignItems: 'center', justifyContent: 'center', borderRadius: 21, backgroundColor: '#eaf2e5' },
  summaryIconWarning: { backgroundColor: '#fff0dd' },
  summaryNumber: { maxWidth: '100%', marginTop: 4, color: INK, fontFamily: ENGLISH_FONT_FAMILY, fontSize: 20, lineHeight: 24, fontWeight: '700' },
  summaryLabel: { color: MUTED, fontFamily: ENGLISH_FONT_FAMILY, fontSize: 12, lineHeight: 16 },
  summaryDivider: { width: 1, height: 62, backgroundColor: '#e0ddd4' },
  searchRow: { flexDirection: 'row', gap: 8 },
  searchBox: { flex: 1, height: 46, flexDirection: 'row', alignItems: 'center', gap: 8, paddingHorizontal: 12, borderWidth: 1, borderColor: '#dedbd2', borderRadius: 16, backgroundColor: '#fffefa' },
  searchInput: { flex: 1, minWidth: 0, padding: 0, color: INK, fontFamily: ENGLISH_FONT_FAMILY, fontSize: 14, lineHeight: 18 },
  filterButton: { width: 48, height: 46, alignItems: 'center', justifyContent: 'center', borderWidth: 1, borderColor: '#e8e5dc', borderRadius: 16, backgroundColor: '#fffefa' },
  segment: { minHeight: 42, flexDirection: 'row', alignItems: 'stretch', borderRadius: 21, borderWidth: 1, borderColor: '#dedbd2', overflow: 'hidden', backgroundColor: '#fbfaf5' },
  segmentButton: { flex: 1, minHeight: 42, alignItems: 'center', justifyContent: 'center', paddingHorizontal: 4 },
  segmentDivider: { borderLeftWidth: 1, borderColor: '#e4e1d9' },
  segmentSelected: { borderRadius: 21, borderLeftWidth: 0, backgroundColor: GREEN },
  segmentText: { color: MUTED, fontFamily: ENGLISH_FONT_FAMILY, fontSize: 13, lineHeight: 17, textAlign: 'center' },
  segmentTextSelected: { color: PAPER, fontWeight: '700' },
  farmCards: { gap: 10 },
  farmCard: { minHeight: 136, flexDirection: 'row', alignItems: 'center', gap: 11, padding: 10, borderRadius: 20, backgroundColor: '#fffefa', borderWidth: 1, borderColor: '#e8e5dc', boxShadow: '0px 2px 8px rgba(30, 54, 37, 0.06)', elevation: 1 },
  farmImage: { width: 105, height: 116, flexShrink: 0, borderRadius: 14, backgroundColor: '#e8e6dd' },
  farmInfo: { flex: 1, minWidth: 0 },
  farmTitleRow: { flexDirection: 'row', alignItems: 'center', gap: 6 },
  farmName: { flex: 1, minWidth: 0, color: INK, fontFamily: ENGLISH_FONT_FAMILY, fontSize: 18, lineHeight: 23, fontWeight: '700' },
  statusPill: { overflow: 'hidden', paddingHorizontal: 8, paddingVertical: 4, borderRadius: 12, fontFamily: ENGLISH_FONT_FAMILY, fontSize: 10, lineHeight: 13, fontWeight: '700' },
  activePill: { color: GREEN, backgroundColor: '#e8f1e4' },
  idlePill: { color: MUTED, backgroundColor: '#eff0ed' },
  mainDetail: { minHeight: 26, marginTop: 5, flexDirection: 'row', alignItems: 'center', gap: 6 },
  mainDetailText: { flex: 1, color: '#28443d', fontFamily: ENGLISH_FONT_FAMILY, fontSize: 13, lineHeight: 17, fontWeight: '600' },
  detailRow: { minHeight: 22, flexDirection: 'row', alignItems: 'center', gap: 5 },
  detailText: { flex: 1, minWidth: 0, color: MUTED, fontFamily: ENGLISH_FONT_FAMILY, fontSize: 12, lineHeight: 16 },
  signalRow: { alignSelf: 'flex-start', minHeight: 28, marginTop: 6, paddingHorizontal: 8, flexDirection: 'row', alignItems: 'center', gap: 5, borderRadius: 14, backgroundColor: '#eaf2e5' },
  signalRowWarning: { backgroundColor: '#fff0dd' },
  signalText: { maxWidth: 150, color: GREEN, fontFamily: ENGLISH_FONT_FAMILY, fontSize: 12, lineHeight: 16, fontWeight: '700' },
  signalTextWarning: { color: '#c84a1d' },
  farmChevron: { width: 20, flexShrink: 0, alignItems: 'center', justifyContent: 'center' },
  emptyCard: { minHeight: 250, alignItems: 'center', justifyContent: 'center', padding: 24, borderWidth: 1, borderColor: '#e8e5dc', borderRadius: 20, backgroundColor: '#fffefa' },
  emptyIcon: { width: 66, height: 66, alignItems: 'center', justifyContent: 'center', borderRadius: 34, backgroundColor: '#eaf2e5' },
  emptyTitle: { marginTop: 13, color: INK, fontFamily: ENGLISH_FONT_FAMILY, fontSize: 20, lineHeight: 25, fontWeight: '700' },
  emptyText: { marginTop: 4, color: MUTED, fontFamily: ENGLISH_FONT_FAMILY, fontSize: 14, lineHeight: 19, textAlign: 'center' },
  addButton: { minHeight: 46, marginTop: 16, paddingHorizontal: 18, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 7, borderRadius: 16, backgroundColor: GREEN },
  addButtonText: { color: PAPER, fontFamily: ENGLISH_FONT_FAMILY, fontSize: 15, lineHeight: 19, fontWeight: '700' },
  notice: { color: MUTED, fontFamily: ENGLISH_FONT_FAMILY, fontSize: 13, lineHeight: 18, textAlign: 'center' },
  modalBackdrop: { flex: 1, justifyContent: 'flex-end', paddingHorizontal: 14, paddingBottom: 18, backgroundColor: 'rgba(16, 24, 32, 0.38)' },
  filterSheet: { padding: 16, borderRadius: 20, backgroundColor: PAPER },
  filterTitle: { marginBottom: 7, color: INK, fontFamily: ENGLISH_FONT_FAMILY, fontSize: 20, lineHeight: 25, fontWeight: '700' },
  filterOption: { minHeight: 50, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', borderBottomWidth: 1, borderBottomColor: '#e5e2d8' },
  filterOptionText: { color: INK, fontFamily: ENGLISH_FONT_FAMILY, fontSize: 15, lineHeight: 20 },
  radio: { width: 19, height: 19, borderRadius: 10, borderWidth: 1.5, borderColor: '#abb6ad' },
  filterCancel: { minHeight: 46, alignItems: 'center', justifyContent: 'center', marginTop: 8, borderRadius: 12, backgroundColor: '#edf2e8' },
  filterCancelText: { color: GREEN, fontFamily: ENGLISH_FONT_FAMILY, fontSize: 15, lineHeight: 19, fontWeight: '700' },
});
