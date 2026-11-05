// 댓글 API 호출 함수
import { apiFetch } from "./client";
import type { Comment, Page, PageParams } from "./types";

export const MAX_COMMENT_LENGTH = 300; // comment.content varchar(300)

// 작성 시각 오름차순입니다.
export function getComments(postId: number, page: PageParams) {
  return apiFetch<Page<Comment>>(`/posts/${postId}/comments`, { query: page });
}

export function createComment(postId: number, content: string) {
  return apiFetch<Comment>(`/posts/${postId}/comments`, {
    method: "POST",
    body: { content },
  });
}

export function deleteComment(id: number) {
  return apiFetch<void>(`/comments/${id}`, { method: "DELETE" });
}
