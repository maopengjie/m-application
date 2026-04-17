import { requestClient } from "./request";

/**
 * 获取风险中心 feed
 */
export async function getRisksApi() {
  return requestClient.get<any[]>("/risks");
}
