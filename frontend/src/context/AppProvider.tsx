import React, { createContext, useContext, useState } from 'react';
import {
  ChatMessage,
  ChatThread,
  DEMO_CREDENTIALS,
  DEMO_FARMLANDS,
  FarmCheckIn,
  Farmland,
  FarmProblem,
  ProblemStatus,
  TaskStatus,
} from '../data/demo';

type AppContextType = {
  user: { name: string; phone: string } | null;
  login: (phone: string, pass: string) => boolean;
  logout: () => void;
  farmlands: Farmland[];
  addFarmland: (farm: Farmland) => void;
  addTask: (farmId: string, title: string, dueAt: string | null) => void;
  updateTaskStatus: (farmId: string, taskId: string, status: TaskStatus) => void;
  addCheckIn: (farmId: string, notes: string, observations: FarmCheckIn['observations']) => void;
  addProblem: (farmId: string, description: string) => void;
  updateProblemStatus: (farmId: string, problemId: string, status: ProblemStatus) => void;
  updateGrowthStage: (farmId: string, stageId: string) => void;
  conversations: Record<string, ChatThread[]>;
  activeConversationIds: Record<string, string | undefined>;
  createConversation: (farmId: string) => string;
  selectConversation: (farmId: string, conversationId: string) => void;
  addChatMessage: (farmId: string, conversationId: string, text: string) => void;
};

const AppContext = createContext<AppContextType | undefined>(undefined);

export function AppProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<{ name: string; phone: string } | null>(null);
  const [farmlands, setFarmlands] = useState<Farmland[]>(DEMO_FARMLANDS);
  const [conversations, setConversations] = useState<Record<string, ChatThread[]>>({});
  const [activeConversationIds, setActiveConversationIds] = useState<Record<string, string | undefined>>({});

  const login = (phone: string, pass: string) => {
    if (phone === DEMO_CREDENTIALS.phone && pass === DEMO_CREDENTIALS.password) {
      setUser({ name: 'Demo Farmer', phone });
      return true;
    }
    // Allow any signup through if they type something else, just for demo purposes
    if (phone && pass && phone !== DEMO_CREDENTIALS.phone) {
      setUser({ name: 'New Farmer', phone });
      return true;
    }
    return false;
  };

  const logout = () => {
    setUser(null);
  };

  const addFarmland = (farm: Farmland) => {
    setFarmlands(current => [...current, farm]);
  };

  const addTask = (farmId: string, title: string, dueAt: string | null) => {
    const task = {
      id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
      title: title.trim(),
      status: 'pending' as const,
      dueAt,
      priority: 'normal' as const,
      source: 'farmer' as const,
    };
    setFarmlands(current => current.map(farm =>
      farm.id === farmId ? { ...farm, tasks: [task, ...farm.tasks] } : farm,
    ));
  };

  const updateTaskStatus = (farmId: string, taskId: string, status: TaskStatus) => {
    setFarmlands(current => current.map(farm => farm.id !== farmId ? farm : {
      ...farm,
      tasks: farm.tasks.map(task => task.id === taskId ? { ...task, status } : task),
    }));
  };

  const addCheckIn = (
    farmId: string,
    notes: string,
    observations: FarmCheckIn['observations'],
  ) => {
    const now = new Date();
    const checkIn: FarmCheckIn = {
      id: `${now.getTime()}-${Math.random().toString(36).slice(2, 8)}`,
      at: now.toISOString(),
      notes: notes.trim(),
      stageName: farmlands.find(farm => farm.id === farmId)?.growthStage ?? 'Not set',
      observations,
    };
    setFarmlands(current => current.map(farm => farm.id === farmId
      ? { ...farm, checkIns: [checkIn, ...farm.checkIns] }
      : farm,
    ));
  };

  const addProblem = (farmId: string, description: string) => {
    const problem: FarmProblem = {
      id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
      category: 'Farmer report',
      description: description.trim(),
      source: 'farmer',
      severity: 'moderate',
      status: 'open',
      createdAt: new Date().toISOString(),
    };
    setFarmlands(current => current.map(farm => farm.id === farmId
      ? { ...farm, problems: [problem, ...farm.problems] }
      : farm,
    ));
  };

  const updateProblemStatus = (
    farmId: string,
    problemId: string,
    status: ProblemStatus,
  ) => {
    setFarmlands(current => current.map(farm => farm.id !== farmId ? farm : {
      ...farm,
      problems: farm.problems.map(problem => problem.id === problemId
        ? {
          ...problem,
          status,
          resolvedAt: status === 'resolved' ? new Date().toISOString() : undefined,
        }
        : problem,
      ),
    }));
  };

  const updateGrowthStage = (farmId: string, stageId: string) => {
    setFarmlands(current => current.map(farm => {
      if (farm.id !== farmId) return farm;
      const stageIndex = farm.seasonPlan.findIndex(stage => stage.id === stageId);
      if (stageIndex < 0) return farm;
      return {
        ...farm,
        currentGrowthStageId: stageId,
        growthStage: farm.seasonPlan[stageIndex].name,
        seasonPlan: farm.seasonPlan.map((stage, index) => ({
          ...stage,
          status: index < stageIndex ? 'completed' : index === stageIndex ? 'current' : 'upcoming',
        })),
      };
    }));
  };

  const createConversation = (farmId: string) => {
    const now = Date.now();
    const conversation: ChatThread = {
      id: `${now}-${Math.random().toString(36).slice(2, 8)}`,
      title: 'New chat',
      messages: [],
      updatedAt: now,
    };

    setConversations(current => ({
      ...current,
      [farmId]: [conversation, ...(current[farmId] ?? [])],
    }));
    setActiveConversationIds(current => ({ ...current, [farmId]: conversation.id }));
    return conversation.id;
  };

  const selectConversation = (farmId: string, conversationId: string) => {
    setActiveConversationIds(current => ({ ...current, [farmId]: conversationId }));
  };

  const addChatMessage = (farmId: string, conversationId: string, text: string) => {
    const now = Date.now();
    const message: ChatMessage = {
      id: `${now}-${Math.random().toString(36).slice(2, 8)}`,
      text,
      sender: 'farmer',
      timestamp: new Date(now).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' }),
    };

    setConversations(current => ({
      ...current,
      [farmId]: (current[farmId] ?? []).map(conversation => {
        if (conversation.id !== conversationId) return conversation;

        const isFirstMessage = conversation.messages.length === 0;
        const normalizedText = text.trim().replace(/\s+/g, ' ');
        const title = normalizedText.length > 40
          ? `${normalizedText.slice(0, 40)}...`
          : normalizedText;

        return {
          ...conversation,
          title: isFirstMessage ? title : conversation.title,
          messages: [...conversation.messages, message],
          updatedAt: now,
        };
      }),
    }));
  };

  return (
    <AppContext.Provider value={{
      user,
      login,
      logout,
      farmlands,
      addFarmland,
      addTask,
      updateTaskStatus,
      addCheckIn,
      addProblem,
      updateProblemStatus,
      updateGrowthStage,
      conversations,
      activeConversationIds,
      createConversation,
      selectConversation,
      addChatMessage,
    }}>
      {children}
    </AppContext.Provider>
  );
}

export function useAppContext() {
  const context = useContext(AppContext);
  if (!context) throw new Error('useAppContext must be used within AppProvider');
  return context;
}
