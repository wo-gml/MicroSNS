// 댓글 목록, 답글 들여쓰기
"use client";

import { useMemo, useState, type FormEvent } from "react";
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

type CommentRow = { comment: Comment; depth: number };

const MAX_INDENT_DEPTH = 3;

// 답글이 부모 바로 아래에 오도록 정렬하고 깊이를 계산합니다.
function toRows(comments: Comment[]) {
  const ids = new Set(comments.map((comment) => comment.id));
  const children = new Map<number | null, Comment[]>();
  for (const comment of comments) {
    // 부모가 삭제된 답글은 맨 위 단계로 표시합니다.
    const parent = comment.parent_id !== null && ids.has(comment.parent_id) ? comment.parent_id : null;
    children.set(parent, [...(children.get(parent) ?? []), comment]);
  }
  const rows: CommentRow[] = [];
  const visit = (parent: number | null, depth: number) => {
    for (const comment of children.get(parent) ?? []) {
      rows.push({ comment, depth });
      visit(comment.id, depth + 1);
    }
  };
  visit(null, 0);
  return rows;
}

function CommentComposer({
  postId,
  parentId,
  user,
  placeholder,
  autoFocus = false,
  onCreated,
  onCancel,
}: {
  postId: number;
  parentId: number | null;
  user?: UserSummary; // 있으면 시안의 댓글 입력 줄처럼 아바타를 표시합니다.
  placeholder: string;
  autoFocus?: boolean;
  onCreated: (comment: Comment) => void;
  onCancel?: () => void;
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
      onCreated(await createComment(postId, content.trim(), parentId));
      setContent("");
    } catch (caught) {
      setError(toApiError(caught).message);
    } finally {
      setPending(false);
    }
  }

  return (
    <form className={`comment-composer${user ? "" : " comment-composer--reply"}`} onSubmit={handleSubmit}>
      <div className="comment-composer-row">
        {user && <Avatar user={user} />}
        <input
          className="comment-input"
          aria-label={placeholder}
          placeholder={placeholder}
          maxLength={MAX_COMMENT_LENGTH}
          autoFocus={autoFocus}
          value={content}
          onChange={(event) => setContent(event.target.value)}
        />
        {onCancel && (
          <button className="button" type="button" onClick={onCancel}>
            취소
          </button>
        )}
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
  row: { comment, depth },
  replying,
  onReply,
  onCreated,
  onDelete,
}: {
  row: CommentRow;
  replying: boolean;
  onReply: (id: number | null) => void;
  onCreated: (comment: Comment) => void;
  onDelete: (id: number) => Promise<void>;
}) {
  const { status, user } = useAuth();
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
    <li
      className="comment"
      style={{ "--depth": Math.min(depth, MAX_INDENT_DEPTH) } as React.CSSProperties}
    >
      <Avatar user={comment.author} />
      <div className="comment-main">
        <header className="post-meta">
          <Link className="name" href={`/users/${comment.author.id}`}>
            {comment.author.name}
          </Link>
          <time className="meta" dateTime={comment.created_at} title={formatFullDate(comment.created_at)}>
            {formatRelativeTime(comment.created_at)}
          </time>
          {status === "authenticated" && (
            <button className="text-button" type="button" onClick={() => onReply(comment.id)}>
              답글
            </button>
          )}
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
        {replying && (
          <CommentComposer
            postId={comment.post_id}
            parentId={comment.id}
            autoFocus
            placeholder={`${comment.author.name}님에게 답글 입력`}
            onCreated={(reply) => {
              onCreated(reply);
              onReply(null);
            }}
            onCancel={() => onReply(null)}
          />
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
  const [replyingTo, setReplyingTo] = useState<number | null>(null);
  const rows = useMemo(() => toRows(list.items), [list.items]);

  function handleCreated(comment: Comment) {
    list.appendItem(comment);
    onChanged();
  }

  // 답글까지 함께 지워질 수 있으므로 서버 기준으로 다시 받습니다.
  async function handleDelete(id: number) {
    await deleteComment(id);
    await list.reload();
    onChanged();
  }

  return (
    <section aria-label="댓글">
      {user ? (
        <CommentComposer
          postId={postId}
          parentId={null}
          user={user}
          placeholder="댓글을 입력하세요"
          onCreated={handleCreated}
        />
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
            {rows.map((row) => (
              <CommentItem
                key={row.comment.id}
                row={row}
                replying={replyingTo === row.comment.id}
                onReply={setReplyingTo}
                onCreated={handleCreated}
                onDelete={handleDelete}
              />
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
