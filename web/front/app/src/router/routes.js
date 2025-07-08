import { isLoggedIn } from "@/middlewares/isLoggedIn";

export const routes = [
  {
    path: "/",
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
      title: 'Просмотр пациента',
      middlewares: [isLoggedIn],
    },
  },
  {
    path: '/patients/:patient_id/sessions/:id',
    name: 'session-detail',
    component: () => import('@/views/sessions/SessionDetail.vue'),
    meta: {
      title: 'Просмотр сессии',
      middlewares: [isLoggedIn],
    },
  },
  {
    path: "/profile",
    name: "profile",
    component: () => import("@/views/users/ProfileView.vue"),
    meta: {
      title: 'Профиль пользователя',
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
    path: "/users",
    name: "user",
    component: () => import("@/views/users/UserView.vue"),
    meta: {
      title: 'Пользователи',
      middlewares: [isLoggedIn],
    },
  },
  {
    path: "/organizations",
    name: "organization",
    component: () => import("@/views/organizations/OrganizationView.vue"),
    meta: {
      title: 'Организации',
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