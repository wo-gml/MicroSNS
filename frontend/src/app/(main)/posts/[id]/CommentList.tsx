// 댓글 목록
"use client";

import { useState, type FormEvent } from "react";
import Link from "next/link";
import { toApiError } from "@/api/client";
import { createComment, deleteComment, getComments, MAX_COMMENT_LENGTH } from "@/api/comments";
import type { Comment, UserSummary } from "@/api/types";
import Avatar from "@/components/Avatar";
import RichText from "@/components/RichText";
import { EmptyState, ErrorState, ListFooter, LoadingState } from "@/components/States";
import { useAuth } from "@/hooks/useAuth";
import { usePagedList } from "@/hooks/usePagedList";
import { formatFullDate, formatRelativeTime } from "@/lib/format";

const PLACEHOLDER = "댓글을 입력하세요";

function CommentComposer({
  postId,
  user,
  onCreated,
}: {
  postId: number;
  user: UserSummary;
  onCreated: (comment: Comment) => void;
}) {
  const [content, setContent] = useState("");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (pending || !content.trim()) return;
    setPending(true);
    setError(null);
    try {
      onCreated(await createComment(postId, content.trim()));
      setContent("");
    } catch (caught) {
      setError(toApiError(caught).message);
    } finally {
      setPending(false);
    }
  }

  return (
    <form className="comment-composer" onSubmit={handleSubmit}>
      <div className="comment-composer-row">
        <Avatar user={user} />
        <input
          className="comment-input"
          aria-label={PLACEHOLDER}
          placeholder={PLACEHOLDER}
          maxLength={MAX_COMMENT_LENGTH}
          value={content}
          onChange={(event) => setContent(event.target.value)}
        />
        <button className="button button--primary" type="submit" disabled={pending}>
          {pending ? "등록 중…" : "등록"}
        </button>
      </div>
      {error && (
        <p className="inline-error" role="alert">
          {error}
        </p>
      )}
    </form>
  );
}

function CommentItem({
  comment,
  onDelete,
}: {
  comment: Comment;
  onDelete: (id: number) => Promise<void>;
}) {
  const { user } = useAuth();
  const [error, setError] = useState<string | null>(null);

  async function handleDelete() {
    if (!window.confirm("이 댓글을 삭제할까요?")) return;
    setError(null);
    try {
      await onDelete(comment.id);
    } catch (caught) {
      setError(toApiError(caught).message);
    }
  }

  return (
    <li className="comment">
      <Avatar user={comment.author} />
      <div className="comment-main">
        <header className="post-meta">
          <Link className="name" href={`/users/${comment.author.id}`}>
            {comment.author.name}
          </Link>
          <time className="meta" dateTime={comment.created_at} title={formatFullDate(comment.created_at)}>
            {formatRelativeTime(comment.created_at)}
          </time>
          {user?.id === comment.author.id && (
            <button className="text-button" type="button" onClick={handleDelete}>
              삭제
            </button>
          )}
        </header>
        <p className="post-text">
          <RichText text={comment.content} />
        </p>
        {error && (
          <p className="inline-error" role="alert">
            {error}
          </p>
        )}
      </div>
    </li>
  );
}

export default function CommentList({
  postId,
  onChanged,
}: {
  postId: number;
  onChanged: () => void; // 댓글 수가 바뀌었을 때 호출합니다.
}) {
  const { status, user } = useAuth();
  const list = usePagedList<Comment>((page) => getComments(postId, page));

  function handleCreated(comment: Comment) {
    list.appendItem(comment);
    onChanged();
  }

  async function handleDelete(id: number) {
    await deleteComment(id);
    list.removeItem(id);
    onChanged();
  }

  return (
    <section aria-label="댓글">
      {user ? (
        <CommentComposer postId={postId} user={user} onCreated={handleCreated} />
      ) : (
        status !== "loading" && (
          <p className="comment-login">
            <Link href={`/login?next=${encodeURIComponent(`/posts/${postId}`)}`}>로그인</Link>하면 댓글을
            남길 수 있습니다.
          </p>
        )
      )}
      {list.status === "loading" && <LoadingState rows={2} />}
      {list.status === "error" && list.error && (
        <ErrorState error={list.error} onRetry={list.reload} />
      )}
      {list.status === "ready" && list.items.length === 0 && (
        <EmptyState title="아직 댓글이 없습니다." hint="첫 댓글을 남겨 보세요." />
      )}
      {list.status === "ready" && list.items.length > 0 && (
        <>
          <ul>
            {list.items.map((comment) => (
              <CommentItem key={comment.id} comment={comment} onDelete={handleDelete} />
            ))}
          </ul>
          <ListFooter
            hasMore={list.hasMore}
            loadingMore={list.loadingMore}
            error={list.error}
            onLoadMore={list.loadMore}
          />
        </>
      )}
    </section>
  );
}
