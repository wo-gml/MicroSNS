"use client";

import { useParams, useRouter } from "next/navigation";
import { getPost } from "@/api/posts";
import CommentList from "./CommentList";
import PostDetailCard from "./PostDetailCard";
import RecruitmentPanel from "./RecruitmentPanel";
import { EmptyState, ErrorState, LoadingState } from "@/components/States";
import { useResource } from "@/hooks/useResource";
import { parseId } from "@/lib/format";

function PostDetail({ id }: { id: number }) {
  const router = useRouter();
  const { data: post, setData, error, reload } = useResource(() => getPost(id));

  if (error) return <ErrorState error={error} onRetry={reload} />;
  if (!post) return <LoadingState rows={1} />;
  return (
    <>
      <PostDetailCard post={post} onChange={setData} onDeleted={() => router.replace("/")} />
      {post.recruitment && (
        <RecruitmentPanel
          recruitment={post.recruitment}
          postId={id}
          authorId={post.author.id}
          onChanged={reload}
        />
      )}
      <CommentList key={id} postId={id} onChanged={reload} />
    </>
  );
}

export default function PostDetailView() {
  const id = parseId(useParams().id);
  if (id === null) return <EmptyState title="게시글을 찾을 수 없습니다." />;
  return <PostDetail key={id} id={id} />;
}
