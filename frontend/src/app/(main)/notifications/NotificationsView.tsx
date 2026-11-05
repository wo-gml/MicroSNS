"use client";

import Link from "next/link";
import {
  getNotifications,
  markNotificationRead,
  NOTIFICATIONS_CHANGED_EVENT,
} from "@/api/notifications";
import type { Notification, NotificationType } from "@/api/types";
import Avatar from "@/components/Avatar";
import Icon from "@/components/Icon";
import { EmptyState, ErrorState, ListFooter, LoadingState } from "@/components/States";
import { refreshAuth } from "@/hooks/useAuth";
import { usePagedList } from "@/hooks/usePagedList";
import { useRequireLogin } from "@/hooks/useRequireLogin";
import { formatFullDate, formatRelativeTime } from "@/lib/format";

const MESSAGES: Record<NotificationType, string> = {
  like: "님이 회원님의 글을 좋아합니다.",
  comment: "님이 회원님의 글에 댓글을 남겼습니다.",
  reply: "님이 회원님의 댓글에 답글을 남겼습니다.",
  follow: "님이 회원님을 팔로우하기 시작했습니다.",
};

function NotificationList() {
  const list = usePagedList<Notification>(getNotifications);

  function handleOpen(item: Notification) {
    if (item.is_read) return;
    list.replaceItem({ ...item, is_read: true });
    // 이동을 막지 않도록 기다리지 않습니다. 실패하면 다음 조회 때 안 읽음으로 돌아옵니다.
    markNotificationRead(item.id).then(
      () => window.dispatchEvent(new Event(NOTIFICATIONS_CHANGED_EVENT)),
      () => {},
    );
  }

  if (list.status === "loading") return <LoadingState />;
  if (list.status === "error" && list.error) {
    return <ErrorState error={list.error} onRetry={list.reload} />;
  }
  if (list.items.length === 0) return <EmptyState title="새로운 알림이 없습니다." />;

  return (
    <>
      <ul>
        {list.items.map((item) => (
          <li key={item.id}>
            <Link
              className={`notification${item.is_read ? "" : " notification--unread"}`}
              href={item.post_id ? `/posts/${item.post_id}` : `/users/${item.actor.id}`}
              onClick={() => handleOpen(item)}
            >
              <Avatar user={item.actor} />
              <span className="notification-main">
                <span className="notification-line">
                  <span>
                    <strong>{item.actor.name}</strong>
                    {MESSAGES[item.type]}
                  </span>
                  <span className="notification-meta">
                    <time className="meta" dateTime={item.created_at} title={formatFullDate(item.created_at)}>
                      {formatRelativeTime(item.created_at)}
                    </time>
                    {!item.is_read && (
                      <>
                        <Icon name="unread-dot" />
                        <span className="sr-only">읽지 않음</span>
                      </>
                    )}
                  </span>
                </span>
                {item.preview && <span className="notification-preview">{item.preview}</span>}
              </span>
            </Link>
          </li>
        ))}
      </ul>
      <ListFooter
        hasMore={list.hasMore}
        loadingMore={list.loadingMore}
        error={list.error}
        onLoadMore={list.loadMore}
      />
    </>
  );
}

export default function NotificationsView() {
  const { status, user, error } = useRequireLogin("/notifications");
  if (status === "error") return <ErrorState error={error} onRetry={refreshAuth} />;
  if (status !== "authenticated") return <LoadingState />;
  return <NotificationList key={user.id} />;
}
