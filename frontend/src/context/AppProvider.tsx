import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { apiRequest, clearAccessToken, getStoredAccessToken, saveAccessToken, setUnauthorizedHandler } from '../services/api-client';
import {
  CheckinDto,
  FarmStateDto,
  FarmlandCreateInput,
  FarmlandProfileDto,
  ProblemDto,
  TaskDto,
  mapFarmlandData,
} from '../services/farm-data';
import type { ChatMessage, ChatThread, Farmland, FarmCheckIn, ProblemStatus, TaskStatus } from '../data/demo';
import {
  ChatMessageItem,
  createConversation as createRemoteConversation,
  getConversation,
  listConversations,
  sendMessage as sendRemoteMessage,
} from '../services/m5-chat';

type Farmer = { id: string; name: string; phone: string };
type FarmerProfile = {
  farming_experience_years: number | string | null;
  equipment: string[];
  livestock: string[];
  preferred_language: 'bn' | 'en';
  onboarding_completed_at: string | null;
};
type ProfileResponse = {
  farmer: { id: string; name: string; phone_e164: string };
  profile: FarmerProfile | null;
  farmlands: FarmlandProfileDto[];
};
type TokenResponse = { access_token: string; farmer_id: string };
type AppContextType = {
  user: Farmer | null;
  profile: FarmerProfile | null;
  authLoading: boolean;
  dataLoading: boolean;
  loadError: string;
  farmlands: Farmland[];
  login: (phoneE164: string, password: string) => Promise<void>;
  register: (name: string, phoneE164: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshProfile: () => Promise<void>;
  refreshFarmland: (farmId: string) => Promise<void>;
  createFarmland: (input: FarmlandCreateInput) => Promise<Farmland>;
  updateFarmland: (farmId: string, changes: Record<string, unknown>) => Promise<void>;
  updateFarmerProfile: (changes: Record<string, unknown>) => Promise<void>;
  addTask: (farmId: string, title: string, dueAt: string | null) => Promise<void>;
  updateTaskStatus: (farmId: string, taskId: string, status: TaskStatus) => Promise<void>;
  addCheckIn: (farmId: string, notes: string, observations: FarmCheckIn['observations']) => Promise<void>;
  addProblem: (farmId: string, description: string) => Promise<void>;
  updateProblemStatus: (farmId: string, problemId: string, status: ProblemStatus) => Promise<void>;
  updateGrowthStage: (farmId: string, stageId: string) => Promise<void>;
  conversations: Record<string, ChatThread[]>;
  activeConversationIds: Record<string, string | undefined>;
  refreshConversations: (farmId: string) => Promise<void>;
  createConversation: (farmId: string) => Promise<string>;
  selectConversation: (farmId: string, conversationId: string) => Promise<void>;
  addChatMessage: (farmId: string, conversationId: string, text: string, clientRequestId: string) => Promise<void>;
};

const AppContext = createContext<AppContextType | undefined>(undefined);

function readableError(error: unknown): string {
  return error instanceof Error ? error.message : 'The request could not be completed.';
}

async function loadFarm(profile: FarmlandProfileDto): Promise<Farmland> {
  const farmPath = `/farmlands/${encodeURIComponent(profile.id)}`;
  const [stateResult, tasksResult, problemsResult, checkinsResult] = await Promise.allSettled([
    apiRequest<FarmStateDto>(`${farmPath}/state`),
    apiRequest<TaskDto[]>(`${farmPath}/tasks?limit=200`),
    apiRequest<ProblemDto[]>(`${farmPath}/problems`),
    apiRequest<CheckinDto[]>(`${farmPath}/check-ins?limit=100`),
  ]);

  const state = stateResult.status === 'fulfilled' ? stateResult.value : null;
  const taskList = tasksResult.status === 'fulfilled' ? tasksResult.value : state?.tasks ?? [];
  const problemList = problemsResult.status === 'fulfilled' ? problemsResult.value : state?.open_problems ?? [];
  const checkinList = checkinsResult.status === 'fulfilled' ? checkinsResult.value : [];
  const farm = mapFarmlandData(profile, state, taskList, problemList, checkinList);
  const partialFailures = [stateResult, tasksResult, problemsResult, checkinsResult]
    .filter(result => result.status === 'rejected').length;
  if (partialFailures) {
    farm.dataWarning = 'Some farm records could not be refreshed. Pull to refresh or try again.';
  }
  return farm;
}

function mapChatMessage(message: ChatMessageItem): ChatMessage {
  const createdAt = new Date(message.created_at);
  return {
    id: message.id,
    text: message.message ?? '',
    sender: message.sender_type === 'farmer' ? 'farmer' : 'assistant',
    timestamp: Number.isNaN(createdAt.getTime())
      ? ''
      : createdAt.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' }),
  };
}

function mapChatDetail(detail: Awaited<ReturnType<typeof getConversation>>): ChatThread {
  return {
    id: detail.id,
    title: detail.title || 'New chat',
    messages: detail.messages.map(mapChatMessage),
    updatedAt: new Date(detail.updated_at).getTime() || Date.now(),
  };
}

export function AppProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<Farmer | null>(null);
  const [profile, setProfile] = useState<FarmerProfile | null>(null);
  const [farmlands, setFarmlands] = useState<Farmland[]>([]);
  const [conversations, setConversations] = useState<Record<string, ChatThread[]>>({});
  const [activeConversationIds, setActiveConversationIds] = useState<Record<string, string | undefined>>({});
  const [authLoading, setAuthLoading] = useState(true);
  const [dataLoading, setDataLoading] = useState(false);
  const [loadError, setLoadError] = useState('');

  const applyProfile = useCallback(async (response: ProfileResponse) => {
    const loadedFarms = await Promise.all(response.farmlands.map(loadFarm));
    setUser({
      id: response.farmer.id,
      name: response.farmer.name,
      phone: response.farmer.phone_e164,
    });
    setProfile(response.profile);
    setFarmlands(loadedFarms);
    setLoadError('');
  }, []);

  const refreshProfile = useCallback(async () => {
    setDataLoading(true);
    try {
      const response = await apiRequest<ProfileResponse>('/profile');
      await applyProfile(response);
    } catch (error) {
      setLoadError(readableError(error));
      throw error;
    } finally {
      setDataLoading(false);
    }
  }, [applyProfile]);

  const refreshFarmland = useCallback(async (farmId: string) => {
    const response = await apiRequest<FarmlandProfileDto>(`/farmlands/${encodeURIComponent(farmId)}`);
    const farm = await loadFarm(response);
    setFarmlands(current => current.map(item => item.id === farmId ? farm : item));
  }, []);

  useEffect(() => {
    setUnauthorizedHandler(async () => {
      await clearAccessToken().catch(() => undefined);
      setUser(null);
      setProfile(null);
      setFarmlands([]);
      setConversations({});
      setActiveConversationIds({});
      setLoadError('Your session expired. Please sign in again.');
    });

    let active = true;
    const restore = async () => {
      try {
        const token = await getStoredAccessToken();
        if (token) {
          const response = await apiRequest<ProfileResponse>('/profile');
          if (active) await applyProfile(response);
        }
      } catch (error) {
        if (active) setLoadError(readableError(error));
      } finally {
        if (active) setAuthLoading(false);
      }
    };
    void restore();
    return () => {
      active = false;
      setUnauthorizedHandler(null);
    };
  }, [applyProfile]);

  const authenticate = useCallback(async (path: '/auth/login' | '/auth/register', body: Record<string, unknown>) => {
    const response = await apiRequest<TokenResponse>(path, { method: 'POST', body });
    await saveAccessToken(response.access_token);
    await refreshProfile();
  }, [refreshProfile]);

  const login = useCallback(async (phoneE164: string, password: string) => {
    await authenticate('/auth/login', { phone_e164: phoneE164, password });
  }, [authenticate]);

  const register = useCallback(async (name: string, phoneE164: string, password: string) => {
    await authenticate('/auth/register', { name: name.trim(), phone_e164: phoneE164, password });
  }, [authenticate]);

  const logout = useCallback(async () => {
    await clearAccessToken();
    setUser(null);
    setProfile(null);
    setFarmlands([]);
    setConversations({});
    setActiveConversationIds({});
    setLoadError('');
  }, []);

  const createFarmland = useCallback(async (input: FarmlandCreateInput) => {
    const response = await apiRequest<FarmlandProfileDto>('/farmlands', { method: 'POST', body: input });
    const farm = await loadFarm(response);
    setFarmlands(current => [...current, farm]);
    return farm;
  }, []);

  const updateFarmland = useCallback(async (farmId: string, changes: Record<string, unknown>) => {
    await apiRequest<FarmlandProfileDto>(`/farmlands/${encodeURIComponent(farmId)}`, { method: 'PATCH', body: changes });
    await refreshFarmland(farmId);
  }, [refreshFarmland]);

  const updateFarmerProfile = useCallback(async (changes: Record<string, unknown>) => {
    const response = await apiRequest<FarmerProfile>('/profile/farmer-profile', { method: 'PATCH', body: changes });
    setProfile(response);
  }, []);

  const addTask = useCallback(async (farmId: string, title: string, dueAt: string | null) => {
    await apiRequest<TaskDto>(`/farmlands/${encodeURIComponent(farmId)}/tasks`, {
      method: 'POST',
      body: { title: title.trim(), due_at: dueAt, source: 'farmer', priority: 'normal' },
    });
    await refreshFarmland(farmId);
  }, [refreshFarmland]);

  const updateTaskStatus = useCallback(async (farmId: string, taskId: string, status: TaskStatus) => {
    await apiRequest<TaskDto>(`/farmlands/${encodeURIComponent(farmId)}/tasks/${encodeURIComponent(taskId)}`, {
      method: 'PATCH', body: { status },
    });
    await refreshFarmland(farmId);
  }, [refreshFarmland]);

  const addCheckIn = useCallback(async (
    farmId: string,
    notes: string,
    observations: FarmCheckIn['observations'],
  ) => {
    const farm = farmlands.find(item => item.id === farmId);
    await apiRequest<CheckinDto>(`/farmlands/${encodeURIComponent(farmId)}/check-ins`, {
      method: 'POST',
      body: {
        season_id: farm?.activeSeasonId ?? null,
        growth_stage_id: farm?.currentGrowthStageId ?? null,
        notes: notes.trim(),
        observations: {
          crop_condition: observations.cropCondition ?? null,
          water_condition: observations.waterCondition ?? null,
          pest_observed: observations.pestObserved ?? false,
          disease_observed: observations.diseaseObserved ?? false,
        },
      },
    });
    await refreshFarmland(farmId);
  }, [farmlands, refreshFarmland]);

  const addProblem = useCallback(async (farmId: string, description: string) => {
    const farm = farmlands.find(item => item.id === farmId);
    await apiRequest<ProblemDto>(`/farmlands/${encodeURIComponent(farmId)}/problems`, {
      method: 'POST',
      body: {
        season_id: farm?.activeSeasonId ?? null,
        source: 'farmer',
        category: 'Farmer report',
        description: description.trim(),
        severity: 'moderate',
      },
    });
    await refreshFarmland(farmId);
  }, [farmlands, refreshFarmland]);

  const updateProblemStatus = useCallback(async (farmId: string, problemId: string, status: ProblemStatus) => {
    await apiRequest<ProblemDto>(`/farmlands/${encodeURIComponent(farmId)}/problems/${encodeURIComponent(problemId)}`, {
      method: 'PATCH', body: { status },
    });
    await refreshFarmland(farmId);
  }, [refreshFarmland]);

  const updateGrowthStage = useCallback(async (farmId: string, stageId: string) => {
    await apiRequest(`/farmlands/${encodeURIComponent(farmId)}/state/growth-stage`, {
      method: 'PATCH', body: { growth_stage_id: stageId },
    });
    await refreshFarmland(farmId);
  }, [refreshFarmland]);

  const refreshConversations = useCallback(async (farmId: string) => {
    const summaries = await listConversations(farmId);
    setConversations(current => ({
      ...current,
      [farmId]: summaries.map(summary => ({
        id: summary.id,
        title: summary.title || 'New chat',
        messages: current[farmId]?.find(item => item.id === summary.id)?.messages ?? [],
        updatedAt: new Date(summary.updated_at).getTime() || Date.now(),
      })),
    }));
    const selectedId = summaries[0]?.id;
    setActiveConversationIds(current => ({ ...current, [farmId]: selectedId }));
    if (selectedId) {
      const detail = await getConversation(farmId, selectedId);
      const thread = mapChatDetail(detail);
      setConversations(current => ({
        ...current,
        [farmId]: (current[farmId] ?? []).map(item => item.id === thread.id ? thread : item),
      }));
    }
  }, []);

  const createConversation = useCallback(async (farmId: string) => {
    const detail = await createRemoteConversation(farmId);
    const thread = mapChatDetail(detail);
    setConversations(current => ({ ...current, [farmId]: [thread, ...(current[farmId] ?? [])] }));
    setActiveConversationIds(current => ({ ...current, [farmId]: thread.id }));
    return thread.id;
  }, []);

  const selectConversation = useCallback(async (farmId: string, conversationId: string) => {
    setActiveConversationIds(current => ({ ...current, [farmId]: conversationId }));
    const detail = await getConversation(farmId, conversationId);
    const thread = mapChatDetail(detail);
    setConversations(current => ({
      ...current,
      [farmId]: (current[farmId] ?? []).map(item => item.id === conversationId ? thread : item),
    }));
  }, []);

  const addChatMessage = useCallback(async (farmId: string, conversationId: string, text: string, clientRequestId: string) => {
    const response = await sendRemoteMessage(farmId, conversationId, text.trim(), clientRequestId);
    const farmerMessage = mapChatMessage(response.farmer_message);
    const assistantMessage = mapChatMessage(response.assistant_message);
    const now = new Date(response.assistant_message.created_at).getTime() || Date.now();
    setConversations(current => ({
      ...current,
      [farmId]: (current[farmId] ?? []).map(thread => {
        if (thread.id !== conversationId) return thread;
        const firstMessage = thread.messages.length === 0;
        const title = text.trim().replace(/\s+/g, ' ');
        return {
          ...thread,
          title: firstMessage ? (title.length > 40 ? `${title.slice(0, 40)}…` : title) : thread.title,
          messages: [...thread.messages, farmerMessage, assistantMessage],
          updatedAt: now,
        };
      }),
    }));
  }, []);

  const value = useMemo<AppContextType>(() => ({
    user,
    profile,
    authLoading,
    dataLoading,
    loadError,
    farmlands,
    login,
    register,
    logout,
    refreshProfile,
    refreshFarmland,
    createFarmland,
    updateFarmland,
    updateFarmerProfile,
    addTask,
    updateTaskStatus,
    addCheckIn,
    addProblem,
    updateProblemStatus,
    updateGrowthStage,
    conversations,
    activeConversationIds,
    refreshConversations,
    createConversation,
    selectConversation,
    addChatMessage,
  }), [
    user, profile, authLoading, dataLoading, loadError, farmlands, login, register, logout,
    refreshProfile, refreshFarmland, createFarmland, updateFarmland, updateFarmerProfile,
    addTask, updateTaskStatus, addCheckIn, addProblem, updateProblemStatus, updateGrowthStage,
    conversations, activeConversationIds, refreshConversations, createConversation, selectConversation, addChatMessage,
  ]);

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}

export function useAppContext() {
  const context = useContext(AppContext);
  if (!context) throw new Error('useAppContext must be used within AppProvider');
  return context;
}
