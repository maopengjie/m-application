<script setup lang="ts">
import { computed, ref, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { getProductDetailApi } from '#/api/product';
import { getSkuDecisionApi } from '#/api/decision';
import { createPriceAlertApi } from '#/api/alert';
import { ElMessage, ElMessageBox } from 'element-plus';
import PriceCompareTable from '#/components/PriceCompareTable.vue';
import PriceTrendChart from '#/components/PriceTrendChart.vue';
import DecisionCard from '#/components/DecisionCard.vue';
import RiskPanel from '#/components/RiskPanel.vue';

const route = useRoute();
const router = useRouter();
const productId = route.params.id as string;

const loading = ref(true);
const product = ref<any>(null);
const decision = ref<any>(null);

const selectedSku = computed(() => {
  const skus = product.value?.skus || [];
  return skus.find((s: any) => s.is_official) || skus[0] || null;
});

const aggregatedHistory = computed(() => {
  const sku = selectedSku.value;
  if (!sku?.price_history) return [];
  return sku.price_history.map((item: any) => ({
    ...item,
    date: item.recorded_at,
  }));
});

const aggregatedCoupons = computed(() => selectedSku.value?.coupons || []);

const riskPanel = computed(() => {
  const risk = selectedSku.value?.risk_score;
  if (!risk) {
    return {
      level: 'low',
      risks: ['当前渠道风险较低，建议按需采购。'],
    };
  }

  const level = risk.score >= 90 ? 'low' : risk.score >= 70 ? 'medium' : 'high';
  const risks = [];
  if (risk.comment_abnormal) risks.push('评论质量存在异常波动');
  if (risk.sales_abnormal) risks.push('销量变化存在异常波动');
  if (risks.length === 0) risks.push(`综合风险评分 ${risk.score}，当前渠道表现稳定`);

  return { level, risks };
});

const fetchData = async () => {
  loading.value = true;
  try {
    const [productRes] = await Promise.all([
      getProductDetailApi(productId),
    ]);
    product.value = productRes;

    // Fetch decision for the official or first SKU
    const officialSku = productRes.skus?.find((s: any) => s.is_official) || productRes.skus?.[0];
    if (officialSku) {
      const decisionRes = await getSkuDecisionApi(officialSku.id);
      decision.value = decisionRes;
    }
  } catch (error) {
    console.error('Fetch detail failed:', error);
    ElMessage.error('获取商品详情失败');
  } finally {
    loading.value = false;
  }
};

const handleCreateAlert = (sku: any) => {
  ElMessageBox.prompt('请输入目标价格', '设置降价提醒', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    inputPattern: /^\d+(\.\d{1,2})?$/,
    inputErrorMessage: '请输入有效的价格',
    inputValue: sku.price,
  }).then(async ({ value }) => {
    try {
      await createPriceAlertApi({
        sku_id: sku.id,
        target_price: parseFloat(value),
        user_id: 1, // Mock user
      });
      ElMessage.success('订阅成功！当价格达到目标时将通知您。');
    } catch (error) {
      ElMessage.error('订阅失败');
    }
  });
};

onMounted(() => {
  fetchData();
});
</script>

<template>
  <div v-loading="loading" class="p-6 max-w-7xl mx-auto space-y-6">
    <!-- Breadcrumb / Header -->
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-4">
        <el-button @click="router.back()" circle>
          <el-icon><ArrowLeft /></el-icon>
        </el-button>
        <div>
          <div class="text-xs text-blue-600 font-medium">{{ product?.brand }} | {{ product?.category }}</div>
          <h1 class="text-2xl font-bold text-gray-800">{{ product?.name }}</h1>
        </div>
      </div>
      <div class="flex gap-3">
        <el-button type="warning" plain>收藏商品</el-button>
        <el-button type="primary">立即购买</el-button>
      </div>
    </div>

    <div v-if="product" class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- Main Content -->
      <div class="lg:col-span-2 space-y-6">
        <!-- Gallery & Info -->
        <div class="bg-white p-6 rounded-2xl border border-gray-100 shadow-sm flex flex-col md:flex-row gap-8">
          <div class="w-full md:w-64 aspect-square bg-gray-50 rounded-xl flex items-center justify-center p-6 border border-gray-50">
            <img :src="product.main_image" :alt="product.name" class="max-h-full object-contain">
          </div>
          <div class="flex-1 space-y-4">
            <div class="grid grid-cols-2 gap-4">
              <div class="bg-blue-50/50 p-4 rounded-xl border border-blue-50">
                <div class="text-xs text-blue-600 mb-1">最低价</div>
                <div class="text-2xl font-black text-blue-700">¥{{ Math.min(...(product.skus?.map((s: any) => s.price) || [0])) }}</div>
              </div>
              <div class="bg-purple-50/50 p-4 rounded-xl border border-purple-50">
                <div class="text-xs text-purple-600 mb-1">平台数量</div>
                <div class="text-2xl font-black text-purple-700">{{ product.skus?.length || 0 }} 家</div>
              </div>
            </div>
            <div class="text-gray-500 text-sm leading-relaxed">
              {{ product.description || '该商品暂无详细描述。本平台提供实时比价、历史价格追踪及基于AI的采购决策建议。' }}
            </div>
          </div>
        </div>

        <!-- Price Trend -->
        <div class="bg-white p-6 rounded-2xl border border-gray-100 shadow-sm">
          <div class="flex items-center justify-between mb-6">
            <h3 class="font-bold text-gray-800 flex items-center gap-2">
              <el-icon class="text-blue-500"><Histogram /></el-icon>
              价格走势分析
            </h3>
            <el-radio-group size="small">
              <el-radio-button label="30">近30天</el-radio-button>
              <el-radio-button label="90">近90天</el-radio-button>
            </el-radio-group>
          </div>
          <PriceTrendChart :history="aggregatedHistory" />
        </div>
        
        <!-- Comparison Table -->
        <div class="bg-white p-6 rounded-2xl border border-gray-100 shadow-sm">
          <h3 class="font-bold text-gray-800 mb-6 flex items-center gap-2">
            <el-icon class="text-orange-500"><Shop /></el-icon>
            全网实时比价
          </h3>
          <PriceCompareTable :data="product.skus || []" @create-alert="handleCreateAlert" />
        </div>
      </div>

      <!-- Sidebar -->
      <div class="space-y-6">
        <DecisionCard :decision="decision" />
        
        <div class="bg-white p-6 rounded-2xl border border-gray-100 shadow-sm">
          <h3 class="font-bold text-gray-800 mb-6 flex items-center gap-2">
            <el-icon class="text-red-500"><Warning /></el-icon>
            风控建议
          </h3>
          <RiskPanel :level="riskPanel.level" :risks="riskPanel.risks" />
        </div>

        <!-- Coupons -->
        <div class="bg-white p-6 rounded-2xl border border-gray-100 shadow-sm">
          <h3 class="font-bold text-gray-800 mb-4">当前可用优惠</h3>
          <div v-if="aggregatedCoupons.length" class="space-y-3">
            <div v-for="coupon in aggregatedCoupons" :key="coupon.id" class="flex items-center justify-between p-3 bg-red-50 rounded-lg border border-red-100">
              <div>
                <div class="text-red-600 font-bold text-sm">{{ coupon.type }} ¥{{ coupon.amount }}</div>
                <div class="text-xs text-red-400">
                  满 {{ coupon.condition_amount || 0 }} 可用
                </div>
              </div>
              <el-button type="danger" size="small" link>领取</el-button>
            </div>
          </div>
          <div v-else class="text-center py-4 text-gray-400 text-sm italic">
            暂无当前生效的优惠券
          </div>
        </div>
      </div>
    </div>

    <!-- Empty State -->
    <div v-else-if="!loading" class="text-center py-32">
      <el-empty description="无法找到该商品" />
    </div>
  </div>
</template>

<script lang="ts">
import { ArrowLeft, Histogram, Shop, Warning } from '@element-plus/icons-vue';
export default {
  components: {
    ArrowLeft,
    Histogram,
    Shop,
    Warning
  }
}
</script>
