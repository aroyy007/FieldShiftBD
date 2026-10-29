import type { JsonValue, ProposedAction, TaskDiffOperation } from '../shared/contracts.generated';

type TaskSnapshot = Record<string, JsonValue>;

const SNAPSHOT_FIELDS = ['status', 'title', 'description', 'due_at', 'priority', 'updated_at'] as const;

export function actionConfirmationKeyId(
  actionId: string,
  version: number,
  decision: 'confirm' | 'reject',
): string {
  return `${actionId}:${version}:${decision}`;
}

function isRecord(value: JsonValue | null | undefined): value is TaskSnapshot {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function snapshotFor(action: ProposedAction, change: TaskDiffOperation): TaskSnapshot | null {
  if (!change.task_id) return null;
  const precondition = action.preconditions.find(item =>
    item.kind === 'task_state_matches' && item.subject === change.task_id,
  );
  return isRecord(precondition?.expected_value) ? precondition.expected_value : null;
}

function hasCompleteSnapshot(snapshot: TaskSnapshot | null): snapshot is TaskSnapshot {
  return snapshot !== null && SNAPSHOT_FIELDS.every(field => Object.hasOwn(snapshot, field));
}

function displayDate(value: JsonValue | null | undefined): string {
  if (value == null) return 'not scheduled';
  if (typeof value !== 'string') return String(value);
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? value : parsed.toLocaleString();
}

function displayValue(value: JsonValue | null | undefined): string {
  if (value == null || value === '') return 'empty';
  return typeof value === 'string' ? value : JSON.stringify(value);
}

export function canReviewTaskChange(action: ProposedAction, change: TaskDiffOperation): boolean {
  if (change.operation === 'create') return Boolean(change.title?.trim());
  const snapshot = snapshotFor(action, change);
  if (!hasCompleteSnapshot(snapshot) || snapshot.status !== 'pending') return false;
  if (change.operation !== 'update') return true;
  return change.title != null || change.description != null || change.due_at != null || change.priority != null;
}

export function isActionReviewable(action: ProposedAction): boolean {
  return action.task_diff.operations.length > 0
    && action.task_diff.operations.every(change => canReviewTaskChange(action, change));
}

export function summarizeTaskChange(action: ProposedAction, change: TaskDiffOperation): string {
  if (change.operation === 'create') {
    const details = [`title: ${change.title ?? 'New task'}`];
    if (change.description != null) details.push(`description: ${change.description}`);
    if (change.due_at != null) details.push(`due: ${displayDate(change.due_at)}`);
    if (change.priority != null) details.push(`priority: ${change.priority}`);
    return `Add task (${details.join('; ')})`;
  }

  const snapshot = snapshotFor(action, change);
  if (!hasCompleteSnapshot(snapshot)) return `Task ${change.task_id ?? 'unknown'} cannot be reviewed safely`;
  const title = displayValue(snapshot.title);
  if (change.operation === 'complete') return `Complete “${title}” (pending → completed)`;
  if (change.operation === 'cancel') return `Cancel “${title}” (pending → cancelled)`;

  const changes: string[] = [];
  if (change.title != null) changes.push(`title: ${displayValue(snapshot.title)} → ${change.title}`);
  if (change.description != null) changes.push(`description: ${displayValue(snapshot.description)} → ${change.description}`);
  if (change.due_at != null) changes.push(`due: ${displayDate(snapshot.due_at)} → ${displayDate(change.due_at)}`);
  if (change.priority != null) changes.push(`priority: ${displayValue(snapshot.priority)} → ${change.priority}`);
  return `Update “${title}” (${changes.join('; ')})`;
}
