// 팔로워/팔로잉 목록
"use client";

import Link from "next/link";
import type { Page, PageParams, UserListItem } from "@/api/types";
import Avatar from "@/components/Avatar";
import FollowButton from "@/components/FollowButton";
import { EmptyState, ErrorState, ListFooter, LoadingState } from "@/components/States";
import { usePagedList } from "@/hooks/usePagedList";

export default function UserList({
  fetchPage,
  emptyTitle,
  onFollowChange,
}: {
  fetchPage: (page: PageParams) => Promise<Page<UserListItem>>;
  emptyTitle: string;
  onFollowChange: () => void;
}) {
  const list = usePagedList(fetchPage);

  if (list.status === "loading") return <LoadingState />;
  if (list.status === "error" && list.error) {
    return <ErrorState error={list.error} onRetry={list.reload} />;
  }
  if (list.items.length === 0) return <EmptyState title={emptyTitle} />;

  return (
    <>
      <ul>
        {list.items.map((user) => (
          <li className="user-row" key={user.id}>
            <Avatar user={user} />
            <div className="user-row-main">
              <Link className="name" href={`/users/${user.id}`}>
                {user.name}
              </Link>
              {user.bio && <p className="meta">{user.bio}</p>}
            </div>
            <FollowButton
              userId={user.id}
              following={user.is_following}
              onChange={(is_following) => {
                list.replaceItem({ ...user, is_following });
                onFollowChange();
              }}
            />
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
