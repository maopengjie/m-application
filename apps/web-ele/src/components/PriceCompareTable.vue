<script setup lang="ts">
import { ElTable, ElTableColumn, ElTag, ElButton, ElPopover } from 'element-plus';
import type { ProductSKU } from '#/api/types';

defineProps<{
  data: ProductSKU[];
  selectedId?: number | string;
}>();

const emit = defineEmits(['createAlert', 'select']);
</script>

<template>
  <el-table 
    :data="data" 
    style="width: 100%" 
    border 
    highlight-current-row
    @row-click="(row) => emit('select', row)"
  >
    <el-table-column label="状态" width="80">
      <template #default="{ row }">
        <el-tag v-if="row.id === selectedId" type="primary" size="small">分析中</el-tag>
      </template>
    </el-table-column>
    <el-table-column prop="platform" label="平台" width="100">
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
    <el-table-column prop="price" label="当前价" width="100">
      <template #default="{ row }">
        <span class="text-gray-600 dark:text-zinc-400">¥{{ row.price }}</span>
      </template>
    </el-table-column>
    <el-table-column label="优惠 / 到手价" min-width="160">
      <template #default="{ row }">
        <div class="flex flex-col">
          <div class="flex items-center gap-1">
            <span class="text-red-500 font-bold text-lg">¥{{ row.final_price || row.price }}</span>
            <el-popover
              v-if="row.promotions && row.promotions.length"
              placement="top"
              :width="200"
              trigger="hover"
            >
              <template #reference>
                <el-tag size="small" type="danger" effect="plain" class="cursor-pointer">优惠包</el-tag>
              </template>
              <div class="space-y-2">
                <div v-for="(p, i) in row.promotions" :key="i" class="flex justify-between text-xs">
                  <span>{{ p.title }}</span>
                  <span class="text-red-500">-¥{{ p.amount }}</span>
                </div>
              </div>
            </el-popover>
          </div>
          <span v-if="row.original_price" class="text-xs text-gray-400 line-through">原价 ¥{{ row.original_price }}</span>
        </div>
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
