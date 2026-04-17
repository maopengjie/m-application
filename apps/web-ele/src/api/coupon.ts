import { requestClient } from "./request";
import type { Coupon } from "./types";

/**
 * 获取优惠券列表
 */
export async function getCouponsApi() {
  return requestClient.get<Coupon[]>("/coupons");
}
