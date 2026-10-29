export type OfflineChatMessage = {
  id: string;
  text: string;
  sender: 'farmer' | 'assistant';
  timestamp: string;
};

export type QueuedChatMessage = {
  accountId: string;
  farmId: string;
  conversationId: string | null;
  clientRequestId: string;
  text: string;
  createdAt: string;
  retryCount?: number;
  nextAttemptAt?: string;
  deliveryState?: 'queued' | 'needs_attention';
  attentionReason?: 'backend_rejected' | 'retry_limit';
};

export type OfflineConsent = {
  decision: 'granted';
  policyVersion: string;
  capturedAt: string;
  synchronized: boolean;
};

export type M5OfflineRecordType = 'conversation' | 'queued_message' | 'consent';

export type M5OfflineRecord<T = unknown> = {
  key: string;
  accountId: string;
  farmId: string;
  type: M5OfflineRecordType;
  value: T;
  updatedAt: string;
};

export interface M5OfflineStorage {
  get<T>(key: string): Promise<M5OfflineRecord<T> | null>;
  put<T>(record: M5OfflineRecord<T>): Promise<void>;
  remove(key: string): Promise<void>;
  list(): Promise<M5OfflineRecord[]>;
}

export type CachedConversation = {
  id: string;
  title: string;
  messages: OfflineChatMessage[];
  updatedAt: number;
};

const CONSENT_FARM_SCOPE = '__account__';
const MAX_CHAT_LENGTH = 4000;
const MAX_QUEUED_MESSAGES_PER_FARM = 50;
const MAX_CACHED_CONVERSATIONS_PER_FARM = 5;
const MAX_CACHED_MESSAGES_PER_CONVERSATION = 200;
const OFFLINE_RETENTION_MS = 30 * 24 * 60 * 60 * 1000;
const RETRY_BASE_MS = 2_000;
const RETRY_MAX_MS = 5 * 60 * 1000;
const MAX_RETRY_ATTEMPTS = 8;

export function isRetryableQueuedFailure(status: number | undefined, message: string): boolean {
  if (status === undefined) return message.includes('Could not connect to the backend');
  return status === 408 || status === 429 || status >= 500;
}

function assertScope(accountId: string, farmId: string): void {
  if (!accountId.trim() || !farmId.trim()) throw new Error('Account and farm are required for offline data.');
}

function scopedKey(type: string, accountId: string, farmId: string, id: string): string {
  return [type, accountId, farmId, id].map(part => encodeURIComponent(part)).join(':');
}

export class M5OfflineRepository {
  private readonly storage: M5OfflineStorage;
  private readonly now: () => Date;

  constructor(storage: M5OfflineStorage, now = () => new Date()) {
    this.storage = storage;
    this.now = now;
  }

  async saveConversation(accountId: string, farmId: string, conversation: CachedConversation): Promise<void> {
    assertScope(accountId, farmId);
    const now = this.now();
    const cutoff = now.getTime() - OFFLINE_RETENTION_MS;
    const existing = await this.storage.list();
    const expired = existing.filter(record =>
      record.accountId === accountId
      && record.farmId === farmId
      && record.type !== 'consent'
      && Date.parse(record.updatedAt) < cutoff,
    );
    await Promise.all(expired.map(record => this.storage.remove(record.key)));
    await this.storage.put({
      key: scopedKey('conversation', accountId, farmId, conversation.id),
      accountId,
      farmId,
      type: 'conversation',
      value: {
        ...conversation,
        messages: conversation.messages.slice(-MAX_CACHED_MESSAGES_PER_CONVERSATION),
      },
      updatedAt: now.toISOString(),
    });
    const conversations = (await this.storage.list())
      .filter(record => record.accountId === accountId && record.farmId === farmId && record.type === 'conversation')
      .sort((left, right) => right.updatedAt.localeCompare(left.updatedAt));
    await Promise.all(conversations.slice(MAX_CACHED_CONVERSATIONS_PER_FARM).map(record => this.storage.remove(record.key)));
  }

  async latestConversation(accountId: string, farmId: string): Promise<CachedConversation | null> {
    assertScope(accountId, farmId);
    const records = await this.storage.list();
    const cutoff = this.now().getTime() - OFFLINE_RETENTION_MS;
    await Promise.all(records
      .filter(record => record.accountId === accountId && record.farmId === farmId
        && record.type === 'conversation' && Date.parse(record.updatedAt) < cutoff)
      .map(record => this.storage.remove(record.key)));
    const latest = records
      .filter(record => record.accountId === accountId && record.farmId === farmId
        && record.type === 'conversation' && Date.parse(record.updatedAt) >= cutoff)
      .sort((left, right) => right.updatedAt.localeCompare(left.updatedAt))[0];
    return (latest?.value as CachedConversation | undefined) ?? null;
  }

  async grantOfflineConsent(accountId: string, policyVersion: string): Promise<void> {
    if (!accountId.trim() || !policyVersion.trim()) throw new Error('Account and consent policy are required.');
    const capturedAt = this.now().toISOString();
    await this.storage.put({
      key: scopedKey('consent', accountId, CONSENT_FARM_SCOPE, 'offline_storage'),
      accountId,
      farmId: CONSENT_FARM_SCOPE,
      type: 'consent',
      value: { decision: 'granted', policyVersion, capturedAt, synchronized: false } satisfies OfflineConsent,
      updatedAt: capturedAt,
    });
  }

  async offlineConsent(accountId: string): Promise<OfflineConsent | null> {
    if (!accountId.trim()) return null;
    const record = await this.storage.get<OfflineConsent>(
      scopedKey('consent', accountId, CONSENT_FARM_SCOPE, 'offline_storage'),
    );
    return record?.value ?? null;
  }

  async markConsentSynchronized(accountId: string): Promise<void> {
    const consent = await this.offlineConsent(accountId);
    if (!consent || consent.synchronized) return;
    await this.storage.put({
      key: scopedKey('consent', accountId, CONSENT_FARM_SCOPE, 'offline_storage'),
      accountId,
      farmId: CONSENT_FARM_SCOPE,
      type: 'consent',
      value: { ...consent, synchronized: true },
      updatedAt: this.now().toISOString(),
    });
  }

  async enqueueMessage(input: QueuedChatMessage): Promise<void> {
    assertScope(input.accountId, input.farmId);
    const text = input.text.trim();
    if (!input.clientRequestId.trim() || !text || text.length > MAX_CHAT_LENGTH || !Number.isFinite(Date.parse(input.createdAt))) {
      throw new Error('Offline chat message is invalid or too long.');
    }
    const key = scopedKey('queued_message', input.accountId, input.farmId, input.clientRequestId);
    const existing = await this.storage.get<QueuedChatMessage>(key);
    if (existing) {
      if (existing.value.text !== text) throw new Error('This offline request ID already belongs to another message.');
      return;
    }
    const pending = await this.queuedMessages(input.accountId, input.farmId);
    if (pending.length >= MAX_QUEUED_MESSAGES_PER_FARM) {
      throw new Error('The offline message queue is full. Connect to send saved messages before adding another.');
    }
    const record: QueuedChatMessage = { ...input, text };
    await this.storage.put({
      key,
      accountId: input.accountId,
      farmId: input.farmId,
      type: 'queued_message',
      value: record,
      updatedAt: this.now().toISOString(),
    });
  }

  async attachConversation(accountId: string, farmId: string, clientRequestId: string, conversationId: string): Promise<void> {
    assertScope(accountId, farmId);
    const key = scopedKey('queued_message', accountId, farmId, clientRequestId);
    const record = await this.storage.get<QueuedChatMessage>(key);
    if (!record) return;
    await this.storage.put({
      ...record,
      value: { ...record.value, conversationId },
      updatedAt: this.now().toISOString(),
    });
  }

  async queuedMessages(accountId: string, farmId: string): Promise<QueuedChatMessage[]> {
    assertScope(accountId, farmId);
    const records = await this.storage.list();
    const cutoff = this.now().getTime() - OFFLINE_RETENTION_MS;
    const matching = records.filter(record => record.accountId === accountId
      && record.farmId === farmId && record.type === 'queued_message');
    const expired = matching.filter(record => {
      const value = record.value as QueuedChatMessage;
      return !Number.isFinite(Date.parse(value.createdAt)) || Date.parse(value.createdAt) < cutoff;
    });
    await Promise.all(expired.map(record => this.storage.remove(record.key)));
    return matching
      .filter(record => !expired.includes(record))
      .map(record => record.value as QueuedChatMessage)
      .sort((left, right) => left.createdAt.localeCompare(right.createdAt));
  }

  async recordRetry(accountId: string, farmId: string, clientRequestId: string): Promise<QueuedChatMessage | null> {
    assertScope(accountId, farmId);
    const key = scopedKey('queued_message', accountId, farmId, clientRequestId);
    const record = await this.storage.get<QueuedChatMessage>(key);
    if (!record) return null;
    if (record.value.deliveryState === 'needs_attention') return record.value;
    const retryCount = (record.value.retryCount ?? 0) + 1;
    const exhausted = retryCount >= MAX_RETRY_ATTEMPTS;
    const delay = Math.min(RETRY_MAX_MS, RETRY_BASE_MS * (2 ** Math.min(retryCount - 1, 16)));
    const updated: QueuedChatMessage = {
      ...record.value,
      retryCount,
      deliveryState: exhausted ? 'needs_attention' : 'queued',
    };
    if (exhausted) {
      updated.attentionReason = 'retry_limit';
      delete updated.nextAttemptAt;
    } else {
      delete updated.attentionReason;
      updated.nextAttemptAt = new Date(this.now().getTime() + delay).toISOString();
    }
    await this.storage.put({ ...record, value: updated, updatedAt: this.now().toISOString() });
    return updated;
  }

  async markNeedsAttention(
    accountId: string,
    farmId: string,
    clientRequestId: string,
    reason: 'backend_rejected' | 'retry_limit',
  ): Promise<QueuedChatMessage | null> {
    assertScope(accountId, farmId);
    const key = scopedKey('queued_message', accountId, farmId, clientRequestId);
    const record = await this.storage.get<QueuedChatMessage>(key);
    if (!record) return null;
    const updated: QueuedChatMessage = { ...record.value, deliveryState: 'needs_attention', attentionReason: reason };
    delete updated.nextAttemptAt;
    await this.storage.put({ ...record, value: updated, updatedAt: this.now().toISOString() });
    return updated;
  }

  async acknowledgeMessage(accountId: string, farmId: string, clientRequestId: string): Promise<void> {
    assertScope(accountId, farmId);
    await this.storage.remove(scopedKey('queued_message', accountId, farmId, clientRequestId));
  }

  async removeQueuedMessage(accountId: string, farmId: string, clientRequestId: string): Promise<void> {
    await this.acknowledgeMessage(accountId, farmId, clientRequestId);
  }

  async clearAccount(accountId: string): Promise<void> {
    if (!accountId.trim()) return;
    const records = await this.storage.list();
    await Promise.all(records.filter(record => record.accountId === accountId).map(record => this.storage.remove(record.key)));
  }

  async clearFarm(accountId: string, farmId: string): Promise<void> {
    assertScope(accountId, farmId);
    const records = await this.storage.list();
    await Promise.all(records
      .filter(record => record.accountId === accountId && record.farmId === farmId)
      .map(record => this.storage.remove(record.key)));
  }

  async clearOtherAccounts(activeAccountId: string): Promise<void> {
    if (!activeAccountId.trim()) return;
    const records = await this.storage.list();
    await Promise.all(records.filter(record => record.accountId !== activeAccountId).map(record => this.storage.remove(record.key)));
  }
}
