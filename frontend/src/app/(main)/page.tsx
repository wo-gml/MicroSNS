// 피드: 팔로우한 사람의 글
import PageHeader from "@/components/PageHeader";
import FeedView from "./FeedView";
import "./feed.css";

export default function FeedPage() {
  return (
    <>
      <PageHeader title="피드" />
      <FeedView />
    </>
  );
}
