import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  ActivityIndicator,
  Pressable,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import { Href, useLocalSearchParams, useRouter } from 'expo-router';
import { Button, Card } from '../../../components/ui';
import CropAdvisorPresentation from '../../../components/CropAdvisorPresentation';
import OptionPickerModal from '../../../components/OptionPickerModal';
import type { CropAdvisorIconName } from '../../../components/crop-advisor-icons';
import { useAppContext } from '../../../context/AppProvider';
import {
  CropAssessment,
  CropRecommendation,
  HarvestGuidance,
  RecommendationSet,
  RegionalContext,
  Season,
  SeasonPlan,
  m2Request,
} from '../../../services/m2-advisor';
import {
  CropCatalogItem,
  ProfileVocabulary,
  landTypeLabel,
  loadCropCatalog,
  loadProfileVocabulary,
} from '../../../services/m1-reference';
import { COLORS, SPACING, TYPOGRAPHY } from '../../../theme/theme';

type BusyAction = 'recommend' | 'select' | 'plan' | 'activate' | 'harvest' | 'close' | 'import' | 'history' | null;
type PickerKind = 'crop' | 'variety' | null;

const DATE_PATTERN = /^\d{4}-\d{2}-\d{2}$/;
const FIELD_LABELS: Record<string, string> = {
  soil_type: 'soil type', land_type: 'land type', upazila: 'upazila', district: 'district',
  division: 'division', irrigation_available: 'irrigation', water_source: 'water source',
};
const SHARE_LABELS: [string, string][] = [
  ['very_suitable', 'Very suitable'],
  ['suitable', 'Suitable'],
  ['moderately_suitable', 'Moderately suitable'],
  ['marginally_suitable', 'Marginally suitable'],
  ['not_suitable', 'Not suitable'],
];

const formatDate = (value: string | null) => value
  ? new Date(`${value}T00:00:00`).toLocaleDateString('en-BD', { day: 'numeric', month: 'short', year: 'numeric' })
  : 'No date set';

const errorText = (error: unknown, fallback: string) => error instanceof Error ? error.message : fallback;

export default function CropAdvisorScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const farmlandId = Array.isArray(id) ? id[0] : id;
  const { farmlands, authLoading, dataLoading, refreshFarmland } = useAppContext();
  const router = useRouter();
  const farm = farmlands.find(item => item.id === farmlandId);

  const [catalog, setCatalog] = useState<CropCatalogItem[]>([]);
  const [vocabulary, setVocabulary] = useState<ProfileVocabulary | null>(null);
  const [result, setResult] = useState<RecommendationSet | null>(null);
  const [savedRecommendations, setSavedRecommendations] = useState<CropRecommendation[]>([]);
  const [seasons, setSeasons] = useState<Season[]>([]);
  const [loadState, setLoadState] = useState<'loading' | 'ready' | 'error'>('loading');
  const [loadError, setLoadError] = useState('');
  const [selectedSeason, setSelectedSeason] = useState<Season | null>(null);
  const [plan, setPlan] = useState<SeasonPlan | null>(null);
  const [planMessage, setPlanMessage] = useState('');
  const [harvest, setHarvest] = useState<HarvestGuidance | null>(null);
  const [harvestMessage, setHarvestMessage] = useState('');
  const [chosenCropId, setChosenCropId] = useState<string | null>(null);
  const [chosenRecommendationId, setChosenRecommendationId] = useState<string | null>(null);
  const [chosenVarietyId, setChosenVarietyId] = useState<string | null>(null);
  const [picker, setPicker] = useState<PickerKind>(null);
  const [plantingDate, setPlantingDate] = useState('');
  const [harvestDate, setHarvestDate] = useState('');
  const [budget, setBudget] = useState('');
  const [yieldAmount, setYieldAmount] = useState('');
  const [yieldUnit, setYieldUnit] = useState('kg');
  const [outcomeNotes, setOutcomeNotes] = useState('');
  const [actualHarvestDate, setActualHarvestDate] = useState('');
  const [busy, setBusy] = useState<BusyAction>(null);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [showFarmTools, setShowFarmTools] = useState(true);

  const cropById = useMemo(() => new Map(catalog.map(crop => [crop.crop_id, crop])), [catalog]);
  const cropName = (cropId: string) => cropById.get(cropId)?.name ?? 'Crop no longer in catalog';
  // The saved list contains every request; show the newest record per crop.
  const latestSaved = useMemo(() => {
    const seen = new Set<string>();
    return savedRecommendations.filter(item => {
      if (item.status === 'expired' || seen.has(item.crop.crop_id)) return false;
      seen.add(item.crop.crop_id);
      return true;
    });
  }, [savedRecommendations]);
  const visibleRecommendations = result ? result.recommendations : latestSaved;
  const featuredRecommendation = visibleRecommendations.find(item => item.status !== 'dismissed');
  const openSeason = seasons.find(season => season.status === 'planned' || season.status === 'active') ?? null;
  const chosenCrop = chosenCropId ? cropById.get(chosenCropId) : undefined;
  const chosenVariety = chosenCrop?.varieties.find(item => item.crop_variety_id === chosenVarietyId);

  const fetchAdvisorData = useCallback(() => Promise.all([
    loadCropCatalog(),
    loadProfileVocabulary(),
    m2Request<Season[]>(`/advisor/farmlands/${farmlandId}/seasons`),
    m2Request<CropRecommendation[]>(`/advisor/farmlands/${farmlandId}/recommendations`),
  ])
    .then(([cropCatalog, profileVocabulary, history, saved]) => {
      setCatalog(cropCatalog);
      setVocabulary(profileVocabulary);
      setSeasons(history);
      setSavedRecommendations(saved);
      setLoadState('ready');
    })
    .catch(requestError => {
      setLoadError(errorText(requestError, 'Could not load crop advisor data.'));
      setLoadState('error');
    }), [farmlandId]);

  useEffect(() => {
    if (farm) void fetchAdvisorData();
  }, [farm?.id, fetchAdvisorData]); // eslint-disable-line react-hooks/exhaustive-deps

  function loadAdvisorData() {
    setLoadState('loading');
    setLoadError('');
    void fetchAdvisorData();
  }

  async function refreshLists() {
    const [history, saved] = await Promise.all([
      m2Request<Season[]>(`/advisor/farmlands/${farmlandId}/seasons`),
      m2Request<CropRecommendation[]>(`/advisor/farmlands/${farmlandId}/recommendations`),
    ]);
    setSeasons(history);
    setSavedRecommendations(saved);
  }

  async function requestRecommendations() {
    setError('');
    setNotice('');
    setBusy('recommend');
    try {
      const response = await m2Request<RecommendationSet>(`/advisor/farmlands/${farmlandId}/recommendations`, { method: 'POST' });
      setResult(response);
      await refreshLists();
    } catch (requestError) {
      setError(errorText(requestError, 'Could not check crop matches.'));
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
        `/advisor/recommendations/${recommendation.recommendation_id}/dismiss`, { method: 'POST' },
      );
      const replace = (item: CropRecommendation) => item.recommendation_id === dismissed.recommendation_id ? dismissed : item;
      setSavedRecommendations(current => current.map(replace));
      setResult(current => current ? { ...current, recommendations: current.recommendations.map(replace) } : current);
      setNotice('Recommendation dismissed.');
    } catch (requestError) {
      setError(errorText(requestError, 'Could not dismiss the recommendation.'));
    } finally {
      setBusy(null);
    }
  }

  function chooseRecommendation(recommendation: CropRecommendation) {
    setChosenCropId(recommendation.crop.crop_id);
    setChosenRecommendationId(recommendation.recommendation_id);
    setChosenVarietyId(null);
    setError('');
    setNotice(`${recommendation.crop.name ?? 'Crop'} chosen. Add season details below, then create the season.`);
  }

  async function createSeason() {
    if (!chosenCrop) {
      setError('Choose a crop for the season first.');
      return;
    }
    for (const [label, value] of [['Planting date', plantingDate], ['Expected harvest date', harvestDate]] as const) {
      if (value.trim() && !DATE_PATTERN.test(value.trim())) {
        setError(`${label} must use the YYYY-MM-DD format.`);
        return;
      }
    }
    const parsedBudget = budget.trim() ? Number(budget) : null;
    if (parsedBudget !== null && (!Number.isFinite(parsedBudget) || parsedBudget < 0)) {
      setError('Budget must be zero or greater.');
      return;
    }
    setBusy('select');
    setError('');
    setNotice('');
    try {
      const created = await m2Request<Season>('/advisor/seasons', {
        method: 'POST',
        body: JSON.stringify({
          farmland_id: farmlandId,
          crop_id: chosenCrop.crop_id,
          crop_variety_id: chosenVariety?.crop_variety_id ?? null,
          variety_name: chosenVariety?.name ?? null,
          recommendation_id: chosenRecommendationId,
          planting_date: plantingDate.trim() || null,
          expected_harvest_date: harvestDate.trim() || null,
          budget_amount: parsedBudget,
          budget_currency: 'BDT',
        }),
      });
      if (chosenRecommendationId) {
        const markSelected = (item: CropRecommendation) =>
          item.recommendation_id === chosenRecommendationId ? { ...item, status: 'selected' } : item;
        setResult(current => current ? { ...current, recommendations: current.recommendations.map(markSelected) } : current);
      }
      setSelectedSeason(created);
      setPlan(null);
      setPlanMessage('');
      setHarvest(null);
      setHarvestMessage('');
      setChosenCropId(null);
      setChosenRecommendationId(null);
      setNotice(`A planned ${chosenCrop.name} season was created.`);
      await refreshLists();
    } catch (requestError) {
      setError(errorText(requestError, 'Could not create the season.'));
    } finally {
      setBusy(null);
    }
  }

  async function createPlan() {
    if (!selectedSeason) return;
    setBusy('plan');
    setError('');
    setPlanMessage('');
    try {
      const created = await m2Request<SeasonPlan>(`/advisor/seasons/${selectedSeason.season_id}/plan`, {
        method: 'POST',
        body: JSON.stringify({
          season_id: selectedSeason.season_id,
          title: `${farm?.name ?? 'Farm'} · ${cropName(selectedSeason.crop_id)} season plan`,
          status: 'draft',
        }),
      });
      setPlan(created);
      setNotice('Season plan created from approved evidence.');
    } catch (requestError) {
      setPlanMessage(errorText(requestError, 'Could not create the season plan.'));
    } finally {
      setBusy(null);
    }
  }

  async function activateSeason() {
    if (!selectedSeason) return;
    setBusy('activate');
    setError('');
    try {
      const updated = await m2Request<Season>(`/advisor/seasons/${selectedSeason.season_id}/activate`, { method: 'POST' });
      setSelectedSeason(updated);
      setNotice('Season activated. Module 3 now tracks its current growth stage and tasks.');
      await refreshLists();
      await refreshFarmland(farmlandId).catch(() => undefined);
    } catch (requestError) {
      setError(errorText(requestError, 'Could not activate the season.'));
    } finally {
      setBusy(null);
    }
  }

  async function loadHarvestGuidance() {
    if (!selectedSeason) return;
    setBusy('harvest');
    setHarvestMessage('');
    try {
      setHarvest(await m2Request<HarvestGuidance>(`/advisor/seasons/${selectedSeason.season_id}/harvest-guidance`));
    } catch (requestError) {
      setHarvest(null);
      setHarvestMessage(errorText(requestError, 'Could not load harvest guidance.'));
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
      setError('There are no task definitions with a growth stage and due day to send to Module 3.');
      return;
    }
    setBusy('import');
    setError('');
    try {
      const imported = await m2Request<{ created_count: number; existing_count: number }>(
        `/farmlands/${farmlandId}/seasons/${selectedSeason.season_id}/tasks/from-plan`,
        { method: 'POST', body: JSON.stringify({ tasks }) },
      );
      setNotice(`${imported.created_count} task${imported.created_count === 1 ? '' : 's'} added to Module 3${imported.existing_count ? `; ${imported.existing_count} already existed` : ''}.`);
    } catch (requestError) {
      setError(errorText(requestError, 'Could not send task definitions to Module 3.'));
    } finally {
      setBusy(null);
    }
  }

  async function closeSeason() {
    if (!selectedSeason) return;
    const parsedYield = yieldAmount.trim() ? Number(yieldAmount) : null;
    if (parsedYield !== null && (!Number.isFinite(parsedYield) || parsedYield < 0)) {
      setError('Yield must be zero or greater.');
      return;
    }
    if (actualHarvestDate.trim() && !DATE_PATTERN.test(actualHarvestDate.trim())) {
      setError('Actual harvest date must use the YYYY-MM-DD format.');
      return;
    }
    setBusy('close');
    setError('');
    try {
      const closed = await m2Request<Season>(`/advisor/seasons/${selectedSeason.season_id}/close`, {
        method: 'POST',
        body: JSON.stringify({
          season_id: selectedSeason.season_id,
          actual_yield: parsedYield,
          yield_unit: parsedYield === null ? null : yieldUnit.trim() || 'kg',
          actual_harvest_date: actualHarvestDate.trim() || null,
          outcome_notes: outcomeNotes.trim() || null,
          status: 'completed',
        }),
      });
      setSelectedSeason(current => current ? { ...current, ...closed } : current);
      setNotice('Season outcome saved.');
      await refreshLists();
    } catch (requestError) {
      setError(errorText(requestError, 'Could not save the season outcome.'));
    } finally {
      setBusy(null);
    }
  }

  async function openExistingSeason(season: Season) {
    setSelectedSeason(season);
    setPlan(null);
    setPlanMessage('');
    setHarvest(null);
    setHarvestMessage('');
    setActualHarvestDate(season.actual_harvest_date ?? '');
    setYieldAmount(season.actual_yield?.toString() ?? '');
    setYieldUnit(season.yield_unit ?? 'kg');
    setOutcomeNotes(season.outcome_notes ?? '');
    setError('');
    setBusy('history');
    try {
      setPlan(await m2Request<SeasonPlan>(`/advisor/seasons/${season.season_id}/plan`));
    } catch (requestError) {
      const message = errorText(requestError, '');
      setPlanMessage(message.includes('No plan is saved') ? 'No plan has been created for this season yet.' : message);
    } finally {
      setBusy(null);
    }
  }

  if (!farm) {
    return (
      <View style={styles.centered}>
        {authLoading || dataLoading
          ? <ActivityIndicator accessibilityLabel="Loading farmland" color={COLORS.primary} />
          : (
            <Card style={styles.stateCard}>
              <Text style={styles.sectionTitle}>Farmland not found</Text>
              <Text style={styles.body}>This farmland is not in your saved farms. Open Crop Advisor from one of your farmlands.</Text>
              <Button accessibilityRole="button" title="Back to farmlands" onPress={() => router.replace('/farmlands' as Href)} />
            </Card>
          )}
      </View>
    );
  }

  const profileRows: [string, string][] = [
    ['Location', farm.location ?? 'Not set'],
    ['Soil type', farm.soilType ?? 'Not set'],
    ['Land type', landTypeLabel(vocabulary, farm.landType)],
    ['Irrigation', farm.irrigationAvailable == null ? 'Not set' : farm.irrigationAvailable ? 'Available' : 'Not available'],
    ['Water source', farm.waterSource ?? 'Not set'],
  ];
  const missingFields = result?.missing_profile_fields ?? [];
  const recommendationReasons = featuredRecommendation
    ? featuredRecommendation.reasoning.positive_factors.slice(0, 5).map(factor => ({
      icon: factorIcon(factor.factor), title: factorLabel(factor.factor), detail: factor.explanation,
    }))
    : null;
  const recommendationWatchOuts = featuredRecommendation
    ? [...featuredRecommendation.reasoning.risks_or_concerns, ...featuredRecommendation.reasoning.limiting_factors]
      .slice(0, 2)
      .map(factor => ({
        icon: /disease|pest/i.test(factor.factor) ? 'bug' as const : 'drop' as const,
        title: factorLabel(factor.factor), detail: factor.explanation,
      }))
    : null;
  const seasonStages = plan?.growth_stages.length
    ? plan.growth_stages.map(stage => ({
      name: stage.name,
      timing: stage.start_day == null && stage.end_day == null ? `Stage ${stage.sequence}` : `Day ${stage.start_day ?? 0}–${stage.end_day ?? '—'}`,
    }))
    : farm.seasonPlan.map(stage => ({ name: stage.name, timing: stage.dateRange }));
  const activeCropName = farm.activeSeasonId ? farm.crop : null;

  return (
    <>
      <CropAdvisorPresentation
        cropName={featuredRecommendation?.crop.name || activeCropName || 'No crop match yet'}
        cropEyebrow={featuredRecommendation
          ? featuredRecommendation.status === 'selected' ? 'Selected crop' : 'Evidence-backed crop match'
          : activeCropName ? 'Current active crop' : 'Farm profile'}
        cropDescription={featuredRecommendation?.reasoning.positive_factors[0]?.explanation
          || result?.message
          || (activeCropName
            ? 'Current crop and growth stage come from your saved season.'
            : 'Check crop matches to see crops supported by approved agricultural evidence.')}
        location={farm.location || 'Farm location not set'}
        landArea={String(Number(farm.acreage.toFixed(2)))}
        reasons={recommendationReasons}
        watchOuts={recommendationWatchOuts}
        seasonStages={seasonStages}
        hasRecommendation={Boolean(featuredRecommendation)}
        toolsOpen={showFarmTools}
        onBack={() => router.replace(`/farmlands/${farm.id}` as Href)}
        onStartPlan={() => {
          setShowFarmTools(true);
          if (featuredRecommendation && featuredRecommendation.status === 'proposed') chooseRecommendation(featuredRecommendation);
          else void requestRecommendations();
        }}
        onOtherCrops={() => { setShowFarmTools(true); setPicker('crop'); }}
        onTabPress={tab => {
          const routes = {
            Home: '/farmlands', Tasks: `/farmlands/${farm.id}/tasks`, Chat: `/farmlands/${farm.id}/chat`,
            Scan: `/farmlands/${farm.id}/crop-health`, Profile: '/farmlands/profile-setup',
          };
          router.push(routes[tab] as Href);
        }}
        toolsContent={
          <View style={styles.toolsContent}>
            {loadState === 'loading' && (
              <View style={styles.loaderRow}>
                <ActivityIndicator accessibilityLabel="Loading crop advisor" color={COLORS.primary} />
                <Text style={styles.helper}>Loading saved recommendations and seasons…</Text>
              </View>
            )}
            {loadState === 'error' && (
              <Card style={styles.errorCard}>
                <Text accessibilityRole="alert" style={styles.errorText}>{loadError}</Text>
                <Button accessibilityRole="button" title="Try again" variant="outline" onPress={loadAdvisorData} />
              </Card>
            )}

            <Card>
              <Text style={styles.sectionTitle}>Saved farm profile</Text>
              <Text style={styles.helper}>Crop matches use only these saved details. Edit them in your farm profile.</Text>
              {profileRows.map(([label, value]) => (
                <View key={label} style={styles.profileRow}>
                  <Text style={styles.profileLabel}>{label}</Text>
                  <Text style={[styles.profileValue, value === 'Not set' && styles.missingValue]}>{value}</Text>
                </View>
              ))}
              <Button accessibilityRole="button" title="Edit farm profile" variant="outline" onPress={() => router.push('/farmlands/profile-setup' as Href)} />
              <Button
                accessibilityRole="button"
                disabled={busy !== null || loadState !== 'ready'}
                title={busy === 'recommend' ? 'Checking evidence…' : 'Check crop matches'}
                onPress={() => void requestRecommendations()}
              />
            </Card>

            {error ? <Text accessibilityRole="alert" style={styles.error}>{error}</Text> : null}
            {notice ? <Text accessibilityLiveRegion="polite" style={styles.success}>{notice}</Text> : null}

            {result && (
              <View>
                <Text style={styles.sectionTitle}>Results for your farm</Text>
                <Card style={result.status === 'available' ? styles.infoCard : styles.warningCard}>
                  <Text style={styles.infoTitle}>{statusTitle(result.status)}</Text>
                  <Text style={styles.body}>{statusBody(result)}</Text>
                  {missingFields.length > 0 && (
                    <Button accessibilityRole="button" title="Complete farm profile" variant="outline" onPress={() => router.push('/farmlands/profile-setup' as Href)} />
                  )}
                </Card>
              </View>
            )}

            {visibleRecommendations.length > 0 && (
              <View>
                {!result && <Text style={styles.sectionTitle}>Saved recommendations</Text>}
                {visibleRecommendations.map(item => (
                  <RecommendationCard
                    key={item.recommendation_id ?? item.crop.crop_id}
                    recommendation={item}
                    busy={busy === 'select'}
                    canSelect={!openSeason}
                    onSelect={() => chooseRecommendation(item)}
                    onDismiss={() => void dismissRecommendation(item)}
                  />
                ))}
              </View>
            )}
            {loadState === 'ready' && !result && visibleRecommendations.length === 0 && (
              <Text style={styles.helper}>No crop matches have been checked for this farm yet.</Text>
            )}

            {result?.crop_assessments && result.crop_assessments.some(item => item.status !== 'supported_fit') && (
              <Card>
                <Text style={styles.sectionTitle}>Other crops checked</Text>
                {result.crop_assessments.filter(item => item.status !== 'supported_fit').map(item => (
                  <AssessmentRow key={item.crop.crop_id} assessment={item} />
                ))}
              </Card>
            )}

            {result?.regional_context && result.regional_context.length > 0 && (
              <Card>
                <Text style={styles.sectionTitle}>Area-level context (not your field)</Text>
                <Text style={styles.helper}>BARC crop-zoning shares for your upazila. They describe the whole area BARC mapped, not your farm, and they are never used to recommend a crop.</Text>
                {result.regional_context.map(item => <RegionalContextBlock key={`${item.crop.crop_id}-${item.scope}`} context={item} />)}
              </Card>
            )}

            <Card>
              <Text style={styles.sectionTitle}>Start a season</Text>
              {openSeason ? (
                <Text style={styles.body}>
                  This farm already has a {openSeason.status} {cropName(openSeason.crop_id)} season. Complete it before starting another.
                </Text>
              ) : (
                <>
                  <Text style={styles.helper}>Choose a recommended crop above, or plan any catalog crop. Choosing a crop yourself is not a recommendation.</Text>
                  <Pressable accessibilityRole="button" onPress={() => setPicker('crop')} style={styles.pickerField}>
                    <Text style={styles.label}>Crop</Text>
                    <Text style={styles.pickerText}>{chosenCrop ? `${chosenCrop.name}${chosenRecommendationId ? ' (recommended)' : ''}` : 'Choose a crop'}</Text>
                  </Pressable>
                  <Pressable accessibilityRole="button" disabled={!chosenCrop || chosenCrop.varieties.length === 0} onPress={() => setPicker('variety')} style={styles.pickerField}>
                    <Text style={styles.label}>Variety (optional)</Text>
                    <Text style={styles.pickerText}>
                      {chosenVariety?.name ?? (chosenCrop ? (chosenCrop.varieties.length ? 'Choose a variety' : 'No varieties listed') : 'Choose a crop first')}
                    </Text>
                  </Pressable>
                  <Text style={styles.label}>Planting date (YYYY-MM-DD)</Text>
                  <TextInput accessibilityLabel="Planting date" autoCapitalize="none" onChangeText={setPlantingDate} placeholder="Optional" style={styles.input} value={plantingDate} />
                  <Text style={styles.label}>Expected harvest date (YYYY-MM-DD)</Text>
                  <TextInput accessibilityLabel="Expected harvest date" autoCapitalize="none" onChangeText={setHarvestDate} placeholder="Optional" style={styles.input} value={harvestDate} />
                  <Text style={styles.label}>Budget (BDT)</Text>
                  <TextInput accessibilityLabel="Budget" keyboardType="decimal-pad" onChangeText={setBudget} placeholder="Optional" style={styles.input} value={budget} />
                  <Button accessibilityRole="button" disabled={busy !== null || !chosenCrop} title={busy === 'select' ? 'Creating season…' : 'Create planned season'} onPress={() => void createSeason()} />
                </>
              )}
            </Card>

            {selectedSeason && (
              <View>
                <Card>
                  <Text style={styles.sectionTitle}>{cropName(selectedSeason.crop_id)} season</Text>
                  <Text style={styles.body}>
                    {seasonStatus(selectedSeason.status)} · Planted: {formatDate(selectedSeason.planting_date)}
                    {selectedSeason.variety_name ? ` · ${selectedSeason.variety_name}` : ''}
                  </Text>
                  {!plan && selectedSeason.status === 'planned' && (
                    <Button accessibilityRole="button" disabled={busy !== null} title={busy === 'plan' ? 'Checking plan evidence…' : 'Create season plan'} onPress={() => void createPlan()} />
                  )}
                  {planMessage ? <Text style={styles.warningText}>{planMessage}</Text> : null}
                  {plan && (
                    <>
                      <Text style={styles.planTitle}>{plan.title}</Text>
                      <Text style={styles.helper}>Sources: {plan.knowledge_refs.map(ref => ref.source_name).join(', ') || 'No sources listed'}</Text>
                      {plan.growth_stages.map(stage => (
                        <View key={stage.growth_stage_id ?? stage.sequence} style={styles.stageRow}>
                          <Text style={styles.stageNumber}>{stage.sequence}</Text>
                          <View style={styles.stageCopy}>
                            <Text style={styles.stageName}>{stage.name}</Text>
                            <Text style={styles.helper}>{stage.start_day ?? '—'}–{stage.end_day ?? '—'} days</Text>
                          </View>
                        </View>
                      ))}
                      {plan.initial_tasks.length > 0 && (
                        <View style={styles.taskDefinitions}>
                          <Text style={styles.label}>Task definitions for Module 3</Text>
                          {plan.initial_tasks.map((task, index) => <Text key={`${task.title}-${index}`} style={styles.body}>• {task.title}{task.due_day_offset === null ? '' : ` · ${task.due_day_offset} days after planting`}</Text>)}
                          <Button accessibilityRole="button" disabled={busy !== null} title={busy === 'import' ? 'Sending…' : 'Add to Module 3 task list'} variant="outline" onPress={() => void importTasksToModule3()} />
                        </View>
                      )}
                      {selectedSeason.status === 'planned' && <Button accessibilityRole="button" disabled={busy !== null} title={busy === 'activate' ? 'Activating…' : 'Activate season'} onPress={() => void activateSeason()} />}
                    </>
                  )}
                </Card>

                <Card>
                  <Text style={styles.sectionTitle}>Harvest guidance and outcome</Text>
                  <Button accessibilityRole="button" disabled={busy !== null} title={busy === 'harvest' ? 'Loading guidance…' : 'View harvest guidance'} variant="outline" onPress={() => void loadHarvestGuidance()} />
                  {harvestMessage ? <Text style={styles.warningText}>{harvestMessage}</Text> : null}
                  {harvest && <HarvestBlock guidance={harvest} />}
                  <Text style={styles.label}>Actual harvest date (YYYY-MM-DD)</Text>
                  <TextInput accessibilityLabel="Actual harvest date" onChangeText={setActualHarvestDate} placeholder="YYYY-MM-DD" style={styles.input} value={actualHarvestDate} />
                  <View style={styles.inlineFields}>
                    <View style={styles.flexOne}>
                      <Text style={styles.label}>Yield</Text>
                      <TextInput accessibilityLabel="Yield" keyboardType="decimal-pad" onChangeText={setYieldAmount} placeholder="Optional" style={styles.input} value={yieldAmount} />
                    </View>
                    <View style={styles.flexOne}>
                      <Text style={styles.label}>Unit</Text>
                      <TextInput accessibilityLabel="Yield unit" onChangeText={setYieldUnit} style={styles.input} value={yieldUnit} />
                    </View>
                  </View>
                  <Text style={styles.label}>Season notes</Text>
                  <TextInput accessibilityLabel="Season notes" multiline onChangeText={setOutcomeNotes} placeholder="Describe the outcome" style={[styles.input, styles.multiline]} value={outcomeNotes} />
                  {selectedSeason.status !== 'active'
                    ? <Text style={styles.helper}>Only an active season can be closed with a harvest outcome.</Text>
                    : <Button accessibilityRole="button" disabled={busy !== null} title={busy === 'close' ? 'Saving…' : 'Save season outcome'} variant="outline" onPress={() => void closeSeason()} />}
                </Card>
              </View>
            )}

            <View style={styles.historySection}>
              <View style={styles.historyHeading}>
                <Text style={styles.sectionTitle}>Seasons</Text>
                <Pressable accessibilityRole="button" disabled={busy !== null} onPress={loadAdvisorData}>
                  <Text style={styles.link}>Refresh</Text>
                </Pressable>
              </View>
              {loadState === 'ready' && seasons.length === 0
                ? <Text style={styles.helper}>No seasons have been saved for this farm yet.</Text>
                : seasons.map(season => (
                  <Pressable key={season.season_id} accessibilityRole="button" onPress={() => void openExistingSeason(season)}>
                    <Card style={styles.historyCard}>
                      <Text style={styles.historyTitle}>{cropName(season.crop_id)}{season.variety_name ? ` · ${season.variety_name}` : ''}</Text>
                      <Text style={styles.helper}>{seasonStatus(season.status)} · {formatDate(season.planting_date)} – {formatDate(season.actual_harvest_date ?? season.expected_harvest_date)}</Text>
                      {season.actual_yield !== null && <Text style={styles.body}>Yield: {season.actual_yield} {season.yield_unit ?? ''}</Text>}
                    </Card>
                  </Pressable>
                ))}
            </View>
          </View>
        }
      />
      <OptionPickerModal
        visible={picker === 'crop'}
        title="Crop"
        options={catalog.map(crop => ({ value: crop.crop_id, label: crop.name, detail: crop.name_bn ?? undefined }))}
        selected={chosenCropId}
        onSelect={value => {
          setPicker(null);
          if (value === chosenCropId) return;
          const recommended = visibleRecommendations.find(item => item.crop.crop_id === value && item.status === 'proposed');
          setChosenCropId(value);
          setChosenRecommendationId(recommended?.recommendation_id ?? null);
          setChosenVarietyId(null);
        }}
        onClose={() => setPicker(null)}
      />
      <OptionPickerModal
        visible={picker === 'variety'}
        title={`${chosenCrop?.name ?? 'Crop'} variety`}
        options={(chosenCrop?.varieties ?? []).map(variety => ({ value: variety.crop_variety_id, label: variety.name }))}
        selected={chosenVarietyId}
        allowClear
        onSelect={value => { setChosenVarietyId(value); setPicker(null); }}
        onClose={() => setPicker(null)}
      />
    </>
  );
}

function statusTitle(status: RecommendationSet['status']) {
  return {
    available: 'Crops supported by evidence',
    profile_incomplete: 'More farm details needed',
    no_supported_fit: 'No crop is supported for this profile',
    no_approved_knowledge: 'No approved evidence for this farm',
  }[status];
}

function statusBody(result: RecommendationSet) {
  const missing = (result.missing_profile_fields ?? []).map(field => FIELD_LABELS[field] ?? field.replace(/_/g, ' '));
  switch (result.status) {
    case 'available':
      return 'These crops match published conditions in approved sources. Review the reasons and sources before deciding.';
    case 'profile_incomplete':
      return `Add your ${missing.join(' and ')} so published crop conditions can be checked. No crop is suggested from incomplete information.`;
    case 'no_supported_fit':
      return 'Approved evidence exists, but none of it supports a crop for your saved land and soil details. No crop is suggested without evidence.';
    default:
      return 'There is no approved, current agricultural evidence that applies to this farm yet. No crop is suggested from unverified information.';
  }
}

function AssessmentRow({ assessment }: { assessment: CropAssessment }) {
  return (
    <View style={styles.assessmentRow}>
      <Text style={styles.factorName}>{assessment.crop.name ?? 'Crop'}</Text>
      <Text style={styles.body}>{assessment.message}</Text>
    </View>
  );
}

function RegionalContextBlock({ context }: { context: RegionalContext }) {
  return (
    <View style={styles.regionalBlock}>
      <Text style={styles.factorName}>{context.crop.name} · {context.scope}</Text>
      {context.entries.map((entry, index) => (
        <View key={`${entry.season}-${entry.situation}-${index}`} style={styles.regionalEntry}>
          <Text style={styles.helper}>
            {[entry.source_crop_name !== context.crop.name ? entry.source_crop_name : null, entry.season, entry.situation].filter(Boolean).join(' · ')}
          </Text>
          {SHARE_LABELS.map(([key, label]) => {
            const share = entry.class_shares_percent[key];
            if (share == null) return null;
            return (
              <View key={key} style={styles.shareRow}>
                <Text style={styles.shareLabel}>{label}</Text>
                <View style={styles.shareTrack}><View style={[styles.shareFill, { width: `${Math.min(100, share)}%` }]} /></View>
                <Text style={styles.shareValue}>{share.toFixed(1)}%</Text>
              </View>
            );
          })}
        </View>
      ))}
      <Text style={styles.helper}>{context.explanation}</Text>
      {context.knowledge_refs.map((ref, index) => (
        <Text key={`${ref.source_name}-${index}`} style={styles.sourceText}>Source: {ref.source_name}{ref.effective_to ? ` · valid until ${formatDate(ref.effective_to)}` : ''}</Text>
      ))}
    </View>
  );
}

function HarvestBlock({ guidance }: { guidance: HarvestGuidance }) {
  return (
    <View style={styles.guidance}>
      {guidance.recommended_window_start && (
        <Text style={styles.infoTitle}>
          Estimated harvest window: {formatDate(guidance.recommended_window_start)} – {formatDate(guidance.recommended_window_end)}
        </Text>
      )}
      {guidance.maturity_indicators.map((item, index) => <Text key={`m-${index}`} style={styles.body}>• Maturity sign: {item}</Text>)}
      {guidance.guidance.map((item, index) => <Text key={`g-${index}`} style={styles.body}>• {item}</Text>)}
      {guidance.uncertainty_notes.map((item, index) => <Text key={`u-${index}`} style={styles.helper}>Note: {item}</Text>)}
      {guidance.knowledge_refs.map((ref, index) => (
        <Text key={`r-${index}`} style={styles.sourceText}>
          Source: {ref.source_name}{ref.acceptance_method?.startsWith('automated_source_policy:') ? ' · accepted by automated source checks' : ''}
        </Text>
      ))}
    </View>
  );
}

function RecommendationCard({ recommendation, busy, canSelect, onSelect, onDismiss }: {
  recommendation: CropRecommendation; busy: boolean; canSelect: boolean; onSelect: () => void; onDismiss: () => void;
}) {
  const groups = [
    ['Why it fits', recommendation.reasoning.positive_factors],
    ['Limitations', recommendation.reasoning.limiting_factors],
    ['Risks and cautions', recommendation.reasoning.risks_or_concerns],
  ] as const;
  return (
    <Card>
      <Text style={styles.cropName}>{recommendation.crop.name ?? 'Crop name unavailable'}</Text>
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
        <Text key={`${reference.source_name}-${index}`} style={styles.sourceText}>
          Source: {reference.source_name}
          {reference.acceptance_method?.startsWith('automated_source_policy:') ? ' · accepted by automated source checks' : ''}
          {reference.effective_to ? ` · valid until ${formatDate(reference.effective_to)}` : ''}
          {reference.source_reference ? ` · ${reference.source_reference}` : ''}
        </Text>
      ))}
      {recommendation.status === 'proposed' ? (
        <>
          <Button accessibilityRole="button" disabled={busy || !canSelect} title="Choose this crop" onPress={onSelect} />
          <Button accessibilityRole="button" disabled={busy} title="Not now" variant="outline" onPress={onDismiss} />
        </>
      ) : <Text style={styles.helper}>Recommendation status: {recommendation.status === 'dismissed' ? 'Dismissed' : recommendation.status === 'selected' ? 'Selected' : 'Expired'}</Text>}
    </Card>
  );
}

function seasonStatus(status: Season['status']) {
  return { planned: 'Planned', active: 'Active', completed: 'Completed', cancelled: 'Cancelled' }[status];
}

function factorLabel(factor: string) {
  const labels: Record<string, string> = {
    land_and_soil: 'Land and soil', soil: 'Soil', soil_factor: 'Soil type', irrigation: 'Irrigation',
    irrigation_factor: 'Irrigation access', planting_timing: 'Planting time', climate: 'Climate',
    land_area: 'Land area', budget: 'Budget',
  };
  return labels[factor] ?? factor.replace(/_/g, ' ');
}

function factorIcon(factor: string): CropAdvisorIconName {
  const normalized = factor.toLowerCase();
  if (normalized.includes('soil')) return 'sprout';
  if (normalized.includes('irrigation') || normalized.includes('water')) return 'drop';
  if (normalized.includes('timing') || normalized.includes('plant')) return 'calendar';
  if (normalized.includes('land') || normalized.includes('area')) return 'field';
  if (normalized.includes('budget') || normalized.includes('cost')) return 'coins';
  return 'sprout';
}

const styles = StyleSheet.create({
  centered: { flex: 1, alignItems: 'center', justifyContent: 'center', padding: SPACING.lg, backgroundColor: COLORS.background },
  stateCard: { width: '100%', maxWidth: 420 },
  toolsContent: { gap: SPACING.md },
  loaderRow: { flexDirection: 'row', alignItems: 'center', gap: SPACING.sm },
  sectionTitle: { ...TYPOGRAPHY.h3, marginBottom: SPACING.sm },
  body: { ...TYPOGRAPHY.body, color: COLORS.textSecondary, lineHeight: 23 },
  label: { ...TYPOGRAPHY.caption, fontWeight: '600', color: COLORS.text, marginTop: SPACING.sm, marginBottom: SPACING.xs },
  input: { minHeight: 48, width: '100%', borderWidth: 1, borderColor: COLORS.border, borderRadius: 12, backgroundColor: COLORS.surface, paddingHorizontal: 14, paddingVertical: 11, color: COLORS.text, fontSize: 16, marginBottom: SPACING.xs },
  helper: { ...TYPOGRAPHY.caption, color: COLORS.textSecondary, lineHeight: 19, marginBottom: SPACING.sm },
  sourceText: { ...TYPOGRAPHY.caption, color: COLORS.textSecondary, lineHeight: 18, marginBottom: SPACING.xs },
  profileRow: { flexDirection: 'row', justifyContent: 'space-between', gap: SPACING.sm, paddingVertical: 6, borderBottomWidth: 1, borderBottomColor: COLORS.border },
  profileLabel: { ...TYPOGRAPHY.caption, color: COLORS.textSecondary },
  profileValue: { ...TYPOGRAPHY.caption, flexShrink: 1, textAlign: 'right', color: COLORS.text, fontWeight: '600' },
  missingValue: { color: COLORS.error },
  pickerField: { minHeight: 52, justifyContent: 'center', borderWidth: 1, borderColor: COLORS.border, borderRadius: 12, paddingHorizontal: 14, paddingBottom: 8, marginBottom: SPACING.xs, backgroundColor: COLORS.surface },
  pickerText: { ...TYPOGRAPHY.body, color: COLORS.text },
  infoCard: { backgroundColor: '#f0f5ee', borderLeftWidth: 3, borderLeftColor: COLORS.primary },
  warningCard: { backgroundColor: '#fff8ea', borderLeftWidth: 3, borderLeftColor: '#d97614' },
  errorCard: { backgroundColor: '#fff0ee', borderLeftWidth: 3, borderLeftColor: COLORS.error },
  errorText: { ...TYPOGRAPHY.body, color: COLORS.error, marginBottom: SPACING.sm },
  warningText: { ...TYPOGRAPHY.body, color: '#8a4b07', backgroundColor: '#fff8ea', padding: SPACING.sm, borderRadius: 8, marginVertical: SPACING.sm },
  infoTitle: { ...TYPOGRAPHY.body, fontWeight: '700', marginBottom: SPACING.xs },
  error: { ...TYPOGRAPHY.body, color: COLORS.error, padding: SPACING.md, backgroundColor: '#fff0ee', borderRadius: 8 },
  success: { ...TYPOGRAPHY.body, color: COLORS.primaryDark, padding: SPACING.md, backgroundColor: '#eaf5e9', borderRadius: 8 },
  cropName: { ...TYPOGRAPHY.h2, fontSize: 21, marginBottom: SPACING.xs },
  factorGroup: { marginTop: SPACING.sm },
  factorRow: { borderLeftWidth: 2, borderLeftColor: COLORS.primaryLight, paddingLeft: SPACING.sm, marginBottom: SPACING.sm },
  factorName: { ...TYPOGRAPHY.caption, fontWeight: '700', color: COLORS.text, marginBottom: 2 },
  assessmentRow: { paddingVertical: SPACING.xs, borderBottomWidth: 1, borderBottomColor: COLORS.border },
  regionalBlock: { paddingVertical: SPACING.sm, borderBottomWidth: 1, borderBottomColor: COLORS.border },
  regionalEntry: { marginVertical: SPACING.xs },
  shareRow: { flexDirection: 'row', alignItems: 'center', gap: SPACING.xs, marginBottom: 3 },
  shareLabel: { ...TYPOGRAPHY.caption, width: 128, color: COLORS.textSecondary, fontSize: 12 },
  shareTrack: { flex: 1, height: 8, borderRadius: 4, backgroundColor: '#e7ece4', overflow: 'hidden' },
  shareFill: { height: 8, backgroundColor: COLORS.primaryLight },
  shareValue: { ...TYPOGRAPHY.caption, width: 46, textAlign: 'right', fontSize: 12, color: COLORS.text },
  planTitle: { ...TYPOGRAPHY.body, fontWeight: '700', marginTop: SPACING.md, marginBottom: SPACING.xs },
  stageRow: { flexDirection: 'row', alignItems: 'center', borderBottomWidth: 1, borderBottomColor: COLORS.border, paddingVertical: SPACING.sm },
  stageNumber: { width: 30, height: 30, textAlign: 'center', textAlignVertical: 'center', borderRadius: 15, overflow: 'hidden', backgroundColor: '#e7f0e8', color: COLORS.primaryDark, fontWeight: '700', marginRight: SPACING.sm },
  stageCopy: { flex: 1, minWidth: 0 },
  stageName: { ...TYPOGRAPHY.body, fontWeight: '600' },
  taskDefinitions: { paddingTop: SPACING.md },
  guidance: { gap: SPACING.xs, marginVertical: SPACING.sm },
  inlineFields: { flexDirection: 'row', gap: SPACING.sm },
  flexOne: { flex: 1 },
  multiline: { minHeight: 80, textAlignVertical: 'top' },
  historySection: { marginTop: SPACING.md },
  historyHeading: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  link: { ...TYPOGRAPHY.caption, color: COLORS.primary, fontWeight: '700' },
  historyCard: { marginBottom: SPACING.sm },
  historyTitle: { ...TYPOGRAPHY.body, fontWeight: '600', marginBottom: SPACING.xs },
});
