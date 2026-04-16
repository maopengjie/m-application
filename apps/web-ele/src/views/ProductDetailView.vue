<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { useRoute } from 'vue-router';

import { Page } from '@vben/common-ui';

import { ElMessage } from 'element-plus';

import { createPriceAlertApi } from '#/api/alert';
import { getSkuDecisionApi } from '#/api/decision';
import { getProductDetailApi } from '#/api/product';
import AlertDialog from '#/components/AlertDialog.vue';
import CouponPanel from '#/components/CouponPanel.vue';
import DecisionCard from '#/components/DecisionCard.vue';
import PriceCompareTable from '#/components/PriceCompareTable.vue';
import PriceTrendChart from '#/components/PriceTrendChart.vue';
import RiskPanel from '#/components/RiskPanel.vue';
import { computed } from 'vue';

const route = useRoute();
const productId = route.query.id as string;

const loading = ref(true);
const product = ref<any>(null);
const decision = ref<any>(null);
const alertDialogVisible = ref(false);
const selectedShop = ref<any>(null);

const selectedSku = computed(() => {
  return product.value?.skus?.[0] || null;
});

const riskLevel = computed(() => {
  const score = selectedSku.value?.risk_score?.score;
  if (score === undefined) return 'low';
  if (score < 40) return 'high';
  if (score < 70) return 'medium';
  return 'low';
});

const risksList = computed(() => {
  const rs = selectedSku.value?.risk_score;
  const list = [];
  if (rs?.comment_abnormal) list.push('评价内容疑似异常');
  if (rs?.sales_abnormal) list.push('销量波动异常');
  return list;
});

const fetchDetail = async () => {
  if (!productId) return;
  
  loading.value = true;
  try {
    const res = await getProductDetailApi(productId);
    product.value = res;
    
    // Fetch decision if there's a SKU
    if (res.skus?.length) {
      try {
        const dRes = await getSkuDecisionApi(res.skus[0].id);
        decision.value = dRes;
      } catch (e) {
        console.error('Failed to fetch decision:', e);
      }
    }
  } catch (error: any) {
    ElMessage.error(error.message || '获取详情失败');
  } finally {
    loading.value = false;
  }
};

const handleCreateAlert = (shop: any) => {
  selectedShop.value = {
    ...shop,
    image: product.value?.main_image,
    title: product.value?.name
  };
  alertDialogVisible.value = true;
};

const handleAlertSubmit = async (data: any) => {
  try {
    await createPriceAlertApi({
      sku_id: data.sku_id || selectedSku.value?.id,
      target_price: data.targetPrice,
    });
    ElMessage.success('提醒设置成功！当价格降至 ¥' + data.targetPrice + ' 时将通知您');
  } catch (error: any) {
    ElMessage.error(error.message || '设置提醒失败');
  }
};

onMounted(fetchDetail);
</script>

<template>
  <Page 
    :title="product?.name || '商品详情'" 
    :description="product ? `品牌: ${product.brand || '未知'} | ID: ${product.id}` : ''"
  >
    <div v-loading="loading" class="min-h-[400px]">
      <div v-if="product" class="space-y-6">
      <!-- Header Section -->
      <div class="flex flex-col lg:flex-row gap-8 bg-white dark:bg-zinc-900 p-8 rounded-2xl shadow-sm border border-gray-100 dark:border-zinc-800">
        <div class="w-full lg:w-96 flex-shrink-0">
          <img :src="product.main_image" :alt="product.name" class="w-full h-auto aspect-square object-contain rounded-xl border border-gray-100 dark:border-zinc-800 p-4 bg-white dark:bg-zinc-900" />
        </div>
        
        <div class="flex-grow flex flex-col justify-between">
          <div>
            <div class="flex items-center gap-2 mb-3">
              <el-tag :type="selectedSku?.platform === 'JD' ? 'danger' : 'success'" effect="dark">{{ selectedSku?.platform || '未知' }}</el-tag>
              <span class="text-gray-500 dark:text-zinc-400 text-sm">商品 ID: {{ product.id }}</span>
            </div>
            <h1 class="text-2xl font-bold text-gray-900 dark:text-zinc-100 leading-tight mb-4">
              {{ product.name }}
            </h1>
            
            <div class="flex items-baseline gap-4 mb-6">
              <span class="text-4xl font-black text-red-500">¥{{ selectedSku?.price }}</span>
              <span v-if="selectedSku?.original_price" class="text-lg text-gray-400 line-through">¥{{ selectedSku.original_price }}</span>
              <el-tag v-if="selectedSku?.price < selectedSku?.original_price" type="danger" size="small" plain>-{{ Math.round((1 - selectedSku.price / selectedSku.original_price) * 100) }}%</el-tag>
            </div>
            
            <div class="flex flex-wrap gap-4 mb-8">
              <el-button type="primary" size="large" icon="lucide--shopping-cart" class="px-8 !rounded-xl">去购买</el-button>
              <el-button size="large" icon="lucide--bell" class="px-8 !rounded-xl" @click="handleCreateAlert(selectedSku)">降价提醒</el-button>
            </div>
          </div>
          
          <div class="border-t dark:border-zinc-800 pt-6 grid grid-cols-3 gap-4 text-center">
            <div>
              <div class="text-xs text-gray-400 dark:text-zinc-500 mb-1">同款比价</div>
              <div class="font-bold text-gray-800 dark:text-zinc-200">全网最低</div>
            </div>
            <div>
              <div class="text-xs text-gray-400 dark:text-zinc-500 mb-1">历史价格</div>
              <div class="font-bold text-gray-800 dark:text-zinc-200">平稳</div>
            </div>
            <div>
              <div class="text-xs text-gray-400 dark:text-zinc-500 mb-1">用户评价</div>
              <div class="font-bold text-gray-800 dark:text-zinc-200">{{ product.rating || '98%' }} 好评</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Main Content Grid -->
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <!-- Left: Analysis -->
        <div class="lg:col-span-2 space-y-6">
          <!-- Price Trend -->
          <div class="bg-white dark:bg-zinc-900 p-6 rounded-xl border border-gray-100 dark:border-zinc-800 shadow-sm">
            <h3 class="text-lg font-bold mb-6 flex items-center gap-2 dark:text-zinc-100">
              <span class="iconify lucide--trending-down text-blue-500"></span>
              价格趋势分析
            </h3>
            <PriceTrendChart :history="selectedSku?.price_history || []" />
          </div>

          <!-- Shop Comparison -->
          <div class="bg-white dark:bg-zinc-900 p-6 rounded-xl border border-gray-100 dark:border-zinc-800 shadow-sm">
            <h3 class="text-lg font-bold mb-6 flex items-center gap-2 dark:text-zinc-100">
              <span class="iconify lucide--layout-grid text-purple-500"></span>
              全网同款比价
            </h3>
            <PriceCompareTable :data="product.skus || []" @create-alert="handleCreateAlert" />
          </div>
        </div>

        <!-- Right: Cards -->
        <div class="space-y-6">
          <DecisionCard v-if="decision" :decision="decision" />
          
          <CouponPanel :coupons="selectedSku?.coupons || []" />
          
          <RiskPanel :level="riskLevel" :risks="risksList" />
        </div>
      </div>
    </div>

    <div v-else-if="!loading" class="flex flex-col items-center justify-center py-40">
      <el-empty description="未找到商品详情" />
      <el-button type="primary" @click="() => $router.back()">返回搜索</el-button>
    </div>

    <!-- Alert Dialog -->
    <AlertDialog
      v-model="alertDialogVisible"
      :product="selectedShop"
      @submit="handleAlertSubmit"
    />
    </div>
  </Page>
</template>
