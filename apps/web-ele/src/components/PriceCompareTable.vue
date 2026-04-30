<script setup lang="ts">
import type { ProductSKU } from "#/api/types";

import { ElPopover, ElTable, ElTableColumn } from "element-plus";

const props = defineProps<{
  data: ProductSKU[];
  selectedId?: number | string;
}>();

const emit = defineEmits(["createAlert", "select"]);

// Analysis for recommendation highlighting
const recommendationLabel = (sku: ProductSKU) => {
  const allFinalPrices = props.data.map((s) => s.final_price || s.price);
  const minPrice = Math.min(...allFinalPrices);
  const currentPrice = sku.final_price || sku.price;

  // Logic: Official + Mid Price is "Best Value"
  // Lowest Price is "Lowest"
  if (currentPrice === minPrice && sku.is_official) return "全网最优";
  if (currentPrice === minPrice) return "全网最低";
  if (sku.is_official) return "尊享官方";
  return null;
};

const getRecommendationColor = (label: string) => {
  if (label === "全网最优") return "bg-red-500 text-white ring-2 ring-red-500/20";
  if (label === "全网最低") return "bg-green-600 text-white";
  if (label === "尊享官方") return "bg-blue-600 text-white";
  return "";
};
</script>

<template>
  <div class="modern-table-container">
    <ElTable
      :data="data"
      style="width: 100%"
      highlight-current-row
      class="premium-table"
      @row-click="(row) => emit('select', row)"
    >
      <ElTableColumn label="综合推荐" width="105">
        <template #default="{ row }">
          <div
            v-if="recommendationLabel(row)"
            class="text-[9px] font-black px-2.5 py-1 rounded-md inline-block uppercase tracking-widest shadow-sm"
            :class="getRecommendationColor(recommendationLabel(row))"
          >
            {{ recommendationLabel(row) }}
          </div>
          <div
            v-else-if="row.id === selectedId"
            class="text-[9px] font-black text-primary uppercase tracking-widest bg-primary/5 px-2 py-1 rounded-md border border-primary/20"
          >
            正在选定
          </div>
        </template>
      </ElTableColumn>

      <ElTableColumn prop="platform" label="平台" width="100">
        <template #default="{ row }">
          <div class="flex items-center gap-2">
            <div
              :class="
                row.platform === 'JD'
                  ? 'bg-red-600'
                  : row.platform === 'TM'
                    ? 'bg-orange-500'
                    : 'bg-zinc-400'
              "
              class="w-4 h-4 rounded text-[8px] font-black text-white flex items-center justify-center shadow-sm"
            >
              {{ row.platform?.charAt(0) }}
            </div>
            <span class="text-xs font-black text-zinc-700 dark:text-zinc-300">{{
              row.platform === "JD" ? "京东" : row.platform === "TM" ? "天猫" : row.platform
            }}</span>
          </div>
        </template>
      </ElTableColumn>

      <ElTableColumn prop="shop_name" label="商家与资质" min-width="200" show-overflow-tooltip>
        <template #default="{ row }">
          <div class="flex flex-col gap-1.5 py-1">
            <div class="flex items-center gap-2">
              <span class="text-xs font-bold text-zinc-800 dark:text-zinc-200">{{
                row.shop_name
              }}</span>
              <div v-if="row.is_official" class="flex items-center gap-1">
                <div
                  class="bg-blue-600 text-white text-[8px] px-1.5 py-0.5 rounded-sm font-black flex items-center gap-0.5"
                >
                  <span class="iconify lucide--shield-check w-2.5 h-2.5"></span>
                  官方
                </div>
                <span
                  v-if="row.shop_name?.includes('旗舰')"
                  class="bg-zinc-900 text-gold-400 text-[8px] px-1.5 py-0.5 rounded-sm font-black text-white"
                  >旗舰店</span>
              </div>
            </div>
            <div class="flex items-center gap-2">
              <span class="text-[8px] font-black text-zinc-400 tracking-widest">{{
                row.is_official ? "高信用渠道" : "第三方零售商"
              }}</span>
            </div>
          </div>
        </template>
      </ElTableColumn>

      <ElTableColumn prop="price" label="平台标价" width="120">
        <template #default="{ row }">
          <span class="text-xs font-mono text-zinc-400 line-through">¥{{ row.price }}</span>
        </template>
      </ElTableColumn>

      <ElTableColumn label="预估到手价" min-width="160">
        <template #default="{ row }">
          <div class="flex flex-col py-2">
            <div class="flex items-center gap-2">
              <span class="text-red-600 font-black text-lg font-mono tracking-tighter">¥{{ row.final_price || row.price }}</span>
              <ElPopover
                v-if="row.promotions && row.promotions.length > 0"
                placement="top"
                :width="220"
                trigger="hover"
                popper-class="premium-popover"
              >
                <template #reference>
                  <div
                    class="text-[9px] font-black text-red-500 border border-red-200 bg-red-50 px-1.5 py-0.5 rounded cursor-help"
                  >
                    {{ row.promotions.length }} 项优惠
                  </div>
                </template>
                <div class="p-2 space-y-3">
                  <div
                    class="text-[10px] font-black text-zinc-400 uppercase tracking-widest border-b pb-2"
                  >
                    明细清单
                  </div>
                  <div class="space-y-1.5">
                    <div
                      v-for="(p, i) in row.promotions"
                      :key="i"
                      class="flex justify-between items-center text-[11px]"
                    >
                      <span class="text-zinc-500 font-bold">{{ p.title }}</span>
                      <span class="text-red-500 font-black">-¥{{ p.amount }}</span>
                    </div>
                  </div>
                  <div
                    class="pt-2 border-t border-dashed flex justify-between items-center text-xs"
                  >
                    <span class="font-bold">累积节省</span>
                    <span class="font-black text-red-600">¥{{ (row.price - (row.final_price || row.price)).toFixed(0) }}</span>
                  </div>
                </div>
              </ElPopover>
            </div>
          </div>
        </template>
      </ElTableColumn>

      <ElTableColumn label="行动建议" width="140" fixed="right">
        <template #default="{ row }">
          <div class="flex items-center gap-2">
            <button
              class="text-[11px] font-black text-primary hover:underline flex items-center gap-1 group"
              @click.stop="emit('createAlert', row)"
            >
              <span class="iconify lucide--bell w-3 h-3 group-hover:animate-bounce"></span>
              设置提醒
            </button>
            <div class="w-[1px] h-3 bg-zinc-200 dark:bg-zinc-800"></div>
            <button
              class="text-[11px] font-black text-zinc-600 dark:text-zinc-400 hover:text-primary transition-colors"
            >
              去看看
            </button>
          </div>
        </template>
      </ElTableColumn>
    </ElTable>
  </div>
</template>

<style scoped>
.premium-table :deep(.el-table__header-wrapper th) {
  font-size: 10px;
  font-weight: 900;
  color: hsl(var(--zinc-400));
  text-transform: uppercase;
  letter-spacing: 0.1em;
  background-color: transparent;
}

.premium-table :deep(.el-table__row) {
  cursor: pointer;
  transition: all 0.3s;
}

.premium-table :deep(.el-table__row:hover) {
  background-color: hsl(var(--primary) / 2%) !important;
}

.premium-table :deep(.el-table__row.current-row) {
  background-color: hsl(var(--primary) / 5%) !important;
}

.premium-table :deep(.el-table__cell) {
  border-bottom: 1px solid hsl(var(--zinc-100));
}

.dark .premium-table :deep(.el-table__cell) {
  border-bottom: 1px solid hsl(var(--zinc-800) / 50%);
}

.tracking-tighter {
  letter-spacing: -0.05em;
}
</style>
