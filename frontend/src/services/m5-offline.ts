import { M5OfflineRepository } from './m5-offline-core';
import { m5OfflineStorage } from './m5-offline-storage';

export const m5Offline = new M5OfflineRepository(m5OfflineStorage);
