// 상세 페이지의 게시글. 작성자 줄에 팔로우 버튼이 있고 본문과 작성 시각을 크게 표시합니다.
"use client";

import Link from "next/link";
import Avatar from "@/components/Avatar";
import FollowButton from "@/components/FollowButton";
import { PostActions, PostMedia, type PostCardProps } from "@/components/PostCard";
import { PostText } from "@/components/RichText";
import { formatFullDate } from "@/lib/format";

export default function PostDetailCard(props: PostCardProps) {
  const { post, onChange } = props;
  return (
    <article className="post-detail">
      <header className="post-author">
        <Avatar user={post.author} />
        <Link className="name" href={`/users/${post.author.id}`}>
          {post.author.name}
        </Link>
        <FollowButton
          userId={post.author.id}
          following={post.author.is_following}
          onChange={(is_following) =>
            onChange({ ...post, author: { ...post.author, is_following } })
          }
        />
      </header>
      <PostText content={post.content} />
      <PostMedia post={post} />
      <time className="meta" dateTime={post.created_at}>
        {formatFullDate(post.created_at)}
      </time>
      <PostActions {...props} />
    </article>
  );
}
