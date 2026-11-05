// 로그인 상태. 모든 컴포넌트가 하나의 상태를 공유하도록 모듈 스토어로 둡니다.
"use client";

import { useEffect, useSyncExternalStore } from "react";
import * as authApi from "@/api/auth";
import { ApiError, setUnauthorizedHandler, toApiError } from "@/api/client";
import type { CurrentUser } from "@/api/types";

type AuthState =
  | { status: "loading"; user: null; error: null }
  | { status: "authenticated"; user: CurrentUser; error: null }
  | { status: "anonymous"; user: null; error: null }
  // 서버 장애 등으로 로그인 여부를 알 수 없는 상태입니다. 로그아웃으로 취급하지 않습니다.
  | { status: "error"; user: null; error: ApiError };

const LOADING: AuthState = { status: "loading", user: null, error: null };
const ANONYMOUS: AuthState = { status: "anonymous", user: null, error: null };

let state: AuthState = LOADING;
let started = false;
let latestRequest = 0;
const listeners = new Set<() => void>();

function setState(next: AuthState) {
  state = next;
  listeners.forEach((listener) => listener());
}

function setUser(user: CurrentUser) {
  latestRequest++; // 진행 중인 refreshAuth 결과가 덮어쓰지 못하게 합니다.
  setState({ status: "authenticated", user, error: null });
}

setUnauthorizedHandler(() => {
  latestRequest++;
  setState(ANONYMOUS);
});

export async function refreshAuth() {
  const request = ++latestRequest;
  setState(LOADING);
  try {
    const user = await authApi.getMe();
    if (request === latestRequest) setState({ status: "authenticated", user, error: null });
  } catch (error) {
    if (request !== latestRequest) return;
    const apiError = toApiError(error);
    setState(
      apiError.status === 401 ? ANONYMOUS : { status: "error", user: null, error: apiError },
    );
  }
}

export async function login(input: authApi.LoginInput) {
  setUser(await authApi.login(input));
}

export async function signup(input: authApi.SignupInput) {
  setUser(await authApi.signup(input));
}

export async function logout() {
  await authApi.logout();
  latestRequest++;
  setState(ANONYMOUS);
}

function subscribe(listener: () => void) {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}

export function useAuth() {
  const auth = useSyncExternalStore(
    subscribe,
    () => state,
    () => LOADING,
  );
  useEffect(() => {
    if (started) return;
    started = true;
    void refreshAuth();
  }, []);
  return auth;
}
