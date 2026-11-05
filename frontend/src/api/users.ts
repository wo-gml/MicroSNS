// 회원 프로필/팔로우 API 호출 함수
import { apiFetch } from "./client";
import type { Page, PageParams, Post, UserListItem, UserProfile } from "./types";

export function getUser(id: number) {
  return apiFetch<UserProfile>(`/users/${id}`);
}

export function getUserPosts(id: number, page: PageParams) {
  return apiFetch<Page<Post>>(`/users/${id}/posts`, { query: page });
}

export function getUserLikes(id: number, page: PageParams) {
  return apiFetch<Page<Post>>(`/users/${id}/likes`, { query: page });
}

export function getFollowers(id: number, page: PageParams) {
  return apiFetch<Page<UserListItem>>(`/users/${id}/followers`, { query: page });
}

export function getFollowing(id: number, page: PageParams) {
  return apiFetch<Page<UserListItem>>(`/users/${id}/following`, { query: page });
}

export function followUser(id: number) {
  return apiFetch<void>(`/users/${id}/follow`, { method: "POST" });
}

export function unfollowUser(id: number) {
  return apiFetch<void>(`/users/${id}/follow`, { method: "DELETE" });
}
