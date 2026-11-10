"use client";

import { getFeed } from "@/api/posts";
import type { CurrentUser } from "@/api/types";
import PostForm from "./PostForm";
import { PostListView } from "@/components/PostList";
import { ErrorState, LoadingState } from "@/components/States";
import { refreshAuth } from "@/hooks/useAuth";
import { usePagedList } from "@/hooks/usePagedList";
import { useRequireLogin } from "@/hooks/useRequireLogin";

function Feed({ user }: { user: CurrentUser }) {
  const list = usePagedList(getFeed);
  return (
    <>
      <PostForm user={user} onCreated={list.prependItem} />
      <PostListView
        list={list}
        empty={{
          title: "피드가 아직 비어 있습니다.",
          hint: "인기 해시태그에서 함께할 사람을 찾아 팔로우해 보세요.",
        }}
      />
    </>
  );
}

export default function FeedView() {
  const { status, user, error } = useRequireLogin();
  if (status === "error") return <ErrorState error={error} onRetry={refreshAuth} />;
  if (status !== "authenticated") return <LoadingState />;
  // 다른 계정으로 바꾸면 이전 계정의 목록이 남지 않도록 새로 만듭니다.
  return <Feed key={user.id} user={user} />;
}
