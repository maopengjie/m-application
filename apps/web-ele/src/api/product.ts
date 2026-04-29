import type { PriceHistoryStats, Product, ProductDetailResponse, UserFollow } from "./types";

import { requestClient } from "./request";

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
  return requestClient.get<SearchResponse>("/search", { params });
}

/**
 * 获取产品详情
 */
export async function getProductDetailApi(id: number | string) {
  return requestClient.get<ProductDetailResponse>(`/products/${id}`);
}

/**
 * 获取产品列表 (兼容旧调用)
 */
export async function getProductListApi(params?: Partial<SearchParams>) {
  return requestClient.get<Product[]>("/products", { params });
}

/**
 * 获取 SKU 历史价格
 */
export async function getSkuPriceHistoryApi(skuId: number | string, days: number = 30) {
  return requestClient.get<PriceHistoryStats>(`/products/skus/${skuId}/history`, {
    params: { days },
  });
}

/**
 * 获取替代商品
 */
export async function getAlternativesApi(productId: number | string, limit: number = 5) {
  return requestClient.get<Product[]>(`/products/${productId}/alternatives`, {
    params: { limit },
  });
}

/**
 * 关注商品
 */
export async function followProductApi(productId: number | string) {
  return requestClient.post(`/products/${productId}/follow`);
}

/**
 * 取消关注商品
 */
export async function unfollowProductApi(productId: number | string) {
  return requestClient.delete(`/products/${productId}/follow`);
}

/**
 * 获取关注列表
 */
export async function getFollowListApi() {
  return requestClient.get<UserFollow[]>("/products/follows");
}
