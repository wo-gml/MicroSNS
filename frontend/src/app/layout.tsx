import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "microSNS",
  description: "스터디·프로젝트 모집 SNS",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="ko">
      <body>{children}</body>
    </html>
  );
}
