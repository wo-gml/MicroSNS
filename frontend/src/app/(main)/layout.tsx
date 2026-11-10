// 왼쪽 내비게이션, 가운데 본문, 오른쪽 인기 해시태그의 3단 레이아웃
import { Suspense } from "react";
import SideNav from "@/components/SideNav";
import TrendingPanel from "@/components/TrendingPanel";
import "./layout.css";

export default function MainLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="shell">
      {/* SideNav는 현재 주소를 읽으므로 동적 경로의 사전 렌더링을 위해 Suspense가 필요합니다. */}
      <Suspense fallback={<aside className="sidenav" />}>
        <SideNav />
      </Suspense>
      <main className="main">{children}</main>
      <aside className="aside">
        <TrendingPanel />
      </aside>
    </div>
  );
}
