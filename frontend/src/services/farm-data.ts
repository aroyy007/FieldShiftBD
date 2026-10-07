import type { Farmland } from '../data/demo';

export type FarmlandProfileDto = {
  id: string;
  name: string;
  division: string | null;
  district: string | null;
  upazila: string | null;
  village_or_locality: string | null;
  land_area_sqm: number | string;
  land_area_display_unit: string;
  soil_type: string | null;
  irrigation_available: boolean | null;
  water_source: string | null;
  budget_amount?: number | string | null;
  budget_currency?: string | null;
};

export type GrowthStageDto = {
  id: string;
  name: string;
  sequence: number;
  start_day: number | null;
  end_day: number | null;
};

export type FarmStateDto = {
  active_season: {
    id: string;
    crop_name: string;
    planting_date: string | null;
    expected_harvest_date: string | null;
  } | null;
  current_growth_stage: GrowthStageDto | null;
  growth_stages: GrowthStageDto[];
  season_progress_percent: number | null;
  days_since_planting: number | null;
  tasks?: TaskDto[];
  open_problems?: ProblemDto[];
};

export type TaskDto = {
  id: string;
  title: string;
  description: string | null;
  status: Farmland['tasks'][number]['status'];
  due_at: string | null;
  priority: Farmland['tasks'][number]['priority'];
  source: Farmland['tasks'][number]['source'];
  growth_stage_id: string | null;
};

export type ProblemDto = {
  id: string;
  category: string;
  description: string;
  source: Farmland['problems'][number]['source'];
  severity: Farmland['problems'][number]['severity'];
  status: Farmland['problems'][number]['status'];
  created_at: string;
  resolved_at: string | null;
};

export type CheckinDto = {
  id: string;
  checkin_at: string;
  growth_stage_id: string | null;
  notes: string | null;
  observations: Record<string, unknown>;
};

export type FarmlandCreateInput = {
  name: string;
  land_area_sqm: number;
  land_area_display_unit: 'square_metre' | 'decimal' | 'acre' | 'hectare';
  division?: string | null;
  district?: string | null;
  upazila?: string | null;
  village_or_locality?: string | null;
  latitude?: number | null;
  longitude?: number | null;
  soil_type?: string | null;
  irrigation_available?: boolean | null;
  water_source?: string | null;
};

export function normalizeBangladeshPhone(input: string): string {
  const digits = input.replace(/\D/g, '');
  if (digits.startsWith('880')) return `+${digits}`;
  if (digits.startsWith('0')) return `+88${digits}`;
  return `+880${digits}`;
}

function numberOrZero(value: number | string): number {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : 0;
}

function locationLabel(profile: FarmlandProfileDto): string {
  return [profile.village_or_locality, profile.upazila, profile.district, profile.division]
    .filter((part): part is string => Boolean(part?.trim()))
    .join(', ');
}

function mapTask(task: TaskDto): Farmland['tasks'][number] {
  return {
    id: task.id,
    title: task.title,
    description: task.description ?? undefined,
    status: task.status,
    dueAt: task.due_at,
    priority: task.priority,
    source: task.source,
    growthStageId: task.growth_stage_id ?? undefined,
  };
}

function mapProblem(problem: ProblemDto): Farmland['problems'][number] {
  return {
    id: problem.id,
    category: problem.category,
    description: problem.description,
    source: problem.source,
    severity: problem.severity,
    status: problem.status,
    createdAt: problem.created_at,
    resolvedAt: problem.resolved_at ?? undefined,
  };
}

function mapCheckin(
  checkin: CheckinDto,
  stages: GrowthStageDto[],
): Farmland['checkIns'][number] {
  const stageName = stages.find(stage => stage.id === checkin.growth_stage_id)?.name ?? 'Not set';
  const observations = checkin.observations ?? {};
  const cropCondition = observations.crop_condition ?? observations.cropCondition;
  const waterCondition = observations.water_condition ?? observations.waterCondition;
  const pestObserved = observations.pest_observed ?? observations.pestObserved;
  const diseaseObserved = observations.disease_observed ?? observations.diseaseObserved;

  return {
    id: checkin.id,
    at: checkin.checkin_at,
    notes: checkin.notes ?? '',
    stageName,
    observations: {
      ...(typeof cropCondition === 'string' ? { cropCondition } : {}),
      ...(typeof waterCondition === 'string' ? { waterCondition } : {}),
      ...(typeof pestObserved === 'boolean' ? { pestObserved } : {}),
      ...(typeof diseaseObserved === 'boolean' ? { diseaseObserved } : {}),
    },
  };
}

export function mapFarmlandData(
  profile: FarmlandProfileDto,
  state: FarmStateDto | null,
  tasks: TaskDto[] = [],
  problems: ProblemDto[] = [],
  checkIns: CheckinDto[] = [],
): Farmland {
  const currentStageId = state?.current_growth_stage?.id ?? null;
  const growthStages = state?.growth_stages ?? [];
  const currentSequence = growthStages.find(stage => stage.id === currentStageId)?.sequence ?? -1;
  const acres = numberOrZero(profile.land_area_sqm) / 4046.8564224;

  return {
    id: profile.id,
    name: profile.name,
    crop: state?.active_season?.crop_name ?? 'No active crop',
    acreage: acres,
    growthStage: state?.current_growth_stage?.name ?? 'No active stage',
    currentGrowthStageId: currentStageId,
    tasks: tasks.map(mapTask),
    alerts: [],
    seasonPlan: growthStages.map(stage => ({
      id: stage.id,
      name: stage.name,
      status: stage.id === currentStageId
        ? 'current'
        : stage.sequence < currentSequence ? 'completed' : 'upcoming',
      dateRange: stage.start_day != null || stage.end_day != null
        ? `Day ${stage.start_day ?? 0}–${stage.end_day ?? '—'}`
        : `Stage ${stage.sequence}`,
    })),
    problems: problems.map(mapProblem),
    checkIns: checkIns.map(item => mapCheckin(item, growthStages)),
    cropHealth: {
      status: 'No scan data',
      diseaseRisk: 'Unknown',
      recentIssues: [],
    },
    location: locationLabel(profile) || 'Location not set',
    district: profile.district,
    landAreaUnit: profile.land_area_display_unit,
    soilType: profile.soil_type,
    irrigationAvailable: profile.irrigation_available,
    waterSource: profile.water_source,
    budgetAmount: profile.budget_amount == null ? null : numberOrZero(profile.budget_amount),
    budgetCurrency: profile.budget_currency ?? 'BDT',
    activeSeasonId: state?.active_season?.id ?? null,
    plantingDate: state?.active_season?.planting_date ?? null,
    expectedHarvestDate: state?.active_season?.expected_harvest_date ?? null,
    seasonProgressPercent: state?.season_progress_percent ?? null,
    daysSincePlanting: state?.days_since_planting ?? null,
  };
}
