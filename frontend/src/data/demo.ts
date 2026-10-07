export type TaskStatus = 'pending' | 'completed' | 'skipped' | 'cancelled';
export type TaskSource = 'season_plan' | 'weather' | 'disease' | 'farmer' | 'system';
export type TaskPriority = 'low' | 'normal' | 'high' | 'urgent';
export type TaskScheduleState = TaskStatus | 'upcoming' | 'due' | 'overdue' | 'unscheduled';

export type Task = {
  id: string;
  title: string;
  description?: string;
  status: TaskStatus;
  dueAt: string | null;
  priority: TaskPriority;
  source: TaskSource;
  growthStageId?: string;
};

export type Alert = { id: string; title: string; severity: 'high' | 'medium' | 'low'; date: string };
export type SeasonStage = { id: string; name: string; status: 'completed' | 'current' | 'upcoming'; dateRange: string };
export type ChatMessage = { id: string; text: string; sender: 'farmer' | 'assistant'; timestamp: string };
export type ChatThread = { id: string; title: string; messages: ChatMessage[]; updatedAt: number };
export type CropHealth = { status: string; diseaseRisk: string; recentIssues: string[] };
export type ProblemStatus = 'open' | 'monitoring' | 'resolved' | 'dismissed';
export type ProblemSeverity = 'low' | 'moderate' | 'high' | 'critical';
export type FarmProblem = {
  id: string;
  category: string;
  description: string;
  source: 'farmer' | 'weather' | 'disease_detection' | 'system';
  severity: ProblemSeverity;
  status: ProblemStatus;
  createdAt: string;
  resolvedAt?: string;
};
export type FarmCheckIn = {
  id: string;
  at: string;
  notes: string;
  stageName: string;
  observations: {
    cropCondition?: string;
    waterCondition?: string;
    pestObserved?: boolean;
    diseaseObserved?: boolean;
  };
};

export type Farmland = {
  id: string;
  name: string;
  crop: string;
  acreage: number;
  growthStage: string;
  currentGrowthStageId: string | null;
  tasks: Task[];
  alerts: Alert[];
  seasonPlan: SeasonStage[];
  problems: FarmProblem[];
  checkIns: FarmCheckIn[];
  cropHealth: CropHealth;
  location?: string;
  district?: string | null;
  landAreaUnit?: string;
  soilType?: string | null;
  irrigationAvailable?: boolean | null;
  waterSource?: string | null;
  budgetAmount?: number | null;
  budgetCurrency?: string | null;
  activeSeasonId?: string | null;
  plantingDate?: string | null;
  expectedHarvestDate?: string | null;
  seasonProgressPercent?: number | null;
  daysSincePlanting?: number | null;
  dataWarning?: string;
};

export const DEMO_CREDENTIALS = {
  phone: '01700000000',
  password: 'demo123',
};

export const DEMO_FARMLANDS: Farmland[] = [
  {
    id: 'f1',
    name: 'North Valley Field',
    crop: 'Wheat',
    acreage: 45.5,
    growthStage: 'Tillering',
    currentGrowthStageId: 's2',
    tasks: [
      {
        id: 't1',
        title: 'Apply nitrogen fertilizer',
        description: 'Apply the planned top dressing to the wheat rows.',
        status: 'pending',
        dueAt: '2026-10-06T12:00:00+06:00',
        priority: 'high',
        source: 'season_plan',
        growthStageId: 's2',
      },
      {
        id: 't2',
        title: 'Inspect irrigation system',
        status: 'completed',
        dueAt: '2026-10-05T12:00:00+06:00',
        priority: 'normal',
        source: 'farmer',
        growthStageId: 's2',
      },
      {
        id: 't4',
        title: 'Check drainage before rain',
        status: 'pending',
        dueAt: '2026-10-07T12:00:00+06:00',
        priority: 'urgent',
        source: 'weather',
        growthStageId: 's2',
      },
    ],
    alerts: [
      { id: 'a1', title: 'High humidity expected tomorrow. Risk of rust.', severity: 'medium', date: 'Today' },
    ],
    seasonPlan: [
      { id: 's1', name: 'Preparation & Seeding', status: 'completed', dateRange: 'Sep 1 - Sep 15' },
      { id: 's2', name: 'Tillering & Stem Extension', status: 'current', dateRange: 'Sep 16 - Nov 30' },
      { id: 's3', name: 'Heading & Ripening', status: 'upcoming', dateRange: 'Dec 1 - Jan 15' },
    ],
    problems: [
      {
        id: 'p1',
        category: 'Leaf disease',
        description: 'Possible leaf disease reported during the last field check.',
        source: 'disease_detection',
        severity: 'moderate',
        status: 'open',
        createdAt: '2026-10-04T08:00:00+06:00',
      },
    ],
    checkIns: [
      {
        id: 'c1',
        at: '2026-10-04T08:00:00+06:00',
        notes: 'Irrigation completed. Leaves look healthy overall.',
        stageName: 'Tillering',
        observations: { waterCondition: 'Adequate' },
      },
    ],
    cropHealth: {
      status: 'Good',
      diseaseRisk: 'Moderate (Fungal)',
      recentIssues: ['Minor aphid presence detected 2 weeks ago (resolved)'],
    },
  },
  {
    id: 'f2',
    name: 'East Riverside Plot',
    crop: 'Corn',
    acreage: 120.0,
    growthStage: 'Silking',
    currentGrowthStageId: 's6',
    tasks: [
      {
        id: 't3',
        title: 'Check soil moisture sensors',
        status: 'pending',
        dueAt: '2026-10-06T12:00:00+06:00',
        priority: 'normal',
        source: 'season_plan',
        growthStageId: 's6',
      },
    ],
    alerts: [
      { id: 'a2', title: 'Pest activity (Corn Borer) reported in neighboring farms.', severity: 'high', date: 'Today' },
    ],
    seasonPlan: [
      { id: 's4', name: 'Planting', status: 'completed', dateRange: 'Apr 10 - Apr 25' },
      { id: 's5', name: 'Vegetative Growth', status: 'completed', dateRange: 'Apr 26 - Jul 10' },
      { id: 's6', name: 'Silking & Tasseling', status: 'current', dateRange: 'Jul 11 - Aug 5' },
      { id: 's7', name: 'Harvest', status: 'upcoming', dateRange: 'Sep 15 - Oct 10' },
    ],
    problems: [],
    checkIns: [],
    cropHealth: {
      status: 'Excellent',
      diseaseRisk: 'Low',
      recentIssues: [],
    },
  },
];
