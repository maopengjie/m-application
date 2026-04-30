import { requestClient } from "#/api/request";

/**
 * AI 智能情报相关接口
 */

/**
 * 手动触发 AI 参数提取
 */
export async function extractProductSpecsApi(productId: number, url: string) {
  return requestClient.post(`/intelligence/extract-specs/${productId}`, { url });
}

/**
 * 触发评论情感分析
 */
export async function analyzeReviewsApi(skuId: number) {
  return requestClient.post(`/intelligence/analyze-reviews/${skuId}`);
}

/**
 * 获取全网比价结果
 */
export async function getPriceComparisonApi(productId: number) {
  return requestClient.get<any>(`/intelligence/price-comparison/${productId}`);
}

/**
 * 获取库存分析与补货预测
 */
export async function getInventoryAnalysisApi(skuId: number) {
  return requestClient.get<any>(`/intelligence/inventory-analysis/${skuId}`);
}

/**
 * 获取动态定价建议
 */
export async function getPricingAdviceApi(productId: number) {
  return requestClient.get<any>(`/intelligence/pricing-advice/${productId}`);
}

/**
 * 获取 AI 综合情报研判综述
 */
export async function getProductInsightApi(productId: number) {
  return requestClient.get<any>(`/intelligence/product-insight/${productId}`);
}

/**
 * 获取全网实时市场快报
 */
export async function getMarketInsightsApi(limit: number = 20) {
  return requestClient.get<any>("/intelligence/market-insights", { params: { limit } });
}
