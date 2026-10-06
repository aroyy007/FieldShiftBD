import type { Task, TaskScheduleState } from '../data/demo';

const DHAKA_UTC_OFFSET = '+06:00';

function dhakaDateKey(date: Date) {
  return new Intl.DateTimeFormat('en-CA', {
    timeZone: 'Asia/Dhaka',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  }).format(date);
}

export function getTaskScheduleState(
  task: Pick<Task, 'status' | 'dueAt'>,
  asOf = new Date(),
): TaskScheduleState {
  if (task.status !== 'pending') return task.status;
  if (!task.dueAt) return 'unscheduled';

  const dueAt = new Date(task.dueAt);
  if (Number.isNaN(dueAt.getTime())) return 'unscheduled';
  if (dueAt.getTime() <= asOf.getTime()) return 'overdue';
  if (dhakaDateKey(dueAt) === dhakaDateKey(asOf)) return 'due';
  return 'upcoming';
}

export function taskDueAtForDhakaDate(dateText: string): string | null {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(dateText)) return null;

  const [year, month, day] = dateText.split('-').map(Number);
  const calendarDate = new Date(Date.UTC(year, month - 1, day));
  if (
    calendarDate.getUTCFullYear() !== year
    || calendarDate.getUTCMonth() !== month - 1
    || calendarDate.getUTCDate() !== day
  ) {
    return null;
  }

  return new Date(`${dateText}T23:59:59.999${DHAKA_UTC_OFFSET}`).toISOString();
}

export function formatDhakaDate(value: string | null): string {
  if (!value) return 'No date';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return 'No date';
  return new Intl.DateTimeFormat('en-BD', {
    timeZone: 'Asia/Dhaka',
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  }).format(date);
}
