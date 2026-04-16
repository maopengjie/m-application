<script setup lang="ts">
import { computed } from 'vue';
import { ElTag } from 'element-plus';

const props = defineProps<{
  product?: any;
}>();

const emit = defineEmits(['click']);

const title = computed(() => props.product?.title || props.product?.name || '未知商品');
const price = computed(() => props.product?.final_price || props.product?.price || props.product?.min_price || 0);
const originalPrice = computed(() => props.product?.original_price || (props.product?.final_price ? props.product?.price || props.product?.min_price : null));
const image = computed(() => props.product?.image || props.product?.main_image || '');
const platform = computed(() => props.product?.platform || 'JD');
</script>

<template>
  <div 
    class="group bg-white dark:bg-zinc-900 rounded-2xl border border-gray-100 dark:border-zinc-800 shadow-sm hover:shadow-xl hover:-translate-y-1 transition-all duration-300 overflow-hidden cursor-pointer flex flex-col h-full"
    @click="emit('click', product)"
  >
    <!-- Image section with overlay -->
    <div class="relative aspect-square overflow-hidden bg-gray-50 dark:bg-zinc-800 p-6 flex items-center justify-center">
      <img 
        v-if="image" 
        :src="image" 
        class="w-full h-full object-contain mix-blend-multiply dark:mix-blend-normal group-hover:scale-110 transition-transform duration-500" 
      />
      <div v-else class="text-gray-300">
        <span class="iconify lucide--image text-4xl"></span>
      </div>
      
      <!-- Platform Tag -->
      <div class="absolute top-3 left-3">
        <el-tag 
          :type="platform === 'JD' ? 'danger' : 'success'" 
          effect="dark" 
          size="small"
          class="!border-none !rounded-lg px-2"
        >
          {{ platform }}
        </el-tag>
      </div>

      <!-- Hover Quick View -->
      <div class="absolute inset-0 bg-black/5 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
        <div class="bg-white/90 backdrop-blur-sm text-gray-800 text-xs font-bold py-2 px-4 rounded-full shadow-lg">
          点击查看详情
        </div>
      </div>
    </div>

    <!-- Info Section -->
    <div class="p-4 flex flex-col flex-grow">
      <h3 class="text-sm font-bold text-gray-800 dark:text-zinc-200 line-clamp-2 leading-snug mb-3 group-hover:text-primary transition-colors">
        {{ title }}
      </h3>
      
      <div class="mt-auto">
        <div class="flex flex-col gap-1">
          <div v-if="product?.final_price" class="flex items-center gap-1">
             <span class="text-[10px] bg-red-500 text-white px-1 rounded">到手价</span>
             <span class="text-xl font-black text-red-500">¥{{ price }}</span>
          </div>
          <div v-else class="flex items-baseline gap-1">
            <span class="text-xs text-red-500 font-bold">¥</span>
            <span class="text-xl font-black text-red-500">{{ price }}</span>
          </div>
          <div v-if="originalPrice" class="text-[10px] text-gray-400 line-through">¥{{ originalPrice }}</div>
        </div>
        
        <div class="flex items-center justify-between mt-3 text-[10px] text-gray-400 dark:text-zinc-500">
          <span class="flex items-center gap-1">
            <span class="iconify lucide--store w-3 h-3"></span>
            {{ product?.shop_name || '直营店' }}
          </span>
          <span v-if="product?.comments" class="flex items-center gap-1">
            {{ product.comments }}+ 评价
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.text-primary {
  color: var(--el-color-primary);
}
</style>
