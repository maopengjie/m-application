<script setup lang="ts">
import { computed, ref, watch } from "vue";

import {
  ElButton,
  ElCheckbox,
  ElCheckboxGroup,
  ElDialog,
  ElForm,
  ElFormItem,
  ElInput,
  ElInputNumber,
} from "element-plus";

interface AlertProductInfo {
  id: number;
  name?: string;
  title?: string;
  image?: string;
  main_image?: string;
  price?: number;
  min_price?: number;
  final_price?: number;
}

const props = defineProps<{
  modelValue: boolean;
  product?: AlertProductInfo;
}>();

const emit = defineEmits<{
  (e: "update:modelValue", value: boolean): void;
  (e: "submit", data: AlertSubmitData): void;
}>();

interface AlertSubmitData {
  skuId?: number;
  targetPrice: number;
  notifyMethods: string[];
  email: string;
  phone: string;
}

import type { FormInstance, FormRules } from "element-plus";

const formRef = ref<FormInstance>();
const currentPrice = computed(() => {
  return props.product?.final_price ?? props.product?.price ?? props.product?.min_price ?? 0;
});
const productTitle = computed(() => props.product?.title ?? props.product?.name ?? "未知商品");
const productImage = computed(() => props.product?.image ?? props.product?.main_image ?? "");
const form = ref({
  targetPrice: 0,
  email: "",
  phone: "",
  notifyMethods: ["web"] as string[],
});

const rules = computed<FormRules>(() => ({
  targetPrice: [
    { required: true, message: "请输入目标价", trigger: "blur" },
    { type: "number", min: 0.01, message: "价格必须大于 0", trigger: "blur" },
    {
      validator: (_rule, value, callback) => {
        if (props.product && value >= currentPrice.value) {
          callback(new Error("目标价应低于当前价格才有意义"));
        } else {
          callback();
        }
      },
      trigger: "blur",
    },
  ],
  notifyMethods: [
    { type: "array", required: true, message: "请至少选择一种通知方式", trigger: "change" },
  ],
  email: [
    {
      required: form.value.notifyMethods.includes("email"),
      message: "请输入邮箱地址",
      trigger: "blur",
    },
    { type: "email", message: "请输入正确的邮箱格式", trigger: "blur" },
  ],
  phone: [
    {
      required: form.value.notifyMethods.includes("sms"),
      message: "请输入手机号码",
      trigger: "blur",
    },
    { pattern: /^1[3-9]\d{9}$/, message: "请输入正确的手机号格式", trigger: "blur" },
  ],
}));

watch(
  () => props.product,
  (newVal) => {
    if (newVal) {
      form.value.targetPrice = Math.floor(currentPrice.value * 0.9);
    }
  },
  { immediate: true },
);

const visible = ref(props.modelValue);
watch(
  () => props.modelValue,
  (val) => (visible.value = val),
);
watch(visible, (val) => emit("update:modelValue", val));

const submitting = ref(false);

const handleImageError = (e: Event) => {
  const target = e.target as HTMLImageElement;
  target.src =
    "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI0MDAiIGhlaWdodD0iNDAwIiB2aWV3Qm94PSIwIDAgNDAwIDQwMCI+PHJlY3Qgd2lkdGg9IjQwMCIgaGVpZ2h0PSI0MDAiIGZpbGw9IiNmM2Y0ZjYiLz48dGV4dCB4PSI1MCUiIHk9IjUwJSIgZG9taW5hbnQtYmFzZWxpbmU9Im1pZGRsZSIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZm9udC1mYW1pbHk9InNhbnMtc2VyaWYiIGZvbnQtc2l6ZT0iMjAiIGZpbGw9IiM5Y2EzYWYiPkltYWdlIE5vdCBGb3VuZDwvdGV4dD48L3N2Zz4=";
};

const handleSubmit = async () => {
  if (!formRef.value || submitting.value) return;

  await formRef.value.validate(async (valid) => {
    if (valid) {
      submitting.value = true;
      try {
        await emit("submit", {
          skuId: props.product?.id,
          ...form.value,
        });
        visible.value = false;
      } finally {
        submitting.value = false;
      }
    }
  });
};
</script>

<template>
  <ElDialog
    v-model="visible"
    title="设置降价提醒"
    width="460px"
    class="rounded-xl overflow-hidden"
    destroy-on-close
  >
    <div
      v-if="product"
      class="flex items-center gap-4 p-3 bg-gray-50 dark:bg-zinc-800/50 border border-transparent dark:border-zinc-800 rounded-lg mb-6"
    >
      <img
        :src="productImage"
        class="w-16 h-16 object-cover rounded border dark:border-zinc-700 bg-white dark:bg-zinc-900"
        @error="handleImageError"
      />
      <div class="flex-grow min-w-0">
        <div class="text-sm font-bold truncate dark:text-zinc-200">{{ productTitle }}</div>
        <div class="text-xs text-gray-500 dark:text-zinc-500 mt-1">
          当前价: <span class="text-red-500 font-bold">¥{{ currentPrice }}</span>
        </div>
      </div>
    </div>

    <ElForm ref="formRef" :model="form" :rules="rules" label-position="top">
      <ElFormItem label="期望价格 (当价格低于此值时提醒)" prop="targetPrice">
        <ElInputNumber v-model="form.targetPrice" :precision="2" :step="10" class="!w-full" />
      </ElFormItem>

      <ElFormItem label="通过以下方式通知我" prop="notifyMethods">
        <ElCheckboxGroup v-model="form.notifyMethods">
          <ElCheckbox value="web">站内信</ElCheckbox>
          <ElCheckbox value="email">邮件</ElCheckbox>
          <ElCheckbox value="sms">短信</ElCheckbox>
        </ElCheckboxGroup>
      </ElFormItem>

      <ElFormItem v-if="form.notifyMethods.includes('email')" label="邮箱地址" prop="email">
        <ElInput v-model="form.email" placeholder="example@mail.com" />
      </ElFormItem>

      <ElFormItem v-if="form.notifyMethods.includes('sms')" label="手机号码" prop="phone">
        <ElInput v-model="form.phone" placeholder="13800138000" />
      </ElFormItem>
    </ElForm>

    <template #footer>
      <div class="flex gap-3">
        <ElButton class="flex-grow" @click="visible = false">取消</ElButton>
        <ElButton
          type="primary"
          class="flex-grow"
          :loading="submitting"
          :disabled="submitting"
          @click="handleSubmit"
        >
          开启提醒
        </ElButton>
      </div>
    </template>
  </ElDialog>
</template>
