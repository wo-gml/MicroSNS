// 인기 해시태그
"use client";

import Link from "next/link";
import { getTrendingHashtags } from "@/api/hashtags";
import { useResource } from "@/hooks/useResource";

export default function TrendingPanel() {
  const { data, error } = useResource(() => getTrendingHashtags());

  // 보조 정보라 불러오지 못하거나 태그가 없으면 패널을 숨깁니다.
  if (error || data?.length === 0) return null;

  return (
    <section className="trending" aria-labelledby="trending-title">
      <h2 id="trending-title">인기 해시태그</h2>
      {data?.map(({ name, post_count }) => (
        <Link className="trending-row" key={name} href={`/hashtags/${encodeURIComponent(name)}`}>
          <span className="trending-tag">#{name}</span>
          <span className="meta">{post_count}개의 글</span>
        </Link>
      ))}
    </section>
  );
}
