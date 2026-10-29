import type { M5OfflineRecord, M5OfflineStorage } from './m5-offline-core';

const DATABASE_NAME = 'fieldshift-m5-offline-v1';
const STORE_NAME = 'records';

function openDatabase(): Promise<IDBDatabase> {
  if (typeof indexedDB === 'undefined') return Promise.reject(new Error('Browser offline storage is unavailable.'));
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DATABASE_NAME, 1);
    request.onupgradeneeded = () => {
      const database = request.result;
      if (!database.objectStoreNames.contains(STORE_NAME)) {
        const store = database.createObjectStore(STORE_NAME, { keyPath: 'key' });
        store.createIndex('accountId', 'accountId', { unique: false });
        store.createIndex('accountFarm', ['accountId', 'farmId'], { unique: false });
      }
    };
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error ?? new Error('Could not open browser offline storage.'));
    request.onblocked = () => reject(new Error('Close other FieldShift tabs to open offline storage.'));
  });
}

function requestResult<T>(request: IDBRequest<T>): Promise<T> {
  return new Promise((resolve, reject) => {
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error ?? new Error('Browser offline storage request failed.'));
  });
}

function transactionDone(transaction: IDBTransaction): Promise<void> {
  return new Promise((resolve, reject) => {
    transaction.oncomplete = () => resolve();
    transaction.onerror = () => reject(transaction.error ?? new Error('Browser offline storage transaction failed.'));
    transaction.onabort = () => reject(transaction.error ?? new Error('Browser offline storage transaction was cancelled.'));
  });
}

export const m5OfflineStorage: M5OfflineStorage = {
  async get<T>(key: string): Promise<M5OfflineRecord<T> | null> {
    const database = await openDatabase();
    const transaction = database.transaction(STORE_NAME, 'readonly');
    const done = transactionDone(transaction);
    try {
      const result = await requestResult(transaction.objectStore(STORE_NAME).get(key) as IDBRequest<M5OfflineRecord<T> | undefined>);
      await done;
      return result ?? null;
    } finally {
      database.close();
    }
  },

  async put<T>(record: M5OfflineRecord<T>): Promise<void> {
    const database = await openDatabase();
    const transaction = database.transaction(STORE_NAME, 'readwrite');
    const done = transactionDone(transaction);
    try {
      transaction.objectStore(STORE_NAME).put(record);
      await done;
    } finally {
      database.close();
    }
  },

  async remove(key: string): Promise<void> {
    const database = await openDatabase();
    const transaction = database.transaction(STORE_NAME, 'readwrite');
    const done = transactionDone(transaction);
    try {
      transaction.objectStore(STORE_NAME).delete(key);
      await done;
    } finally {
      database.close();
    }
  },

  async list(): Promise<M5OfflineRecord[]> {
    const database = await openDatabase();
    const transaction = database.transaction(STORE_NAME, 'readonly');
    const done = transactionDone(transaction);
    try {
      const records = await requestResult(transaction.objectStore(STORE_NAME).getAll() as IDBRequest<M5OfflineRecord[]>);
      await done;
      return records;
    } finally {
      database.close();
    }
  },
};
