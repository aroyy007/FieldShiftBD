import type { CachePort, ConsentPort, OutboxPort, SpeechPort } from './ports';

export type ChallengeFeature =
  | 'climate'
  | 'advisory'
  | 'rotation'
  | 'adaptive_decisions'
  | 'action_confirmation'
  | 'disease_problem_sync'
  | 'voice';

export type FeatureStatus = {
  enabled: boolean;
  adapter_ready: boolean;
};

export type FoundationAvailability = {
  contract_version: '1.0.0';
  offline_mode: boolean;
  features: Record<ChallengeFeature, FeatureStatus>;
};

export class FoundationUnavailableError extends Error {
  constructor(feature: string) {
    super(`The ${feature} capability is currently unavailable.`);
    this.name = 'FoundationUnavailableError';
  }
}

export class DisabledCache<T> implements CachePort<T> {
  async read(_key: string): Promise<T | null> {
    throw new FoundationUnavailableError('offline cache');
  }
  async write(_key: string, _value: T): Promise<void> {
    throw new FoundationUnavailableError('offline cache');
  }
  async remove(_key: string): Promise<void> {
    throw new FoundationUnavailableError('offline cache');
  }
}

export class DisabledOutbox<T> implements OutboxPort<T> {
  async enqueue(_item: T): Promise<void> {
    throw new FoundationUnavailableError('offline outbox');
  }
  async listPending(): Promise<T[]> {
    throw new FoundationUnavailableError('offline outbox');
  }
  async acknowledge(_id: string): Promise<void> {
    throw new FoundationUnavailableError('offline outbox');
  }
}

export class DeniedConsent implements ConsentPort {
  async request(_purpose: string): Promise<'denied'> {
    return 'denied';
  }
}

export class TapConsentAdapter implements ConsentPort {
  private readonly askForExplicitTap: (purpose: string) => Promise<boolean>;

  constructor(askForExplicitTap: (purpose: string) => Promise<boolean>) {
    this.askForExplicitTap = askForExplicitTap;
  }

  async request(purpose: string): Promise<'granted' | 'denied'> {
    return await this.askForExplicitTap(purpose) ? 'granted' : 'denied';
  }
}

export class DisabledSpeech implements SpeechPort {
  readonly availability = 'unavailable' as const;
  async speak(_text: string, _language: 'bn' | 'en'): Promise<'unavailable'> {
    return 'unavailable';
  }
  async stop(): Promise<void> {}
}

export type ConfirmationCardModel = {
  actionId: string;
  version: number;
  summary: string;
  consequences: string[];
  requiresExplicitTap: true;
  expiresAt: string;
};

export const defaultFoundationAdapters = {
  cache: new DisabledCache<unknown>(),
  outbox: new DisabledOutbox<unknown>(),
  consent: new DeniedConsent(),
  speech: new DisabledSpeech(),
} as const;
