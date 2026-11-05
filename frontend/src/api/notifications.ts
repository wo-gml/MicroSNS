// 알림 API 호출 함수
import { apiFetch } from "./client";
import type { Notification, Page, PageParams } from "./types";

// 알림을 읽음 처리한 뒤 발생시킵니다. NotificationBell이 듣고 배지를 새로 고칩니다.
export const NOTIFICATIONS_CHANGED_EVENT = "notifications:changed";

export function getNotifications(page: PageParams) {
  return apiFetch<Page<Notification>>("/notifications", { query: page });
}

export async function getUnreadCount() {
  const { count } = await apiFetch<{ count: number }>("/notifications/unread-count");
  return count;
}

export function markNotificationRead(id: number) {
  return apiFetch<void>(`/notifications/${id}/read`, { method: "POST" });
}
