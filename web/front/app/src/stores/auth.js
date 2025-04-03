import { defineStore } from "pinia";
import resources from "@/services/resources"; // API-ресурсы
import jwtService from "@/services/jwt/jwt.service"; // Работа с токенами
import { jwtDecode } from "jwt-decode"; // Декодирование JWT

export const useAuthStore = defineStore("auth", {
  state: () => ({
    user: null, // Текущий пользователь
  }),

  getters: {
    /**
     * Проверка, аутентифицирован ли пользователь.
     * Возвращает true, если access-токен действителен.
     */
    isAuthenticated() {
      const decodedToken = this.getAuthData();
      return decodedToken.exp > Math.floor(Date.now() / 1000);
    },
  },

  actions: {
    /**
     * Декодирует access-токен и возвращает данные пользователя.
     */
    getAuthData() {
      return jwtDecode(jwtService.getAccessToken());
    },

    /**
     * Обновление access-токена по refresh-токену.
     * При неудаче выполняется выход из системы.
     */
    async refresh() {
      const result = await resources.auth.refresh({
        refresh_token: jwtService.getRefreshToken(),
      });

      if (result.__state === "success") {
        jwtService.saveAccessToken(result.data.access_token);
        resources.auth.setAuthHeader(jwtService.getAccessToken());
      } else {
        await this.logout();
      }
    },

    /**
     * Аутентификация пользователя.
     * Сохраняет токены при успешной авторизации.
     * Возвращает "success" или сообщение об ошибке.
     */
    async login(credentials) {
      const result = await resources.auth.login(credentials);

      if (result.__state === "success") {
        jwtService.saveAccessToken(result.data.access_token);
        jwtService.saveRefreshToken(result.data.refresh_token);
        resources.auth.setAuthHeader(result.data.access_token); // исправлена опечатка
        return result.__state;
      }

      return result.data?.message || "Ошибка авторизации";
    },

    /**
     * Получение информации о текущем пользователе.
     */
    async getMe() {
      this.user = await resources.auth.whoAmI();
    },

    /**
     * Выход пользователя из системы.
     * Удаляет токены и очищает заголовок авторизации.
     */
    async logout() {
      const result = await resources.auth.logout({
        access_token: jwtService.getAccessToken(),
        refresh_token: jwtService.getRefreshToken(),
      });

      if (result.__state === "success") {
        jwtService.destroyTokens();
        resources.auth.setAuthHeader("");
        this.user = null;
      }
    },
  },
});
