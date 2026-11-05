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
      {data?.map(({ tag, post_count }) => (
        <Link className="trending-row" key={tag} href={`/hashtags/${encodeURIComponent(tag)}`}>
          <span className="trending-tag">#{tag}</span>
          <span className="meta">{post_count}개의 글</span>
        </Link>
      ))}
    </section>
  );
}
