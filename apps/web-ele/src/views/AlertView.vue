<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { getPriceAlertsApi } from '#/api/alert';
import { ElMessage } from 'element-plus';
import { Bell, Delete } from '@element-plus/icons-vue';

const alerts = ref<any[]>([]);
const loading = ref(false);

const fetchAlerts = async () => {
  loading.value = true;
  try {
    const res = await getPriceAlertsApi(1); // Mock user_id 1
    alerts.value = res || [];
  } catch (error) {
    console.error('Fetch alerts failed:', error);
    ElMessage.error('获取提醒列表失败');
  } finally {
    loading.value = false;
  }
};

onMounted(() => {
  fetchAlerts();
});
</script>

<template>
  <div class="p-6 max-w-5xl mx-auto">
    <div class="flex items-center justify-between mb-8">
      <div>
        <h1 class="text-2xl font-bold text-gray-800">降价提醒</h1>
        <p class="text-gray-500 mt-1">订阅商品价格变动，时刻掌握最佳购买时机</p>
      </div>
      <el-button type="primary" @click="fetchAlerts">刷新列表</el-button>
    </div>

    <div v-loading="loading">
      <div v-if="alerts.length > 0" class="space-y-4">
        <div
          v-for="item in alerts"
          :key="item.id"
          class="bg-white p-6 rounded-xl border border-gray-100 shadow-sm flex items-center gap-6"
        >
          <div class="w-12 h-12 bg-blue-50 text-blue-600 rounded-full flex items-center justify-center flex-shrink-0">
            <el-icon :size="24"><Bell /></el-icon>
          </div>
          <div class="flex-1">
            <div class="text-sm text-gray-500 mb-1">SKU ID: {{ item.sku_id }}</div>
            <div class="text-gray-800 font-medium">目标价格: <span class="text-red-500 font-bold">¥{{ item.target_price }}</span></div>
            <div class="text-xs text-gray-400 mt-1">创建时间: {{ new Date(item.created_at).toLocaleString() }}</div>
          </div>
          <div class="flex items-center gap-4">
            <el-tag :type="item.is_active ? 'success' : 'info'" size="small">
              {{ item.is_active ? '进行中' : '已完成' }}
            </el-tag>
            <el-button link type="danger">
              <el-icon><Delete /></el-icon>
            </el-button>
          </div>
        </div>
      </div>

      <div v-else-if="!loading" class="text-center py-20 bg-white rounded-2xl border border-dashed border-gray-200">
        <el-empty description="暂无订阅提醒，去搜索喜欢的商品吧" />
      </div>
    </div>
  </div>
</template>
