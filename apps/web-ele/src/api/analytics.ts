import { requestClient } from "./request";

/**
 * 核心埋点事件名称定义 (M1-01)
 */
export const AnalyticsEvents = {
  SEARCH_TRIGGERED: "search_triggered", // 首页或搜索栏发起搜索
  SEARCH_RESULT_CLICK: "search_result_click", // 搜索结果页点击商品
  PRODUCT_DETAIL_VIEW: "product_detail_view", // 进入详情页
  BUY_BUTTON_CLICK: "buy_button_click", // 详情页点击“去购买”
  ALERT_CREATED: "alert_created", // 详情页创建提醒
  ALERT_RETURN_CLICK: "alert_return_click", // 提醒列表点击回访详情
  PRODUCT_FOLLOW: "product_follow", // 关注商品
  PRODUCT_UNFOLLOW: "product_unfollow", // 取消关注
  FOLLOW_LIST_DETAIL_CLICK: "follow_list_detail_click", // 关注列表点击详情
  INSIGHT_PAGE_VIEW: "insight_page_view", // 访问异动聚合页
  INSIGHT_EVENT_CLICK: "insight_event_click", // 点击聚合页中的单条异动
} as const;

/**
 * 上报埋点事件
 */
export async function logAnalyticsEventApi(
  eventName: string,
  properties: Record<string, any> = {},
) {
  return requestClient.post("/analytics/events", {
    event_name: eventName,
    properties,
  });
}

/**
 * 获取指标看板数据 (M1-07)
 */
export async function getAnalyticsDashboardApi(days: number = 7) {
  return requestClient.get("/analytics/dashboard", {
    params: { days },
  });
}
