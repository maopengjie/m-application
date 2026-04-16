<script setup lang="ts">
import { ref, watch } from 'vue';
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

const props = defineProps<{
  modelValue: boolean;
  product?: any;
}>();

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void;
  (e: 'submit', data: any): void;
}>();

const form = ref({
  targetPrice: 0,
  email: '',
  phone: '',
  notifyMethods: ['web']
});

watch(() => props.product, (newVal) => {
  if (newVal) {
    form.value.targetPrice = Math.floor(newVal.price * 0.9);
  }
}, { immediate: true });

const visible = ref(props.modelValue);
watch(() => props.modelValue, (val) => visible.value = val);
watch(visible, (val) => emit('update:modelValue', val));

const handleSubmit = () => {
  emit('submit', {
    productId: props.product?.id,
    ...form.value
  });
  visible.value = false;
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
      <img :src="product.image" class="w-16 h-16 object-cover rounded border dark:border-zinc-700 bg-white dark:bg-zinc-900" />
      <div class="flex-grow min-w-0">
        <div class="text-sm font-bold truncate dark:text-zinc-200">{{ product.title }}</div>
        <div class="text-xs text-gray-500 dark:text-zinc-500 mt-1">当前价: <span class="text-red-500 font-bold">¥{{ product.price }}</span></div>
      </div>
    </div>

    <el-form label-position="top">
      <el-form-item label="期望价格 (当价格低于此值时提醒)">
        <el-input-number v-model="form.targetPrice" :precision="2" :step="10" class="!w-full" />
      </el-form-item>
      
      <el-form-item label="通过以下方式通知我">
        <el-checkbox-group v-model="form.notifyMethods">
          <el-checkbox value="web">站内信</el-checkbox>
          <el-checkbox value="email">邮件</el-checkbox>
          <el-checkbox value="sms">短信</el-checkbox>
        </el-checkbox-group>
      </el-form-item>

      <el-form-item v-if="form.notifyMethods.includes('email')" label="邮箱地址">
        <el-input v-model="form.email" placeholder="example@mail.com" />
      </el-form-item>

      <el-form-item v-if="form.notifyMethods.includes('sms')" label="手机号码">
        <el-input v-model="form.phone" placeholder="13800138000" />
      </el-form-item>
    </el-form>

    <template #footer>
      <div class="flex gap-3">
        <el-button class="flex-grow" @click="visible = false">取消</el-button>
        <el-button type="primary" class="flex-grow" @click="handleSubmit">开启提醒</el-button>
      </div>
    </template>
  </el-dialog>
</template>
