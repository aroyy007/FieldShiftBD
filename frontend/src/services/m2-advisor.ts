const API_BASE_URL = process.env.EXPO_PUBLIC_API_URL ?? 'http://localhost:8000';
const FARMER_TOKEN = process.env.EXPO_PUBLIC_FARMER_TOKEN;

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
  if (FARMER_TOKEN) headers.set('Authorization', `Bearer ${FARMER_TOKEN}`);

  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, { ...init, headers });
  } catch {
    throw new Error('Backend-এর সঙ্গে সংযোগ করা যাচ্ছে না। Backend চালু আছে কি না দেখুন।');
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
  if (status === 401) return 'M3-এর task list-এ পাঠাতে আগে backend authentication যুক্ত করতে হবে।';
  if (status === 404 && detail.toLowerCase().includes('farmland')) {
    return 'এই জমির তথ্য backend-এ নেই। M1 থেকে আসা একটি সংরক্ষিত Farmland ID ব্যবহার করুন।';
  }
  if (detail.includes('No approved season-plan knowledge')) {
    return 'এই ফসলের জন্য যাচাই করা season plan এখনো যোগ হয়নি। তাই কোনো stage বা task বানিয়ে দেখানো হচ্ছে না।';
  }
  if (detail.includes('No approved harvest guidance')) {
    return 'এই ফসলের harvest guidance-এর জন্য অনুমোদিত source এখনো নেই।';
  }
  const knownDetails: Record<string, string> = {
    'Crop not found': 'এই ফসলের তথ্য backend-এ পাওয়া যায়নি।',
    'Season not found': 'মৌসুমটি আর পাওয়া যাচ্ছে না।',
    'Season plan not found': 'এই মৌসুমের জন্য কোনো plan সংরক্ষিত নেই।',
    'Generate a season plan before activation': 'মৌসুম active করার আগে একটি season plan তৈরি করুন।',
    'Completed or cancelled seasons cannot be activated': 'সম্পন্ন বা বাতিল মৌসুম active করা যাবে না।',
    'Another season is already active on this farmland': 'এই জমিতে অন্য একটি মৌসুম এখনো চলমান।',
    'Completed or cancelled seasons cannot receive a new plan': 'সম্পন্ন বা বাতিল মৌসুমের জন্য নতুন plan তৈরি করা যাবে না।',
    'An active season\'s plan cannot be replaced without coordinating current-stage state with Module 3': 'মৌসুমটি চলমান। Module 3-এর current stage-এর সঙ্গে সমন্বয় না করে plan বদলানো যাবে না।',
    'The season plan has no growth stages': 'Season plan-এ কোনো growth stage নেই।',
    'Only proposed recommendations can be dismissed': 'শুধু প্রস্তাবিত পরামর্শই বাদ দেওয়া যায়।',
    'Recommendation is no longer proposed': 'এই পরামর্শটি আর প্রস্তাবিত অবস্থায় নেই।',
  };
  if (knownDetails[detail]) return knownDetails[detail];
  if (status === 404) return 'চাওয়া তথ্যটি পাওয়া যায়নি।';
  if (status === 409) return 'এই ধাপটি এখন করা যাচ্ছে না। মৌসুমের অবস্থা ও plan দেখে আবার চেষ্টা করুন।';
  if (status === 422) return 'দেওয়া তথ্যগুলো আরেকবার মিলিয়ে দেখুন।';
  return `Backend অনুরোধটি গ্রহণ করেনি (${status})। কিছুক্ষণ পর আবার চেষ্টা করুন।`;
}
