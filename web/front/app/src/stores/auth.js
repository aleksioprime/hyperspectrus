import { defineStore } from "pinia";
import resources from "@/services/resources"; // API-ресурсы
import jwtService from "@/services/jwt/jwt.service"; // Работа с токенами
import { jwtDecode } from "jwt-decode"; // Декодирование JWT

export const useAuthStore = defineStore("auth", {
  state: () => ({
    user: null, // Текущий пользователь
    access_token: jwtService.getAccessToken(),
  }),

  getters: {
    /**
     * Проверка, аутентифицирован ли пользователь.
     * Возвращает true, если access-токен действителен.
     */
    isAuthenticated(state) {
      const token = state.access_token;
      if (!token) return false;

      try {
        const decodedToken = jwtDecode(token);
        const now = Math.floor(Date.now() / 1000);
        return decodedToken.exp > now;
      } catch (e) {
        return false;
      }
    },

    isAdmin(state) {
      return state.user?.roles?.some(role => role.name === 'admin');
    },

    isEmployee(state) {
      return state.user?.roles?.some(role => role.name === 'employee');
    },

    isSuperuser(state) {
      return state.user?.is_superuser;
    },
  },

  actions: {
    /**
     * Возвращает строку с оставшимся временем действия токена в формате "X мин Y сек".
     * Если токен уже истёк, возвращает строку "Токен истёк".
     */
    timeUntilExpiration(token) {
      const now = Math.floor(Date.now() / 1000);
      const secondsLeft = token.exp - now;

      if (secondsLeft <= 0) {
        return 'Токен истёк';
      }

      const minutes = Math.floor(secondsLeft / 60);
      const seconds = secondsLeft % 60;
      return `${minutes} мин ${seconds} сек`;
    },
    /**
     * Декодирует access-токен и возвращает данные пользователя.
     */
    getAuthData() {
      return jwtDecode(jwtService.getAccessToken());
    },
    // Получение ролей из переменной пользователя
    getAuthRoles() {
      return this.user?.roles?.map(gr => gr.name);
    },
    /**
     * Обновление access-токена по refresh-токену.
     * При неудаче выполняется выход из системы.
     */
    async refresh() {
      const token = jwtService.getRefreshToken()

      if (!token) return;

      const result = await resources.auth.refresh({
        refresh_token: token,
      });

      if (result.__state === "success") {
        this.access_token = result.data.access_token;
        jwtService.saveAccessToken(result.data.access_token);
        resources.auth.setAuthHeader(result.data.access_token);
        await this.getMe();
        return true;
      }

      await this.logout();
      return false;
    },

    /**
     * Аутентификация пользователя.
     * Сохраняет токены при успешной авторизации
     */
    async login(credentials) {
      const result = await resources.auth.login(credentials);

      if (result.__state === "success") {
        this.access_token = result.data.access_token;
        jwtService.saveAccessToken(result.data.access_token);
        jwtService.saveRefreshToken(result.data.refresh_token);
        resources.auth.setAuthHeader(result.data.access_token);
        return result.__state;
      }
      return (
        result.data?.response?.data?.detail ||
        result.data?.message ||
        "Ошибка авторизации"
      )
    },

    /**
     * Получение информации о текущем пользователе.
     */
    async getMe() {
      const result = await resources.auth.whoAmI();
      if (result.__state === "success") {
        this.user = result.data;
        return true;
      }
      jwtService.destroyTokens();
      resources.auth.setAuthHeader("");
      this.user = null;
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
