import type {
  ActionExecutionReceipt,
  ConsentRecordInput,
  ProposedAction,
} from '../modules/shared/contracts.generated';

export type M5ActionRequest = {
  method?: string;
  headers?: Record<string, string>;
  body?: Record<string, unknown>;
};

export type M5ActionRequester = <T>(path: string, options?: M5ActionRequest) => Promise<T>;

export function createM5ActionApi(request: M5ActionRequester) {
  return {
    listPendingActions(farmlandId: string): Promise<ProposedAction[]> {
      return request<ProposedAction[]>(`/farmlands/${encodeURIComponent(farmlandId)}/actions/pending`);
    },

    confirmAction(
      farmlandId: string,
      action: ProposedAction,
      decision: 'confirm' | 'reject',
      idempotencyKey: string,
    ): Promise<ActionExecutionReceipt> {
      if (action.farmland_id !== farmlandId || action.status !== 'awaiting_confirmation') {
        throw new Error('This action is no longer available for the selected farm. Refresh and review it again.');
      }
      return request<ActionExecutionReceipt>(
        `/farmlands/${encodeURIComponent(farmlandId)}/actions/${encodeURIComponent(action.action_id)}/confirm`,
        {
          method: 'POST',
          body: {
            expected_version: action.version,
            idempotency_key: idempotencyKey,
            decision,
          },
        },
      );
    },

    recordConsent(consent: ConsentRecordInput, idempotencyKey: string): Promise<{ consent_record_id: string }> {
      return request<{ consent_record_id: string }>('/challenge/consents', {
        method: 'POST',
        headers: { 'Idempotency-Key': idempotencyKey },
        body: consent,
      });
    },
  };
}
