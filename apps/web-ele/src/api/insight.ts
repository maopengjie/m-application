import type { InsightResponse } from "./types";

import { requestClient } from "./request";

/**
 * 获取商品异动聚合列表 (G2-02)
 */
export async function getAggregatedInsightsApi() {
  return requestClient.get<InsightResponse>("/insights");
}
