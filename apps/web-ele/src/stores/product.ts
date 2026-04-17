import { ref } from "vue";

import { defineStore } from "pinia";

import { getProductDetailApi, getProductListApi } from "#/api/product";

export const useProductStore = defineStore("product", () => {
  const currentProduct = ref<any>(null);
  const productList = ref<any[]>([]);
  const loading = ref(false);

  async function fetchProductList(params?: any) {
    try {
      loading.value = true;
      const data = await getProductListApi(params);
      productList.value = data;
    } finally {
      loading.value = false;
    }
  }

  async function fetchProductDetail(id: number | string) {
    try {
      loading.value = true;
      const data = await getProductDetailApi(id);
      currentProduct.value = data;
    } finally {
      loading.value = false;
    }
  }

  return {
    currentProduct,
    productList,
    loading,
    fetchProductList,
    fetchProductDetail,
  };
});
