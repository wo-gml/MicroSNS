// 로그인해야 볼 수 있는 페이지에서 사용합니다. 비로그인이면 로그인 페이지로 보냅니다.
"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/hooks/useAuth";

export function useRequireLogin(nextPath?: string) {
  const auth = useAuth();
  const router = useRouter();
  const anonymous = auth.status === "anonymous";

  useEffect(() => {
    if (!anonymous) return;
    router.replace(nextPath ? `/login?next=${encodeURIComponent(nextPath)}` : "/login");
  }, [anonymous, nextPath, router]);

  return auth;
}
