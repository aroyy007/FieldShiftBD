import { apiRequest } from './api-client';
import type { RotationCompareRequest, RotationComparisonV2 } from '../modules/shared/contracts-v2.generated';

export function loadRegionalComparison(farmlandId: string, request: RotationCompareRequest, signal?: AbortSignal) {
  return apiRequest<RotationComparisonV2>(`/advisor/v2/farmlands/${encodeURIComponent(farmlandId)}/rotation-comparisons`, {
    method: 'POST', body: request, signal,
  });
}
