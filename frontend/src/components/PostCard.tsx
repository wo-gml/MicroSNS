// 목록용 게시글 카드. 카드 전체가 상세 페이지 링크입니다.
"use client";

import { useState } from "react";
import Link from "next/link";
import { toApiError } from "@/api/client";
import { deletePost } from "@/api/posts";
import type { Post } from "@/api/types";
import Avatar from "@/components/Avatar";
import Icon from "@/components/Icon";
import LikeButton from "@/components/LikeButton";
import { PostText } from "@/components/RichText";
import { useAuth } from "@/hooks/useAuth";
import { formatFullDate, formatRelativeTime } from "@/lib/format";

export type PostCardProps = {
  post: Post;
  onChange: (post: Post) => void;
  onDeleted: (id: number) => void;
};

export function PostMedia({ post }: { post: Post }) {
  if (post.image_urls.length === 0) return null;
  return (
    <div className="media">
      {post.image_urls.map((url) => (
        <img key={url} src={url} alt="" />
      ))}
    </div>
  );
}

export function PostActions({ post, onChange, onDeleted }: PostCardProps) {
  const { user } = useAuth();
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleDelete() {
    if (!window.confirm("이 글을 삭제할까요?")) return;
    setDeleting(true);
    setError(null);
    try {
      await deletePost(post.id);
      onDeleted(post.id);
    } catch (caught) {
      setError(toApiError(caught).message);
      setDeleting(false);
    }
  }

  return (
    <footer className="post-actions">
      <LikeButton
        postId={post.id}
        liked={post.liked_by_me}
        count={post.like_count}
        onChange={(liked_by_me, like_count) => onChange({ ...post, liked_by_me, like_count })}
      />
      <Link className="action" href={`/posts/${post.id}`} aria-label={`댓글 ${post.comment_count}개`}>
        <Icon name="message" />
        <span>{post.comment_count}</span>
      </Link>
      {user?.id === post.author.id && (
        <button
          className="text-button post-delete"
          type="button"
          disabled={deleting}
          onClick={handleDelete}
        >
          삭제
        </button>
      )}
      {error && (
        <span className="inline-error" role="alert">
          {error}
        </span>
      )}
    </footer>
  );
}

export default function PostCard(props: PostCardProps) {
  const { post } = props;
  return (
    <article className="post">
      <Link
        className="post-link"
        href={`/posts/${post.id}`}
        aria-label={`${post.author.name}님의 글 자세히 보기`}
      />
      <Avatar user={post.author} />
      <div className="post-main">
        <header className="post-meta">
          <Link className="name" href={`/users/${post.author.id}`}>
            {post.author.name}
          </Link>
          <time className="meta" dateTime={post.created_at} title={formatFullDate(post.created_at)}>
            {formatRelativeTime(post.created_at)}
          </time>
        </header>
        <PostText content={post.content} />
        <PostMedia post={post} />
        <PostActions {...props} />
      </div>
    </article>
  );
}

