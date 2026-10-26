import { apiRequest } from './api-client';

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

export async function listConversations(farmlandId: string): Promise<ConversationSummary[]> {
  return apiRequest<ConversationSummary[]>(`/farmlands/${encodeURIComponent(farmlandId)}/conversations`);
}

export async function getConversation(farmlandId: string, conversationId: string): Promise<ConversationDetail> {
  return apiRequest<ConversationDetail>(`/farmlands/${encodeURIComponent(farmlandId)}/conversations/${encodeURIComponent(conversationId)}`);
}

export async function createConversation(farmlandId: string, title?: string): Promise<ConversationDetail> {
  return apiRequest<ConversationDetail>(`/farmlands/${encodeURIComponent(farmlandId)}/conversations`, {
    method: 'POST',
    body: { title },
  });
}

export async function sendMessage(
  farmlandId: string,
  conversationId: string,
  message: string,
  clientRequestId: string,
): Promise<ChatResponsePayload> {
  return apiRequest<ChatResponsePayload>(`/farmlands/${encodeURIComponent(farmlandId)}/conversations/${encodeURIComponent(conversationId)}/messages`, {
    method: 'POST',
    body: { message, message_type: 'text', client_request_id: clientRequestId },
  });
}
