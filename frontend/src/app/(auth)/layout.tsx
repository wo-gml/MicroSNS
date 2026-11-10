// 로그인·회원가입: 내비게이션 없이 가운데 폼만 표시합니다.
import "./auth.css";

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return <main className="auth-page">{children}</main>;
}
