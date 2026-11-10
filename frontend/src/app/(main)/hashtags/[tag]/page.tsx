// #태그 검색 결과
import { Suspense } from "react";
import type { Metadata } from "next";
import { LoadingState } from "@/components/States";
import HashtagView from "./HashtagView";

export const metadata: Metadata = { title: "해시태그" };

export default function HashtagPage() {
  return (
    <Suspense fallback={<LoadingState />}>
      <HashtagView />
    </Suspense>
  );
}
