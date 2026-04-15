import { requestClient } from './request';

/**
 * 获取 SKU 决策建议
 */
export async function getSkuDecisionApi(skuId: string | number) {
  return requestClient.get(`/decisions/${skuId}`);
}
