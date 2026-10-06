const API_BASE_URL = process.env.EXPO_PUBLIC_API_URL ?? 'http://localhost:8000';
type AccessTokenProvider = () => Promise<string | null>;
let accessTokenProvider: AccessTokenProvider = async () => null;

export function setM2AccessTokenProvider(provider: AccessTokenProvider) {
  accessTokenProvider = provider;
}

export type KnowledgeReference = {
  source_name: string;
  source_type?: string | null;
  source_reference?: string | null;
  category?: string | null;
};

export type SuitabilityFactor = {
  factor: string;
  explanation: string;
  knowledge_refs: KnowledgeReference[];
};

export type CropRecommendation = {
  recommendation_id: string | null;
  farmland_id: string;
  crop: { crop_id: string; name: string | null; scientific_name: string | null };
  score: number | null;
  status: string;
  reasoning: {
    summary: string | null;
    positive_factors: SuitabilityFactor[];
    limiting_factors: SuitabilityFactor[];
    risks_or_concerns: SuitabilityFactor[];
  };
  knowledge_refs: KnowledgeReference[];
};

export type RecommendationSet = {
  farmland_id: string;
  status: 'available' | 'no_approved_knowledge' | 'no_supported_fit';
  message: string;
  recommendations: CropRecommendation[];
};

export type Season = {
  season_id: string;
  farmland_id: string;
  crop_id: string;
  crop_variety_id: string | null;
  variety_name: string | null;
  planting_date: string | null;
  expected_harvest_date: string | null;
  status: 'planned' | 'active' | 'completed' | 'cancelled';
  budget_amount: number | null;
  budget_currency: string;
  actual_harvest_date: string | null;
  actual_yield: number | null;
  yield_unit: string | null;
  outcome_notes: string | null;
};

export type InitialTaskDefinition = {
  title: string;
  description: string | null;
  due_day_offset: number | null;
  priority: 'low' | 'normal' | 'high' | 'urgent';
  growth_stage_id: string | null;
};

export type SeasonPlan = {
  season_plan_id: string;
  season_id: string;
  title: string;
  description: string | null;
  status: string;
  growth_stages: { growth_stage_id: string | null; name: string; sequence: number; start_day: number | null; end_day: number | null }[];
  initial_tasks: InitialTaskDefinition[];
  knowledge_refs: KnowledgeReference[];
};

export type HarvestGuidance = {
  maturity_indicators: string[];
  recommended_window_start: string | null;
  recommended_window_end: string | null;
  guidance: string[];
  uncertainty_notes: string[];
  knowledge_refs: KnowledgeReference[];
};

type ApiError = Error & { status?: number };

export async function m2Request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  headers.set('Content-Type', 'application/json');
  let accessToken: string | null;
  try {
    accessToken = await accessTokenProvider();
  } catch {
    throw new Error('Could not read your sign-in session. Please sign in again.');
  }
  if (accessToken) headers.set('Authorization', `Bearer ${accessToken}`);

  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, { ...init, headers });
  } catch {
    throw new Error('Could not connect to the backend. Check that it is running.');
  }

  const payload = await response.json().catch(() => null);
  if (!response.ok) {
    const detail = typeof payload?.detail === 'string' ? payload.detail : '';
    const message = translateApiError(response.status, detail);
    const error = new Error(message) as ApiError;
    error.status = response.status;
    throw error;
  }
  return payload as T;
}

export function translateApiError(status: number, detail: string): string {
  if (status === 401) return 'Sign in with a verified farmer account to access this farm. Module 1 authentication is not connected yet.';
  if (status === 404 && detail.toLowerCase().includes('farmland')) {
    return 'This farmland is not saved in the backend. Enter a saved Farmland ID from M1.';
  }
  if (detail.includes('No approved season-plan knowledge')) {
    return 'There is no approved season-plan evidence for this crop yet. No stages or tasks were invented.';
  }
  if (detail.includes('No approved harvest guidance')) {
    return 'There is no approved source for harvest guidance for this crop yet.';
  }
  const knownDetails: Record<string, string> = {
    'Crop not found': 'Crop not found in the backend.',
    'Season not found': 'This season is no longer available.',
    'Season plan not found': 'No plan is saved for this season.',
    'Generate a season plan before activation': 'Create a season plan before activating the season.',
    'Completed or cancelled seasons cannot be activated': 'Completed or cancelled seasons cannot be activated.',
    'Another season is already active on this farmland': 'Another season is already active on this farmland.',
    'Completed or cancelled seasons cannot receive a new plan': 'Completed or cancelled seasons cannot receive a new plan.',
    'Cannot create or replace an active season plan without coordinating current-stage state with Module 3': 'This season is active. Coordinate the current growth stage with Module 3 before creating another plan.',
    'The season plan has no growth stages': 'The season plan has no growth stages.',
    'Only proposed recommendations can be dismissed': 'Only proposed recommendations can be dismissed.',
    'Recommendation is no longer proposed': 'This recommendation is no longer proposed.',
  };
  if (knownDetails[detail]) return knownDetails[detail];
  if (status === 404) return 'The requested information was not found.';
  if (status === 409) return 'This action is not available now. Check the season status and plan, then try again.';
  if (status === 422) return 'Check the information you entered and try again.';
  return `The backend rejected the request (${status}). Please try again shortly.`;
}
