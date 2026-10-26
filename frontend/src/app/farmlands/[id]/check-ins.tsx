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
import { formatDhakaDate } from '../../../utils/task-dates';

const PAPER = '#fffdf7';
const CARD = '#fffefa';
const GREEN = '#07543a';
const GREEN_DARK = '#064832';
const INK = '#111a23';
const MUTED = '#52677a';
const BORDER = '#e9e7df';

type ChoiceRowProps = {
  title: string;
  icon: FieldIconName;
  options: string[];
  value: string;
  onChange: (value: string) => void;
  compact: boolean;
};

function ChoiceRow({ title, icon, options, value, onChange, compact }: ChoiceRowProps) {
  return (
    <View style={styles.choiceRow}>
      <View style={[styles.choiceIcon, compact && styles.choiceIconCompact]}>
        <FieldIcon name={icon} size={22} color={GREEN} />
      </View>
      <Text numberOfLines={2} style={[styles.choiceTitle, compact && styles.choiceTitleCompact]}>{title}</Text>
      <View style={styles.choiceGroup}>
        {options.map(option => {
          const selected = value === option;
          return (
            <Pressable
              key={option}
              accessibilityRole="button"
              accessibilityState={{ selected }}
              onPress={() => onChange(option)}
              style={[styles.choicePill, { flex: option.length > 12 ? 1.3 : 1 }, selected && styles.choicePillSelected]}
            >
              <Text numberOfLines={compact ? 2 : 1} style={[styles.choiceLabel, compact && styles.choiceLabelCompact, selected && styles.choiceLabelSelected]}>{option}</Text>
            </Pressable>
          );
        })}
      </View>
    </View>
  );
}

export default function CheckIns() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const farmId = Array.isArray(id) ? id[0] : id;
  const router = useRouter();
  const { width } = useWindowDimensions();
  const compact = width < 375;
  const { farmlands, addCheckIn, updateTaskStatus } = useAppContext();
  const farm = farmlands.find(item => item.id === farmId);
  const [condition, setCondition] = useState('Good');
  const [vigor, setVigor] = useState('Moderate');
  const [water, setWater] = useState('Balanced');
  const [weeds, setWeeds] = useState('Medium');
  const [symptoms, setSymptoms] = useState('None');
  const [notes, setNotes] = useState('');
  const [historyOpen, setHistoryOpen] = useState(false);
  const [notice, setNotice] = useState('');
  const [saved, setSaved] = useState(false);
  const [saving, setSaving] = useState(false);
  const openCheckinTask = farm?.tasks.find(item => /field check-in|check-in|field observation/i.test(item.title) && item.status === 'pending');

  if (!farm || !farmId) {
    return <SafeAreaView style={styles.safe} edges={['bottom', 'left', 'right']}><Text style={styles.empty}>Farm not found.</Text></SafeAreaView>;
  }

  const saveCheckIn = async () => {
    const cleanNotes = notes.trim();
    setSaving(true);
    setNotice('');
    try {
      await addCheckIn(farmId, cleanNotes, {
      cropCondition: `${condition} field condition; ${vigor.toLowerCase()} plant vigor; ${weeds.toLowerCase()} weed pressure; ${symptoms === 'None' ? 'no disease symptoms' : `${symptoms} symptoms`}`,
      waterCondition: water,
      pestObserved: weeds === 'High',
      diseaseObserved: symptoms !== 'None',
      });
      setSaved(true);
      setNotice('Check-in saved to your farm history.');
    } catch (error) {
      setSaved(false);
      setNotice(error instanceof Error ? error.message : 'Could not save this check-in. Please try again.');
    } finally {
      setSaving(false);
    }
  };

  const markTaskComplete = async () => {
    if (!openCheckinTask) {
      setNotice('There is no open field check-in task linked to this farm.');
      return;
    }
    try {
      await updateTaskStatus(farmId, openCheckinTask.id, 'completed');
      setNotice('Field check-in task marked complete.');
    } catch (error) {
      setNotice(error instanceof Error ? error.message : 'Could not update this task.');
    }
  };

  const openLink = (route: 'problems' | 'alerts' | 'tasks') => {
    router.push(`/farmlands/${farmId}/${route}` as Href);
  };

  return (
    <SafeAreaView style={styles.safe} edges={['bottom', 'left', 'right']}>
      <View style={styles.frame}>
        <FieldScreenHeader
          title="Field Check-in"
          subtitle={`${farm.crop} · ${farm.growthStage} · ${farm.location ?? 'Location not set'}`}
          backHref={`/farmlands/${farmId}` as Href}
          actionLabel="View check-in history"
          actionIcon="history"
          onAction={() => setHistoryOpen(true)}
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
              <Text numberOfLines={1} style={[styles.heroTitle, compact && styles.heroTitleCompact]}>{farm.name}</Text>
              <Text style={[styles.heroSubhead, compact && styles.heroSubheadCompact]}>Today’s field record</Text>
              <Text style={[styles.heroDescription, compact && styles.heroDescriptionCompact]}>Record crop condition, water status, and field observations.</Text>
              <View style={styles.heroMeta}>
                <FieldIcon name="location" size={17} color={GREEN} />
                <Text numberOfLines={1} style={styles.metaText}>{farm.location ?? 'Location not set'}</Text>
                <View style={styles.metaDivider} />
                <FieldIcon name="rice" size={20} color={GREEN} />
                <Text style={styles.metaText}>{farm.acreage.toLocaleString(undefined, { maximumFractionDigits: 2 })} acres</Text>
              </View>
              <View style={styles.heroBadges}>
                {openCheckinTask ? <View style={styles.dueBadge}><FieldIcon name="calendar" size={16} color="#c83d19" /><Text style={styles.dueText}>Check-in task open</Text></View> : null}
                {farm.seasonProgressPercent != null ? <View style={styles.weekBadge}><Text style={styles.weekText}>{farm.seasonProgressPercent}% season</Text></View> : null}
              </View>
            </View>
          </View>

          <View style={styles.card}>
            <Text style={[styles.sectionTitle, compact && styles.sectionTitleCompact]}>Today’s observation</Text>
            <View style={styles.choiceRows}>
              <ChoiceRow title="Overall field condition" icon="leaf" options={['Good', 'Watch', 'Needs attention']} value={condition} onChange={value => { setCondition(value); setSaved(false); setNotice(''); }} compact={compact} />
              <ChoiceRow title="Plant vigor" icon="sprout" options={['Strong', 'Moderate', 'Weak']} value={vigor} onChange={value => { setVigor(value); setSaved(false); setNotice(''); }} compact={compact} />
              <ChoiceRow title="Water status" icon="droplet" options={['Balanced', 'Dry', 'Standing water']} value={water} onChange={value => { setWater(value); setSaved(false); setNotice(''); }} compact={compact} />
              <ChoiceRow title="Weed pressure" icon="weeds" options={['Low', 'Medium', 'High']} value={weeds} onChange={value => { setWeeds(value); setSaved(false); setNotice(''); }} compact={compact} />
              <ChoiceRow title="Disease symptoms" icon="leaf" options={['None', 'Brown spot', 'Other']} value={symptoms} onChange={value => { setSymptoms(value); setSaved(false); setNotice(''); }} compact={compact} />
            </View>
            <View style={styles.notesRow}>
              <View style={[styles.choiceIcon, compact && styles.choiceIconCompact]}><FieldIcon name="note" size={21} color={GREEN} /></View>
              <Text style={[styles.notesLabel, compact && styles.choiceTitleCompact]}>Notes</Text>
              <View style={styles.notesBox}>
                <TextInput
                  accessibilityLabel="Field check-in notes"
                  value={notes}
                  onChangeText={value => { setNotes(value.slice(0, 500)); setSaved(false); setNotice(''); }}
                  placeholder="Add field notes"
                  placeholderTextColor="#7a8790"
                  multiline
                  maxLength={500}
                  textAlignVertical="top"
                  style={styles.notesInput}
                />
                <Text style={styles.characterCount}>{notes.length}/500</Text>
              </View>
            </View>
          </View>

          <View style={[styles.card, styles.linkedCard]}>
            <Text style={[styles.sectionTitle, compact && styles.sectionTitleCompact]}>Linked records</Text>
            {farm.problems.filter(problem => problem.status === 'open' || problem.status === 'monitoring').slice(0, 2).map(problem => (
              <LinkedRow key={problem.id} icon="leaf" title={problem.category} subtitle={problem.description} badge={problem.status} badgeTone="orange" onPress={() => openLink('problems')} />
            ))}
            {farm.tasks.filter(task => task.status === 'pending').slice(0, 2).map(task => (
              <LinkedRow key={task.id} icon="list" title={task.title} subtitle={task.description ?? 'Scheduled farm task'} badge={task.priority} badgeTone="green" onPress={() => openLink('tasks')} />
            ))}
            {!farm.problems.some(problem => problem.status === 'open' || problem.status === 'monitoring') && farm.tasks.filter(task => task.status === 'pending').length === 0
              ? <Text style={styles.historyEmpty}>No linked problems or open tasks.</Text> : null}
          </View>
          {notice ? <Text accessibilityLiveRegion={saved ? 'polite' : 'assertive'} accessibilityRole={saved ? undefined : 'alert'} style={[styles.notice, saved && styles.noticeSaved]}>{notice}</Text> : null}
        </ScrollView>

        <View style={styles.actionBar}>
          <Pressable accessibilityRole="button" onPress={markTaskComplete} style={styles.completeButton}>
            <FieldIcon name="checkCircle" size={22} color={GREEN} />
            <Text style={styles.completeLabel}>Mark task complete</Text>
          </Pressable>
          <Pressable accessibilityRole="button" disabled={saving} onPress={() => void saveCheckIn()} style={[styles.saveButton, saved && styles.saveButtonSaved, saving && styles.saveButtonDisabled]}>
            <FieldIcon name="save" size={21} color="#fffdf7" />
            <Text style={styles.saveLabel}>{saving ? 'Saving…' : saved ? 'Check-in saved' : 'Save check-in'}</Text>
          </Pressable>
        </View>
        <FieldBottomNav active="Tasks" farmId={farmId} />
      </View>

      <Modal visible={historyOpen} transparent animationType="fade" onRequestClose={() => setHistoryOpen(false)}>
        <View style={styles.modalBackdrop}>
          <View style={styles.historyModal}>
            <View style={styles.modalHeading}>
              <View><Text style={styles.modalTitle}>Check-in history</Text><Text style={styles.modalSubtitle}>{farm.checkIns.length} recorded field visits</Text></View>
              <Pressable accessibilityRole="button" accessibilityLabel="Close history" onPress={() => setHistoryOpen(false)} style={styles.closeButton}><FieldIcon name="close" size={20} color={INK} /></Pressable>
            </View>
            <ScrollView style={styles.historyList}>
              {farm.checkIns.length ? farm.checkIns.map(item => (
                <View key={item.id} style={styles.historyItem}>
                  <View style={styles.historyItemTop}><Text style={styles.historyStage}>{item.stageName}</Text><Text style={styles.historyDate}>{formatDhakaDate(item.at)}</Text></View>
                  <Text style={styles.historyNotes}>{item.notes}</Text>
                  {item.observations.waterCondition ? <Text style={styles.historyMeta}>Water · {item.observations.waterCondition}</Text> : null}
                </View>
              )) : <Text style={styles.historyEmpty}>No previous check-ins recorded.</Text>}
            </ScrollView>
          </View>
        </View>
      </Modal>
    </SafeAreaView>
  );
}

function LinkedRow({
  icon, title, subtitle, badge, badgeTone, onPress, last = false,
}: {
  icon: FieldIconName; title: string; subtitle: string; badge: string; badgeTone: 'orange' | 'green'; onPress: () => void; last?: boolean;
}) {
  return (
    <Pressable accessibilityRole="button" onPress={onPress} style={[styles.linkedRow, last && styles.linkedRowLast]}>
      <View style={styles.linkedIcon}><FieldIcon name={icon} size={22} color={GREEN} /></View>
      <View style={styles.linkedCopy}><Text numberOfLines={1} style={styles.linkedTitle}>{title}</Text><Text numberOfLines={1} style={styles.linkedSubtitle}>{subtitle}</Text></View>
      <View style={[styles.linkedBadge, badgeTone === 'orange' ? styles.linkedBadgeOrange : styles.linkedBadgeGreen]}><Text style={[styles.linkedBadgeText, badgeTone === 'orange' ? styles.orangeText : styles.greenText]}>{badge}</Text></View>
      <FieldIcon name="chevron" size={19} color="#243f54" />
    </Pressable>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: PAPER },
  frame: { flex: 1, width: '100%', maxWidth: 520, alignSelf: 'center', backgroundColor: PAPER },
  scroll: { flex: 1 },
  content: { paddingHorizontal: 12, paddingTop: 6, paddingBottom: 6 },
  hero: { height: 136, overflow: 'hidden', borderRadius: 18, marginBottom: 7, borderWidth: 1, borderColor: BORDER, backgroundColor: '#edf1e6' },
  heroCompact: { height: 138 },
  heroImage: { width: '100%', height: '100%' },
  heroShade: { ...StyleSheet.absoluteFill, backgroundColor: 'rgba(19, 45, 27, .04)' },
  heroCopy: { position: 'absolute', top: 0, left: 0, bottom: 0, width: '70%', paddingLeft: 10, paddingRight: 6, paddingTop: 6, backgroundColor: PAPER, borderTopRightRadius: 42, borderBottomRightRadius: 36 },
  heroCopyCompact: { width: '74%', paddingLeft: 8 },
  heroTitle: { color: INK, fontFamily: 'Georgia', fontWeight: '700', fontSize: 24, lineHeight: 28 },
  heroTitleCompact: { fontSize: 22, lineHeight: 26 },
  heroSubhead: { color: INK, fontFamily: 'Georgia', fontSize: 13, lineHeight: 16, fontWeight: '700' },
  heroSubheadCompact: { fontSize: 12 },
  heroDescription: { color: MUTED, fontSize: 10, lineHeight: 13, marginTop: 2 },
  heroDescriptionCompact: { fontSize: 9.5, lineHeight: 12 },
  heroMeta: { flexDirection: 'row', alignItems: 'center', gap: 4, marginTop: 5 },
  metaText: { color: MUTED, fontSize: 9, flexShrink: 1 },
  metaDivider: { width: 1, height: 16, backgroundColor: BORDER, marginHorizontal: 2 },
  heroBadges: { flexDirection: 'row', gap: 6, marginTop: 5 },
  dueBadge: { height: 23, flexDirection: 'row', alignItems: 'center', gap: 4, paddingHorizontal: 8, borderRadius: 15, backgroundColor: '#ffecdb' },
  dueText: { color: '#bd3015', fontSize: 9, fontWeight: '600' },
  weekBadge: { height: 23, minWidth: 59, alignItems: 'center', justifyContent: 'center', paddingHorizontal: 8, borderRadius: 15, backgroundColor: '#eaf2e6' },
  weekText: { color: GREEN_DARK, fontSize: 9, fontWeight: '600' },
  card: { paddingHorizontal: 8, paddingVertical: 6, marginBottom: 7, borderWidth: 1, borderColor: BORDER, borderRadius: 17, backgroundColor: CARD, boxShadow: '0px 1px 5px rgba(79, 80, 55, 0.05)' },
  sectionTitle: { color: INK, fontFamily: 'Georgia', fontSize: 17, lineHeight: 21, fontWeight: '700' },
  sectionTitleCompact: { fontSize: 16, lineHeight: 20 },
  choiceRows: { marginTop: 1 },
  choiceRow: { minHeight: 28, flexDirection: 'row', alignItems: 'center', gap: 5, borderBottomWidth: 1, borderBottomColor: '#efeee8' },
  choiceIcon: { width: 26, height: 26, flexShrink: 0, alignItems: 'center', justifyContent: 'center', borderRadius: 18, backgroundColor: '#e9f2e5' },
  choiceIconCompact: { width: 24, height: 24 },
  choiceTitle: { width: 88, color: INK, fontSize: 10, lineHeight: 12, flexShrink: 1 },
  choiceTitleCompact: { width: 76, fontSize: 9, lineHeight: 11 },
  choiceGroup: { flex: 1, flexDirection: 'row', gap: 4, minWidth: 0 },
  choicePill: { flex: 1, height: 23, minWidth: 0, alignItems: 'center', justifyContent: 'center', paddingHorizontal: 1, borderRadius: 17, backgroundColor: '#f3f2ed' },
  choicePillSelected: { backgroundColor: GREEN },
  choiceLabel: { color: MUTED, fontSize: 8, lineHeight: 10, textAlign: 'center' },
  choiceLabelCompact: { fontSize: 7.5, lineHeight: 9 },
  choiceLabelSelected: { color: '#fffdf7', fontWeight: '600' },
  notesRow: { minHeight: 51, flexDirection: 'row', alignItems: 'center', gap: 6, paddingTop: 3 },
  notesLabel: { width: 42, color: INK, fontSize: 10 },
  notesBox: { flex: 1, minHeight: 48, borderWidth: 1, borderColor: '#e0ded5', borderRadius: 11, paddingHorizontal: 7, paddingTop: 5, paddingBottom: 3 },
  notesInput: { minHeight: 30, padding: 0, color: MUTED, fontSize: 10, lineHeight: 13, outlineStyle: 'none' as never },
  characterCount: { alignSelf: 'flex-end', color: '#718090', fontSize: 8, lineHeight: 10 },
  photosHeading: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginBottom: 4 },
  photoCount: { color: MUTED, fontSize: 9 },
  photoRow: { height: 60 },
  photoRowContent: { height: 60, flexDirection: 'row', gap: 6 },
  photoItem: { position: 'relative', height: 60, overflow: 'hidden', borderRadius: 10, backgroundColor: '#e5e9df' },
  photoItemWide: { width: 116 },
  photoItemNarrow: { width: 50 },
  photoItemWideCompact: { width: 105 },
  photoItemNarrowCompact: { width: 46 },
  photoImage: { width: '100%', height: '100%' },
  removePhoto: { position: 'absolute', top: 4, right: 4, width: 22, height: 22, borderRadius: 12, alignItems: 'center', justifyContent: 'center', backgroundColor: '#102b25' },
  addPhoto: { width: 68, height: 60, alignItems: 'center', justifyContent: 'center', gap: 3, borderWidth: 1, borderStyle: 'dashed', borderColor: '#d5d2c8', borderRadius: 10, backgroundColor: '#f9f8f2' },
  addPhotoCompact: { width: 62 },
  addPhotoLabel: { color: MUTED, fontSize: 9, textAlign: 'center' },
  weatherCard: { minHeight: 82, flexDirection: 'row', alignItems: 'flex-start', overflow: 'hidden', position: 'relative', marginBottom: 7, paddingHorizontal: 8, paddingVertical: 7, borderRadius: 16, backgroundColor: '#c9dff0' },
  weatherCardCompact: { minHeight: 86, paddingHorizontal: 7 },
  weatherImage: { width: '100%', height: '100%', borderRadius: 17 },
  weatherWash: { ...StyleSheet.absoluteFill, backgroundColor: 'rgba(190, 219, 241, .82)' },
  weatherIcon: { width: 37, paddingTop: 3, alignItems: 'center' },
  weatherCopy: { flex: 1, minWidth: 0, paddingRight: 4 },
  weatherTitle: { color: INK, fontFamily: 'Georgia', fontSize: 14, lineHeight: 17, fontWeight: '700' },
  weatherText: { color: '#173958', fontSize: 9, lineHeight: 12, marginTop: 1 },
  weatherHint: { color: '#4d6277', fontSize: 8.5, lineHeight: 11, marginTop: 2 },
  weatherAction: { position: 'absolute', right: 7, bottom: 6, minHeight: 24, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 3, paddingHorizontal: 7, borderRadius: 16, backgroundColor: GREEN },
  weatherActionText: { color: '#fffdf7', fontSize: 8, fontWeight: '600' },
  linkedCard: { paddingBottom: 3 },
  linkedRow: { minHeight: 31, flexDirection: 'row', alignItems: 'center', gap: 5, paddingHorizontal: 1, borderTopWidth: 1, borderTopColor: '#eceae2' },
  linkedRowLast: { borderBottomWidth: 0 },
  linkedIcon: { width: 26, height: 26, flexShrink: 0, alignItems: 'center', justifyContent: 'center', borderRadius: 15, backgroundColor: '#e9f2e5' },
  linkedCopy: { flex: 1, minWidth: 0 },
  linkedTitle: { color: INK, fontSize: 9.5, lineHeight: 12, fontWeight: '500' },
  linkedSubtitle: { color: MUTED, fontSize: 8, lineHeight: 10 },
  linkedBadge: { minWidth: 63, paddingHorizontal: 5, paddingVertical: 4, alignItems: 'center', justifyContent: 'center', borderRadius: 12 },
  linkedBadgeOrange: { backgroundColor: '#ffecd9' },
  linkedBadgeGreen: { backgroundColor: '#e9f2e7' },
  linkedBadgeText: { fontSize: 8, fontWeight: '500' },
  orangeText: { color: '#c83719' },
  greenText: { color: GREEN_DARK },
  notice: { paddingVertical: 6, paddingHorizontal: 8, marginBottom: 4, color: '#a34416', fontSize: 11, textAlign: 'center' },
  noticeSaved: { color: GREEN },
  actionBar: { flexDirection: 'row', gap: 7, paddingHorizontal: 12, paddingVertical: 5, backgroundColor: PAPER },
  completeButton: { flex: 1, minHeight: 38, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 5, borderWidth: 1.4, borderColor: GREEN_DARK, borderRadius: 11, backgroundColor: CARD },
  completeLabel: { color: GREEN_DARK, fontSize: 10, fontWeight: '600' },
  saveButton: { flex: 1, minHeight: 38, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 6, borderRadius: 11, backgroundColor: GREEN },
  saveButtonSaved: { backgroundColor: GREEN_DARK },
  saveButtonDisabled: { opacity: 0.65 },
  saveLabel: { color: '#fffdf7', fontSize: 10, fontWeight: '600' },
  empty: { padding: 24, color: MUTED, fontSize: 15, textAlign: 'center' },
  modalBackdrop: { flex: 1, justifyContent: 'center', paddingHorizontal: 20, backgroundColor: 'rgba(18, 33, 27, .42)' },
  historyModal: { width: '100%', maxWidth: 460, maxHeight: '76%', alignSelf: 'center', padding: 18, borderRadius: 20, backgroundColor: PAPER },
  modalHeading: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingBottom: 12 },
  modalTitle: { color: INK, fontFamily: 'Georgia', fontSize: 21, fontWeight: '700' },
  modalSubtitle: { marginTop: 3, color: MUTED, fontSize: 12 },
  closeButton: { width: 36, height: 36, alignItems: 'center', justifyContent: 'center', borderRadius: 18, backgroundColor: '#efeee7' },
  historyList: { flexGrow: 0 },
  historyItem: { paddingVertical: 12, borderTopWidth: 1, borderTopColor: BORDER },
  historyItemTop: { flexDirection: 'row', justifyContent: 'space-between', gap: 10 },
  historyStage: { color: INK, fontSize: 14, fontWeight: '600' },
  historyDate: { color: MUTED, fontSize: 11 },
  historyNotes: { marginTop: 5, color: MUTED, fontSize: 12, lineHeight: 18 },
  historyMeta: { marginTop: 6, color: GREEN, fontSize: 11 },
  historyEmpty: { paddingVertical: 18, color: MUTED, fontSize: 13, textAlign: 'center' },
});
