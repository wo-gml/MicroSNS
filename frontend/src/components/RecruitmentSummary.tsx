// 글에 달린 모집 정보 한 줄
"use client";

import { isRecruiting, RECRUITMENT_TYPE_LABELS } from "@/api/recruitments";
import type { Recruitment } from "@/api/types";
import { formatDeadline } from "@/lib/format";

export default function RecruitmentSummary({ recruitment }: { recruitment: Recruitment }) {
  const open = isRecruiting(recruitment);
  return (
    <p className="recruitment-summary">
      <span className={`recruitment-status${open ? " recruitment-status--open" : ""}`}>
        {open ? "모집 중" : "마감"}
      </span>
      <span className="meta">
        {RECRUITMENT_TYPE_LABELS[recruitment.type]} · {recruitment.accepted_count}/{recruitment.capacity}명 ·{" "}
        {formatDeadline(recruitment.deadline)} 마감
      </span>
    </p>
  );
}
