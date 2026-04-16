import type { Product, PriceHistoryStats } from './types';
import { requestClient } from './request';

export interface SearchParams {
  q: string;
  sort_by?: string;
  platforms?: string[];
  min_price?: number;
  max_price?: number;
  brand?: string;
  category?: string;
  page?: number;
  page_size?: number;
}

export interface SearchResponse {
  items: Product[];
  total: number;
}

/**
 * 搜索产品
 */
export async function searchProductsApi(params: SearchParams) {
  return requestClient.get<SearchResponse>('/search', { params });
}

/**
 * 获取产品详情
 */
export async function getProductDetailApi(id: string | number) {
  return requestClient.get<Product>(`/products/${id}`);
}

/**
 * 获取产品列表 (兼容旧调用)
 */
export async function getProductListApi(params?: Partial<SearchParams>) {
  return requestClient.get<Product[]>('/products', { params });
}

/**
 * 获取 SKU 历史价格
 */
export async function getSkuPriceHistoryApi(skuId: string | number, days: number = 30) {
  return requestClient.get<PriceHistoryStats>(`/products/skus/${skuId}/history`, {
    params: { days },
  });
}
