// 좋아요 버튼. 먼저 화면에 반영하고 요청이 실패하면 되돌립니다.
"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { likePost, unlikePost } from "@/api/posts";
import Icon from "@/components/Icon";
import { useAuth } from "@/hooks/useAuth";

export default function LikeButton({
  postId,
  liked,
  count,
  onChange,
}: {
  postId: number;
  liked: boolean;
  count: number;
  onChange: (liked: boolean, count: number) => void;
}) {
  const { status } = useAuth();
  const router = useRouter();
  const [pending, setPending] = useState(false);
  const [failed, setFailed] = useState(false);

  async function toggle() {
    if (status !== "authenticated") {
      const next = window.location.pathname + window.location.search;
      router.push(`/login?next=${encodeURIComponent(next)}`);
      return;
    }
    setPending(true);
    setFailed(false);
    onChange(!liked, count + (liked ? -1 : 1));
    try {
      await (liked ? unlikePost(postId) : likePost(postId));
    } catch {
      onChange(liked, count);
      setFailed(true);
    } finally {
      setPending(false);
    }
  }

  return (
    <>
      <button
        className={`action${liked ? " action--active" : ""}`}
        type="button"
        aria-pressed={liked}
        aria-label={`좋아요 ${count}개`}
        disabled={pending}
        onClick={toggle}
      >
        <Icon name={liked ? "heart-filled" : "heart"} />
        <span>{count}</span>
      </button>
      {failed && (
        <span className="inline-error" role="alert">
          좋아요를 반영하지 못했습니다.
        </span>
      )}
    </>
  );
}
