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
  recruitment: Recruitment | null; // recruitment.post_id가 유니크라 글 하나에 최대 하나입니다.
};

export type Comment = {
  id: number;
  post_id: number;
  author: UserSummary;
  content: string;
  created_at: string;
};

// ERD 이미지에 enum 값이 보이지 않아 임시로 정한 값입니다. 스키마가 나오면 맞춥니다.
export type RecruitmentType = "study" | "project";
export type RecruitmentStatus = "open" | "closed";
export type ApplicationStatus = "pending" | "accepted" | "rejected";
export type NotificationType = "like" | "comment" | "follow" | "application" | "application_result";

export type Recruitment = {
  id: number;
  post_id: number;
  type: RecruitmentType;
  capacity: number;
  deadline: string;
  status: RecruitmentStatus;
  created_at: string;
  updated_at: string;
  accepted_count: number; // status가 accepted인 지원 수
  my_application: MyApplication | null; // 로그인한 회원의 지원. 없거나 비로그인이면 null입니다.
};

export type MyApplication = {
  id: number;
  message: string | null;
  status: ApplicationStatus;
};

export type Application = MyApplication & {
  recruitment_id: number;
  applicant: UserSummary;
  created_at: string;
  updated_at: string;
};

export type Notification = {
  id: number;
  type: NotificationType;
  actor: UserSummary;
  post_id: number | null;
  content: string; // 화면에 그대로 보여 주는 알림 문구
  is_read: boolean;
  created_at: string;
};

export type HashtagStat = { name: string; post_count: number };
