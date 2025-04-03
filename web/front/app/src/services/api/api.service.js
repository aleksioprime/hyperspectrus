import { backendClient } from "./axios.clients";
import { handleTokenRefresh } from "./token.service";
import jwtService from "@/services/jwt/jwt.service";
import logger from '@/common/helpers/logger';
import { jwtDecode } from "jwt-decode";
import { getApiError } from "./api.error";


export class ApiService {
  constructor() {
    this.client = backendClient;
    this.initRequestInterceptor();
    this.initResponseInterceptor();
  }

  // Перехватчик запросов для проверки, обновления или добавления токена
  initRequestInterceptor() {
    this.client.interceptors.request.use(
      async (config) => {
        const excludedUrls = ["api/v1/login", "api/v1/refresh"];
        if (excludedUrls.some(url => config.url.includes(url))) return config;

        // Получение токена. Если его нет, то пропускаем запрос
        let token = jwtService.getAccessToken();
        if (!token) return config;

        // Проверка срока действия токена
        const decodedToken = jwtDecode(token);
        if (decodedToken.exp < Date.now() / 1000) {
          // Если токен истёк, то посылаем запрос на обновление
          logger.info(decodedToken, config.url);
          token = await handleTokenRefresh();
          if (!token) {
            logger.error("Ошибка обновления токена");
            this._redirectToLogin();
          }
        }

        // Добавляем токен в заголовок
        config.headers["Authorization"] = `Bearer ${token}`;
        return config;
      },
      (error) => Promise.reject(error)
    );
  }

  // Перехватчик ответов для перенаправления на авторизацию
  initResponseInterceptor() {
    this.client.interceptors.response.use(
      response => response,
      (error) => {
        const { config, response } = error;
        // Если в ответе ошибка авторизации, то перенаправляется на страницу логирования
        if (response && (response.status === 401 || response.status === 403) && !config._retry) {
          logger.error("Ошибка авторизации запроса");
          config._retry = true;
          this._redirectToLogin();
        }
        return Promise.reject(error);
      }
    );
  }

  // Перенаправление на страницу логирования сервиса авторизации
  async _redirectToLogin() {
    jwtService.destroyTokens();

    // Переход на страницу логирования в сервисе авторизации
    // const currentUrl = `${window.location.origin}${window.location.pathname}${window.location.search}`;
    // const authUrl = `${import.meta.env.VITE_AUTH_URL}/login?needAuth=true&redirect=${encodeURIComponent(currentUrl)}`;
    // window.location.href = authUrl;

    // Переход на страницу логирования в текущем сервисе
    // window.location.href = '/login';
  }

  // Логирование запросов
  _logRequest(method, url, params) {
    logger.info(`Выполнение ${method}-запроса по адресу "${url}" с параметрами:`, params || "-");
  }

  // Логирование ответов
  _logResponse(response) {
    logger.info(`Получен ответ (${response.status}, ${response.statusText}) ${response.config.method.toUpperCase()}-запроса  ${response.request.responseURL}: `, response.data || "-");
  }

  // Логирование ошибок
  _logError(e) {
    logger.info(`Данные ошибки`, e)
  }

  // Метод для получения ошибки
  _getError(e) {
    this._logError(e);
    return getApiError(e);
  }

  // Запросы без тела: GET, DELETE
  _wrapper1(method, methodName, url, config) {
    return async () => {
      this._logRequest(methodName, url, config);
      try {
        const response = await method(url, config);
        this._logResponse(response);
        return {
          __state: "success",
          ...response,
        };
      } catch (e) {
        return {
          __state: "error",
          data: this._getError(e),
        };
      }
    };
  }

  // Запросы с телом: POST, PUT, UPDATE
  _wrapper2(method, methodName, url, payload) {
    return async () => {
      this._logRequest(methodName, url, payload);
      try {
        const response = await method(url, payload);
        this._logResponse(response);
        return {
          __state: "success",
          ...response,
        };
      } catch (e) {
        return {
          __state: "error",
          data: this._getError(e),
        };
      }
    };
  }

  $get(url, config) {
    return this._wrapper1(this.client.get, "GET", url, config)();
  }

  $post(url, payload) {
    return this._wrapper2(this.client.post, "POST", url, payload)();
  }

  $put(url, payload) {
    return this._wrapper2(this.client.put, "PUT", url, payload)();
  }

  $patch(url, payload) {
    return this._wrapper2(this.client.patch, "PATCH", url, payload)();
  }

  $delete(url, payload) {
    return this._wrapper1(this.client.delete, "DELETE", url, payload)();
  }

  setAuthHeader(token) {
    this.client.defaults.headers.common["Authorization"] = token ? `Bearer ${token}` : "";
  }
}
