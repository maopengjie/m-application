import { requestClient } from './request';

/**
 * 搜索产品
 */
export async function searchProductsApi(params: { q: string; page?: number; page_size?: number }) {
  return requestClient.get('/search', { params });
}

/**
 * 获取产品详情
 */
export async function getProductDetailApi(id: string | number) {
  return requestClient.get(`/products/${id}`);
}

/**
 * 获取产品列表 (兼容旧调用)
 */
export async function getProductListApi(params?: any) {
  return requestClient.get('/products', { params });
}
