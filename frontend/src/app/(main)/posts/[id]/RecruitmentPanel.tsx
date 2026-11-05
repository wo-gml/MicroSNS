// 글 상세의 모집 영역. 작성자는 지원을 처리하고, 다른 회원은 지원합니다.
"use client";

import { useState, type FormEvent } from "react";
import Link from "next/link";
import { toApiError } from "@/api/client";
import {
  applyToRecruitment,
  cancelApplication,
  closeRecruitment,
  getApplications,
  isRecruiting,
  MAX_APPLICATION_MESSAGE_LENGTH,
  updateApplicationStatus,
} from "@/api/recruitments";
import type { Application, ApplicationStatus, Recruitment } from "@/api/types";
import Avatar from "@/components/Avatar";
import RecruitmentSummary from "@/components/RecruitmentSummary";
import { ErrorState, ListFooter, LoadingState } from "@/components/States";
import { useAuth } from "@/hooks/useAuth";
import { usePagedList } from "@/hooks/usePagedList";
import { formatFullDate, formatRelativeTime } from "@/lib/format";

const STATUS_LABELS: Record<ApplicationStatus, string> = {
  pending: "대기 중",
  accepted: "수락됨",
  rejected: "거절됨",
};

function ApplicationRow({
  application,
  canAccept,
  onUpdated,
}: {
  application: Application;
  canAccept: boolean;
  onUpdated: (application: Application) => void;
}) {
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { applicant } = application;

  async function decide(status: "accepted" | "rejected") {
    if (status === "rejected" && !window.confirm(`${applicant.name}님의 지원을 거절할까요?`)) return;
    setPending(true);
    setError(null);
    try {
      onUpdated(await updateApplicationStatus(application.id, status));
    } catch (caught) {
      setError(toApiError(caught).message);
    } finally {
      setPending(false);
    }
  }

  return (
    <li className="application">
      <Avatar user={applicant} />
      <div className="application-main">
        <header className="post-meta">
          <Link className="name" href={`/users/${applicant.id}`}>
            {applicant.name}
          </Link>
          <time
            className="meta"
            dateTime={application.created_at}
            title={formatFullDate(application.created_at)}
          >
            {formatRelativeTime(application.created_at)}
          </time>
        </header>
        {application.message && <p className="post-text">{application.message}</p>}
        {error && (
          <p className="inline-error" role="alert">
            {error}
          </p>
        )}
      </div>
      {application.status === "pending" ? (
        <div className="application-actions">
          <button className="button" type="button" disabled={pending} onClick={() => decide("rejected")}>
            거절
          </button>
          <button
            className="button button--primary"
            type="button"
            disabled={pending || !canAccept}
            onClick={() => decide("accepted")}
          >
            수락
          </button>
        </div>
      ) : (
        <span className="meta">{STATUS_LABELS[application.status]}</span>
      )}
    </li>
  );
}

function ApplicationManager({
  recruitment,
  onChanged,
}: {
  recruitment: Recruitment;
  onChanged: () => void;
}) {
  const list = usePagedList<Application>((page) => getApplications(recruitment.id, page));

  if (list.status === "loading") return <LoadingState rows={1} />;
  if (list.status === "error" && list.error) {
    return <ErrorState error={list.error} onRetry={list.reload} />;
  }
  if (list.items.length === 0) return <p className="recruitment-note">아직 지원자가 없습니다.</p>;

  return (
    <>
      <h2 className="recruitment-title">지원자</h2>
      <ul>
        {list.items.map((application) => (
          <ApplicationRow
            key={application.id}
            application={application}
            canAccept={recruitment.accepted_count < recruitment.capacity}
            onUpdated={(next) => {
              list.replaceItem(next);
              onChanged(); // 수락 인원이 바뀝니다.
            }}
          />
        ))}
      </ul>
      <ListFooter
        hasMore={list.hasMore}
        loadingMore={list.loadingMore}
        error={list.error}
        onLoadMore={list.loadMore}
      />
    </>
  );
}

function ApplyForm({
  recruitment,
  onChanged,
}: {
  recruitment: Recruitment;
  onChanged: () => void;
}) {
  const [message, setMessage] = useState("");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (pending) return;
    setPending(true);
    setError(null);
    try {
      await applyToRecruitment(recruitment.id, message.trim() || null);
      onChanged();
    } catch (caught) {
      setError(toApiError(caught).message);
    } finally {
      setPending(false);
    }
  }

  return (
    <form className="application-form" onSubmit={handleSubmit}>
      <label className="sr-only" htmlFor="application-message">
        지원 메시지
      </label>
      <textarea
        id="application-message"
        className="application-input"
        rows={2}
        maxLength={MAX_APPLICATION_MESSAGE_LENGTH}
        placeholder="지원 메시지를 입력하세요 (선택)"
        value={message}
        onChange={(event) => setMessage(event.target.value)}
      />
      {error && (
        <p className="inline-error" role="alert">
          {error}
        </p>
      )}
      <button className="button button--primary" type="submit" disabled={pending}>
        {pending ? "지원 중…" : "지원하기"}
      </button>
    </form>
  );
}

function MyApplicationStatus({
  recruitment,
  onChanged,
}: {
  recruitment: Recruitment;
  onChanged: () => void;
}) {
  const application = recruitment.my_application;
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  if (!application) return null;
  const { id, message, status } = application;

  async function handleCancel() {
    if (!window.confirm("지원을 취소할까요?")) return;
    setPending(true);
    setError(null);
    try {
      await cancelApplication(id);
      onChanged();
    } catch (caught) {
      setError(toApiError(caught).message);
    } finally {
      setPending(false);
    }
  }

  return (
    <div className="my-application">
      <p className="my-application-status">
        내 지원: <strong>{STATUS_LABELS[status]}</strong>
        {status === "pending" && (
          <button className="text-button" type="button" disabled={pending} onClick={handleCancel}>
            지원 취소
          </button>
        )}
      </p>
      {message && <p className="post-text">{message}</p>}
      {error && (
        <p className="inline-error" role="alert">
          {error}
        </p>
      )}
    </div>
  );
}

function CloseButton({
  recruitment,
  onChanged,
}: {
  recruitment: Recruitment;
  onChanged: () => void;
}) {
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleClose() {
    if (!window.confirm("모집을 마감할까요? 마감하면 더 이상 지원을 받지 않습니다.")) return;
    setPending(true);
    setError(null);
    try {
      await closeRecruitment(recruitment.id);
      onChanged();
    } catch (caught) {
      setError(toApiError(caught).message);
    } finally {
      setPending(false);
    }
  }

  return (
    <>
      <button className="text-button" type="button" disabled={pending} onClick={handleClose}>
        모집 마감
      </button>
      {error && (
        <span className="inline-error" role="alert">
          {error}
        </span>
      )}
    </>
  );
}

export default function RecruitmentPanel({
  recruitment,
  postId,
  authorId,
  onChanged,
}: {
  recruitment: Recruitment;
  postId: number;
  authorId: number;
  onChanged: () => void; // 지원 상태나 모집 상태가 바뀌었을 때 호출합니다.
}) {
  const { status, user } = useAuth();
  const isAuthor = user?.id === authorId;
  const open = isRecruiting(recruitment);

  return (
    <section className="recruitment" aria-label="모집">
      <div className="recruitment-header">
        <RecruitmentSummary recruitment={recruitment} />
        {isAuthor && recruitment.status === "open" && (
          <CloseButton recruitment={recruitment} onChanged={onChanged} />
        )}
      </div>
      {isAuthor && <ApplicationManager recruitment={recruitment} onChanged={onChanged} />}
      {!isAuthor && recruitment.my_application && (
        // 취소 후 다시 지원하면 이전 상태가 남지 않도록 지원마다 새로 만듭니다.
        <MyApplicationStatus
          key={recruitment.my_application.id}
          recruitment={recruitment}
          onChanged={onChanged}
        />
      )}
      {user && !isAuthor && !recruitment.my_application && open && (
        <ApplyForm recruitment={recruitment} onChanged={onChanged} />
      )}
      {!user && status !== "loading" && open && (
        <p className="recruitment-note">
          <Link href={`/login?next=${encodeURIComponent(`/posts/${postId}`)}`}>로그인</Link>하면 지원할 수
          있습니다.
        </p>
      )}
    </section>
  );
}
