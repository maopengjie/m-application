<script setup lang="ts">
import ProductCard from './ProductCard.vue';

defineProps<{
  products: any[];
  loading?: boolean;
}>();

const emit = defineEmits<{
  (e: 'click', product: any): void;
}>();
</script>

<template>
  <div v-loading="loading" class="min-h-[400px]">
    <div v-if="products.length > 0" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
      <ProductCard
        v-for="product in products"
        :key="product.id"
        :product="product"
        @click="emit('click', product)"
      />
    </div>
    
    <div v-else-if="!loading" class="flex flex-col items-center justify-center py-20 text-gray-400">
      <span class="iconify lucide--package-open text-6xl mb-4 opacity-20"></span>
      <p>暂无相关商品，换个关键词试试吧</p>
    </div>
  </div>
</template>
