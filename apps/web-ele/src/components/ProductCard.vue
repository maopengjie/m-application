<script setup lang="ts">
import type { Product } from "#/api/types";

import { computed } from "vue";

const props = defineProps<{
  product: Product;
}>();

const emit = defineEmits(["click"]);

const title = computed(() => props.product?.title || props.product?.name || "未知商品");
const price = computed(
  () => props.product?.final_price || props.product?.price || props.product?.min_price || 0,
);
const originalPrice = computed(
  () =>
    props.product?.original_price ||
    (props.product?.final_price ? props.product?.price || props.product?.min_price : null),
);
const image = computed(() => props.product?.image || props.product?.main_image || "");
const platform = computed(() => props.product?.platform || "JD");
const platformCount = computed(() => props.product?.platform_count || 1);
const tags = computed(() => props.product?.tags || []);
const brand = computed(() => props.product?.brand || "");

const handleImageError = (e: Event) => {
  const target = e.target as HTMLImageElement;
  target.src =
    "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI0MDAiIGhlaWdodD0iNDAwIiB2aWV3Qm94PSIwIDAgNDAwIDQwMCI+PHJlY3Qgd2lkdGg9IjQwMCIgaGVpZ2h0PSI0MDAiIGZpbGw9IiNmM2Y0ZjYiLz48dGV4dCB4PSI1MCUiIHk9IjUwJSIgZG9taW5hbnQtYmFzZWxpbmU9Im1pZGRsZSIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZm9udC1mYW1pbHk9InNhbnMtc2VyaWYiIGZvbnQtc2l6ZT0iMjAiIGZpbGw9IiM5Y2EzYWYiPkltYWdlIE5vdCBGb3VuZDwvdGV4dD48L3N2Zz4=";
};
</script>

<template>
  <div
    class="group bg-white dark:bg-zinc-900/60 backdrop-blur-md rounded-3xl border border-gray-100 dark:border-zinc-800 shadow-sm hover:shadow-2xl hover:-translate-y-1.5 transition-all duration-500 overflow-hidden cursor-pointer flex flex-col h-full"
    @click="emit('click', product)"
  >
    <!-- Image section with overlay -->
    <div
      class="relative aspect-square overflow-hidden bg-gray-50 dark:bg-zinc-950/50 p-4 flex items-center justify-center"
    >
      <img
        v-if="image"
        :src="image"
        class="w-full h-full object-contain mix-blend-multiply dark:mix-blend-normal group-hover:scale-110 transition-transform duration-700"
        @error="handleImageError"
      />
      <div v-else class="text-gray-300">
        <span class="iconify lucide--image text-5xl opacity-20"></span>
      </div>

      <!-- Top Overlay Badges -->
      <div class="absolute top-3 left-3 flex flex-col gap-1.5">
        <div
          v-if="platformCount > 1"
          class="bg-blue-600 text-white text-[10px] font-black px-2.5 py-1 rounded-full shadow-lg flex items-center gap-1"
        >
          <span class="iconify lucide--layers w-3 h-3"></span>
          {{ platformCount }} 个平台比价
        </div>
        <div
          v-else
          :class="platform === 'JD' ? 'bg-red-600' : 'bg-orange-500'"
          class="text-white text-[10px] font-black px-2.5 py-1 rounded-full shadow-lg"
        >
          {{ platform === "JD" ? "京东" : platform === "TM" ? "天猫" : platform }}
        </div>
      </div>

      <!-- Brand Overlay -->
      <div v-if="brand" class="absolute bottom-3 right-3">
        <span
          class="bg-black/5 dark:bg-white/5 backdrop-blur-md text-[10px] font-black px-2 py-0.5 rounded-md text-zinc-400 uppercase tracking-tighter"
        >
          {{ brand }}
        </span>
      </div>
    </div>

    <!-- Info Section -->
    <div class="p-4 flex flex-col flex-grow space-y-3">
      <!-- Title -->
      <h3
        class="text-[13px] font-black text-zinc-800 dark:text-zinc-100 line-clamp-2 leading-snug group-hover:text-primary transition-colors h-9"
      >
        <span v-if="brand" class="text-primary mr-1">[{{ brand }}]</span>
        {{ title }}
      </h3>

      <!-- Price & Tags -->
      <div class="mt-auto space-y-2.5">
        <!-- Tags Row -->
        <div v-if="tags.length > 0" class="flex flex-wrap gap-1">
          <span
            v-for="tag in tags"
            :key="tag"
            class="text-[9px] px-1.5 py-0.5 rounded bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 font-bold border border-blue-100 dark:border-blue-800/50"
          >
            {{ tag }}
          </span>
        </div>

        <!-- Price Row -->
        <div class="flex items-end justify-between">
          <div class="flex flex-col">
            <div v-if="product?.final_price" class="flex items-center gap-1.5">
              <span class="text-[10px] font-black text-red-600 uppercase">到手价</span>
              <div class="flex items-baseline">
                <span class="text-[12px] font-black text-red-600 mr-0.5">¥</span>
                <span class="text-2xl font-black text-red-600 tracking-tighter">{{ price }}</span>
              </div>
            </div>
            <div v-else class="flex items-baseline">
              <span class="text-[12px] font-black text-red-600 mr-0.5">¥</span>
              <span class="text-2xl font-black text-red-600 tracking-tighter">{{ price }}</span>
            </div>
            <div
              v-if="originalPrice"
              class="text-[10px] text-zinc-400 line-through font-medium ml-0.5"
            >
              参考价 ¥{{ originalPrice }}
            </div>
          </div>

          <div
            class="text-[10px] text-zinc-400 bg-zinc-50 dark:bg-zinc-800/50 px-2 py-1 rounded-lg flex items-center gap-1"
          >
            <span class="iconify lucide--store w-3 h-3"></span>
            {{ product?.shop_name || "官方自营" }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.text-primary {
  color: hsl(var(--primary));
}

.tracking-tighter {
  letter-spacing: -0.05em;
}
</style>
