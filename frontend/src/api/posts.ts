// 게시글 API 호출 함수
import { apiFetch } from "./client";
import type { RecruitmentInput } from "./recruitments";
import type { Page, PageParams, Post } from "./types";

export const MAX_POST_LENGTH = 500; // post.content varchar(500)
export const MAX_POST_IMAGES = 2;

export function getFeed(page: PageParams) {
  return apiFetch<Page<Post>>("/posts/feed", { query: page });
}

export function getPost(id: number) {
  return apiFetch<Post>(`/posts/${id}`);
}

// 글과 모집 정보가 함께 저장되도록 한 요청으로 보냅니다.
export function createPost(content: string, imageUrls: string[], recruitment: RecruitmentInput | null) {
  return apiFetch<Post>("/posts", {
    method: "POST",
    body: { content, image_urls: imageUrls, recruitment },
  });
}

export function deletePost(id: number) {
  return apiFetch<void>(`/posts/${id}`, { method: "DELETE" });
}

export function likePost(id: number) {
  return apiFetch<void>(`/posts/${id}/like`, { method: "POST" });
}

export function unlikePost(id: number) {
  return apiFetch<void>(`/posts/${id}/like`, { method: "DELETE" });
}

export async function uploadImage(file: File) {
  const body = new FormData();
  body.append("file", file);
  const { url } = await apiFetch<{ url: string }>("/uploads", { method: "POST", body });
  return url;
}
