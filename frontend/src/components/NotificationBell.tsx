// 안 읽은 알림 개수
"use client";

import { useEffect, useState } from "react";
import { usePathname } from "next/navigation";
import { getUnreadCount, NOTIFICATIONS_CHANGED_EVENT } from "@/api/notifications";
import { useAuth } from "@/hooks/useAuth";

const POLL_INTERVAL = 30_000;

export default function NotificationBell() {
  const { status } = useAuth();
  const pathname = usePathname();
  const [count, setCount] = useState(0);
  const authenticated = status === "authenticated";

  useEffect(() => {
    if (!authenticated) return;
    let active = true;
    const refresh = () => {
      getUnreadCount()
        .then((next) => {
          if (active) setCount(next);
        })
        .catch(() => {}); // 배지는 보조 정보라 실패해도 화면을 막지 않습니다.
    };
    const poll = () => {
      if (!document.hidden) refresh();
    };
    refresh();
    const timer = window.setInterval(poll, POLL_INTERVAL);
    window.addEventListener(NOTIFICATIONS_CHANGED_EVENT, refresh);
    return () => {
      active = false;
      window.clearInterval(timer);
      window.removeEventListener(NOTIFICATIONS_CHANGED_EVENT, refresh);
    };
  }, [authenticated, pathname]);

  if (!authenticated || count === 0) return null;
  return (
    <span className="badge">
      <span aria-hidden="true">{count > 99 ? "99+" : count}</span>
      <span className="sr-only">안 읽은 알림 {count}개</span>
    </span>
  );
}
