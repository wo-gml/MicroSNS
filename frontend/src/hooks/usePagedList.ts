// limit/offset 목록 조회. 대상이 바뀌면 호출하는 쪽에서 key로 컴포넌트를 새로 만듭니다.
"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { ApiError, toApiError } from "@/api/client";
import type { Page, PageParams } from "@/api/types";

const PAGE_SIZE = 20;
const MAX_LIMIT = 100; // backend/app/pagination.py의 상한

export function usePagedList<T extends { id: number }>(
  fetchPage: (page: PageParams) => Promise<Page<T>>,
) {
  const [items, setItems] = useState<T[]>([]);
  const [status, setStatus] = useState<"loading" | "ready" | "error">("loading");
  const [error, setError] = useState<ApiError | null>(null);
  const [hasMore, setHasMore] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);

  const fetchRef = useRef(fetchPage);
  const latestRequest = useRef(0);
  const nextOffset = useRef(0); // 서버 기준으로 지금까지 읽은 행 수

  useEffect(() => {
    fetchRef.current = fetchPage;
  });

  const reload = useCallback(async () => {
    const request = ++latestRequest.current;
    const loaded = nextOffset.current;
    try {
      // 이미 펼쳐 둔 만큼 다시 받아 스크롤 위치가 유지되게 합니다.
      const limit = Math.min(MAX_LIMIT, Math.max(PAGE_SIZE, loaded));
      const page = await fetchRef.current({ limit, offset: 0 });
      if (request !== latestRequest.current) return;
      setItems(page.items);
      setHasMore(page.has_more);
      nextOffset.current = page.items.length;
      setError(null);
      setStatus("ready");
    } catch (caught) {
      if (request !== latestRequest.current) return;
      setError(toApiError(caught));
      // 이미 보이는 목록이 있으면 목록은 유지하고 아래쪽에 에러만 표시합니다.
      if (loaded === 0) setStatus("error");
    }
  }, []);

  // 페이지가 숨겨졌다 다시 보일 때(Activity)도 이 효과가 다시 실행되어 최신 값을 받습니다.
  useEffect(() => {
    void reload();
    return () => {
      latestRequest.current++;
      setLoadingMore(false);
    };
  }, [reload]);

  const loadMore = useCallback(async () => {
    const request = ++latestRequest.current;
    setLoadingMore(true);
    try {
      const page = await fetchRef.current({ limit: PAGE_SIZE, offset: nextOffset.current });
      if (request !== latestRequest.current) return;
      // 그 사이 새 글이 생기면 offset이 밀려 같은 항목이 다시 올 수 있습니다.
      setItems((current) => {
        const seen = new Set(current.map((item) => item.id));
        return [...current, ...page.items.filter((item) => !seen.has(item.id))];
      });
      setHasMore(page.has_more);
      nextOffset.current += page.items.length;
      setError(null);
    } catch (caught) {
      if (request === latestRequest.current) setError(toApiError(caught));
    } finally {
      if (request === latestRequest.current) setLoadingMore(false);
    }
  }, []);

  const prependItem = useCallback((item: T) => {
    nextOffset.current += 1;
    setItems((current) => [item, ...current]);
  }, []);

  // 오름차순 목록의 끝에 추가합니다. 다음 페이지에 다시 오면 loadMore가 중복을 걸러냅니다.
  const appendItem = useCallback((item: T) => {
    setItems((current) => [...current, item]);
  }, []);

  const removeItem = useCallback((id: number) => {
    nextOffset.current = Math.max(0, nextOffset.current - 1);
    setItems((current) => current.filter((item) => item.id !== id));
  }, []);

  const replaceItem = useCallback((next: T) => {
    setItems((current) => current.map((item) => (item.id === next.id ? next : item)));
  }, []);

  return {
    items,
    status,
    error,
    hasMore,
    loadingMore,
    reload,
    loadMore,
    prependItem,
    appendItem,
    removeItem,
    replaceItem,
  };
}

export type PagedList<T extends { id: number }> = ReturnType<typeof usePagedList<T>>;
