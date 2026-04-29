/**
 * 业务数据模型定义
 */

export interface RiskScore {
  score: number;
  comment_abnormal: boolean;
  sales_abnormal: boolean;
  price_abnormal: boolean;
  rating_low: boolean;
  details: string[];
  updated_at: string;
}

export interface Review {
  id: number;
  rating: number;
  content: string;
  sentiment_score?: number;
  sentiment_label?: string;
  created_at: string;
}

export interface Coupon {
  id: number;
  title: string;
  desc?: string;
  type: string;
  amount: number;
  condition_amount?: number;
}

export interface PriceHistoryItem {
  price: number;
  recorded_at: string;
}

export interface Promotion {
  title: string;
  desc?: string;
  amount: number;
  type: string;
}

export interface ProductSKU {
  id: number;
  product_id: number;
  platform: string;
  platform_sku_id: string;
  title: string;
  price: number;
  original_price?: number;
  shop_name?: string;
  buy_url?: string;
  is_official: boolean;
  final_price?: number;
  visual_hash?: string;
  last_screenshot?: string;
  promotions?: Promotion[];
  price_history?: PriceHistoryItem[];
  coupons?: Coupon[];
  reviews?: Review[];
  risk_score?: RiskScore;
}

export interface Product {
  id: number;
  product_id?: number; // Backend search returns product_id
  name: string;
  title?: string;
  brand?: string;
  category?: string;
  main_image?: string;
  image?: string; // Search schema uses image
  rating?: number;
  platform_count?: number;
  comments_count?: number;
  shop_name?: string;
  platform?: string;
  tags?: string[];
  price?: number;
  min_price?: number;
  original_price?: number;
  final_price?: number;
  ai_attributes?: Record<string, any>;
  skus: ProductSKU[];
  created_at?: string;
  updated_at?: string;
}

export interface DecisionResult {
  product_id: number;
  sku_id: number;
  score: number;
  suggestion: string;
  reason: string;
  confidence: number;
  price_score: number;
  history_score: number;
  coupon_score: number;
  risk_score: number;
  best_platform?: string;
  recommendation?: string;
  pros?: string[];
  cons?: string[];
  evidence_text?: string;
  evidence_delta_percent?: number;
  risk_text?: string;
  action_label?: string;
  action_type?: string;
  original_price?: number;
  final_price?: number;
  total_discount?: number;
  discount_details?: string[];
}

export interface PriceHistoryStats {
  history: PriceHistoryItem[];
  min_price: number;
  max_price: number;
  avg_price: number;
  current_price: number;
}

export interface PriceAlert {
  id: number;
  sku_id: number;
  target_price: number;
  is_triggered: boolean;
  status: string;
  triggered_at?: string;
  triggered_price?: number;
  current_price?: number;
  trigger_reason?: string;
  created_at: string;
  sku?: ProductSKU & {
    product: {
      main_image: string;
      name: string;
    };
    product_id: number;
  };
}

export interface ProductDetailResponse {
  product: Product;
  is_followed: boolean;
  is_alert_set: boolean;
  active_alert_count: number;
  revisit_summary?: {
    content: string;
    icon?: string;
    title: string;
    type: "info" | "success" | "warning";
  };
}

export interface UserFollow {
  id: number;
  user_id: number;
  product_id: number;
  product: Product;
  created_at: string;
  price_change_percent?: number;
  risk_status?: string;
  is_near_low?: boolean;
  current_status_text?: string;
}

export interface InsightEvent {
  id: string;
  product_id: number;
  sku_id?: number;
  event_type:
    | "ALERT_HIT"
    | "HIST_LOW"
    | "NEAR_TARGET"
    | "NEW_COUPON"
    | "PRICE_DROP"
    | "RISK_CHANGE";
  priority: number;
  title: string;
  description: string;
  current_price: number;
  original_price?: number;
  diff_amount?: number;
  diff_percent?: number;
  image?: string;
  platform?: string;
  timestamp: string;
  metadata: Record<string, any>;
}

export interface InsightResponse {
  events: InsightEvent[];
  total: number;
  summary: string;
}
