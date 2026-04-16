<script setup lang="ts">
import { ref, watch, computed } from 'vue';
import { 
  ElDialog, 
  ElForm, 
  ElFormItem, 
  ElInputNumber, 
  ElCheckboxGroup, 
  ElCheckbox, 
  ElInput, 
  ElButton 
} from 'element-plus';

import type { Product } from '#/api/types';

const props = defineProps<{
  modelValue: boolean;
  product?: Product;
}>();

interface AlertSubmitData {
  productId?: number;
  targetPrice: number;
  notifyMethods: string[];
  email: string;
  phone: string;
}

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void;
  (e: 'submit', data: AlertSubmitData): void;
}>();

import type { FormInstance, FormRules } from 'element-plus';

const formRef = ref<FormInstance>();
const form = ref({
  targetPrice: 0,
  email: '',
  phone: '',
  notifyMethods: ['web'] as string[]
});

const rules = computed<FormRules>(() => ({
  targetPrice: [
    { required: true, message: '请输入目标价', trigger: 'blur' },
    { type: 'number', min: 0.01, message: '价格必须大于 0', trigger: 'blur' },
    {
      validator: (_rule, value, callback) => {
        if (props.product && value >= props.product.price) {
          callback(new Error('目标价应低于当前价格才有意义'));
        } else {
          callback();
        }
      },
      trigger: 'blur'
    }
  ],
  notifyMethods: [
    { type: 'array', required: true, message: '请至少选择一种通知方式', trigger: 'change' }
  ],
  email: [
    { 
      required: form.value.notifyMethods.includes('email'), 
      message: '请输入邮箱地址', 
      trigger: 'blur' 
    },
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
  ],
  phone: [
    { 
      required: form.value.notifyMethods.includes('sms'), 
      message: '请输入手机号码', 
      trigger: 'blur' 
    },
    { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号格式', trigger: 'blur' }
  ]
}));

watch(() => props.product, (newVal) => {
  if (newVal) {
    form.value.targetPrice = Math.floor(newVal.price * 0.9);
  }
}, { immediate: true });

const visible = ref(props.modelValue);
watch(() => props.modelValue, (val) => visible.value = val);
watch(visible, (val) => emit('update:modelValue', val));

const submitting = ref(false);

const handleImageError = (e: Event) => {
  const target = e.target as HTMLImageElement;
  target.src = 'https://via.placeholder.com/200x200?text=No+Image';
};

const handleSubmit = async () => {
  if (!formRef.value || submitting.value) return;
  
  await formRef.value.validate(async (valid) => {
    if (valid) {
      submitting.value = true;
      try {
        await emit('submit', {
          productId: props.product?.id,
          ...form.value
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
  <el-dialog
    v-model="visible"
    title="设置降价提醒"
    width="460px"
    class="rounded-xl overflow-hidden"
    destroy-on-close
  >
    <div v-if="product" class="flex items-center gap-4 p-3 bg-gray-50 dark:bg-zinc-800/50 border border-transparent dark:border-zinc-800 rounded-lg mb-6">
      <img :src="product.image" class="w-16 h-16 object-cover rounded border dark:border-zinc-700 bg-white dark:bg-zinc-900" @error="handleImageError" />
      <div class="flex-grow min-w-0">
        <div class="text-sm font-bold truncate dark:text-zinc-200">{{ product.title }}</div>
        <div class="text-xs text-gray-500 dark:text-zinc-500 mt-1">当前价: <span class="text-red-500 font-bold">¥{{ product.price }}</span></div>
      </div>
    </div>

    <el-form ref="formRef" :model="form" :rules="rules" label-position="top">
      <el-form-item label="期望价格 (当价格低于此值时提醒)" prop="targetPrice">
        <el-input-number v-model="form.targetPrice" :precision="2" :step="10" class="!w-full" />
      </el-form-item>
      
      <el-form-item label="通过以下方式通知我" prop="notifyMethods">
        <el-checkbox-group v-model="form.notifyMethods">
          <el-checkbox value="web">站内信</el-checkbox>
          <el-checkbox value="email">邮件</el-checkbox>
          <el-checkbox value="sms">短信</el-checkbox>
        </el-checkbox-group>
      </el-form-item>

      <el-form-item v-if="form.notifyMethods.includes('email')" label="邮箱地址" prop="email">
        <el-input v-model="form.email" placeholder="example@mail.com" />
      </el-form-item>

      <el-form-item v-if="form.notifyMethods.includes('sms')" label="手机号码" prop="phone">
        <el-input v-model="form.phone" placeholder="13800138000" />
      </el-form-item>
    </el-form>

    <template #footer>
      <div class="flex gap-3">
        <el-button class="flex-grow" @click="visible = false">取消</el-button>
        <el-button type="primary" class="flex-grow" :loading="submitting" :disabled="submitting" @click="handleSubmit">开启提醒</el-button>
      </div>
    </template>
  </el-dialog>
</template>
