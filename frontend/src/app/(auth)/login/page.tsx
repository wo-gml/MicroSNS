// 로그인
import { Suspense } from "react";
import type { Metadata } from "next";
import AuthForm from "../AuthForm";

export const metadata: Metadata = { title: "로그인" };

export default function LoginPage() {
  return (
    <div className="auth">
      <header className="auth-brand">
        <h1>microSNS</h1>
        <p>스터디·프로젝트 모집 SNS</p>
      </header>
      <Suspense>
        <AuthForm mode="login" />
      </Suspense>
    </div>
  );
}
