<script setup lang="ts">
import { useRoute } from "vue-router";

import { Page } from "@vben/common-ui";

import { ElButton, ElEmpty, ElTag } from "element-plus";

import AlertDialog from "#/components/AlertDialog.vue";
import CouponPanel from "#/components/CouponPanel.vue";
import DecisionCard from "#/components/DecisionCard.vue";
import PriceCompareTable from "#/components/PriceCompareTable.vue";
import PriceTrendChart from "#/components/PriceTrendChart.vue";
import RiskPanel from "#/components/RiskPanel.vue";
import { useProductDetail } from "#/views/use-product-detail";

const route = useRoute();
const productId = route.params.id as string;

const {
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
} = useProductDetail(productId);
</script>

<template>
  <Page
    :title="product?.name || '商品详情'"
    :description="product ? `品牌: ${product.brand || '未知'} | ID: ${product.id}` : ''"
  >
    <div v-loading="loading" class="min-h-[400px]">
      <div v-if="product" class="space-y-6">
        <!-- Header Section -->
        <div
          class="flex flex-col lg:flex-row gap-8 bg-white dark:bg-zinc-900 p-8 rounded-2xl shadow-sm border border-gray-100 dark:border-zinc-800"
        >
          <div class="w-full lg:w-96 flex-shrink-0">
            <img
              :src="product.main_image"
              :alt="product.name"
              class="w-full h-auto aspect-square object-contain rounded-xl border border-gray-100 dark:border-zinc-800 p-4 bg-white dark:bg-zinc-900"
              @error="handleImageError"
            />
          </div>

          <div class="flex-grow flex flex-col justify-between">
            <div>
              <div class="flex items-center gap-2 mb-3">
                <ElTag :type="selectedSku?.platform === 'JD' ? 'danger' : 'success'" effect="dark">
                  {{ selectedSku?.platform || "未知" }}
                </ElTag>
                <span class="text-gray-500 dark:text-zinc-400 text-sm">商品 ID: {{ product.id }}</span>
              </div>
              <h1 class="text-2xl font-bold text-gray-900 dark:text-zinc-100 leading-tight mb-4">
                {{ product.name }}
              </h1>

              <div class="flex items-baseline gap-4 mb-2">
                <span
                  class="text-xs font-bold text-red-500 bg-red-50 dark:bg-red-950/30 px-2 py-0.5 rounded"
                  >预计到手价</span>
                <span class="text-4xl font-black text-red-500">¥{{ selectedSku?.final_price || selectedSku?.price }}</span>
                <span v-if="selectedSku?.original_price" class="text-lg text-gray-400 line-through">¥{{ selectedSku.original_price }}</span>
              </div>

              <div v-if="selectedSku?.promotions?.length" class="flex flex-wrap gap-2 mb-6">
                <ElTag
                  v-for="(p, i) in selectedSku.promotions"
                  :key="i"
                  type="danger"
                  size="small"
                  effect="plain"
                >
                  {{ p.title }}
                </ElTag>
                <span class="text-xs text-gray-400 self-center">已省 ¥{{
                    (selectedSku.price - (selectedSku.final_price ?? selectedSku.price)).toFixed(2)
                  }}</span>
              </div>
              <div v-else class="mb-8">
                <span class="text-sm text-gray-500">当前价格: ¥{{ selectedSku?.price }}</span>
              </div>

              <div class="flex flex-wrap gap-4 mb-8">
                <ElButton
                  type="primary"
                  size="large"
                  icon="lucide--shopping-cart"
                  class="px-8 !rounded-xl"
                  @click="handleBuy"
                >
                  去购买
                </ElButton>
                <ElButton
                  size="large"
                  icon="lucide--bell"
                  class="px-8 !rounded-xl"
                  :disabled="!selectedSku"
                  @click="handleCreateAlertForSelectedSku"
                >
                  降价提醒
                </ElButton>
              </div>
            </div>

            <div class="border-t dark:border-zinc-800 pt-6 grid grid-cols-3 gap-4 text-center">
              <div>
                <div class="text-xs text-gray-400 dark:text-zinc-500 mb-1">同款比价</div>
                <div class="font-bold text-gray-800 dark:text-zinc-200">
                  {{ priceComparisonText }}
                </div>
              </div>
              <div>
                <div class="text-xs text-gray-400 dark:text-zinc-500 mb-1">历史价格</div>
                <div class="font-bold text-gray-800 dark:text-zinc-200">{{ priceTrendText }}</div>
              </div>
              <div>
                <div class="text-xs text-gray-400 dark:text-zinc-500 mb-1">用户评价</div>
                <div class="font-bold text-gray-800 dark:text-zinc-200">{{ ratingText }} 好评</div>
              </div>
            </div>
          </div>
        </div>

        <!-- Main Content Grid -->
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <!-- Left: Analysis -->
          <div class="lg:col-span-2 space-y-6">
            <!-- Price Trend -->
            <div
              class="bg-white dark:bg-zinc-900 p-6 rounded-xl border border-gray-100 dark:border-zinc-800 shadow-sm"
            >
              <h3 class="text-lg font-bold mb-6 flex items-center gap-2 dark:text-zinc-100">
                <span class="iconify lucide--trending-down text-blue-500"></span>
                价格趋势分析
              </h3>
              <PriceTrendChart :sku-id="selectedSku?.id" />
            </div>

            <!-- Shop Comparison -->
            <div
              class="bg-white dark:bg-zinc-900 p-6 rounded-xl border border-gray-100 dark:border-zinc-800 shadow-sm"
            >
              <h3 class="text-lg font-bold mb-6 flex items-center gap-2 dark:text-zinc-100">
                <span class="iconify lucide--layout-grid text-purple-500"></span>
                全网同款比价
              </h3>
              <PriceCompareTable
                :data="product.skus || []"
                :selected-id="selectedSkuId ?? undefined"
                @create-alert="handleCreateAlert"
                @select="handleSelectSku"
              />
            </div>
          </div>

          <!-- Right: Cards -->
          <div class="space-y-6">
            <div v-loading="decisionLoading" class="min-h-[200px]">
              <DecisionCard v-if="decision" :decision="decision" />
              <div
                v-else-if="decisionError"
                class="bg-red-50 dark:bg-red-900/10 p-6 rounded-xl border border-red-100 dark:border-red-900/20 text-center"
              >
                <span class="iconify lucide--alert-triangle text-red-500 text-3xl mb-2"></span>
                <p class="text-red-500 text-sm mb-4">{{ decisionError }}</p>
                <ElButton size="small" type="primary" plain @click="handleRetryDecision">
                  重试分析
                </ElButton>
              </div>
              <div
                v-else-if="!decisionLoading"
                class="bg-gray-50 dark:bg-zinc-800 p-6 rounded-xl border border-dashed border-gray-200 dark:border-zinc-700 text-center text-gray-400"
              >
                分析中...
              </div>
            </div>

            <CouponPanel :coupons="selectedSku?.coupons || []" />

            <RiskPanel :level="riskLevel" :risks="risksList" />
          </div>
        </div>
      </div>

      <div v-else-if="error && !loading" class="flex flex-col items-center justify-center py-40">
        <ElEmpty :description="error">
          <template #extra>
            <div class="space-x-4">
              <ElButton @click="() => $router.back()">返回搜索</ElButton>
              <ElButton type="primary" @click="handleRetry">重新尝试</ElButton>
            </div>
          </template>
        </ElEmpty>
      </div>

      <div v-else-if="!loading" class="flex flex-col items-center justify-center py-40">
        <ElEmpty description="未找到商品详情" />
        <ElButton type="primary" @click="() => $router.back()">返回搜索</ElButton>
      </div>

      <!-- Alert Dialog -->
      <AlertDialog
        v-model="alertDialogVisible"
        :product="selectedShop || undefined"
        @submit="handleAlertSubmit"
      />
    </div>
  </Page>
</template>
