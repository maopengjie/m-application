<script setup lang="ts">
import type { Product } from "#/api/types";

import { useRouter } from "vue-router";

defineProps<{
  products: Product[];
  title?: string;
}>();

const router = useRouter();

const handleProductClick = (product: Product) => {
  // A1-04: 点击替代商品进入详情页
  router.push({
    name: "CommerceDetail",
    params: { id: product.id },
  });
};

const formatPrice = (price?: number) => {
  if (price === undefined) return "---";
  return price.toFixed(2);
};
</script>

<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <h3
        class="text-sm font-black text-zinc-800 dark:text-zinc-100 uppercase tracking-widest flex items-center gap-2"
      >
        <span class="iconify lucide--sparkles text-primary w-4 h-4"></span>
        {{ title || "为您推荐的替代商品" }}
      </h3>
    </div>

    <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
      <div
        v-for="product in products"
        :key="product.id"
        class="bg-white dark:bg-zinc-900 rounded-2xl border border-zinc-100 dark:border-zinc-800 p-4 transition-all hover:scale-[1.03] hover:shadow-xl hover:shadow-black/5 cursor-pointer group flex gap-4"
        @click="handleProductClick(product)"
      >
        <!-- Thumbnail -->
        <div
          class="w-20 h-20 bg-zinc-50 dark:bg-zinc-800 rounded-xl flex items-center justify-center p-2 flex-shrink-0 relative overflow-hidden"
        >
          <div
            class="absolute inset-0 bg-primary/5 opacity-0 group-hover:opacity-100 transition-opacity"
          ></div>
          <img
            :src="product.main_image || product.image"
            :alt="product.name"
            class="w-full h-full object-contain relative z-10"
          />
        </div>

        <!-- Info -->
        <div class="flex flex-col justify-between py-0.5 flex-grow min-w-0">
          <div class="space-y-1">
            <div class="flex items-center gap-2">
              <span
                v-if="product.platform"
                class="text-[8px] font-black px-1.5 rounded-sm bg-zinc-100 dark:bg-zinc-800 text-zinc-500"
              >
                {{ product.platform }}
              </span>
              <span class="text-[9px] font-black text-zinc-400 uppercase tracking-tighter">{{
                product.brand || "未知品牌"
              }}</span>
            </div>
            <h4 class="text-xs font-bold text-zinc-800 dark:text-zinc-200 truncate leading-tight">
              {{ product.name || product.title }}
            </h4>
          </div>

          <div class="flex items-baseline gap-1 mt-2">
            <span class="text-[9px] font-black text-red-600 font-mono">¥</span>
            <span class="text-base font-black text-red-600 font-mono tracking-tighter">
              {{ formatPrice(product.final_price || product.price) }}
            </span>
            <span v-if="product.original_price" class="text-[8px] text-zinc-400 line-through ml-1">
              ¥{{ formatPrice(product.original_price) }}
            </span>
          </div>
        </div>

        <!-- Arrow -->
        <div
          class="flex items-center text-zinc-300 group-hover:text-primary transition-colors pr-1"
        >
          <span class="iconify lucide--chevron-right w-4 h-4"></span>
        </div>
      </div>
    </div>

    <div v-if="products.length === 0" class="text-center py-10 opacity-30">
      <span class="iconify lucide--package-open w-8 h-8 mx-auto mb-2"></span>
      <span class="text-[10px] font-black uppercase tracking-widest">暂无精准替代方案</span>
    </div>
  </div>
</template>

<style scoped>
.truncate {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
