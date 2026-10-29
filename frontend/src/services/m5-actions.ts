import { apiRequest } from './api-client';
import { createM5ActionApi } from './m5-actions-core';

const api = createM5ActionApi(apiRequest);

export const listPendingActions = api.listPendingActions;
export const confirmAction = api.confirmAction;
export const recordConsent = api.recordConsent;
