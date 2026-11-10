// 로그인/회원가입 API 호출 함수. 인증은 FastAPI가 심는 httpOnly 쿠키로 처리됩니다.
import { apiFetch } from "./client";
import type { CurrentUser } from "./types";

export type LoginInput = { email: string; password: string };
export type SignupInput = LoginInput & { name: string; bio?: string };

export function getMe() {
  return apiFetch<CurrentUser>("/auth/me");
}

export function login(input: LoginInput) {
  return apiFetch<CurrentUser>("/auth/login", { method: "POST", body: input });
}

export function signup(input: SignupInput) {
  return apiFetch<CurrentUser>("/auth/signup", { method: "POST", body: input });
}

export function logout() {
  return apiFetch<void>("/auth/logout", { method: "POST" });
}
