import { Platform } from 'react-native';
import * as ImagePicker from 'expo-image-picker';

export type DiseaseOutcome = 'healthy' | 'uncertain' | 'possible_disease';
export type ProblemSyncStatus = 'not_required' | 'created' | 'reused' | 'failed';
export type DiseaseVerificationStatus =
  | 'not_configured'
  | 'verified_healthy'
  | 'verified_issue'
  | 'gemini_only_issue'
  | 'disagreement'
  | 'uncertain'
  | 'unavailable';

export type DiseaseVerification = {
  status: DiseaseVerificationStatus;
  finding: 'healthy' | 'possible_issue' | 'uncertain' | 'not_crop' | null;
  crop_match: 'matches_current_crop' | 'different_crop' | 'uncertain' | null;
  visible_signs: string | null;
  model: string | null;
};

export type DiseaseResult = {
  id: string;
  farmland_id: string;
  season_id: string | null;
  crop_id: string | null;
  crop_name: string | null;
  possible_issue: string | null;
  confidence: number | null;
  symptoms: string[];
  recommended_actions: string[];
  model_details: Record<string, unknown>;
  created_at: string;
};

export type FarmProblem = {
  id: string;
  farmland_id: string;
  season_id: string | null;
  source: string;
  category: string;
  description: string;
  severity: string;
  status: string;
  created_at: string;
  resolved_at: string | null;
};

export type DiseaseAnalysis = {
  disease_result: DiseaseResult;
  outcome: DiseaseOutcome;
  verification: DiseaseVerification;
  confidence_level: 'low' | 'moderate' | 'high';
  crop_name: string;
  growth_stage_name: string | null;
  farm_problem: FarmProblem | null;
  problem_sync: ProblemSyncStatus;
  message: string;
  disclaimer: string;
};

export type DiseaseProblemSync = {
  disease_result: DiseaseResult;
  farm_problem: FarmProblem | null;
  problem_sync: ProblemSyncStatus;
  message: string;
};

type AccessTokenProvider = () => Promise<string | null>;
let accessTokenProvider: AccessTokenProvider = async () => null;

export function setApiAccessTokenProvider(provider: AccessTokenProvider) {
  accessTokenProvider = provider;
}

const apiBaseUrl = (process.env.EXPO_PUBLIC_API_URL || 'http://127.0.0.1:8000').replace(/\/+$/, '');

async function requestJson<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers: Record<string, string> = { Accept: 'application/json' };
  const token = await accessTokenProvider();
  if (token) headers.Authorization = 'Bearer ' + token;

  const response = await fetch(apiBaseUrl + path, {
    ...init,
    credentials: 'include',
    headers: { ...headers, ...(init.headers as Record<string, string> | undefined) },
  });
  if (!response.ok) {
    let detail = 'The request could not be completed.';
    try {
      const body = await response.json();
      if (typeof body.detail === 'string') detail = body.detail;
    } catch {
      // Keep the user-facing fallback when the server did not return JSON.
    }

    if (response.status === 401) {
      throw new Error('Sign in with a verified farmer account to use disease detection. Module 1 authentication is not connected yet.');
    }
    if (response.status === 404) {
      throw new Error('This farm is not available to the signed-in farmer.');
    }
    throw new Error(detail);
  }
  return response.json() as Promise<T>;
}

export async function analyzeDiseaseImage(
  farmlandId: string,
  asset: ImagePicker.ImagePickerAsset,
): Promise<DiseaseAnalysis> {
  const form = new FormData();
  if (Platform.OS === 'web' && asset.file) {
    form.append('image', asset.file);
  } else if (Platform.OS === 'web') {
    const response = await fetch(asset.uri);
    form.append('image', await response.blob());
  } else {
    form.append(
      'image',
      {
        uri: asset.uri,
        name: asset.fileName || 'crop-photo.jpg',
        type: asset.mimeType || 'image/jpeg',
      } as unknown as Blob,
    );
  }

  return requestJson<DiseaseAnalysis>(
    '/farmlands/' + encodeURIComponent(farmlandId) + '/disease-results',
    { method: 'POST', body: form },
  );
}

export async function getDiseaseResults(farmlandId: string): Promise<DiseaseResult[]> {
  return requestJson<DiseaseResult[]>(
    '/farmlands/' + encodeURIComponent(farmlandId) + '/disease-results?limit=20',
  );
}

export async function retryDiseaseProblemSync(
  farmlandId: string,
  diseaseResultId: string,
): Promise<DiseaseProblemSync> {
  return requestJson<DiseaseProblemSync>(
    '/farmlands/' + encodeURIComponent(farmlandId)
      + '/disease-results/' + encodeURIComponent(diseaseResultId) + '/sync-problem',
    { method: 'POST' },
  );
}
