import assert from 'node:assert/strict';
import { test } from 'node:test';
import { isRetryableQueuedFailure, M5OfflineRepository } from './m5-offline-core.ts';

class MemoryStorage {
  records = new Map();
  async get(key) { return this.records.get(key) ?? null; }
  async put(record) { this.records.set(record.key, structuredClone(record)); }
  async remove(key) { this.records.delete(key); }
  async list() { return [...this.records.values()].map(record => structuredClone(record)); }
}

function repository() {
  const storage = new MemoryStorage();
  const clock = { value: new Date('2026-10-29T08:00:00.000Z') };
  return { storage, clock, repo: new M5OfflineRepository(storage, () => clock.value) };
}

test('offline conversations are isolated by signed-in account and selected farm', async () => {
  const { repo } = repository();
  const history = { id: 'conversation-a', title: 'North field', messages: [], updatedAt: 10 };
  await repo.saveConversation('account-a', 'farm-a', history);
  await repo.saveConversation('account-b', 'farm-a', { ...history, id: 'conversation-b' });
  await repo.saveConversation('account-a', 'farm-b', { ...history, id: 'conversation-c' });

  assert.equal((await repo.latestConversation('account-a', 'farm-a')).id, 'conversation-a');
  assert.equal((await repo.latestConversation('account-b', 'farm-a')).id, 'conversation-b');
  assert.equal(await repo.latestConversation('account-a', 'farm-c'), null);
});

test('offline queue preserves idempotency and binds records to account and farm', async () => {
  const { repo } = repository();
  const queued = {
    accountId: 'account-a', farmId: 'farm-a', conversationId: null,
    clientRequestId: 'request-001', text: 'আগামীকাল বৃষ্টি হবে?', createdAt: '2026-10-29T08:00:00Z',
  };
  await repo.enqueueMessage(queued);
  await repo.enqueueMessage(queued);
  await repo.enqueueMessage({ ...queued, accountId: 'account-b' });

  assert.equal((await repo.queuedMessages('account-a', 'farm-a')).length, 1);
  assert.equal((await repo.queuedMessages('account-b', 'farm-a')).length, 1);
  await assert.rejects(repo.enqueueMessage({ ...queued, text: 'different message' }), /another message/);

  await repo.attachConversation('account-a', 'farm-a', 'request-001', 'conversation-1');
  assert.equal((await repo.queuedMessages('account-a', 'farm-a'))[0].conversationId, 'conversation-1');
  await repo.acknowledgeMessage('account-a', 'farm-a', 'request-001');
  assert.equal((await repo.queuedMessages('account-a', 'farm-a')).length, 0);
  assert.equal((await repo.queuedMessages('account-b', 'farm-a')).length, 1);
});

test('offline storage requires a valid message and an explicit persisted consent record', async () => {
  const { repo } = repository();
  assert.equal(await repo.offlineConsent('account-a'), null);
  await assert.rejects(repo.enqueueMessage({
    accountId: 'account-a', farmId: 'farm-a', conversationId: null,
    clientRequestId: 'request-002', text: '  ', createdAt: '2026-10-29T08:00:00Z',
  }), /invalid or too long/);

  await repo.grantOfflineConsent('account-a', '2026-10-v1');
  assert.equal((await repo.offlineConsent('account-a')).synchronized, false);
  await repo.markConsentSynchronized('account-a');
  assert.equal((await repo.offlineConsent('account-a')).synchronized, true);
  assert.equal(await repo.offlineConsent('account-b'), null);
});

test('account switch removes inactive records and logout cleanup removes all account records', async () => {
  const { storage, repo } = repository();
  await repo.grantOfflineConsent('account-a', '2026-10-v1');
  await repo.saveConversation('account-a', 'farm-a', { id: 'c-a', title: 'A', messages: [], updatedAt: 1 });
  await repo.saveConversation('account-b', 'farm-b', { id: 'c-b', title: 'B', messages: [], updatedAt: 2 });

  await repo.clearOtherAccounts('account-a');
  assert.equal((await storage.list()).some(record => record.accountId === 'account-b'), false);
  assert.equal((await repo.latestConversation('account-a', 'farm-a')).id, 'c-a');
  await repo.clearAccount('account-a');
  assert.equal((await storage.list()).length, 0);
});

test('offline cache bounds conversation history and expires old farm records', async () => {
  const { repo, clock } = repository();
  await repo.saveConversation('account-a', 'farm-a', {
    id: 'conversation-a', title: 'North field',
    messages: Array.from({ length: 250 }, (_, index) => ({
      id: `message-${index}`, text: `message ${index}`, sender: 'farmer', timestamp: '08:00 AM',
    })),
    updatedAt: clock.value.getTime(),
  });
  assert.equal((await repo.latestConversation('account-a', 'farm-a')).messages.length, 200);
  await repo.enqueueMessage({
    accountId: 'account-a', farmId: 'farm-a', conversationId: null,
    clientRequestId: 'old-request', text: 'old', createdAt: clock.value.toISOString(),
  });
  clock.value = new Date('2026-11-29T08:00:00.001Z');
  assert.equal(await repo.latestConversation('account-a', 'farm-a'), null);
  assert.equal((await repo.queuedMessages('account-a', 'farm-a')).length, 0);
});

test('offline queue has a per-farm limit and retries use persisted exponential backoff', async () => {
  const { repo, clock } = repository();
  for (let index = 0; index < 50; index += 1) {
    await repo.enqueueMessage({
      accountId: 'account-a', farmId: 'farm-a', conversationId: null,
      clientRequestId: `request-${index}`, text: `message ${index}`, createdAt: clock.value.toISOString(),
    });
  }
  await assert.rejects(repo.enqueueMessage({
    accountId: 'account-a', farmId: 'farm-a', conversationId: null,
    clientRequestId: 'request-over-limit', text: 'extra', createdAt: clock.value.toISOString(),
  }), /queue is full/);

  const first = await repo.recordRetry('account-a', 'farm-a', 'request-0');
  assert.equal(first.retryCount, 1);
  assert.equal(first.nextAttemptAt, '2026-10-29T08:00:02.000Z');
  clock.value = new Date(first.nextAttemptAt);
  const second = await repo.recordRetry('account-a', 'farm-a', 'request-0');
  assert.equal(second.retryCount, 2);
  assert.equal(second.nextAttemptAt, '2026-10-29T08:00:06.000Z');
});

test('offline retries stop after the cap and rejected messages can be removed individually', async () => {
  const { repo, clock } = repository();
  const first = {
    accountId: 'account-a', farmId: 'farm-a', conversationId: null,
    clientRequestId: 'retry-cap', text: 'will eventually stop', createdAt: clock.value.toISOString(),
  };
  await repo.enqueueMessage(first);
  for (let attempt = 0; attempt < 8; attempt += 1) {
    const updated = await repo.recordRetry(first.accountId, first.farmId, first.clientRequestId);
    if (updated.nextAttemptAt) clock.value = new Date(updated.nextAttemptAt);
  }
  const capped = (await repo.queuedMessages(first.accountId, first.farmId))[0];
  assert.equal(capped.retryCount, 8);
  assert.equal(capped.deliveryState, 'needs_attention');
  assert.equal(capped.attentionReason, 'retry_limit');
  assert.equal(capped.nextAttemptAt, undefined);
  assert.equal((await repo.recordRetry(first.accountId, first.farmId, first.clientRequestId)).retryCount, 8);

  await repo.enqueueMessage({ ...first, clientRequestId: 'permanent-rejection', text: 'rejected message' });
  await repo.markNeedsAttention(first.accountId, first.farmId, 'permanent-rejection', 'backend_rejected');
  await repo.removeQueuedMessage(first.accountId, first.farmId, 'permanent-rejection');
  assert.deepEqual((await repo.queuedMessages(first.accountId, first.farmId)).map(item => item.clientRequestId), ['retry-cap']);
});

test('offline queue retries transient statuses but parks permanent request failures', () => {
  assert.equal(isRetryableQueuedFailure(undefined, 'Could not connect to the backend. Check that it is running.'), true);
  assert.equal(isRetryableQueuedFailure(undefined, 'Could not read your sign-in session.'), false);
  assert.equal(isRetryableQueuedFailure(408, 'timeout'), true);
  assert.equal(isRetryableQueuedFailure(429, 'rate limited'), true);
  assert.equal(isRetryableQueuedFailure(503, 'unavailable'), true);
  assert.equal(isRetryableQueuedFailure(400, 'invalid message'), false);
  assert.equal(isRetryableQueuedFailure(401, 'sign in again'), false);
  assert.equal(isRetryableQueuedFailure(422, 'message rejected'), false);
});

test('clearing one farm removes its cache and queue without affecting another farm', async () => {
  const { repo } = repository();
  await repo.saveConversation('account-a', 'farm-a', { id: 'a', title: 'A', messages: [], updatedAt: 1 });
  await repo.saveConversation('account-a', 'farm-b', { id: 'b', title: 'B', messages: [], updatedAt: 2 });
  await repo.enqueueMessage({
    accountId: 'account-a', farmId: 'farm-a', conversationId: null,
    clientRequestId: 'request-a', text: 'queued', createdAt: '2026-10-29T08:00:00Z',
  });

  await repo.clearFarm('account-a', 'farm-a');

  assert.equal(await repo.latestConversation('account-a', 'farm-a'), null);
  assert.equal((await repo.queuedMessages('account-a', 'farm-a')).length, 0);
  assert.equal((await repo.latestConversation('account-a', 'farm-b')).id, 'b');
});
