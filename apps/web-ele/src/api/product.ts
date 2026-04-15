import { requestClient } from './request';

/**
 * 获取产品列表
 */
export async function getProductListApi(params?: any) {
  return requestClient.get('/products', { params });
}

/**
 * 获取产品详情
 */
export async function getProductDetailApi(id: string | number) {
  return requestClient.get(`/products/${id}`);
}

/**
 * 搜索产品
 */
export async function searchProductsApi(keyword: string) {
  return requestClient.get('/products/search', { params: { keyword } });
}
