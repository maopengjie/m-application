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
