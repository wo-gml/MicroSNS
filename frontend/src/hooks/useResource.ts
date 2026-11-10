// 단건 데이터 조회. 대상이 바뀌면 호출하는 쪽에서 key로 컴포넌트를 새로 만듭니다.
"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { ApiError, toApiError } from "@/api/client";

export function useResource<T>(fetcher: () => Promise<T>) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<ApiError | null>(null);
  const fetcherRef = useRef(fetcher);
  const latestRequest = useRef(0);
  const hasData = useRef(false);

  useEffect(() => {
    fetcherRef.current = fetcher;
  });

  const reload = useCallback(async () => {
    const request = ++latestRequest.current;
    try {
      const result = await fetcherRef.current();
      if (request !== latestRequest.current) return;
      hasData.current = true;
      setData(result);
      setError(null);
    } catch (caught) {
      // 새로 고침만 실패했다면 이미 보이는 데이터를 유지합니다.
      if (request === latestRequest.current && !hasData.current) setError(toApiError(caught));
    }
  }, []);

  // 페이지가 숨겨졌다 다시 보일 때(Activity)도 이 효과가 다시 실행되어 최신 값을 받습니다.
  useEffect(() => {
    void reload();
    return () => {
      latestRequest.current++;
    };
  }, [reload]);

  return { data, setData, error, reload };
}
