// 알림 목록
import type { Metadata } from "next";
import PageHeader from "@/components/PageHeader";
import NotificationsView from "./NotificationsView";
import "./notifications.css";

export const metadata: Metadata = { title: "알림" };

export default function NotificationPage() {
  return (
    <>
      <PageHeader title="알림" />
      <NotificationsView />
    </>
  );
}
