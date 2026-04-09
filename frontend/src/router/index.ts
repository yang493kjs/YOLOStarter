import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    redirect: '/realtime',
  },
  {
    path: '/realtime',
    name: 'Realtime',
    component: () => import('@/views/realtime/index.vue'),
    meta: { title: '实时预测' },
  },
  {
    path: '/history',
    name: 'History',
    component: () => import('@/views/models/index.vue'),
    meta: { title: '模型管理器' },
  },
  {
    path: '/training',
    name: 'Training',
    component: () => import('@/views/training/index.vue'),
    meta: { title: '训练数据' },
  },
  {
    path: '/dataset',
    name: 'DatasetList',
    component: () => import('@/views/dataset-list/index.vue'),
    meta: { title: '数据集' },
  },
  {
    path: '/dataset/:id',
    name: 'DatasetDetail',
    component: () => import('@/views/dataset/index.vue'),
    meta: { title: '数据集详情' },
  },
  {
    path: '/guide',
    name: 'Guide',
    component: () => import('@/views/guide/index.vue'),
    meta: { title: '使用指南' },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// 路由守卫 - 设置页面标题
router.beforeEach((to, _from, next) => {
  document.title = `${to.meta.title || 'YOLO检测系统'} - YOLO检测系统`
  next()
})

export default router
