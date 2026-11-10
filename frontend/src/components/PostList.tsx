// 게시글 목록
"use client";

import type { Page, PageParams, Post } from "@/api/types";
import PostCard from "@/components/PostCard";
import { EmptyState, ErrorState, ListFooter, LoadingState } from "@/components/States";
import { usePagedList, type PagedList } from "@/hooks/usePagedList";

type Empty = { title: string; hint?: string };

// 목록 상태를 부모가 직접 다뤄야 할 때(글 작성 후 맨 위에 추가 등) 사용합니다.
export function PostListView({ list, empty }: { list: PagedList<Post>; empty: Empty }) {
  if (list.status === "loading") return <LoadingState />;
  if (list.status === "error" && list.error) {
    return <ErrorState error={list.error} onRetry={list.reload} />;
  }
  if (list.items.length === 0) return <EmptyState {...empty} />;
  return (
    <>
      {list.items.map((post) => (
        <PostCard
          key={post.id}
          post={post}
          onChange={list.replaceItem}
          onDeleted={list.removeItem}
        />
      ))}
      <ListFooter
        hasMore={list.hasMore}
        loadingMore={list.loadingMore}
        error={list.error}
        onLoadMore={list.loadMore}
      />
    </>
  );
}

export default function PostList({
  fetchPage,
  empty,
}: {
  fetchPage: (page: PageParams) => Promise<Page<Post>>;
  empty: Empty;
}) {
  const list = usePagedList(fetchPage);
  return <PostListView list={list} empty={empty} />;
}
