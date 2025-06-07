import { isLoggedIn } from "@/middlewares/isLoggedIn";

export const routes = [
  {
    path: "/",
    name: "home",
    component: () => import("@/views/HomeView.vue"),
    meta: {
      title: 'Главная страница',
      middlewares: [isLoggedIn],
    },
  },
  {
    path: "/patients",
    name: "patient",
    component: () => import("@/views/patients/PatientView.vue"),
    meta: {
      title: 'Пациенты',
      middlewares: [isLoggedIn],
    },
  },
  {
    path: '/patients/:id',
    name: 'patient-detail',
    component: () => import('@/views/patients/PatientDetail.vue'),
    meta: {
      title: '',
      middlewares: [isLoggedIn],
    },
  },
  {
    path: '/patients/:patient_id/sessions/:id',
    name: 'session-detail',
    component: () => import('@/views/sessions/SessionDetail.vue'),
    meta: {
      title: '',
      middlewares: [isLoggedIn],
    },
  },
  {
    path: "/profile",
    name: "profile",
    component: () => import("@/views/ProfileView.vue"),
    meta: {
      title: '',
      middlewares: [isLoggedIn],
    },
  },
  {
    path: "/devices",
    name: "device",
    component: () => import("@/views/devices/DeviceView.vue"),
    meta: {
      title: 'Устройства',
      middlewares: [isLoggedIn],
    },
  },
  {
    path: "/chromophores",
    name: "chromophore",
    component: () => import("@/views/chromophores/ChromophoreView.vue"),
    meta: {
      title: 'Хромофоры',
      middlewares: [isLoggedIn],
    },
  },
  {
    path: "/config",
    name: "config",
    component: () => import("@/views/ConfigView.vue"),
    meta: {
      title: '',
      middlewares: [isLoggedIn],
    },
  },
  {
    path: "/login",
    name: "login",
    component: () => import("@/views/Login.vue"),
    meta: {
      title: 'Авторизация',
      layout: "login",
    },
  },
]