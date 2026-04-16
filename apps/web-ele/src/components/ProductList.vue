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
  <div class="min-h-[400px]">
    <template v-if="loading">
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        <el-skeleton v-for="i in 8" :key="i" animated>
          <template #template>
            <el-skeleton-item variant="image" style="height: 200px" />
            <div style="padding: 14px">
              <el-skeleton-item variant="p" style="width: 50%" />
              <div style="display: flex; align-items: center; justify-content: space-between">
                <el-skeleton-item variant="text" style="margin-right: 16px" />
                <el-skeleton-item variant="text" style="width: 30%" />
              </div>
            </div>
          </template>
        </el-skeleton>
      </div>
    </template>

    <div v-else-if="products.length > 0" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
      <ProductCard
        v-for="product in products"
        :key="product.id"
        :product="product"
        @click="emit('click', product)"
      />
    </div>
    
    <div v-else class="flex flex-col items-center justify-center py-20 text-gray-400">
      <el-empty description="暂无相关商品，换个关键词试试吧" />
    </div>
  </div>
</template>
