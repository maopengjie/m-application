import { requestClient } from './request';

/**
 * 获取采购建议
 */
export async function getPurchaseDecisionApi(productId: string | number) {
  return requestClient.get(`/decisions/purchase/${productId}`);
}

/**
 * 获取风险评估
 */
export async function getRiskAssessmentApi(productId: string | number) {
  return requestClient.get(`/decisions/risk/${productId}`);
}
