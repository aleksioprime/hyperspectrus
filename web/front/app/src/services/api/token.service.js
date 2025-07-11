import { backendClient } from "./axios.clients";
import jwtService from "@/services/jwt/jwt.service";
import { jwtDecode } from "jwt-decode";
import logger from '@/common/helpers/logger';
import { useAuthStore } from '@/stores/auth';

let isRefreshing = false;
let refreshSubscribers = [];

function onRefreshed(token) {
  refreshSubscribers.forEach(callback => callback(token));
  refreshSubscribers = [];
}

function addSubscriber(callback) {
  refreshSubscribers.push(callback);
}

async function _refreshToken() {
  logger.info("Токен истёк. Обновление токена...");

  try {
    const result = await backendClient.post("/api/v1/refresh/", {
      refresh_token: jwtService.getRefreshToken(),
    });

    if (result.data.access_token) {
      const authStore = useAuthStore();
      authStore.access_token = result.data.access_token;

      jwtService.saveAccessToken(result.data.access_token);
      logger.info(`Получен новый токен, срок действия: ${_getEncodedTokenData(result.data.access_token)}`);
      return result.data.access_token;
    }
  } catch (error) {
    console.error("Failed to refresh token", error);
    return false;
  }
}

function _getEncodedTokenData(token) {
  const decodedToken = jwtDecode(token);
  return new Date(decodedToken.exp * 1000).toLocaleString();
}

export async function handleTokenRefresh() {
  if (!isRefreshing) {
    isRefreshing = true;
    return _refreshToken()
      .then(token => {
        isRefreshing = false;
        onRefreshed(token);
        return token;
      })
      .catch(error => {
        isRefreshing = false;
        throw error;
      });
  }

  return new Promise((resolve, reject) => {
    addSubscriber(token => token ? resolve(token) : reject(new Error("Token refresh failed")));
  });
}