// 본문 위쪽 제목 줄. back이면 뒤로 가기 버튼을 표시합니다.
"use client";

import { useRouter } from "next/navigation";
import Icon from "@/components/Icon";

export default function PageHeader({
  title,
  back = false,
  children,
}: {
  title: string;
  back?: boolean;
  children?: React.ReactNode;
}) {
  const router = useRouter();

  function goBack() {
    // 주소를 직접 열어 이전 기록이 없으면 피드로 보냅니다.
    if (window.history.length > 1) router.back();
    else router.push("/");
  }

  return (
    <header className="page-header">
      {back && (
        <button className="icon-button" type="button" aria-label="뒤로 가기" onClick={goBack}>
          <Icon name="arrow-left" />
        </button>
      )}
      <h1>{title}</h1>
      {children}
    </header>
  );
}
