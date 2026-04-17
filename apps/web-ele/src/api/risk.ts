import { requestClient } from "./request";

/**
 * 获取风险中心 feed
 */
export async function getRisksApi() {
  return requestClient.get<any[]>("/risks");
}

/**
 * 扫描商品链接风险
 */
export async function scanProductRiskApi(url: string) {
  return requestClient.post<any>("/risks/scan", null, { params: { product_url: url } });
}
