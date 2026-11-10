// 팔로우 버튼. 본인에게는 보이지 않습니다.
"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { toApiError } from "@/api/client";
import { followUser, unfollowUser } from "@/api/users";
import { useAuth } from "@/hooks/useAuth";

export default function FollowButton({
  userId,
  following,
  onChange,
}: {
  userId: number;
  following: boolean;
  onChange: (following: boolean) => void;
}) {
  const { status, user } = useAuth();
  const router = useRouter();
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (user?.id === userId) return null;

  async function toggle() {
    if (status !== "authenticated") {
      const next = window.location.pathname + window.location.search;
      router.push(`/login?next=${encodeURIComponent(next)}`);
      return;
    }
    setPending(true);
    setError(null);
    try {
      await (following ? unfollowUser(userId) : followUser(userId));
      onChange(!following);
    } catch (caught) {
      setError(toApiError(caught).message);
    } finally {
      setPending(false);
    }
  }

  return (
    <span className="follow">
      <button
        className={`button${following ? "" : " button--primary"}`}
        type="button"
        aria-pressed={following}
        disabled={pending}
        onClick={toggle}
      >
        {following ? "팔로잉" : "팔로우"}
      </button>
      {error && (
        <span className="inline-error" role="alert">
          {error}
        </span>
      )}
    </span>
  );
}
