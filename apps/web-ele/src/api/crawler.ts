import { requestClient } from "./request";

/**
 * 获取爬虫任务详情
 */
export async function getCrawlerTasksApi() {
  return requestClient.get<any[]>("/crawler/tasks");
}

/**
 * 触发价格更新
 */
export async function triggerPriceUpdateApi() {
  return requestClient.post("/crawler/trigger-update");
}

/**
 * 获取平台健康快照
 */
export async function getPlatformHealthApi() {
  return requestClient.get<any[]>("/crawler/platform-health");
}

/**
 * 获取健康趋势数据
 */
export async function getHealthTrendsApi(days = 7) {
  return requestClient.get<any>("/crawler/platform-health/trends", {
    params: { days },
  });
}

/**
 * 获取全局巡检汇总
 */
export async function getSmokeStatusApi() {
  return requestClient.get<any>("/crawler/smoke-status");
}

/**
 * 获取具体采集到的数据列表
 */
export async function getScraperResultsApi(params?: {
  limit?: number;
  platform?: string;
  skip?: number;
}) {
  return requestClient.get<any[]>("/crawler/results", { params });
}
