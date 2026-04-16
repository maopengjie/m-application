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
  final_price?: number;
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
  created_at: string;
  sku?: ProductSKU & {
    product: {
      name: string;
      main_image: string;
    }
  };
}
