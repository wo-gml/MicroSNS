// 회원가입
import { Suspense } from "react";
import type { Metadata } from "next";
import AuthForm from "../AuthForm";

export const metadata: Metadata = { title: "회원가입" };

export default function SignupPage() {
  return (
    <div className="auth">
      <header className="auth-brand">
        <h1>microSNS</h1>
        <p>계정을 만들고 함께할 사람을 찾아보세요</p>
      </header>
      <Suspense>
        <AuthForm mode="signup" />
      </Suspense>
    </div>
  );
}
