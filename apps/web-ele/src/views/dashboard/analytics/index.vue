<template>
  <div class="analytics-container p-6 bg-gray-50 dark:bg-zinc-950 min-h-screen">
    <div class="max-w-7xl mx-auto space-y-6">
      <div
        class="flex justify-between items-center bg-white dark:bg-zinc-900 p-6 rounded-2xl shadow-sm border border-gray-100 dark:border-zinc-800 transition-all hover:shadow-md"
      >
        <div>
          <h1 class="text-3xl font-bold text-gray-900 dark:text-zinc-50 tracking-tight">
            数据分析看板
          </h1>
          <p class="mt-1 text-gray-500 dark:text-zinc-400">
            Real-time data insights and performance metrics
          </p>
        </div>
        <div class="flex gap-3">
          <button
            class="px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-xl font-medium transition-all shadow-[0_4px_14px_0_rgba(37,99,235,0.39)]"
          >
            Export Report
          </button>
        </div>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <!-- Stat Cards -->
        <div
          v-for="i in 4"
          :key="i"
          class="bg-white dark:bg-zinc-900 p-6 rounded-2xl shadow-sm border border-gray-100 dark:border-zinc-800 hover:-translate-y-1 transition-all duration-300"
        >
          <div class="flex items-center justify-between mb-4">
            <div
              class="w-10 h-10 rounded-xl bg-blue-50 dark:bg-blue-900/20 flex items-center justify-center"
            >
              <div class="w-5 h-5 bg-blue-500 rounded-full animate-pulse"></div>
            </div>
            <span
              class="text-xs font-semibold px-2 py-1 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 rounded-lg"
              >+12.5%</span>
          </div>
          <h3 class="text-gray-500 dark:text-zinc-400 text-sm font-medium">Metric Title {{ i }}</h3>
          <p class="text-2xl font-bold text-gray-900 dark:text-zinc-100 mt-1">$4,250.00</p>
        </div>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div
          class="lg:col-span-2 bg-white dark:bg-zinc-900 p-8 rounded-2xl shadow-sm border border-gray-100 dark:border-zinc-800 min-h-[400px] flex flex-col items-center justify-center relative overflow-hidden group"
        >
          <div
            class="absolute inset-0 bg-gradient-to-br from-blue-50 to-transparent dark:from-blue-900/10 opacity-50"
          ></div>
          <div class="z-10 text-center">
            <div
              class="w-20 h-20 bg-blue-100 dark:bg-blue-900/30 rounded-full flex items-center justify-center mx-auto mb-4 group-hover:scale-110 transition-transform duration-500"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                class="w-10 h-10 text-blue-600 dark:text-blue-400"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
                stroke-linecap="round"
                stroke-linejoin="round"
              >
                <path d="M3 3v18h18" />
                <path d="m19 9-5 5-4-4-3 3" />
              </svg>
            </div>
            <h2 class="text-xl font-semibold text-gray-900 dark:text-zinc-100">
              Analytics Graph Placeholder
            </h2>
            <p class="text-gray-500 dark:text-zinc-400 mt-2 max-w-sm">
              Detailed performance analytics and trend monitoring visualization will appear here.
            </p>
          </div>
        </div>

        <div
          class="bg-white dark:bg-zinc-900 p-8 rounded-2xl shadow-sm border border-gray-100 dark:border-zinc-800"
        >
          <h3 class="text-lg font-bold text-gray-900 dark:text-zinc-100 mb-6">Recent Activities</h3>
          <div class="space-y-6">
            <div v-for="item in 5" :key="item" class="flex gap-4">
              <div class="w-2 h-2 rounded-full bg-blue-600 mt-2 shrink-0"></div>
              <div>
                <p class="text-sm font-medium text-gray-800 dark:text-zinc-200">
                  System update available
                </p>
                <p class="text-xs text-gray-500 dark:text-zinc-500 mt-1">2 hours ago</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.analytics-container {
  animation: fade-in 0.6s ease-out;
}

@keyframes fade-in {
  from {
    opacity: 0;
    transform: translateY(10px);
  }

  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
