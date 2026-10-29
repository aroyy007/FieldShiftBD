import type { M5OfflineRecord, M5OfflineStorage } from './m5-offline-core';

/** Fails closed on runtimes without a platform persistence adapter. */
export const m5OfflineStorage: M5OfflineStorage = {
  async get<T>(_key: string): Promise<M5OfflineRecord<T> | null> {
    throw new Error('Offline storage is unavailable on this device.');
  },
  async put<T>(_record: M5OfflineRecord<T>): Promise<void> {
    throw new Error('Offline storage is unavailable on this device.');
  },
  async remove(_key: string): Promise<void> {
    throw new Error('Offline storage is unavailable on this device.');
  },
  async list(): Promise<M5OfflineRecord[]> {
    throw new Error('Offline storage is unavailable on this device.');
  },
};
