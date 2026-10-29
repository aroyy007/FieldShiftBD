import type {
  ActionExecutionReceipt,
  AdaptiveRecommendation,
  DistrictClimateBundle,
  DiseaseProblemSyncReceipt,
  DiseaseProblemSyncRequest,
  FarmProfileSnapshot,
  PlantingWindowAdvisory,
  ProposedAction,
  RotationComparison,
  TaskDiff,
} from './contracts.generated';

export type Availability = 'available' | 'unavailable' | 'stale' | 'conflict';

export interface FarmProfileSnapshotPort {
  getSnapshot(farmerId: string, farmlandId: string): Promise<FarmProfileSnapshot>;
}

export interface ClimateBundlePort {
  getBundle(districtCode: string, asOf: string): Promise<DistrictClimateBundle>;
}

export interface AdvisoryPort {
  advise(snapshot: FarmProfileSnapshot, bundle: DistrictClimateBundle, cropCode: string): Promise<PlantingWindowAdvisory>;
  compareRotation(snapshot: FarmProfileSnapshot): Promise<RotationComparison>;
  evaluateAdaptation(snapshot: FarmProfileSnapshot, question: string): Promise<AdaptiveRecommendation>;
}

export interface ActionConfirmationPort {
  propose(action: ProposedAction): Promise<ProposedAction>;
  confirm(input: {
    farmerId: string;
    actionId: string;
    expectedVersion: number;
    idempotencyKey: string;
    decision: 'confirm' | 'reject';
  }): Promise<ActionExecutionReceipt>;
}

export interface TaskDiffOwnerPort {
  apply(input: {
    farmerId: string;
    farmlandId: string;
    seasonId: string | null;
    taskDiff: TaskDiff;
  }): Promise<{ appliedReferences: string[] }>;
}

export interface DeferredDiseaseSyncPort {
  requestSync(request: DiseaseProblemSyncRequest): Promise<DiseaseProblemSyncReceipt>;
}

export interface CachePort<T> {
  read(key: string): Promise<T | null>;
  write(key: string, value: T): Promise<void>;
  remove(key: string): Promise<void>;
}

export interface OutboxPort<T> {
  enqueue(item: T): Promise<void>;
  listPending(): Promise<T[]>;
  acknowledge(id: string): Promise<void>;
}

export interface ConsentPort {
  request(purpose: string): Promise<'granted' | 'denied'>;
}

export interface SpeechPort {
  readonly availability: Availability;
  speak(text: string, language: 'bn' | 'en'): Promise<Availability>;
  stop(): Promise<void>;
}
