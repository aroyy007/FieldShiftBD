import { useEffect, useMemo, useState } from 'react';
import {
  ActivityIndicator,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useLocalSearchParams } from 'expo-router';
import { Button, Card } from '../../../components/ui';
import { useAppContext } from '../../../context/AppProvider';
import {
  CropRecommendation,
  HarvestGuidance,
  RecommendationSet,
  Season,
  SeasonPlan,
  m2Request,
} from '../../../services/m2-advisor';
import { COLORS, SPACING, TYPOGRAPHY } from '../../../theme/theme';

const UUID_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

type BusyAction = 'recommend' | 'select' | 'plan' | 'activate' | 'harvest' | 'close' | 'import' | 'history' | null;

const formatDate = (value: string | null) => value ? new Date(`${value}T00:00:00`).toLocaleDateString('bn-BD') : 'তারিখ দেওয়া নেই';

export default function CropAdvisorScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const routeFarmlandId = Array.isArray(id) ? id[0] : id;
  const { farmlands } = useAppContext();
  const farm = farmlands.find(item => item.id === routeFarmlandId);
  const [farmlandId, setFarmlandId] = useState(UUID_PATTERN.test(routeFarmlandId ?? '') ? routeFarmlandId : '');
  const [district, setDistrict] = useState('');
  const [soilType, setSoilType] = useState('');
  const [landArea, setLandArea] = useState('');
  const [irrigation, setIrrigation] = useState<'unknown' | 'yes' | 'no'>('unknown');
  const [waterSource, setWaterSource] = useState('');
  const [plantingDate, setPlantingDate] = useState('');
  const [harvestDate, setHarvestDate] = useState('');
  const [budget, setBudget] = useState('');
  const [recommendations, setRecommendations] = useState<RecommendationSet | null>(null);
  const [savedRecommendations, setSavedRecommendations] = useState<CropRecommendation[]>([]);
  const [seasons, setSeasons] = useState<Season[]>([]);
  const [selectedSeason, setSelectedSeason] = useState<Season | null>(null);
  const [plan, setPlan] = useState<SeasonPlan | null>(null);
  const [harvest, setHarvest] = useState<HarvestGuidance | null>(null);
  const [yieldAmount, setYieldAmount] = useState('');
  const [yieldUnit, setYieldUnit] = useState('কেজি');
  const [outcomeNotes, setOutcomeNotes] = useState('');
  const [actualHarvestDate, setActualHarvestDate] = useState('');
  const [busy, setBusy] = useState<BusyAction>(null);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');

  const canUseBackend = UUID_PATTERN.test(farmlandId.trim());
  const canImportTasks = Boolean(
    plan?.initial_tasks.some(task => task.growth_stage_id && task.due_day_offset !== null),
  );
  const approvedReferenceCount = useMemo(() => new Set(
    (recommendations?.recommendations ?? []).flatMap(item => item.knowledge_refs.map(ref => ref.source_reference || ref.source_name)),
  ).size, [recommendations]);

  useEffect(() => {
    if (canUseBackend) void loadHistory();
    // Load history when an existing persisted farm ID becomes available.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [canUseBackend, farmlandId]);

  async function loadHistory() {
    if (!canUseBackend) return;
    setBusy('history');
    try {
      const [history, saved] = await Promise.all([
        m2Request<Season[]>(`/advisor/farmlands/${farmlandId.trim()}/seasons`),
        m2Request<CropRecommendation[]>(`/advisor/farmlands/${farmlandId.trim()}/recommendations`),
      ]);
      setSeasons(history);
      setSavedRecommendations(saved);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'মৌসুমের তালিকা আনা যায়নি।');
    } finally {
      setBusy(null);
    }
  }

  async function requestRecommendations() {
    setError('');
    setNotice('');
    if (!canUseBackend) {
      setError('M1 থেকে পাওয়া সংরক্ষিত Farmland ID দিন। Demo farm-এর ID backend-এ নেই।');
      return;
    }
    const parsedArea = Number(landArea);
    if (landArea.trim() && (!Number.isFinite(parsedArea) || parsedArea <= 0)) {
      setError('জমির পরিমাণ শূন্যের চেয়ে বেশি হতে হবে।');
      return;
    }

    setBusy('recommend');
    setRecommendations(null);
    setSelectedSeason(null);
    setPlan(null);
    setHarvest(null);
    try {
      const result = await m2Request<RecommendationSet>('/advisor/recommendations', {
        method: 'POST',
        body: JSON.stringify({
          farmland_id: farmlandId.trim(),
          location: { country_code: 'BD', district: district.trim() || null },
          land_area: landArea.trim() ? parsedArea : null,
          land_unit: landArea.trim() ? 'acre' : null,
          soil_type: soilType.trim() || null,
          irrigation_available: irrigation === 'unknown' ? null : irrigation === 'yes',
          water_source: waterSource.trim() || null,
        }),
      });
      setRecommendations(result);
      setSavedRecommendations(result.recommendations);
      await loadHistory();
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'পরামর্শ আনা যায়নি।');
    } finally {
      setBusy(null);
    }
  }

  async function dismissRecommendation(recommendation: CropRecommendation) {
    if (!recommendation.recommendation_id) return;
    setBusy('select');
    setError('');
    try {
      const dismissed = await m2Request<CropRecommendation>(
        `/advisor/recommendations/${recommendation.recommendation_id}/dismiss`,
        { method: 'POST' },
      );
      setSavedRecommendations(current => current.map(item =>
        item.recommendation_id === dismissed.recommendation_id ? dismissed : item,
      ));
      setRecommendations(current => current ? {
        ...current,
        recommendations: current.recommendations.map(item =>
          item.recommendation_id === dismissed.recommendation_id ? dismissed : item,
        ),
      } : current);
      setNotice('এই পরামর্শটি বাদ দেওয়া হয়েছে।');
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'পরামর্শটি বাদ দেওয়া যায়নি।');
    } finally {
      setBusy(null);
    }
  }

  async function selectCrop(recommendation: CropRecommendation) {
    if (!canUseBackend) return;
    setBusy('select');
    setError('');
    setNotice('');
    try {
      const created = await m2Request<Season>('/advisor/seasons', {
        method: 'POST',
        body: JSON.stringify({
          farmland_id: farmlandId.trim(),
          crop_id: recommendation.crop.crop_id,
          recommendation_id: recommendation.recommendation_id,
          planting_date: plantingDate || null,
          expected_harvest_date: harvestDate || null,
          budget_amount: budget.trim() ? Number(budget) : null,
          budget_currency: 'BDT',
        }),
      });
      setRecommendations(current => current ? {
        ...current,
        recommendations: current.recommendations.map(item =>
          item.recommendation_id === recommendation.recommendation_id
            ? { ...item, status: 'selected' }
            : item,
        ),
      } : current);
      setSavedRecommendations(current => current.map(item =>
        item.recommendation_id === recommendation.recommendation_id
          ? { ...item, status: 'selected' }
          : item,
      ));
      setSelectedSeason(created);
      setPlan(null);
      setHarvest(null);
      setActualHarvestDate('');
      setYieldAmount('');
      setOutcomeNotes('');
      setNotice(`${recommendation.crop.name ?? 'নির্বাচিত ফসল'} নিয়ে একটি planned season তৈরি হয়েছে।`);
      await loadHistory();
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'ফসল নির্বাচন করা যায়নি।');
    } finally {
      setBusy(null);
    }
  }

  async function createPlan() {
    if (!selectedSeason) return;
    setBusy('plan');
    setError('');
    setNotice('');
    try {
      const created = await m2Request<SeasonPlan>(`/advisor/seasons/${selectedSeason.season_id}/plan`, {
        method: 'POST',
        body: JSON.stringify({
          season_id: selectedSeason.season_id,
          title: `${farm?.name ?? 'ফসল'} মৌসুমের পরিকল্পনা`,
          status: 'draft',
        }),
      });
      setPlan(created);
      setNotice('যাচাই করা তথ্যের ভিত্তিতে season plan তৈরি হয়েছে।');
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Season plan তৈরি করা যায়নি।');
    } finally {
      setBusy(null);
    }
  }

  async function activateSeason() {
    if (!selectedSeason) return;
    setBusy('activate');
    setError('');
    setNotice('');
    try {
      const result = await m2Request<Season>(`/advisor/seasons/${selectedSeason.season_id}/activate`, { method: 'POST' });
      setSelectedSeason(result);
      setNotice('মৌসুমটি active হয়েছে। বর্তমান growth stage Module 3-ই পরিচালনা করবে।');
      await loadHistory();
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'মৌসুম active করা যায়নি।');
    } finally {
      setBusy(null);
    }
  }

  async function loadHarvestGuidance() {
    if (!selectedSeason) return;
    setBusy('harvest');
    setError('');
    try {
      const result = await m2Request<HarvestGuidance>(`/advisor/seasons/${selectedSeason.season_id}/harvest-guidance`);
      setHarvest(result);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Harvest guidance আনা যায়নি।');
    } finally {
      setBusy(null);
    }
  }

  async function importTasksToModule3() {
    if (!selectedSeason || !plan) return;
    const tasks = plan.initial_tasks
      .filter(task => task.growth_stage_id && task.due_day_offset !== null)
      .map((task, index) => ({
        reference: `${plan.season_plan_id}-${index + 1}`,
        growth_stage_id: task.growth_stage_id,
        title: task.title,
        description: task.description,
        days_after_planting: task.due_day_offset,
        priority: task.priority,
      }));
    if (!tasks.length) {
      setError('M3-তে পাঠানোর মতো stage ও due day-সহ কোনো task definition নেই।');
      return;
    }
    setBusy('import');
    setError('');
    setNotice('');
    try {
      const result = await m2Request<{ created_count: number; existing_count: number }>(
        `/farmlands/${farmlandId.trim()}/seasons/${selectedSeason.season_id}/tasks/from-plan`,
        { method: 'POST', body: JSON.stringify({ tasks }) },
      );
      setNotice(`Module 3-এ ${result.created_count}টি task যোগ হয়েছে${result.existing_count ? `; ${result.existing_count}টি আগে থেকেই ছিল` : ''}।`);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Task definition Module 3-এ পাঠানো যায়নি।');
    } finally {
      setBusy(null);
    }
  }

  async function closeSeason() {
    if (!selectedSeason) return;
    const parsedYield = yieldAmount.trim() ? Number(yieldAmount) : null;
    if (parsedYield !== null && (!Number.isFinite(parsedYield) || parsedYield < 0)) {
      setError('ফলনের পরিমাণ শূন্য বা তার বেশি হতে হবে।');
      return;
    }
    setBusy('close');
    setError('');
    setNotice('');
    try {
      const result = await m2Request<Season>(`/advisor/seasons/${selectedSeason.season_id}/close`, {
        method: 'POST',
        body: JSON.stringify({
          season_id: selectedSeason.season_id,
          actual_yield: parsedYield,
          yield_unit: parsedYield === null ? null : yieldUnit.trim() || 'কেজি',
          actual_harvest_date: actualHarvestDate || null,
          outcome_notes: outcomeNotes.trim() || null,
          status: 'completed',
        }),
      });
      setSelectedSeason(result);
      setNotice('মৌসুমের ফলাফল সংরক্ষণ হয়েছে।');
      await loadHistory();
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'মৌসুমের ফলাফল সংরক্ষণ হয়নি।');
    } finally {
      setBusy(null);
    }
  }

  async function openSeason(season: Season) {
    setSelectedSeason(season);
    setPlan(null);
    setHarvest(null);
    setActualHarvestDate(season.actual_harvest_date ?? '');
    setYieldAmount(season.actual_yield?.toString() ?? '');
    setYieldUnit(season.yield_unit ?? 'কেজি');
    setOutcomeNotes(season.outcome_notes ?? '');
    setError('');
    setNotice('');
    setBusy('history');
    try {
      const existingPlan = await m2Request<SeasonPlan>(`/advisor/seasons/${season.season_id}/plan`);
      setPlan(existingPlan);
    } catch (requestError) {
      if (!(requestError instanceof Error && requestError.message.includes('plan'))) {
        setError(requestError instanceof Error ? requestError.message : 'Season plan আনা যায়নি।');
      }
    } finally {
      setBusy(null);
    }
  }

  return (
    <SafeAreaView style={styles.safe} edges={['bottom', 'left', 'right']}>
      <ScrollView contentContainerStyle={styles.container} keyboardShouldPersistTaps="handled">
        <Text style={styles.eyebrow}>FIELDSHIFT · MODULE 2</Text>
        <Text style={styles.title}>ফসলের পরামর্শ</Text>
        <Text style={styles.subtitle}>আপনার জমির তথ্যের সঙ্গে মেলে—এমন অনুমোদিত কৃষি-তথ্য থাকলেই পরামর্শ দেখানো হবে।</Text>

        {farm && !UUID_PATTERN.test(routeFarmlandId ?? '') && (
          <Card style={styles.infoCard}>
            <Text style={styles.infoTitle}>Demo farm এখনও backend-এ যুক্ত নয়</Text>
            <Text style={styles.body}>M1 integration না থাকায় এই demo farm-এর ID দিয়ে season তৈরি করা যাবে না। Backend-এ আগে থেকে থাকা Farmland ID থাকলে নিচে দিন।</Text>
          </Card>
        )}

        <Card>
          <Text style={styles.sectionTitle}>জমির তথ্য</Text>
          <Text style={styles.label}>সংরক্ষিত Farmland ID</Text>
          <TextInput
            accessibilityLabel="সংরক্ষিত Farmland ID"
            autoCapitalize="none"
            autoCorrect={false}
            onChangeText={setFarmlandId}
            placeholder="M1 থেকে পাওয়া UUID"
            style={styles.input}
            value={farmlandId}
          />
          <Text style={styles.helper}>উদাহরণ: 123e4567-e89b-12d3-a456-426614174000</Text>

          <Text style={styles.label}>জেলা</Text>
          <TextInput accessibilityLabel="জেলা" onChangeText={setDistrict} placeholder="যেমন: কুমিল্লা" style={styles.input} value={district} />

          <Text style={styles.label}>মাটির ধরন</Text>
          <TextInput accessibilityLabel="মাটির ধরন" onChangeText={setSoilType} placeholder="আপনার জানা থাকলে লিখুন" style={styles.input} />

          <Text style={styles.label}>জমির পরিমাণ (একর)</Text>
          <TextInput accessibilityLabel="জমির পরিমাণ" keyboardType="decimal-pad" onChangeText={setLandArea} placeholder="ঐচ্ছিক" style={styles.input} value={landArea} />

          <Text style={styles.label}>সেচের ব্যবস্থা</Text>
          <View style={styles.choiceRow}>
            {([['unknown', 'জানা নেই'], ['yes', 'আছে'], ['no', 'নেই']] as const).map(([value, label]) => (
              <Pressable key={value} accessibilityRole="radio" accessibilityState={{ selected: irrigation === value }} onPress={() => setIrrigation(value)} style={[styles.choice, irrigation === value && styles.choiceSelected]}>
                <Text style={[styles.choiceText, irrigation === value && styles.choiceTextSelected]}>{label}</Text>
              </Pressable>
            ))}
          </View>

          <Text style={styles.label}>পানির উৎস</Text>
          <TextInput accessibilityLabel="পানির উৎস" onChangeText={setWaterSource} placeholder="যেমন: পুকুর, খাল, নলকূপ" style={styles.input} value={waterSource} />
          <Button disabled={!canUseBackend || busy !== null} title={busy === 'recommend' ? 'তথ্য যাচাই হচ্ছে…' : 'পরামর্শ দেখুন'} onPress={() => void requestRecommendations()} />
        </Card>

        <Card>
          <Text style={styles.sectionTitle}>মৌসুমের তথ্য</Text>
          <Text style={styles.body}>ফসল বাছার আগে বা পরে তারিখ ও budget দিতে পারেন। ফসলের উপযুক্ত সময় নিজে থেকে অনুমান করা হবে না।</Text>
          <Text style={styles.label}>রোপণের তারিখ (YYYY-MM-DD)</Text>
          <TextInput accessibilityLabel="রোপণের তারিখ" autoCapitalize="none" onChangeText={setPlantingDate} placeholder="2026-11-15" style={styles.input} value={plantingDate} />
          <Text style={styles.label}>সম্ভাব্য harvest date (YYYY-MM-DD)</Text>
          <TextInput accessibilityLabel="সম্ভাব্য harvest date" autoCapitalize="none" onChangeText={setHarvestDate} placeholder="ঐচ্ছিক" style={styles.input} value={harvestDate} />
          <Text style={styles.label}>Budget (BDT)</Text>
          <TextInput accessibilityLabel="Budget" keyboardType="decimal-pad" onChangeText={setBudget} placeholder="ঐচ্ছিক" style={styles.input} value={budget} />
        </Card>

        {busy === 'history' && <ActivityIndicator accessibilityLabel="মৌসুমের তালিকা আনা হচ্ছে" color={COLORS.primary} style={styles.loader} />}
        {error ? <Text accessibilityRole="alert" style={styles.error}>{error}</Text> : null}
        {notice ? <Text accessibilityLiveRegion="polite" style={styles.success}>{notice}</Text> : null}

        {recommendations && (
          <View>
            <Text style={styles.sectionTitle}>আপনার জমির জন্য ফলাফল</Text>
            <Text style={styles.body}>{recommendations.status === 'no_approved_knowledge'
              ? 'এই জমির তথ্যের সঙ্গে মেলে এমন অনুমোদিত কৃষি-তথ্য এখনো নেই। যাচাই না হওয়া তথ্য ধরে কোনো ফসল সাজেস্ট করছি না।'
              : recommendations.status === 'no_supported_fit'
                ? 'তথ্য আছে, তবে আপনার জমিতে উপযুক্ত বলে সমর্থন করার মতো মিল পাওয়া যায়নি।'
                : 'নিচের পরামর্শগুলোতে মিলের কারণ ও source দেখে সিদ্ধান্ত নিন।'}</Text>
            {approvedReferenceCount > 0 && <Text style={styles.helper}>ব্যবহৃত source: {approvedReferenceCount}টি</Text>}
            {recommendations.recommendations.map(item => (
              <RecommendationCard key={item.recommendation_id ?? item.crop.crop_id} recommendation={item} busy={busy === 'select'} onSelect={() => void selectCrop(item)} onDismiss={() => void dismissRecommendation(item)} />
            ))}
          </View>
        )}

        {!recommendations && savedRecommendations.length > 0 && (
          <View>
            <Text style={styles.sectionTitle}>সংরক্ষিত পরামর্শ</Text>
            {savedRecommendations.map(item => (
              <RecommendationCard key={item.recommendation_id ?? item.crop.crop_id} recommendation={item} busy={busy === 'select'} onSelect={() => void selectCrop(item)} onDismiss={() => void dismissRecommendation(item)} />
            ))}
          </View>
        )}

        {selectedSeason && (
          <View>
            <Card>
              <Text style={styles.sectionTitle}>নির্বাচিত মৌসুম</Text>
              <Text style={styles.body}>অবস্থা: {seasonStatus(selectedSeason.status)} · রোপণ: {formatDate(selectedSeason.planting_date)}</Text>
              {!plan && <Button disabled={busy !== null} title={busy === 'plan' ? 'তৈরি হচ্ছে…' : 'Season plan তৈরি করুন'} onPress={() => void createPlan()} />}
              {plan && (
                <>
                  <Text style={styles.planTitle}>{plan.title}</Text>
                  <Text style={styles.helper}>Source: {plan.knowledge_refs.map(ref => ref.source_name).join(', ') || 'তথ্য উল্লেখ নেই'}</Text>
                  {plan.growth_stages.map(stage => (
                    <View key={stage.growth_stage_id ?? stage.sequence} style={styles.stageRow}>
                      <Text style={styles.stageNumber}>{stage.sequence}</Text>
                      <View style={styles.stageCopy}>
                        <Text style={styles.stageName}>{stage.name}</Text>
                        <Text style={styles.helper}>{stage.start_day ?? '—'}–{stage.end_day ?? '—'} দিন</Text>
                      </View>
                    </View>
                  ))}
                  {plan.initial_tasks.length > 0 && (
                    <View style={styles.taskDefinitions}>
                      <Text style={styles.label}>Module 3-এর জন্য task definition</Text>
                      {plan.initial_tasks.map((task, index) => <Text key={`${task.title}-${index}`} style={styles.body}>• {task.title}{task.due_day_offset === null ? '' : ` · রোপণের ${task.due_day_offset} দিন পর`}</Text>)}
                      <Text style={styles.helper}>এগুলো এখনো operational task নয়। Import করলে Module 3-এর বর্তমান API-তেই পাঠানো হবে।</Text>
                      <Button disabled={!canImportTasks || busy !== null} title={busy === 'import' ? 'পাঠানো হচ্ছে…' : 'Module 3 task list-এ যোগ করুন'} variant="outline" onPress={() => void importTasksToModule3()} />
                    </View>
                  )}
                  {selectedSeason.status === 'planned' && <Button disabled={busy !== null} title={busy === 'activate' ? 'চালু হচ্ছে…' : 'মৌসুম active করুন'} onPress={() => void activateSeason()} />}
                </>
              )}
            </Card>

            <Card>
              <Text style={styles.sectionTitle}>Harvest ও ফলাফল</Text>
              <Button disabled={busy !== null} title={busy === 'harvest' ? 'তথ্য আনা হচ্ছে…' : 'Harvest guidance দেখুন'} variant="outline" onPress={() => void loadHarvestGuidance()} />
              {harvest && (
                <View style={styles.guidance}>
                  {harvest.guidance.map((item, index) => <Text key={`g-${index}`} style={styles.body}>• {item}</Text>)}
                  {harvest.maturity_indicators.map((item, index) => <Text key={`m-${index}`} style={styles.body}>• লক্ষণ: {item}</Text>)}
                  {harvest.uncertainty_notes.map((item, index) => <Text key={`u-${index}`} style={styles.helper}>মনে রাখুন: {item}</Text>)}
                  <Text style={styles.helper}>Source: {harvest.knowledge_refs.map(ref => ref.source_name).join(', ')}</Text>
                </View>
              )}
              <Text style={styles.label}>বাস্তবে harvest-এর তারিখ</Text>
              <TextInput accessibilityLabel="বাস্তবে harvest-এর তারিখ" onChangeText={setActualHarvestDate} placeholder="YYYY-MM-DD" style={styles.input} value={actualHarvestDate} />
              <View style={styles.inlineFields}>
                <View style={styles.yieldInput}>
                  <Text style={styles.label}>ফলন</Text>
                  <TextInput accessibilityLabel="ফলন" keyboardType="decimal-pad" onChangeText={setYieldAmount} placeholder="ঐচ্ছিক" style={styles.input} value={yieldAmount} />
                </View>
                <View style={styles.unitInput}>
                  <Text style={styles.label}>একক</Text>
                  <TextInput accessibilityLabel="ফলনের একক" onChangeText={setYieldUnit} style={styles.input} value={yieldUnit} />
                </View>
              </View>
              <Text style={styles.label}>মৌসুমের নোট</Text>
              <TextInput accessibilityLabel="মৌসুমের নোট" multiline onChangeText={setOutcomeNotes} placeholder="কেমন ফলন হয়েছে, লিখুন" style={[styles.input, styles.multiline]} value={outcomeNotes} />
              <Button disabled={busy !== null || selectedSeason.status === 'completed' || selectedSeason.status === 'cancelled'} title={busy === 'close' ? 'সংরক্ষণ হচ্ছে…' : 'মৌসুমের ফলাফল সংরক্ষণ করুন'} variant="outline" onPress={() => void closeSeason()} />
            </Card>
          </View>
        )}

        <View style={styles.historySection}>
          <View style={styles.historyHeading}>
            <Text style={styles.sectionTitle}>আগের মৌসুম</Text>
            <Pressable accessibilityRole="button" disabled={!canUseBackend || busy !== null} onPress={() => void loadHistory()}>
              <Text style={[styles.link, !canUseBackend && styles.disabledText]}>Refresh</Text>
            </Pressable>
          </View>
          {seasons.length === 0
            ? <Text style={styles.helper}>{canUseBackend ? 'এখনো কোনো মৌসুম সংরক্ষণ হয়নি।' : 'সংরক্ষিত Farmland ID দিলে মৌসুমের history দেখা যাবে।'}</Text>
            : seasons.map(season => (
              <Pressable key={season.season_id} accessibilityRole="button" onPress={() => void openSeason(season)}>
                <Card style={styles.historyCard}>
                  <Text style={styles.historyTitle}>{cropName(season.crop_id, savedRecommendations, recommendations?.recommendations ?? [])}</Text>
                  <Text style={styles.helper}>{seasonStatus(season.status)} · {formatDate(season.planting_date)} – {formatDate(season.actual_harvest_date ?? season.expected_harvest_date)}</Text>
                  {season.actual_yield !== null && <Text style={styles.body}>ফলন: {season.actual_yield} {season.yield_unit ?? ''}</Text>}
                </Card>
              </Pressable>
            ))}
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

function RecommendationCard({ recommendation, busy, onSelect, onDismiss }: { recommendation: CropRecommendation; busy: boolean; onSelect: () => void; onDismiss: () => void }) {
  const groups = [
    ['মিলের কারণ', recommendation.reasoning.positive_factors],
    ['সীমাবদ্ধতা', recommendation.reasoning.limiting_factors],
    ['ঝুঁকি ও সতর্কতা', recommendation.reasoning.risks_or_concerns],
  ] as const;
  return (
    <Card>
      <Text style={styles.cropName}>{recommendation.crop.name ?? 'ফসলের নাম পাওয়া যায়নি'}</Text>
      {recommendation.crop.scientific_name && <Text style={styles.helper}>{recommendation.crop.scientific_name}</Text>}
      {groups.map(([heading, factors]) => factors.length > 0 && (
        <View key={heading} style={styles.factorGroup}>
          <Text style={styles.label}>{heading}</Text>
          {factors.map((factor, index) => (
            <View key={`${factor.factor}-${index}`} style={styles.factorRow}>
              <Text style={styles.factorName}>{factorLabel(factor.factor)}</Text>
              <Text style={styles.body}>{factor.explanation}</Text>
            </View>
          ))}
        </View>
      ))}
      {recommendation.knowledge_refs.map((reference, index) => (
        <Text key={`${reference.source_name}-${index}`} style={styles.helper}>Source: {reference.source_name}{reference.source_reference ? ` · ${reference.source_reference}` : ''}</Text>
      ))}
      {recommendation.status === 'proposed' ? (
        <>
          <Button disabled={busy} title={busy ? 'সংরক্ষণ হচ্ছে…' : 'এই ফসলটি বেছে নিন'} onPress={onSelect} />
          <Button disabled={busy} title="এখন নয়" variant="outline" onPress={onDismiss} />
        </>
      ) : <Text style={styles.helper}>এই পরামর্শের অবস্থা: {recommendation.status === 'dismissed' ? 'বাদ দেওয়া হয়েছে' : 'নির্বাচিত'}</Text>}
    </Card>
  );
}

function seasonStatus(status: Season['status']) {
  const labels: Record<Season['status'], string> = {
    planned: 'পরিকল্পিত', active: 'চলমান', completed: 'সম্পন্ন', cancelled: 'বাতিল',
  };
  return labels[status];
}

function factorLabel(factor: string) {
  const labels: Record<string, string> = {
    soil: 'মাটি', soil_factor: 'মাটির ধরন', irrigation: 'সেচ', irrigation_factor: 'সেচের সুবিধা',
    planting_timing: 'রোপণের সময়', climate: 'আবহাওয়া', land_area: 'জমির পরিমাণ', budget: 'বাজেট',
  };
  return labels[factor] ?? factor;
}

function cropName(cropId: string, saved: CropRecommendation[], current: CropRecommendation[]) {
  const recommendation = [...current, ...saved].find(item => item.crop.crop_id === cropId);
  return recommendation?.crop.name ?? `ফসল · ${cropId.slice(0, 8)}`;
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: COLORS.background },
  container: { width: '100%', maxWidth: 760, alignSelf: 'center', padding: SPACING.md, paddingBottom: SPACING.xxl },
  eyebrow: { ...TYPOGRAPHY.caption, color: COLORS.primary, fontWeight: '700', letterSpacing: 1, marginBottom: SPACING.xs },
  title: { ...TYPOGRAPHY.h1, fontSize: 28, marginBottom: SPACING.xs },
  subtitle: { ...TYPOGRAPHY.body, color: COLORS.textSecondary, marginBottom: SPACING.md, lineHeight: 24 },
  sectionTitle: { ...TYPOGRAPHY.h3, marginBottom: SPACING.sm },
  body: { ...TYPOGRAPHY.body, color: COLORS.textSecondary, lineHeight: 23 },
  label: { ...TYPOGRAPHY.caption, fontWeight: '600', color: COLORS.text, marginTop: SPACING.sm, marginBottom: SPACING.xs },
  input: { minHeight: 46, width: '100%', borderWidth: 1, borderColor: COLORS.border, borderRadius: 8, backgroundColor: COLORS.surface, paddingHorizontal: 12, paddingVertical: 10, color: COLORS.text, fontSize: 16, marginBottom: SPACING.xs },
  helper: { ...TYPOGRAPHY.caption, color: COLORS.textSecondary, lineHeight: 19, marginBottom: SPACING.sm },
  choiceRow: { flexDirection: 'row', flexWrap: 'wrap', gap: SPACING.sm, marginBottom: SPACING.sm },
  choice: { minHeight: 42, minWidth: 84, paddingHorizontal: 12, justifyContent: 'center', alignItems: 'center', borderWidth: 1, borderColor: COLORS.border, borderRadius: 22, backgroundColor: COLORS.surface },
  choiceSelected: { borderColor: COLORS.primary, backgroundColor: '#e7f0e8' },
  choiceText: { ...TYPOGRAPHY.caption, color: COLORS.textSecondary },
  choiceTextSelected: { color: COLORS.primaryDark, fontWeight: '600' },
  infoCard: { backgroundColor: '#f0f5ee', borderLeftWidth: 3, borderLeftColor: COLORS.primary },
  infoTitle: { ...TYPOGRAPHY.body, fontWeight: '700', marginBottom: SPACING.xs },
  error: { ...TYPOGRAPHY.body, color: COLORS.error, padding: SPACING.md, backgroundColor: '#fff0ee', borderRadius: 8, marginBottom: SPACING.md },
  success: { ...TYPOGRAPHY.body, color: COLORS.primaryDark, padding: SPACING.md, backgroundColor: '#eaf5e9', borderRadius: 8, marginBottom: SPACING.md },
  loader: { marginVertical: SPACING.md },
  cropName: { ...TYPOGRAPHY.h2, fontSize: 21, marginBottom: SPACING.xs },
  factorGroup: { marginTop: SPACING.sm },
  factorRow: { borderLeftWidth: 2, borderLeftColor: COLORS.primaryLight, paddingLeft: SPACING.sm, marginBottom: SPACING.sm },
  factorName: { ...TYPOGRAPHY.caption, fontWeight: '700', color: COLORS.text, marginBottom: 2 },
  planTitle: { ...TYPOGRAPHY.body, fontWeight: '700', marginTop: SPACING.md, marginBottom: SPACING.xs },
  stageRow: { flexDirection: 'row', alignItems: 'center', borderBottomWidth: 1, borderBottomColor: COLORS.border, paddingVertical: SPACING.sm },
  stageNumber: { width: 30, height: 30, textAlign: 'center', textAlignVertical: 'center', borderRadius: 15, overflow: 'hidden', backgroundColor: '#e7f0e8', color: COLORS.primaryDark, fontWeight: '700', marginRight: SPACING.sm },
  stageCopy: { flex: 1, minWidth: 0 },
  stageName: { ...TYPOGRAPHY.body, fontWeight: '600' },
  taskDefinitions: { paddingTop: SPACING.md },
  guidance: { gap: SPACING.xs, marginVertical: SPACING.sm },
  inlineFields: { flexDirection: 'row', gap: SPACING.sm },
  yieldInput: { flex: 1 },
  unitInput: { flex: 1 },
  multiline: { minHeight: 80, textAlignVertical: 'top' },
  historySection: { marginTop: SPACING.md },
  historyHeading: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  link: { ...TYPOGRAPHY.caption, color: COLORS.primary, fontWeight: '700' },
  disabledText: { color: COLORS.textSecondary },
  historyCard: { marginBottom: SPACING.sm },
  historyTitle: { ...TYPOGRAPHY.body, fontWeight: '600', marginBottom: SPACING.xs },
});
