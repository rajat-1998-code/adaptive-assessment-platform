import {
  apiClient,
  API_ENDPOINTS,
  ApiError,
} from "@/lib/api";
import { env } from "@/config/env";
import type {
  AuthMessageResponse,
  AuthStatusResponse,
  AuthenticatedUser,
  LoginRequest,
  MagicLinkRequest,
  RegisterRequest,
  VerifyEmailRequest,
} from "@/types/api";

function oauthUrl(path: string) {
  const baseUrl = env.serverApiBaseUrl || env.apiBaseUrl;

  if (!baseUrl) {
    throw new ApiError(
      "API_BASE_URL or NEXT_PUBLIC_API_BASE_URL is not configured. Set one before using OAuth.",
    );
  }

  return new URL(path, baseUrl).toString();
}

export const authService = {
  getStatus() {
    return apiClient.get<AuthStatusResponse>(API_ENDPOINTS.auth);
  },

  getCurrentUser() {
    return apiClient.get<AuthenticatedUser>(API_ENDPOINTS.authMe);
  },

  login(payload: LoginRequest) {
    return apiClient.post<AuthenticatedUser>(API_ENDPOINTS.authLogin, payload);
  },

  register(payload: RegisterRequest) {
    return apiClient.post<AuthenticatedUser>(API_ENDPOINTS.authRegister, payload);
  },

  refresh() {
    return apiClient.post<AuthenticatedUser>(API_ENDPOINTS.authRefresh);
  },

  logout() {
    return apiClient.post<AuthMessageResponse>(API_ENDPOINTS.authLogout);
  },

  resendOtp() {
    return apiClient.post<AuthMessageResponse>(API_ENDPOINTS.authResendOtp);
  },

  verifyEmail(payload: VerifyEmailRequest) {
    return apiClient.post<AuthenticatedUser>(API_ENDPOINTS.authVerifyEmail, payload);
  },

  requestMagicLink(payload: MagicLinkRequest) {
    return apiClient.post<AuthMessageResponse>(API_ENDPOINTS.authMagicLink, payload);
  },

  verifyMagicLink(token: string) {
    const params = new URLSearchParams({ token });
    return apiClient.get<AuthenticatedUser>(`${API_ENDPOINTS.authMagicLinkVerify}?${params}`);
  },

  getGoogleOauthUrl() {
    return oauthUrl(API_ENDPOINTS.authOauthGoogle);
  },

  getGithubOauthUrl() {
    return oauthUrl(API_ENDPOINTS.authOauthGithub);
  },
};
