<script setup lang="ts">
defineProps<{
  data: any[];
}>();

const emit = defineEmits(['createAlert']);
</script>

<template>
  <el-table :data="data" style="width: 100%" border>
    <el-table-column prop="platform" label="平台" width="120">
      <template #default="{ row }">
        <el-tag :type="row.platform === 'JD' ? 'danger' : 'success'" effect="dark" size="small">
          {{ row.platform }}
        </el-tag>
      </template>
    </el-table-column>
    <el-table-column prop="shop_name" label="店铺" min-width="180" show-overflow-tooltip>
      <template #default="{ row }">
        <div class="flex items-center gap-2">
          <span>{{ row.shop_name }}</span>
          <el-tag v-if="row.is_official" size="small" type="warning" plain>官方</el-tag>
        </div>
      </template>
    </el-table-column>
    <el-table-column prop="price" label="当前价" width="120">
      <template #default="{ row }">
        <span class="text-red-500 font-bold">¥{{ row.price }}</span>
      </template>
    </el-table-column>
    <el-table-column prop="original_price" label="原价" width="120">
      <template #default="{ row }">
        <span class="text-gray-400 dark:text-zinc-500 line-through">¥{{ row.original_price }}</span>
      </template>
    </el-table-column>
    <el-table-column label="操作" width="120" fixed="right">
      <template #default="{ row }">
        <el-button type="primary" link @click="emit('createAlert', row)">
          降价提醒
        </el-button>
      </template>
    </el-table-column>
  </el-table>
</template>
