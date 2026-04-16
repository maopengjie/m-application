<script setup lang="ts">
import { onMounted, ref } from 'vue';

import { Page } from '@vben/common-ui';

import { ElMessage, ElMessageBox } from 'element-plus';

import { deletePriceAlertApi, getPriceAlertsApi } from '#/api/alert';

interface PriceAlert {
  id: number;
  sku_id: number;
  target_price: number;
  is_triggered: boolean;
  status: string;
  created_at: string;
  sku?: {
    platform: string;
    price: number;
    shop_name: string;
    product: {
      name: string;
      main_image: string;
    }
  }
}

const loading = ref(true);
const alerts = ref<PriceAlert[]>([]);

const fetchAlerts = async () => {
  loading.value = true;
  try {
    const res = await getPriceAlertsApi();
    alerts.value = res || [];
  } catch (error: any) {
    ElMessage.error(error.message || '获取提醒列表失败');
  } finally {
    loading.value = false;
  }
};

const handleDelete = (alert: any) => {
  ElMessageBox.confirm('确定要取消此降价提醒吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      await deletePriceAlertApi(alert.id);
      ElMessage.success('已取消提醒');
      fetchAlerts();
    } catch (error: any) {
      ElMessage.error(error.message || '操作失败');
    }
  });
};

onMounted(fetchAlerts);
</script>

<template>
  <Page title="降价提醒" description="管理您关注的所有商品降价提醒">
    <div v-loading="loading" class="min-h-[400px]">
      <div v-if="alerts.length > 0" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div v-for="alert in alerts" :key="alert.id" class="relative group bg-white dark:bg-zinc-900 rounded-xl border border-gray-100 dark:border-zinc-800 p-4 shadow-sm hover:shadow-md transition-shadow">
          <!-- Status Tag -->
          <div class="absolute top-2 right-2">
            <el-tag :type="alert.is_triggered ? 'success' : 'info'" size="small" effect="dark">
              {{ alert.is_triggered ? '已触发' : '监控中' }}
            </el-tag>
          </div>

          <div class="flex gap-4">
            <img :src="alert.sku?.product?.main_image" class="w-20 h-20 object-cover rounded border flex-shrink-0" />
            <div class="flex-grow min-w-0 pr-12">
              <h3 class="text-sm font-bold truncate mb-1 dark:text-zinc-200">{{ alert.sku?.product?.name || '未知商品' }}</h3>
              <div class="text-xs text-gray-400 dark:text-zinc-500 mb-2">
                {{ alert.sku?.platform }} · {{ alert.sku?.shop_name }}
              </div>
              
              <div class="flex items-center justify-between mt-2">
                <div class="flex flex-col">
                  <span class="text-xs text-gray-400 dark:text-zinc-500">目标价</span>
                  <span class="text-red-500 font-bold">¥{{ alert.target_price }}</span>
                </div>
                <div class="flex flex-col text-right">
                  <span class="text-xs text-gray-400 dark:text-zinc-500">当前价</span>
                  <span class="font-bold dark:text-zinc-100">¥{{ alert.sku?.price || 0 }}</span>
                </div>
              </div>
            </div>
          </div>
          
          <div class="mt-4 pt-4 border-t dark:border-zinc-800 flex items-center justify-between">
            <span class="text-[10px] text-gray-400">设置于: {{ new Date(alert.created_at).toLocaleDateString() }}</span>
            <el-button type="danger" link size="small" @click="handleDelete(alert)">取消提醒</el-button>
          </div>
        </div>
      </div>

      <div v-else-if="!loading" class="flex flex-col items-center justify-center py-20 text-gray-400">
        <el-empty description="暂无降价提醒，快去搜索心仪商品吧" />
        <el-button type="primary" @click="() => $router.push('/price-monitor/search')">去搜索</el-button>
      </div>
    </div>
  </Page>
</template>
