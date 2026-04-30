import type { Coupon } from "./types";

import { requestClient } from "./request";

/**
 * 获取优惠券列表
 */
export async function getCouponsApi() {
  return requestClient.get<Coupon[]>("/coupons");
}
