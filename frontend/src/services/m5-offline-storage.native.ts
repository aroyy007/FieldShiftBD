import * as SQLite from 'expo-sqlite';
import type { M5OfflineRecord, M5OfflineStorage, M5OfflineRecordType } from './m5-offline-core';

type StoredRecord = {
  key: string;
  accountId: string;
  farmId: string;
  type: M5OfflineRecordType;
  value: string;
  updatedAt: string;
};

let databasePromise: Promise<SQLite.SQLiteDatabase> | null = null;

async function database(): Promise<SQLite.SQLiteDatabase> {
  databasePromise ??= SQLite.openDatabaseAsync('fieldshift-m5-offline.db').then(async db => {
    await db.execAsync(`
      PRAGMA journal_mode = WAL;
      CREATE TABLE IF NOT EXISTS m5_offline_records (
        key TEXT PRIMARY KEY NOT NULL,
        account_id TEXT NOT NULL,
        farm_id TEXT NOT NULL,
        record_type TEXT NOT NULL,
        value_json TEXT NOT NULL,
        updated_at TEXT NOT NULL
      );
      CREATE INDEX IF NOT EXISTS ix_m5_offline_account_farm
        ON m5_offline_records(account_id, farm_id, record_type);
    `);
    return db;
  });
  return databasePromise;
}

function mapRecord<T>(row: StoredRecord): M5OfflineRecord<T> | null {
  try {
    return {
      key: row.key,
      accountId: row.accountId,
      farmId: row.farmId,
      type: row.type,
      value: JSON.parse(row.value) as T,
      updatedAt: row.updatedAt,
    };
  } catch {
    return null;
  }
}

export const m5OfflineStorage: M5OfflineStorage = {
  async get<T>(key: string): Promise<M5OfflineRecord<T> | null> {
    const db = await database();
    const row = await db.getFirstAsync<StoredRecord>(
      `SELECT key, account_id AS accountId, farm_id AS farmId,
              record_type AS type, value_json AS value, updated_at AS updatedAt
       FROM m5_offline_records WHERE key = ?`,
      [key],
    );
    if (!row) return null;
    const record = mapRecord<T>(row);
    if (!record) await this.remove(key);
    return record;
  },

  async put<T>(record: M5OfflineRecord<T>): Promise<void> {
    const db = await database();
    await db.runAsync(
      `INSERT INTO m5_offline_records(key, account_id, farm_id, record_type, value_json, updated_at)
       VALUES (?, ?, ?, ?, ?, ?)
       ON CONFLICT(key) DO UPDATE SET account_id = excluded.account_id,
         farm_id = excluded.farm_id, record_type = excluded.record_type,
         value_json = excluded.value_json, updated_at = excluded.updated_at`,
      [record.key, record.accountId, record.farmId, record.type, JSON.stringify(record.value), record.updatedAt],
    );
  },

  async remove(key: string): Promise<void> {
    const db = await database();
    await db.runAsync('DELETE FROM m5_offline_records WHERE key = ?', [key]);
  },

  async list(): Promise<M5OfflineRecord[]> {
    const db = await database();
    const rows = await db.getAllAsync<StoredRecord>(
      `SELECT key, account_id AS accountId, farm_id AS farmId,
              record_type AS type, value_json AS value, updated_at AS updatedAt
       FROM m5_offline_records ORDER BY updated_at ASC`,
    );
    const records = rows.map(row => mapRecord(row)).filter((item): item is M5OfflineRecord => item !== null);
    if (records.length !== rows.length) {
      const validKeys = new Set(records.map(record => record.key));
      for (const row of rows) if (!validKeys.has(row.key)) await this.remove(row.key);
    }
    return records;
  },
};
