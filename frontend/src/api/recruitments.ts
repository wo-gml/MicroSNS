// 모집/지원 API 호출 함수
import { apiFetch } from "./client";
import type {
  Application,
  ApplicationStatus,
  Page,
  PageParams,
  Recruitment,
  RecruitmentType,
} from "./types";

export const MAX_APPLICATION_MESSAGE_LENGTH = 300; // application.message varchar(300)

export const RECRUITMENT_TYPE_LABELS: Record<RecruitmentType, string> = {
  study: "스터디",
  project: "프로젝트",
};

export type RecruitmentInput = {
  type: RecruitmentType;
  capacity: number;
  deadline: string;
};

// 마감 처리, 마감일 지남, 정원 초과 중 하나라도 해당하면 더 지원할 수 없습니다.
export function isRecruiting(recruitment: Recruitment) {
  return (
    recruitment.status === "open" &&
    new Date(recruitment.deadline).getTime() > Date.now() &&
    recruitment.accepted_count < recruitment.capacity
  );
}

export function closeRecruitment(id: number) {
  return apiFetch<Recruitment>(`/recruitments/${id}`, {
    method: "PATCH",
    body: { status: "closed" },
  });
}

export function getApplications(recruitmentId: number, page: PageParams) {
  return apiFetch<Page<Application>>(`/recruitments/${recruitmentId}/applications`, { query: page });
}

export function applyToRecruitment(recruitmentId: number, message: string | null) {
  return apiFetch<Application>(`/recruitments/${recruitmentId}/applications`, {
    method: "POST",
    body: { message },
  });
}

export function updateApplicationStatus(id: number, status: ApplicationStatus) {
  return apiFetch<Application>(`/applications/${id}`, { method: "PATCH", body: { status } });
}

export function cancelApplication(id: number) {
  return apiFetch<void>(`/applications/${id}`, { method: "DELETE" });
}
