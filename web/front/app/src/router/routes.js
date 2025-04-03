import { isLoggedIn } from "@/middlewares/isLoggedIn";

export const routes = [
  {
    path: "/",
    name: "home",
    component: () => import("@/views/PatientView.vue"),
    meta: {
      title: 'Главная страница',
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