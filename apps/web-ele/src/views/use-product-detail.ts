import type { ComputedRef, Ref } from "vue";

import type { DecisionResult, Product, ProductSKU } from "#/api/types";

import { computed, onMounted, ref } from "vue";

import { ElMessage } from "element-plus";

import { createPriceAlertApi } from "#/api/alert";
import { getSkuDecisionApi } from "#/api/decision";
import { getProductDetailApi } from "#/api/product";

export interface AlertProduct {
  id: number;
  name?: string;
  image?: string;
  title?: string;
  price?: number;
  min_price?: number;
  final_price?: number;
}

interface AlertSubmitData {
  sku_id?: number;
  targetPrice: number;
  notifyMethods: string[];
  email: string;
  phone: string;
}

interface UseProductDetailResult {
  alertDialogVisible: Ref<boolean>;
  decision: Ref<DecisionResult | null>;
  decisionError: Ref<null | string>;
  decisionLoading: Ref<boolean>;
  error: Ref<null | string>;
  handleAlertSubmit: (data: AlertSubmitData) => Promise<void>;
  handleBuy: () => void;
  handleCreateAlert: (shop: ProductSKU) => void;
  handleCreateAlertForSelectedSku: () => void;
  handleImageError: (event: Event) => void;
  handleRetry: () => void;
  handleRetryDecision: () => void;
  handleSelectSku: (sku: ProductSKU) => void;
  loading: Ref<boolean>;
  priceComparisonText: ComputedRef<string>;
  priceTrendText: ComputedRef<string>;
  product: Ref<null | Product>;
  ratingText: ComputedRef<string>;
  riskLevel: ComputedRef<"high" | "low" | "medium">;
  risksList: ComputedRef<string[]>;
  selectedShop: Ref<AlertProduct | null>;
  selectedSku: ComputedRef<null | ProductSKU>;
  selectedSkuId: Ref<null | number>;
}

export function useProductDetail(productId: string): UseProductDetailResult {
  const loading = ref(true);
  const error = ref<null | string>(null);
  const product = ref<null | Product>(null);
  const decision = ref<DecisionResult | null>(null);
  const alertDialogVisible = ref(false);
  const selectedShop = ref<AlertProduct | null>(null);
  const selectedSkuId = ref<null | number>(null);

  const selectedSku = computed<null | ProductSKU>(() => {
    if (!product.value) return null;
    if (!selectedSkuId.value) return product.value.skus[0] || null;
    return (
      product.value.skus.find((sku) => sku.id === selectedSkuId.value) ||
      product.value.skus[0] ||
      null
    );
  });

  const riskLevel = computed<"high" | "low" | "medium">(() => {
    const score = selectedSku.value?.risk_score?.score;
    if (score === undefined) return "low";
    if (score < 40) return "high";
    if (score < 70) return "medium";
    return "low";
  });

  const risksList = computed(() => {
    const riskScore = selectedSku.value?.risk_score;
    const list: string[] = [];
    if (!riskScore) return list;

    if (riskScore.comment_abnormal) list.push("评价内容疑似异常 (AI 识别)");
    if (riskScore.sales_abnormal) list.push("销量波动显著异常");
    if (riskScore.price_abnormal) list.push("近期价格剧烈跳变");
    if (riskScore.rating_low) list.push("商家整体评分偏低");

    if (riskScore.details && riskScore.details.length > 0) {
      list.push(...riskScore.details);
    }

    return list;
  });

  const priceComparisonText = computed(() => {
    if (!product.value || !selectedSku.value) return "分析中...";
    const prices = product.value.skus.map((sku) => sku.final_price || sku.price);
    const minPrice = Math.min(...prices);
    const maxPrice = Math.max(...prices);
    const currentPrice = selectedSku.value.final_price || selectedSku.value.price;

    if (currentPrice <= minPrice) return "全网最低";
    if (maxPrice === minPrice) return "均价水平";

    const rank = (maxPrice - currentPrice) / (maxPrice - minPrice);
    return `优于 ${(rank * 100).toFixed(0)}% 平台`;
  });

  const priceTrendText = computed(() => {
    if (!decision.value) return "分析中...";
    if (decision.value.history_score >= 90) return "历史低价";
    if (decision.value.history_score >= 70) return "近期较优";
    if (decision.value.history_score >= 40) return "阶段平台";
    return "价格上行";
  });

  const ratingText = computed(() => {
    if (product.value?.rating) {
      return `${(product.value.rating * 20).toFixed(0)}%`;
    }
    if (!decision.value) return "96%";
    return `${Math.max(90, Math.min(100, decision.value.risk_score + 8))}%`;
  });

  const decisionLoading = ref(false);
  const decisionError = ref<null | string>(null);

  const fetchDecision = async (skuId: number) => {
    decisionLoading.value = true;
    decisionError.value = null;
    try {
      decision.value = await getSkuDecisionApi(skuId);
    } catch (error_: unknown) {
      const errMsg = error_ instanceof Error ? error_.message : "决策分析请求失败";
      console.error("Failed to fetch decision:", error_);
      decisionError.value = errMsg;
      decision.value = null;
    } finally {
      decisionLoading.value = false;
    }
  };

  const handleRetryDecision = () => {
    if (selectedSkuId.value) {
      void fetchDecision(selectedSkuId.value);
    }
  };

  const handleSelectSku = (sku: ProductSKU) => {
    selectedSkuId.value = sku.id;
    void fetchDecision(sku.id);
  };

  const fetchDetail = async () => {
    if (!productId) return;

    loading.value = true;
    error.value = null;
    try {
      const result = await getProductDetailApi(productId);
      product.value = result;

      const initialSku = result.skus?.[0];
      if (initialSku) {
        if (!selectedSkuId.value) {
          selectedSkuId.value = initialSku.id;
        }
        if (selectedSkuId.value) {
          await fetchDecision(selectedSkuId.value);
        }
      }
    } catch (error_: unknown) {
      const errMsg = error_ instanceof Error ? error_.message : "网络请求失败，请尝试刷新重试";
      console.error("Fetch detail error:", error_);
      error.value = errMsg;
    } finally {
      loading.value = false;
    }
  };

  const handleRetry = () => {
    void fetchDetail();
  };

  const handleCreateAlert = (shop: ProductSKU) => {
    selectedShop.value = {
      id: shop.id,
      name: product.value?.name,
      image: product.value?.main_image,
      title: product.value?.name,
      price: shop.price,
      min_price: shop.price,
      final_price: shop.final_price,
    };
    alertDialogVisible.value = true;
  };

  const handleCreateAlertForSelectedSku = () => {
    if (selectedSku.value) {
      handleCreateAlert(selectedSku.value);
    }
  };

  const handleAlertSubmit = async (data: AlertSubmitData) => {
    try {
      await createPriceAlertApi({
        sku_id: data.sku_id || selectedSku.value?.id || 0,
        target_price: data.targetPrice,
        notify_methods: data.notifyMethods.join(","),
        email: data.email,
        phone: data.phone,
      });
      ElMessage.success(`提醒设置成功！当价格降至 ¥${data.targetPrice} 时将通知您`);
    } catch (error_: unknown) {
      const errMsg = error_ instanceof Error ? error_.message : "设置提醒失败";
      ElMessage.error(errMsg);
    }
  };

  const handleBuy = () => {
    const url = selectedSku.value?.buy_url;
    if (url) {
      window.open(url, "_blank");
    } else {
      ElMessage.warning("购买链接暂不可用");
    }
  };

  const handleImageError = (event: Event) => {
    const target = event.target as HTMLImageElement;
    target.src = "https://via.placeholder.com/600x600?text=Image+Not+Found";
  };

  onMounted(() => {
    void fetchDetail();
  });

  return {
    alertDialogVisible,
    decision,
    decisionError,
    decisionLoading,
    error,
    handleAlertSubmit,
    handleBuy,
    handleCreateAlert,
    handleCreateAlertForSelectedSku,
    handleImageError,
    handleRetry,
    handleRetryDecision,
    handleSelectSku,
    loading,
    priceComparisonText,
    priceTrendText,
    product,
    ratingText,
    riskLevel,
    risksList,
    selectedShop,
    selectedSku,
    selectedSkuId,
  };
}
