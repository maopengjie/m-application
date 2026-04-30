import { requestClient } from "./request";

/**
 * 获取价格对比数据
 */
export async function getPriceComparisonApi(productId: number | string) {
  return requestClient.get(`/prices/compare/${productId}`);
}

/**
 * 获取价格趋势
 */
export async function getPriceTrendApi(productId: number | string, range: string = "30d") {
  return requestClient.get(`/prices/trend/${productId}`, { params: { range } });
}

/**
 * 获取历史最低价
 */
export async function getHistoryLowApi(productId: number | string) {
  return requestClient.get(`/prices/history-low/${productId}`);
}
