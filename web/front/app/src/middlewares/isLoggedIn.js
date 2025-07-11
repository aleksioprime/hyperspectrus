import { useAuthStore } from "@/stores/auth";
import jwtService from "@/services/jwt/jwt.service";
import logger from '@/common/helpers/logger';

export const isLoggedIn = async ({ to }) => {
  const authStore = useAuthStore();

  // Получаем access_token из локального хранилища
  const accessToken = jwtService.getAccessToken();

  // Если токен отсутствует или невалиден → пробуем обновить
  if (!accessToken || !authStore.isAuthenticated) {
    if (!jwtService.getRefreshToken()) return { name: "login" };
    try {
      logger.info("Попытка обновления токена....");
      await authStore.refresh(); // Обновляем токен
    } catch (error) {
      logger.error("Обновление токена не удалось:", error);
    }
  }

  // Если access-токен всё ещё отсутствует переход на страницу авторизации
  if (!accessToken) {
    return { name: "login" };
  }

  if (!authStore.user) {
    await authStore.getMe();
  }

  return true;
};
