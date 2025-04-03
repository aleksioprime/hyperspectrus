const ID_ACCESS_TOKEN_KEY = "accessToken";
const ID_REFRESH_TOKEN_KEY = "refreshToken";

class JwtService {
  getAccessToken() {
    return window.localStorage.getItem(ID_ACCESS_TOKEN_KEY);
  }

  getRefreshToken() {
    return window.localStorage.getItem(ID_REFRESH_TOKEN_KEY);
  }

  saveAccessToken(token) {
    window.localStorage.setItem(ID_ACCESS_TOKEN_KEY, token);
  }

  saveRefreshToken(token) {
    window.localStorage.setItem(ID_REFRESH_TOKEN_KEY, token);
  }

  destroyTokens() {
    window.localStorage.removeItem(ID_ACCESS_TOKEN_KEY);
    window.localStorage.removeItem(ID_REFRESH_TOKEN_KEY);
  }
}

export default new JwtService();