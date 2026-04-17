<script setup lang="ts">
import type { ProductSKU } from "#/api/types";

import { ElButton, ElPopover, ElTable, ElTableColumn, ElTag } from "element-plus";

defineProps<{
  data: ProductSKU[];
  selectedId?: number | string;
}>();

const emit = defineEmits(["createAlert", "select"]);
</script>

<template>
  <ElTable
    :data="data"
    style="width: 100%"
    border
    highlight-current-row
    @row-click="(row) => emit('select', row)"
  >
    <ElTableColumn label="状态" width="80">
      <template #default="{ row }">
        <ElTag v-if="row.id === selectedId" type="primary" size="small">分析中</ElTag>
      </template>
    </ElTableColumn>
    <ElTableColumn prop="platform" label="平台" width="100">
      <template #default="{ row }">
        <ElTag :type="row.platform === 'JD' ? 'danger' : 'success'" effect="dark" size="small">
          {{ row.platform }}
        </ElTag>
      </template>
    </ElTableColumn>
    <ElTableColumn prop="shop_name" label="店铺" min-width="180" show-overflow-tooltip>
      <template #default="{ row }">
        <div class="flex items-center gap-2">
          <span>{{ row.shop_name }}</span>
          <ElTag v-if="row.is_official" size="small" type="warning" plain>官方</ElTag>
        </div>
      </template>
    </ElTableColumn>
    <ElTableColumn prop="price" label="当前价" width="100">
      <template #default="{ row }">
        <span class="text-gray-600 dark:text-zinc-400">¥{{ row.price }}</span>
      </template>
    </ElTableColumn>
    <ElTableColumn label="优惠 / 到手价" min-width="160">
      <template #default="{ row }">
        <div class="flex flex-col">
          <div class="flex items-center gap-1">
            <span class="text-red-500 font-bold text-lg">¥{{ row.final_price || row.price }}</span>
            <ElPopover
              v-if="row.promotions && row.promotions.length > 0"
              placement="top"
              :width="200"
              trigger="hover"
            >
              <template #reference>
                <ElTag size="small" type="danger" effect="plain" class="cursor-pointer">
                  优惠包
                </ElTag>
              </template>
              <div class="space-y-2">
                <div v-for="(p, i) in row.promotions" :key="i" class="flex justify-between text-xs">
                  <span>{{ p.title }}</span>
                  <span class="text-red-500">-¥{{ p.amount }}</span>
                </div>
              </div>
            </ElPopover>
          </div>
          <span v-if="row.original_price" class="text-xs text-gray-400 line-through">原价 ¥{{ row.original_price }}</span>
        </div>
      </template>
    </ElTableColumn>
    <ElTableColumn label="操作" width="120" fixed="right">
      <template #default="{ row }">
        <ElButton type="primary" link @click="emit('createAlert', row)"> 降价提醒 </ElButton>
      </template>
    </ElTableColumn>
  </ElTable>
</template>
