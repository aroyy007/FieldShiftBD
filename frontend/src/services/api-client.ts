const DEFAULT_API_BASE_URL = 'http://127.0.0.1:8000';
const ACCESS_TOKEN_KEY = 'fieldshift.access-token';

export const API_BASE_URL = (process.env.EXPO_PUBLIC_API_URL || DEFAULT_API_BASE_URL).replace(/\/+$/, '');

export class ApiClientError extends Error {
  status?: number;
  detail?: unknown;

  constructor(message: string, status?: number, detail?: unknown) {
    super(message);
    this.name = 'ApiClientError';
    this.status = status;
    this.detail = detail;
  }
}

type AccessTokenProvider = () => Promise<string | null>;
type ApiRequestOptions = Omit<RequestInit, 'body'> & {
  body?: BodyInit | Record<string, unknown> | null;
};

let accessTokenProvider: AccessTokenProvider = getStoredAccessToken;
let unauthorizedHandler: (() => void | Promise<void>) | null = null;

function browserStorage(): Storage | null {
  if (typeof document === 'undefined' || typeof window === 'undefined') return null;
  try {
    return window.sessionStorage;
  } catch {
    return null;
  }
}

export async function getStoredAccessToken(): Promise<string | null> {
  const storage = browserStorage();
  if (storage) return storage.getItem(ACCESS_TOKEN_KEY);

  const secureStore = await import('expo-secure-store');
  if (!await secureStore.isAvailableAsync()) return null;
  return secureStore.getItemAsync(ACCESS_TOKEN_KEY);
}

export async function saveAccessToken(token: string): Promise<void> {
  const storage = browserStorage();
  if (storage) {
    storage.setItem(ACCESS_TOKEN_KEY, token);
    return;
  }

  const secureStore = await import('expo-secure-store');
  if (!await secureStore.isAvailableAsync()) {
    throw new Error('Secure sign-in storage is unavailable on this device.');
  }
  await secureStore.setItemAsync(ACCESS_TOKEN_KEY, token);
}

export async function clearAccessToken(): Promise<void> {
  const storage = browserStorage();
  if (storage) {
    storage.removeItem(ACCESS_TOKEN_KEY);
    return;
  }

  const secureStore = await import('expo-secure-store');
  if (await secureStore.isAvailableAsync()) {
    await secureStore.deleteItemAsync(ACCESS_TOKEN_KEY);
  }
}

export function setApiAccessTokenProvider(provider: AccessTokenProvider): void {
  accessTokenProvider = provider;
}

export function setUnauthorizedHandler(handler: (() => void | Promise<void>) | null): void {
  unauthorizedHandler = handler;
}

function requestBody(body: ApiRequestOptions['body']): BodyInit | null | undefined {
  if (body == null || typeof body === 'string') return body;
  if (typeof FormData !== 'undefined' && body instanceof FormData) return body;
  if (typeof Blob !== 'undefined' && body instanceof Blob) return body;
  if (body instanceof URLSearchParams) return body;
  return JSON.stringify(body);
}

function isJsonBody(body: ApiRequestOptions['body']): boolean {
  if (body == null) return false;
  if (typeof FormData !== 'undefined' && body instanceof FormData) return false;
  if (typeof Blob !== 'undefined' && body instanceof Blob) return false;
  if (body instanceof URLSearchParams) return false;
  return true;
}

function errorMessage(detail: unknown, fallback: string): string {
  if (typeof detail === 'string' && detail.trim()) return detail;
  if (Array.isArray(detail)) {
    const messages = detail.map((item) => {
      if (typeof item === 'object' && item && 'msg' in item) return String(item.msg);
      return '';
    }).filter(Boolean);
    if (messages.length) return messages.join(' ');
  }
  if (detail && typeof detail === 'object' && 'message' in detail) {
    return String(detail.message);
  }
  return fallback;
}

export async function apiRequest<T>(path: string, options: ApiRequestOptions = {}): Promise<T> {
  const headers = new Headers(options.headers);
  headers.set('Accept', 'application/json');

  let token: string | null;
  try {
    token = await accessTokenProvider();
  } catch {
    throw new ApiClientError('Could not read your sign-in session. Please sign in again.');
  }
  if (token) headers.set('Authorization', `Bearer ${token}`);

  const body = requestBody(options.body);
  if (isJsonBody(options.body) && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }

  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path.startsWith('/') ? path : `/${path}`}`, {
      ...options,
      body,
      headers,
    });
  } catch {
    throw new ApiClientError('Could not connect to the backend. Check that it is running.');
  }

  const payload: unknown = await response.json().catch(() => null);
  if (!response.ok) {
    const detail = payload && typeof payload === 'object' && 'detail' in payload
      ? payload.detail
      : null;
    if (response.status === 401 && token && unauthorizedHandler) {
      await unauthorizedHandler();
    }
    throw new ApiClientError(
      errorMessage(detail, `The backend rejected the request (${response.status}).`),
      response.status,
      detail,
    );
  }

  return payload as T;
}
