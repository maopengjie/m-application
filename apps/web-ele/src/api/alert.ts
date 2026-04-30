import { requestClient } from "./request";

/**
 * 创建降价提醒
 */
export async function createPriceAlertApi(data: {
  email?: string;
  notify_methods?: string;
  phone?: string;
  sku_id: number;
  target_price: number;
  user_id?: number;
}) {
  return requestClient.post("/alerts", data);
}

/**
 * 获取提醒列表
 */
export async function getPriceAlertsApi(userId: number = 1) {
  return requestClient.get("/alerts", { params: { user_id: userId } });
}

/**
 * 删除提醒
 */
export async function deletePriceAlertApi(id: number | string) {
  return requestClient.delete(`/alerts/${id}`);
}
