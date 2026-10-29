import { apiRequest } from '@/services/api-client';
import type { ApiError } from './contracts.generated';
import type { FoundationAvailability } from './runtime';

export type ChallengeApiError = ApiError;

export const challengeApi = {
  getAvailability(): Promise<FoundationAvailability> {
    return apiRequest<FoundationAvailability>('/challenge/foundation/availability');
  },
};

/** Shared request helper for module-local typed endpoint functions. */
export function challengeRequest<TResponse, TRequest = never>(
  path: string,
  init?: { method?: 'GET' | 'POST' | 'PATCH' | 'DELETE'; body?: TRequest },
): Promise<TResponse> {
  return apiRequest<TResponse>(path, {
    method: init?.method ?? 'GET',
    ...(init?.body === undefined ? {} : { body: init.body as Record<string, unknown> }),
  });
}
