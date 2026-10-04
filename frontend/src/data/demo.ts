export type Task = { id: string; title: string; completed: boolean; date: string };
export type Alert = { id: string; title: string; severity: 'high' | 'medium' | 'low'; date: string };
export type SeasonStage = { id: string; name: string; status: 'completed' | 'current' | 'upcoming'; dateRange: string };
export type ChatMessage = { id: string; text: string; sender: 'farmer' | 'assistant'; timestamp: string };
export type CropHealth = { status: string; diseaseRisk: string; recentIssues: string[] };

export type Farmland = {
  id: string;
  name: string;
  crop: string;
  acreage: number;
  growthStage: string;
  tasks: Task[];
  alerts: Alert[];
  seasonPlan: SeasonStage[];
  cropHealth: CropHealth;
  chat: ChatMessage[];
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
    tasks: [
      { id: 't1', title: 'Apply Nitrogen fertilizer', completed: false, date: 'Today' },
      { id: 't2', title: 'Inspect irrigation system', completed: true, date: 'Yesterday' },
    ],
    alerts: [
      { id: 'a1', title: 'High humidity expected tomorrow. Risk of rust.', severity: 'medium', date: 'Today' },
    ],
    seasonPlan: [
      { id: 's1', name: 'Preparation & Seeding', status: 'completed', dateRange: 'Sep 1 - Sep 15' },
      { id: 's2', name: 'Tillering & Stem Extension', status: 'current', dateRange: 'Sep 16 - Nov 30' },
      { id: 's3', name: 'Heading & Ripening', status: 'upcoming', dateRange: 'Dec 1 - Jan 15' },
    ],
    cropHealth: {
      status: 'Good',
      diseaseRisk: 'Moderate (Fungal)',
      recentIssues: ['Minor aphid presence detected 2 weeks ago (resolved)'],
    },
    chat: [
      { id: 'c1', text: 'How much nitrogen should I apply today?', sender: 'farmer', timestamp: '08:00 AM' },
      { id: 'c2', text: 'Based on your soil tests, apply 50 lbs per acre.', sender: 'assistant', timestamp: '08:02 AM' },
    ],
  },
  {
    id: 'f2',
    name: 'East Riverside Plot',
    crop: 'Corn',
    acreage: 120.0,
    growthStage: 'Silking',
    tasks: [
      { id: 't3', title: 'Check soil moisture sensors', completed: false, date: 'Today' },
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
    cropHealth: {
      status: 'Excellent',
      diseaseRisk: 'Low',
      recentIssues: [],
    },
    chat: [
      { id: 'c3', text: 'What is the forecast for next week?', sender: 'farmer', timestamp: '10:00 AM' },
      { id: 'c4', text: 'Expect clear skies with a high of 85°F. Good conditions for silking.', sender: 'assistant', timestamp: '10:01 AM' },
    ],
  },
];
