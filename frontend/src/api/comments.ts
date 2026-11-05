// 댓글/답글 API 호출 함수
import { apiFetch } from "./client";
import type { Comment, Page, PageParams } from "./types";

export const MAX_COMMENT_LENGTH = 280;

// 작성 시각 오름차순이라고 가정합니다. 답글의 부모는 항상 답글보다 먼저 로드됩니다.
export function getComments(postId: number, page: PageParams) {
  return apiFetch<Page<Comment>>(`/posts/${postId}/comments`, { query: page });
}

export function createComment(postId: number, content: string, parentId: number | null) {
  return apiFetch<Comment>(`/posts/${postId}/comments`, {
    method: "POST",
    body: { content, parent_id: parentId },
  });
}

export function deleteComment(id: number) {
  return apiFetch<void>(`/comments/${id}`, { method: "DELETE" });
}
