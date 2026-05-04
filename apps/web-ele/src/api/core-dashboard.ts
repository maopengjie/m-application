import { requestClient } from '#/api/request';

export interface DashboardCapturePoint {
  active_sku_count: number;
  success_rate: number;
  timestamp: string;
}

export interface DashboardAlertItem {
  current_price: number;
  detected_at: string;
  drop_percent: number;
  platform: string;
  previous_price: number;
  product_name: string;
  sku_id: string;
}

export interface DashboardPlatformBreakdownItem {
  platform: string;
  sku_count: number;
}

export interface CoreDashboardOverviewDto {
  active_sku_count: number;
  alert_items: DashboardAlertItem[];
  capture_timeline: DashboardCapturePoint[];
  platform_breakdown: DashboardPlatformBreakdownItem[];
  success_rate: number;
  total_price_records: number;
  total_sku_count: number;
}

export interface CoreDashboardOverview {
  activeSkuCount: number;
  alertItems: DashboardAlertItem[];
  captureTimeline: DashboardCapturePoint[];
  platformBreakdown: DashboardPlatformBreakdownItem[];
  successRate: number;
  totalPriceRecords: number;
  totalSkuCount: number;
}

function mapOverview(data: CoreDashboardOverviewDto): CoreDashboardOverview {
  return {
    activeSkuCount: data.active_sku_count,
    alertItems: data.alert_items,
    captureTimeline: data.capture_timeline,
    platformBreakdown: data.platform_breakdown,
    successRate: data.success_rate,
    totalPriceRecords: data.total_price_records,
    totalSkuCount: data.total_sku_count,
  };
}

export async function getCoreDashboardOverviewApi() {
  const data = await requestClient.get<CoreDashboardOverviewDto>('/core-dashboard/overview');
  return mapOverview(data);
}
