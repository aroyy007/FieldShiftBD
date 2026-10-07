import React, { useEffect, useMemo, useState } from 'react';
import { ImageBackground, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Href, useLocalSearchParams, useRouter } from 'expo-router';
import { DashboardIcon } from '../../../components/dashboard-icons';
import { FarmBottomNavigation, FarmPageHeader } from '../../../components/farmland-mobile-ui';
import { FieldIcon, FieldIconName } from '../../../components/field-screen-ui';
import { useAppContext } from '../../../context/AppProvider';
import { apiRequest } from '../../../services/api-client';
import { getTaskScheduleState } from '../../../utils/task-dates';

const PAPER = '#fffdf7';
const INK = '#101820';
const GREEN = '#07543a';
const MUTED = '#52677a';
type AlertFilter = 'All' | 'Urgent' | 'Resolved';
type AlertCard = {
  id: string;
  type: 'urgent' | 'active' | 'resolved';
  title: string;
  body: string;
  source: string;
  badge: string;
  timing?: string;
  action?: string;
  route: 'alerts' | 'problems' | 'tasks' | 'season-plan';
  icon: FieldIconName;
  visual?: 'weather' | 'problem';
};
type WeatherAssessment = { alerts: { title: string; message: string; recommended_action: string; severity: string; event_type: string }[] };

export default function Alerts() {
  const params = useLocalSearchParams<{ id?: string | string[] }>();
  const farmId = Array.isArray(params.id) ? params.id[0] : params.id;
  const { farmlands } = useAppContext();
  const farm = farmlands.find(item => item.id === farmId);
  const router = useRouter();
  const [filter, setFilter] = useState<AlertFilter>('All');
  const [weather, setWeather] = useState<WeatherAssessment | null>(null);
  const [weatherError, setWeatherError] = useState('');

  useEffect(() => {
    if (!farmId) return;
    let active = true;
    apiRequest<WeatherAssessment>(`/weather/assessment/${encodeURIComponent(farmId)}`)
      .then(result => { if (active) { setWeather(result); setWeatherError(''); } })
      .catch(error => { if (active) setWeatherError(error instanceof Error ? error.message : 'Weather assessment is unavailable.'); });
    return () => { active = false; };
  }, [farmId]);

  const cards = useMemo<AlertCard[]>(() => {
    const result: AlertCard[] = [];
    weather?.alerts.forEach((alert, index) => {
      const urgent = /critical|high|severe/i.test(alert.severity);
      result.push({
        id: `weather-${index}`,
        type: urgent ? 'urgent' : 'active',
        title: alert.title,
        body: `${alert.message} ${alert.recommended_action}`.trim(),
        source: 'Weather',
        badge: alert.severity,
        timing: alert.event_type.replace(/_/g, ' '),
        action: 'View forecast',
        route: 'alerts',
        icon: 'cloudRain',
        visual: 'weather',
      });
    });
    if (weatherError) result.push({
      id: 'weather-unavailable', type: 'active', title: 'Weather assessment unavailable', body: weatherError,
      source: 'Weather', badge: 'Unavailable', route: 'alerts', icon: 'cloudRain', visual: 'weather',
    });
    farm?.problems.forEach(problem => {
      const resolved = problem.status === 'resolved' || problem.status === 'dismissed';
      const urgent = !resolved && (problem.severity === 'high' || problem.severity === 'critical');
      result.push({
        id: `problem-${problem.id}`,
        type: resolved ? 'resolved' : urgent ? 'urgent' : 'active',
        title: problem.category,
        body: problem.description,
        source: problem.source.replace(/_/g, ' '),
        badge: `${problem.severity} · ${problem.status}`,
        timing: new Date(problem.createdAt).toLocaleDateString(),
        action: 'View problem',
        route: 'problems',
        icon: 'leaf',
        visual: 'problem',
      });
    });
    farm?.tasks.forEach(task => {
      const schedule = getTaskScheduleState(task, new Date());
      const resolved = task.status === 'completed' || task.status === 'skipped' || task.status === 'cancelled';
      const overdue = schedule === 'overdue';
      result.push({
        id: `task-${task.id}`,
        type: resolved ? 'resolved' : overdue ? 'urgent' : 'active',
        title: task.title,
        body: task.description || `${task.priority} priority task from ${task.source.replace(/_/g, ' ')}.`,
        source: 'Tasks',
        badge: resolved ? task.status : schedule,
        timing: task.dueAt ? new Date(task.dueAt).toLocaleDateString() : undefined,
        action: 'View tasks',
        route: 'tasks',
        icon: 'tasks',
      });
    });
    return result;
  }, [farm, weather, weatherError]);
  const filteredCards = cards.filter(card =>
    filter === 'All' || (filter === 'Urgent' ? card.type === 'urgent' : card.type === 'resolved'),
  );
  const urgentCount = cards.filter(card => card.type === 'urgent').length;
  const activeCount = cards.filter(card => card.type === 'active').length;
  const resolvedCount = cards.filter(card => card.type === 'resolved').length;

  const openAction = (route: AlertCard['route']) => {
    if (farmId) router.push(`/farmlands/${farmId}/${route}` as Href);
  };

  return (
    <SafeAreaView style={styles.safe} edges={['bottom', 'left', 'right']}>
      <View style={styles.screen}>
        <FarmPageHeader
          title="Alerts"
          subtitle={farm ? `${farm.crop} · ${farm.growthStage} · ${farm.location ?? 'Location not set'}` : 'Farm alerts'}
          actionLabel="Show urgent alerts"
          actionIcon="filters"
          onAction={() => setFilter(current => current === 'Urgent' ? 'All' : 'Urgent')}
          backHref={(farmId ? `/farmlands/${farmId}` : '/farmlands') as Href}
        />
        <ScrollView contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
          <View style={styles.hero}>
            <ImageBackground source={require('../../../../assets/images/verification-rice-field.png')} resizeMode="cover" style={styles.heroImage} imageStyle={styles.heroImageStyle}>
              <View style={styles.heroCopy}>
                <Text style={styles.heroFarmName}>{farm?.name ?? 'Farmland'}</Text>
                <Text style={styles.heroCrop}>{farm ? `${farm.crop} · ${farm.growthStage}` : 'No farmland selected'}</Text>
                <View style={styles.heroMeta}>
                  <DashboardIcon name="location" size={17} color={GREEN} />
                  <Text numberOfLines={1} style={styles.heroMetaText}>{farm?.location ?? 'Location not set'}</Text>
                  <View style={styles.metaDivider} />
                  <DashboardIcon name="acreage" size={17} color={GREEN} />
                  <Text style={styles.heroMetaText}>{farm ? `${farm.acreage.toLocaleString(undefined, { maximumFractionDigits: 2 })} acres` : '—'}</Text>
                </View>
                <Text style={styles.heroSummary}>{cards.length ? 'Review current farm issues and tasks.' : 'No alerts, problems, or tasks are recorded for this farm.'}</Text>
                <View style={styles.statsRow}>
                  <View style={[styles.stat, styles.urgentStat]}>
                    <View style={[styles.statIconCircle, styles.urgentIconCircle]}><FieldIcon name="warning" size={18} color="#e54413" /></View>
                    <View><Text style={styles.statNumber}>{urgentCount}</Text><Text style={[styles.statLabel, styles.urgentText]}>urgent</Text></View>
                  </View>
                  <View style={styles.stat}>
                    <View style={styles.statIconCircle}><FieldIcon name="clock" size={18} color={GREEN} /></View>
                    <View><Text style={styles.statNumber}>{activeCount}</Text><Text style={styles.statLabel}>active</Text></View>
                  </View>
                  <View style={styles.stat}>
                    <View style={styles.statIconCircle}><FieldIcon name="checkCircle" size={18} color={GREEN} /></View>
                    <View><Text style={styles.statNumber}>{resolvedCount}</Text><Text style={styles.statLabel}>resolved</Text></View>
                  </View>
                </View>
              </View>
            </ImageBackground>
          </View>

          <View style={styles.segment} accessibilityRole="tablist">
            {(['All', 'Urgent', 'Resolved'] as const).map((name, index) => {
              const selected = filter === name;
              const count = name === 'All' ? cards.length : name === 'Urgent' ? urgentCount : resolvedCount;
              return (
                <Pressable key={name} accessibilityRole="tab" accessibilityState={{ selected }} onPress={() => setFilter(name)} style={[styles.segmentButton, selected && styles.segmentSelected, index > 0 && styles.segmentDivider]}>
                  <Text style={[styles.segmentText, selected && styles.segmentTextSelected]}>{name} ({count})</Text>
                </Pressable>
              );
            })}
          </View>

          <View style={styles.cards}>
            {filteredCards.map(card => (
              <Pressable
                key={card.id}
                accessibilityRole={card.action ? 'button' : undefined}
                accessibilityLabel={card.action ? `${card.action}: ${card.title}` : card.title}
                onPress={card.action ? () => openAction(card.route) : undefined}
                style={[styles.alertCard, card.visual === 'weather' && styles.rainCard, card.visual === 'problem' && styles.spotCard, card.type === 'resolved' && styles.resolvedCard]}
              >
                {card.visual === 'weather' && <ImageBackground source={require('../../../../assets/images/assistant-rain-field.png')} resizeMode="cover" style={styles.rainImage} imageStyle={styles.rainImageStyle} />}
                {card.visual === 'problem' && <ImageBackground source={require('../../../../assets/images/scan-leaf-preview.jpg')} resizeMode="cover" style={styles.spotImage} imageStyle={styles.spotImageStyle} />}
                <View style={[styles.cardIconWrap, card.visual === 'weather' && styles.rainIconWrap, card.visual === 'problem' && styles.hiddenIconWrap, card.type === 'resolved' && styles.resolvedIconWrap]}>
                  <FieldIcon name={card.icon} size={card.visual === 'weather' ? 34 : 30} color={card.visual === 'weather' ? '#2a668b' : card.type === 'urgent' ? '#e14a18' : GREEN} />
                </View>
                <View style={[styles.cardMain, card.action && styles.cardMainWithAction]}>
                  <Text numberOfLines={2} style={styles.cardTitle}>{card.title}</Text>
                  <Text numberOfLines={2} style={styles.cardBody}>{card.body}</Text>
                  <View style={styles.badges}>
                    <View style={[styles.badge, card.visual === 'weather' ? styles.weatherBadge : styles.greenBadge]}>
                      <FieldIcon name={card.icon} size={14} color={card.visual === 'weather' ? '#2d73a1' : GREEN} />
                      <Text style={[styles.badgeText, card.visual === 'weather' && styles.weatherBadgeText]}>{card.source}</Text>
                    </View>
                    <View style={[styles.badge, card.type === 'urgent' ? styles.warningBadge : styles.greenBadge]}>
                      <FieldIcon name={card.type === 'urgent' ? 'warning' : card.type === 'resolved' ? 'checkCircle' : 'calendar'} size={14} color={card.type === 'urgent' ? '#d93916' : GREEN} />
                      <Text style={[styles.badgeText, card.type === 'urgent' && styles.warningBadgeText]}>{card.badge}</Text>
                    </View>
                    {card.timing && <View style={[styles.badge, styles.warningBadge]}><FieldIcon name="calendar" size={14} color="#d93916" /><Text style={[styles.badgeText, styles.warningBadgeText]}>{card.timing}</Text></View>}
                  </View>
                </View>
                {card.action && <View style={styles.cardAction}><Text style={styles.cardActionText}>{card.action}</Text><FieldIcon name="chevron" size={15} color={PAPER} /></View>}
              </Pressable>
            ))}
            {filteredCards.length === 0 ? <View style={styles.emptyCards}><Text style={styles.emptyCardsText}>Nothing to show in this filter.</Text></View> : null}
          </View>
        </ScrollView>
        <FarmBottomNavigation active="Home" farmId={farm?.id ?? farmId} />
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: PAPER },
  screen: { flex: 1, backgroundColor: PAPER },
  scrollContent: { paddingHorizontal: 12, paddingTop: 8, paddingBottom: 10, gap: 8 },
  hero: { height: 158, borderRadius: 16, overflow: 'hidden', backgroundColor: '#f7f5ec', borderWidth: 1, borderColor: '#eeece3' },
  heroImage: { flex: 1, justifyContent: 'center' },
  heroImageStyle: { borderRadius: 16 },
  heroCopy: { width: '65%', height: '100%', justifyContent: 'center', paddingLeft: 12, paddingRight: 3, backgroundColor: 'rgba(255,253,247,0.96)', borderTopRightRadius: 40, borderBottomRightRadius: 52 },
  heroFarmName: { color: INK, fontFamily: 'Georgia', fontWeight: '700', fontSize: 26, lineHeight: 30 },
  heroCrop: { color: INK, fontSize: 12, lineHeight: 16, fontWeight: '600' },
  heroMeta: { flexDirection: 'row', alignItems: 'center', gap: 4, marginTop: 5 },
  heroMetaText: { color: MUTED, fontSize: 10, lineHeight: 13, flexShrink: 1 },
  metaDivider: { width: 1, height: 14, backgroundColor: '#d6d3c9', marginHorizontal: 3 },
  heroSummary: { marginTop: 7, color: MUTED, fontSize: 11, lineHeight: 15, maxWidth: 230 },
  statsRow: { flexDirection: 'row', alignItems: 'center', gap: 5, marginTop: 8 },
  stat: { height: 35, minWidth: 62, flexDirection: 'row', alignItems: 'center', gap: 4, paddingHorizontal: 6, borderRadius: 9, backgroundColor: '#eaf2e6' },
  urgentStat: { backgroundColor: '#fff0df' },
  statIconCircle: { width: 24, height: 24, borderRadius: 14, alignItems: 'center', justifyContent: 'center', backgroundColor: '#dcebd7' },
  urgentIconCircle: { backgroundColor: '#ffe3c7' },
  statNumber: { color: INK, fontFamily: 'Georgia', fontSize: 18, lineHeight: 20, fontWeight: '700' },
  statLabel: { color: GREEN, fontSize: 9, lineHeight: 11, textAlign: 'center' },
  urgentText: { color: '#cf3810' },
  segment: { minHeight: 36, flexDirection: 'row', alignItems: 'stretch', borderRadius: 22, borderWidth: 1, borderColor: '#dddcd4', overflow: 'hidden', backgroundColor: '#fbfaf5' },
  segmentButton: { flex: 1, minHeight: 36, alignItems: 'center', justifyContent: 'center', paddingHorizontal: 4 },
  segmentDivider: { borderLeftWidth: 1, borderColor: '#e3e0d7' },
  segmentSelected: { borderRadius: 22, backgroundColor: GREEN, borderLeftWidth: 0 },
  segmentText: { color: MUTED, fontSize: 12, lineHeight: 16, textAlign: 'center' },
  segmentTextSelected: { color: PAPER, fontWeight: '600' },
  cards: { gap: 7 },
  alertCard: { minHeight: 82, borderRadius: 14, padding: 8, flexDirection: 'row', alignItems: 'center', gap: 8, overflow: 'hidden', backgroundColor: '#fffefa', borderWidth: 1, borderColor: '#eeece3' },
  rainCard: { minHeight: 96, backgroundColor: '#e0f0f5', borderColor: '#d8e9ed' },
  spotCard: { minHeight: 88 },
  resolvedCard: { minHeight: 70 },
  rainImage: { ...StyleSheet.absoluteFill, opacity: 0.46 },
  rainImageStyle: { borderRadius: 14 },
  spotImage: { width: 52, height: 54, flexShrink: 0, borderRadius: 9, overflow: 'hidden' },
  spotImageStyle: { borderRadius: 9 },
  cardIconWrap: { width: 44, height: 44, flexShrink: 0, borderRadius: 24, alignItems: 'center', justifyContent: 'center', backgroundColor: '#e9f2e5' },
  rainIconWrap: { width: 44, height: 44, backgroundColor: 'rgba(209,230,242,0.9)' },
  hiddenIconWrap: { display: 'none' },
  resolvedIconWrap: { backgroundColor: '#deedda', width: 46, height: 46 },
  cardMain: { flex: 1, minWidth: 0, justifyContent: 'center' },
  cardMainWithAction: { paddingRight: 82 },
  cardTitle: { color: INK, fontFamily: 'Georgia', fontSize: 12, lineHeight: 15, fontWeight: '700' },
  cardBody: { color: MUTED, fontSize: 10, lineHeight: 13, marginTop: 2 },
  badges: { flexDirection: 'row', flexWrap: 'wrap', gap: 4, marginTop: 6 },
  badge: { height: 21, flexDirection: 'row', alignItems: 'center', gap: 2, paddingHorizontal: 4, borderRadius: 8 },
  greenBadge: { backgroundColor: '#eaf2e6' },
  weatherBadge: { backgroundColor: '#e9f2fa' },
  warningBadge: { backgroundColor: '#fff0e1' },
  badgeText: { color: GREEN, fontSize: 8, lineHeight: 11, fontWeight: '500' },
  weatherBadgeText: { color: '#155eaa' },
  warningBadgeText: { color: '#d93916' },
  cardAction: { position: 'absolute', right: 9, top: '50%', marginTop: -19, minHeight: 38, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 1, paddingHorizontal: 6, borderRadius: 12, backgroundColor: GREEN },
  cardActionText: { color: PAPER, fontSize: 9, lineHeight: 12, fontWeight: '600' },
  cardTail: { alignItems: 'center', justifyContent: 'center', gap: 3, marginLeft: 2 },
  completedText: { color: MUTED, fontSize: 9, lineHeight: 12, textAlign: 'right' },
  emptyCards: { paddingHorizontal: 16, paddingVertical: 24, borderRadius: 16, borderWidth: 1, borderColor: '#eeece3', backgroundColor: '#fffefa' },
  emptyCardsText: { color: MUTED, textAlign: 'center', fontSize: 14 },
});
