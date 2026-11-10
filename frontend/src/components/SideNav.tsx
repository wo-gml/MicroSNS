// 왼쪽 내비게이션. 모바일에서는 상단 바와 하단 탭으로 나뉩니다.
"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import Avatar from "@/components/Avatar";
import Icon, { type IconName } from "@/components/Icon";
import NotificationBell from "@/components/NotificationBell";
import { logout, useAuth } from "@/hooks/useAuth";

function NavLink({
  href,
  match,
  label,
  icon,
  children,
}: {
  href: string;
  match: string; // 이 경로로 시작하면 활성 상태로 표시합니다.
  label: string;
  icon: IconName;
  children?: React.ReactNode;
}) {
  const pathname = usePathname();
  const active = match === "/" ? pathname === "/" : pathname.startsWith(match);
  return (
    <Link
      className={`nav-item${active ? " nav-item--active" : ""}`}
      href={href}
      aria-current={active ? "page" : undefined}
    >
      <Icon name={icon} />
      <span>{label}</span>
      {children}
    </Link>
  );
}

export default function SideNav() {
  const { status, user } = useAuth();
  const router = useRouter();
  const [logoutFailed, setLogoutFailed] = useState(false);

  async function handleLogout() {
    setLogoutFailed(false);
    try {
      await logout();
      router.replace("/login");
    } catch {
      setLogoutFailed(true);
    }
  }

  return (
    <aside className="sidenav">
      <div className="sidenav-top">
        <Link className="logo" href="/">
          microSNS
        </Link>
        <nav className="nav" aria-label="주요 메뉴">
          <NavLink href="/" match="/" label="홈" icon="home" />
          {user && (
            <>
              <NavLink href="/notifications" match="/notifications" label="알림" icon="bell">
                <NotificationBell />
              </NavLink>
              <NavLink href={`/users/${user.id}`} match="/users" label="프로필" icon="user" />
            </>
          )}
        </nav>
      </div>
      <div className="sidenav-bottom">
        {logoutFailed && (
          <p className="inline-error" role="alert">
            로그아웃하지 못했습니다.
          </p>
        )}
        {user ? (
          <div className="current-user">
            <Link className="current-user-link" href={`/users/${user.id}`}>
              <Avatar user={user} />
              <span className="name">{user.name}</span>
            </Link>
            <button className="text-button" type="button" onClick={handleLogout}>
              로그아웃
            </button>
          </div>
        ) : (
          status !== "loading" && (
            <Link className="button button--wide" href="/login">
              로그인
            </Link>
          )
        )}
      </div>
    </aside>
  );
}
