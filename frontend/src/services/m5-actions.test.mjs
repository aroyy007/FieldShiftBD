import assert from 'node:assert/strict';
import { test } from 'node:test';
import { createM5ActionApi } from './m5-actions-core.ts';
import { actionConfirmationKeyId, isActionReviewable, summarizeTaskChange } from '../modules/m5/action-summary.ts';

const action = {
  action_id: 'action/one',
  contract_version: '1.0.0',
  created_at: '2026-10-29T08:00:00Z',
  expires_at: '2026-10-30T08:00:00Z',
  farmer_id: 'account-1',
  farmland_id: 'farm/one',
  preconditions: [{ kind: 'farm_state_matches', subject: 'season.status', expected_value: 'active' }],
  required_consent_purposes: [],
  season_id: 'season-1',
  source_module: 'm5',
  status: 'awaiting_confirmation',
  task_diff: { operations: [{ operation: 'create', reference: 'task-1', title: 'Inspect field' }] },
  version: 4,
};

test('opposite decisions use separate idempotency intents while same-decision retries stay stable', () => {
  const confirmKeyId = actionConfirmationKeyId(action.action_id, action.version, 'confirm');
  const confirmRetryKeyId = actionConfirmationKeyId(action.action_id, action.version, 'confirm');
  const rejectKeyId = actionConfirmationKeyId(action.action_id, action.version, 'reject');

  assert.equal(confirmKeyId, confirmRetryKeyId);
  assert.notEqual(confirmKeyId, rejectKeyId);
});

test('confirmation sends the exact farm, action version, decision, and stable idempotency key', async () => {
  let request;
  const api = createM5ActionApi(async (url, options) => {
    request = { url, options };
    return { status: 'conflict', result: { code: 'version_changed' } };
  });

  const response = await api.confirmAction('farm/one', action, 'confirm', 'action-confirm-001');

  assert.equal(response.status, 'conflict');
  assert.equal(request.url, '/farmlands/farm%2Fone/actions/action%2Fone/confirm');
  assert.deepEqual(request.options.body, {
    expected_version: 4,
    idempotency_key: 'action-confirm-001',
    decision: 'confirm',
  });
});

test('confirmation fails closed when the displayed action belongs to a different farm or version state', async () => {
  let requests = 0;
  const api = createM5ActionApi(async () => { requests += 1; throw new Error('must not request'); });

  assert.throws(() => api.confirmAction('farm/two', action, 'confirm', 'action-confirm-002'), /selected farm/);
  assert.throws(() => api.confirmAction('farm/one', { ...action, status: 'expired' }, 'confirm', 'action-confirm-003'), /selected farm/);
  assert.equal(requests, 0);
});

test('declining a proposal sends the same captured version through the confirmation endpoint', async () => {
  let requestBody;
  const api = createM5ActionApi(async (_url, options) => {
    requestBody = options.body;
    return { status: 'rejected' };
  });

  await api.confirmAction('farm/one', action, 'reject', 'action-reject-001');

  assert.deepEqual(requestBody, {
    expected_version: 4,
    idempotency_key: 'action-reject-001',
    decision: 'reject',
  });
});

test('task updates read back the existing values and every proposed value', () => {
  const change = {
    operation: 'update', reference: 'task-update', task_id: 'task-1',
    title: 'Inspect north field', description: 'Check the new pump', priority: 'high',
  };
  const proposal = {
    ...action,
    preconditions: [{
      kind: 'task_state_matches', subject: 'task-1',
      expected_value: {
        status: 'pending', title: 'Inspect field', description: 'Check the pump',
        due_at: null, priority: 'normal', updated_at: '2026-10-29T08:00:00Z',
      },
    }],
    task_diff: { operations: [change] },
  };

  assert.equal(isActionReviewable(proposal), true);
  const summary = summarizeTaskChange(proposal, change);
  assert.match(summary, /Inspect field/);
  assert.match(summary, /Inspect north field/);
  assert.match(summary, /Check the pump/);
  assert.match(summary, /Check the new pump/);
  assert.match(summary, /normal/);
  assert.match(summary, /high/);
});

test('complete and cancel read back the task title and missing snapshots disable confirmation', () => {
  const snapshot = {
    status: 'pending', title: 'Inspect irrigation', description: null,
    due_at: null, priority: 'normal', updated_at: '2026-10-29T08:00:00Z',
  };
  const proposal = {
    ...action,
    preconditions: [{ kind: 'task_state_matches', subject: 'task-1', expected_value: snapshot }],
    task_diff: { operations: [{ operation: 'complete', reference: 'complete-1', task_id: 'task-1' }] },
  };
  assert.equal(isActionReviewable(proposal), true);
  assert.match(summarizeTaskChange(proposal, proposal.task_diff.operations[0]), /Inspect irrigation/);
  assert.match(summarizeTaskChange(proposal, proposal.task_diff.operations[0]), /pending → completed/);
  assert.equal(isActionReviewable({ ...proposal, preconditions: [] }), false);
});
