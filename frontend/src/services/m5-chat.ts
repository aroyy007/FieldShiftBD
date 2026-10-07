const API_BASE_URL = process.env.EXPO_PUBLIC_API_URL ?? 'http://localhost:8000';

type AccessTokenProvider = () => Promise<string | null>;
let accessTokenProvider: AccessTokenProvider = async () => null;

export function setM5AccessTokenProvider(provider: AccessTokenProvider) {
  accessTokenProvider = provider;
}

export type ChatMessageItem = {
  id: string;
  conversation_id: string;
  sender_type: 'farmer' | 'assistant' | 'system';
  message: string | null;
  message_type: 'text' | 'image' | 'system';
  attachment_key?: string | null;
  created_at: string;
};

export type ConversationSummary = {
  id: string;
  farmland_id: string;
  farmer_id: string;
  title: string | null;
  created_at: string;
  updated_at: string;
  message_count: number;
  last_message: string | null;
};

export type ConversationDetail = {
  id: string;
  farmland_id: string;
  farmer_id: string;
  title: string | null;
  created_at: string;
  updated_at: string;
  messages: ChatMessageItem[];
};

export type ChatResponsePayload = {
  conversation_id: string;
  farmer_message: ChatMessageItem;
  assistant_message: ChatMessageItem;
  intent: string;
  context_summary: {
    farmland_name: string;
    active_crop?: string | null;
    growth_stage?: string | null;
    pending_tasks_count: number;
    open_problems_count: number;
  };
  suggested_actions: string[];
};

async function authorizedFetch(path: string, init?: RequestInit): Promise<Response> {
  const token = await accessTokenProvider();
  const headers = new Headers(init?.headers);
  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }
  if (!headers.has('Content-Type') && init?.method && init.method !== 'GET') {
    headers.set('Content-Type', 'application/json');
  }
  return fetch(`${API_BASE_URL}${path}`, { ...init, headers });
}

export async function listConversations(farmlandId: string): Promise<ConversationSummary[]> {
  const res = await authorizedFetch(`/farmlands/${farmlandId}/conversations`);
  if (!res.ok) return [];
  return res.json();
}

export async function getConversation(farmlandId: string, conversationId: string): Promise<ConversationDetail | null> {
  const res = await authorizedFetch(`/farmlands/${farmlandId}/conversations/${conversationId}`);
  if (!res.ok) return null;
  return res.json();
}

export async function createConversation(farmlandId: string, title?: string): Promise<ConversationDetail | null> {
  const res = await authorizedFetch(`/farmlands/${farmlandId}/conversations`, {
    method: 'POST',
    body: JSON.stringify({ title }),
  });
  if (!res.ok) return null;
  return res.json();
}

export async function sendMessage(
  farmlandId: string,
  conversationId: string,
  message: string,
): Promise<ChatResponsePayload | null> {
  const res = await authorizedFetch(`/farmlands/${farmlandId}/conversations/${conversationId}/messages`, {
    method: 'POST',
    body: JSON.stringify({ message, message_type: 'text' }),
  });
  if (!res.ok) return null;
  return res.json();
}