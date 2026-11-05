// 백엔드 라우터가 아직 없어 직접 작성한 타입입니다.
// 라우터가 완성되면 openapi-typescript로 생성한 파일로 교체합니다.

// backend/app/pagination.py의 PageResponse
export type Page<T> = {
  items: T[];
  limit: number;
  offset: number;
  has_more: boolean;
};

export type PageParams = { limit: number; offset: number };

// backend/app/schemas/user.py의 CurrentUser
export type CurrentUser = {
  id: number;
  email: string;
  name: string;
  bio: string | null;
  created_at: string;
};

export type UserSummary = { id: number; name: string };

export type UserListItem = UserSummary & {
  bio: string | null;
  is_following: boolean;
};

export type UserProfile = UserListItem & {
  created_at: string;
  post_count: number;
  follower_count: number;
  following_count: number;
};

export type Post = {
  id: number;
  author: UserSummary & { is_following: boolean };
  content: string;
  image_urls: string[];
  created_at: string;
  like_count: number;
  comment_count: number;
  liked_by_me: boolean;
};

export type Comment = {
  id: number;
  post_id: number;
  parent_id: number | null;
  author: UserSummary;
  content: string;
  created_at: string;
};

export type NotificationType = "like" | "comment" | "reply" | "follow";

export type Notification = {
  id: number;
  type: NotificationType;
  actor: UserSummary;
  post_id: number | null;
  preview: string | null; // 관련 글이나 댓글의 내용. 팔로우 알림에는 없습니다.
  is_read: boolean;
  created_at: string;
};

export type HashtagStat = { tag: string; post_count: number };
