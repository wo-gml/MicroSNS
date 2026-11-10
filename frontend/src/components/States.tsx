// 로딩/빈 목록/에러 화면
"use client";

import Link from "next/link";
import type { ApiError } from "@/api/client";

export function LoadingState({ rows = 3 }: { rows?: number }) {
  return (
    <div className="skeleton-list" role="status">
      <span className="sr-only">불러오는 중입니다.</span>
      {Array.from({ length: rows }, (_, index) => (
        <div className="skeleton-row" key={index} aria-hidden="true">
          <span className="skeleton skeleton--circle" />
          <span className="skeleton-lines">
            <span className="skeleton skeleton--short" />
            <span className="skeleton" />
            <span className="skeleton skeleton--medium" />
          </span>
        </div>
      ))}
    </div>
  );
}

export function EmptyState({ title, hint }: { title: string; hint?: string }) {
  return (
    <div className="state">
      <p className="state-title">{title}</p>
      {hint && <p className="state-hint">{hint}</p>}
    </div>
  );
}

export function LoginPrompt({ title = "로그인이 필요합니다.", next }: { title?: string; next?: string }) {
  return (
    <div className="state">
      <p className="state-title">{title}</p>
      <Link
        className="button button--primary"
        href={next ? `/login?next=${encodeURIComponent(next)}` : "/login"}
      >
        로그인
      </Link>
    </div>
  );
}

export function ErrorState({ error, onRetry }: { error: ApiError; onRetry?: () => void }) {
  if (error.status === 401) return <LoginPrompt />;
  if (error.status === 404) {
    return (
      <div className="state">
        <p className="state-title">{error.message}</p>
        <Link className="button" href="/">
          피드로 돌아가기
        </Link>
      </div>
    );
  }
  return (
    <div className="state" role="alert">
      <p className="state-title">{error.message}</p>
      <p className="state-hint">잠시 후 다시 시도해 주세요.</p>
      {onRetry && (
        <button className="button" type="button" onClick={onRetry}>
          다시 시도
        </button>
      )}
    </div>
  );
}

// 목록 아래의 "더 보기"와 추가 로딩 실패 메시지
export function ListFooter({
  hasMore,
  loadingMore,
  error,
  onLoadMore,
}: {
  hasMore: boolean;
  loadingMore: boolean;
  error: ApiError | null;
  onLoadMore: () => void;
}) {
  if (!hasMore && !error) return null;
  return (
    <div className="list-footer">
      {error && (
        <p className="inline-error" role="alert">
          {error.message}
        </p>
      )}
      {hasMore && (
        <button className="button" type="button" disabled={loadingMore} onClick={onLoadMore}>
          {loadingMore ? "불러오는 중…" : "더 보기"}
        </button>
      )}
    </div>
  );
}
