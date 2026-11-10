"use client";

import Link from "next/link";
import { useParams, useSearchParams } from "next/navigation";
import type { PageParams } from "@/api/types";
import { getFollowers, getFollowing, getUser, getUserLikes, getUserPosts } from "@/api/users";
import Avatar from "@/components/Avatar";
import FollowButton from "@/components/FollowButton";
import PostList from "@/components/PostList";
import { EmptyState, ErrorState, LoadingState } from "@/components/States";
import UserList from "./UserList";
import { useAuth } from "@/hooks/useAuth";
import { useResource } from "@/hooks/useResource";
import { formatYearMonth, parseId } from "@/lib/format";

const TABS = [
  { key: "posts", label: "작성한 글" },
  { key: "likes", label: "좋아요한 글" },
  { key: "followers", label: "팔로워" },
  { key: "following", label: "팔로잉" },
] as const;

type Tab = (typeof TABS)[number]["key"];

function parseTab(value: string | null): Tab {
  return TABS.find((tab) => tab.key === value)?.key ?? "posts";
}

function tabHref(id: number, tab: Tab) {
  return tab === "posts" ? `/users/${id}` : `/users/${id}?tab=${tab}`;
}

function Profile({ id, tab }: { id: number; tab: Tab }) {
  const { user: me } = useAuth();
  const { data: profile, setData, error, reload } = useResource(() => getUser(id));

  if (error) return <ErrorState error={error} onRetry={reload} />;
  if (!profile) return <LoadingState rows={1} />;

  return (
    <>
      <section className="profile">
        <Avatar user={profile} size={88} />
        <div className="profile-info">
          <div className="profile-name-row">
            <h2>{profile.name}</h2>
            <FollowButton
              userId={id}
              following={profile.is_following}
              onChange={(is_following) =>
                setData({
                  ...profile,
                  is_following,
                  follower_count: profile.follower_count + (is_following ? 1 : -1),
                })
              }
            />
          </div>
          <div className="profile-stats">
            <span className="stat">
              글 <strong>{profile.post_count}</strong>
            </span>
            <Link className="stat" href={tabHref(id, "followers")} replace scroll={false}>
              팔로워 <strong>{profile.follower_count}</strong>
            </Link>
            <Link className="stat" href={tabHref(id, "following")} replace scroll={false}>
              팔로잉 <strong>{profile.following_count}</strong>
            </Link>
          </div>
          {profile.bio && <p className="profile-bio">{profile.bio}</p>}
          <p className="meta">{formatYearMonth(profile.created_at)} 가입</p>
        </div>
      </section>

      <nav className="tabs" aria-label="프로필 목록">
        {TABS.map(({ key, label }) => (
          <Link
            key={key}
            className={`tab${tab === key ? " tab--active" : ""}`}
            href={tabHref(id, key)}
            aria-current={tab === key ? "page" : undefined}
            replace
            scroll={false}
          >
            {label}
          </Link>
        ))}
      </nav>

      {tab === "posts" && (
        <PostList
          key="posts"
          fetchPage={(page: PageParams) => getUserPosts(id, page)}
          empty={{ title: me?.id === id ? "아직 작성한 글이 없습니다." : "아직 올라온 글이 없습니다." }}
        />
      )}
      {tab === "likes" && (
        <PostList
          key="likes"
          fetchPage={(page: PageParams) => getUserLikes(id, page)}
          empty={{ title: "좋아요한 글이 없습니다." }}
        />
      )}
      {tab === "followers" && (
        <UserList
          // 이 프로필을 팔로우/취소하면 명단이 달라지므로 다시 받습니다.
          key={`followers-${profile.follower_count}`}
          fetchPage={(page: PageParams) => getFollowers(id, page)}
          emptyTitle="아직 팔로워가 없습니다."
          onFollowChange={reload}
        />
      )}
      {tab === "following" && (
        <UserList
          key="following"
          fetchPage={(page: PageParams) => getFollowing(id, page)}
          emptyTitle="아직 팔로우한 사람이 없습니다."
          onFollowChange={reload}
        />
      )}
    </>
  );
}

export default function ProfileView() {
  const id = parseId(useParams().id);
  const tab = parseTab(useSearchParams().get("tab"));
  if (id === null) return <EmptyState title="회원을 찾을 수 없습니다." />;
  return <Profile key={id} id={id} tab={tab} />;
}
