<script setup lang="ts">
import { onMounted, ref } from "vue";

import { Page } from "@vben/common-ui";

import { Card, CardContent, CardHeader, CardTitle } from "@vben-core/shadcn-ui";

import { ElMessage } from "element-plus";
import { Activity, Clock, PlayCircle, Server } from "lucide-vue-next";

import { getCrawlerTasksApi, triggerPriceUpdateApi } from "#/api/crawler";

const tasks = ref<any[]>([]);
const loading = ref(true);
const error = ref<null | string>(null);

const fetchTasks = async () => {
  loading.value = true;
  error.value = null;
  try {
    tasks.value = await getCrawlerTasksApi();
  } catch (error_: any) {
    error.value = error_.message || "获取任务列表失败";
    console.error("Failed to fetch tasks", error_);
  } finally {
    loading.value = false;
  }
};

const handleTriggerUpdate = async () => {
  try {
    await triggerPriceUpdateApi();
    ElMessage.success("更新任务已触发");
    void fetchTasks();
  } catch {
    ElMessage.error("触发失败");
  }
};

onMounted(() => {
  void fetchTasks();
});

const getStatusBadgeClass = (status: string) => {
  switch (status) {
    case "failed": {
      return "bg-destructive/10 text-destructive border-destructive/20";
    }
    case "running": {
      return "bg-primary/10 text-primary border-primary/20";
    }
    case "success": {
      return "bg-green-500/10 text-green-500 border-green-500/20";
    }
    default: {
      return "bg-muted text-muted-foreground border-muted-foreground/20";
    }
  }
};
</script>

<template>
  <Page
    title="爬虫任务管理"
    description="实时监控数据引擎的抓取任务，支持手动触发价格更新和异常排查。"
  >
    <div class="grid gap-6 md:grid-cols-4 mb-8">
      <Card class="bg-primary/5 border-primary/10">
        <CardHeader class="pb-2">
          <Activity class="h-4 w-4 text-primary" />
          <CardTitle class="text-sm font-medium">存活引擎</CardTitle>
        </CardHeader>
        <CardContent>
          <div class="text-2xl font-bold">1/1</div>
          <p class="text-xs text-muted-foreground">节点状态：正常</p>
        </CardContent>
      </Card>
      <!-- 其他统计卡片可以保留暂存 -->
    </div>

    <Card>
      <CardHeader class="flex flex-row items-center justify-between border-b pb-4">
        <div class="flex items-center gap-2">
          <Server class="h-5 w-5" />
          <CardTitle class="text-lg">任务流水</CardTitle>
        </div>
        <button
          @click="handleTriggerUpdate"
          class="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:opacity-90 transition-all shadow-lg active:scale-95"
        >
          <PlayCircle class="h-4 w-4" />
          触发全量价格更新
        </button>
      </CardHeader>
      <CardContent class="p-0">
        <div v-if="loading" class="flex justify-center items-center py-40">
          <span
            class="animate-spin h-8 w-8 border-4 border-primary border-t-transparent rounded-full"
          ></span>
        </div>

        <div v-else-if="error" class="flex flex-col items-center justify-center py-20">
          <el-empty :description="error">
            <template #extra>
              <el-button type="primary" @click="fetchTasks">重新加载</el-button>
            </template>
          </el-empty>
        </div>

        <div
          v-else-if="tasks.length === 0"
          class="flex flex-col items-center justify-center py-20 text-muted-foreground"
        >
          <el-empty description="暂无任务记录" />
        </div>
        <div v-else class="overflow-x-auto">
          <table class="w-full text-sm text-left">
            <thead class="bg-muted/50 text-muted-foreground uppercase text-xs font-semibold">
              <tr>
                <th class="px-6 py-4">任务ID</th>
                <th class="px-6 py-4">类型</th>
                <th class="px-6 py-4">状态</th>
                <th class="px-6 py-4">进度 (成功/失败/总计)</th>
                <th class="px-6 py-4">执行时间</th>
              </tr>
            </thead>
            <tbody class="divide-y">
              <tr v-for="task in tasks" :key="task.id" class="hover:bg-muted/30 transition-colors">
                <td class="px-6 py-4 font-mono">#{{ task.id }}</td>
                <td class="px-6 py-4">
                  <span class="px-2 py-1 rounded text-xs font-medium border bg-muted/50">
                    {{ task.task_type === "price_update" ? "全量价格更新" : "单一商品抓取" }}
                  </span>
                </td>
                <td class="px-6 py-4">
                  <div class="flex items-center gap-2">
                    <span
                      class="px-2 py-0.5 rounded-full border text-[10px] font-bold uppercase" :class="[
                        getStatusBadgeClass(task.status),
                      ]"
                    >
                      {{ task.status }}
                    </span>
                  </div>
                </td>
                <td class="px-6 py-4">
                  <div class="flex flex-col gap-1 w-32">
                    <div class="flex justify-between text-[10px] text-muted-foreground">
                      <span>{{ task.success_count }} / {{ task.total_count }}</span>
                      <span>{{
                          Math.round((task.success_count / (task.total_count || 1)) * 100)
                        }}%</span>
                    </div>
                    <div class="h-1.5 w-full bg-muted rounded-full overflow-hidden">
                      <div
                        class="h-full bg-primary"
                        :style="{
                          width: `${(task.success_count / (task.total_count || 1)) * 100}%`,
                        }"
                      ></div>
                    </div>
                  </div>
                </td>
                <td class="px-6 py-4 text-muted-foreground flex items-center gap-1">
                  <Clock class="h-3 w-3" />
                  {{ new Date(task.start_time).toLocaleString() }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  </Page>
</template>
