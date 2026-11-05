// 게시글 API 호출 함수
import { apiFetch } from "./client";
import type { Page, PageParams, Post } from "./types";

export const MAX_POST_LENGTH = 280;
export const MAX_POST_IMAGES = 2;

export function getFeed(page: PageParams) {
  return apiFetch<Page<Post>>("/posts/feed", { query: page });
}

export function getPost(id: number) {
  return apiFetch<Post>(`/posts/${id}`);
}

export function createPost(content: string, imageUrls: string[]) {
  return apiFetch<Post>("/posts", {
    method: "POST",
    body: { content, image_urls: imageUrls },
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
