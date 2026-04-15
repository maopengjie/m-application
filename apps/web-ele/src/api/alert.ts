import { requestClient } from './request';

/**
 * 获取告警列表
 */
export async function getAlertListApi(params?: any) {
  return requestClient.get('/alerts', { params });
}

/**
 * 创建价格订阅告警
 */
export async function createPriceAlertApi(data: { productId: string | number; targetPrice: number }) {
  return requestClient.post('/alerts', data);
}

/**
 * 获取未读告警数
 */
export async function getUnreadAlertCountApi() {
  return requestClient.get('/alerts/unread-count');
}
