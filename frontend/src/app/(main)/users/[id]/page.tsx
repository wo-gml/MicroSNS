// 내 글, 좋아요한 글, 팔로워/팔로잉
import { Suspense } from "react";
import type { Metadata } from "next";
import PageHeader from "@/components/PageHeader";
import { LoadingState } from "@/components/States";
import ProfileView from "./ProfileView";
import "./profile.css";

export const metadata: Metadata = { title: "프로필" };

export default function ProfilePage() {
  return (
    <>
      <PageHeader title="프로필" back />
      <Suspense fallback={<LoadingState rows={1} />}>
        <ProfileView />
      </Suspense>
    </>
  );
}
