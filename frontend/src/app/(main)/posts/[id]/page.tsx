// 글 + 모집 + 댓글
import { Suspense } from "react";
import type { Metadata } from "next";
import PageHeader from "@/components/PageHeader";
import { LoadingState } from "@/components/States";
import PostDetailView from "./PostDetailView";
import "./post-detail.css";

export const metadata: Metadata = { title: "게시글" };

export default function PostDetailPage() {
  return (
    <>
      <PageHeader title="게시글" back />
      <Suspense fallback={<LoadingState rows={1} />}>
        <PostDetailView />
      </Suspense>
    </>
  );
}
