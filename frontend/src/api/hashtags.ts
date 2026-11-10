// 해시태그 API 호출 함수
import { apiFetch } from "./client";
import type { HashtagStat, Page, PageParams, Post } from "./types";

export function getTrendingHashtags(limit = 5) {
  return apiFetch<HashtagStat[]>("/hashtags/trending", { query: { limit } });
}

export function getHashtag(tag: string) {
  return apiFetch<HashtagStat>(`/hashtags/${encodeURIComponent(tag)}`);
}

export function getPostsByHashtag(tag: string, page: PageParams) {
  return apiFetch<Page<Post>>(`/hashtags/${encodeURIComponent(tag)}/posts`, { query: page });
}
