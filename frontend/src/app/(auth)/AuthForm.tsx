// 로그인/회원가입 폼
"use client";

import { useEffect, useState, type FormEvent } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { toApiError, type FieldError } from "@/api/client";
import { login, signup, useAuth } from "@/hooks/useAuth";
import { safeNextPath } from "@/lib/format";

const MIN_PASSWORD_LENGTH = 8;

// 검증 에러의 field는 "body.email" 형식입니다.
function fieldMessage(errors: FieldError[], name: string) {
  return errors.find((error) => error.field.split(".").pop() === name)?.message;
}

function TextField({
  label,
  name,
  type = "text",
  placeholder,
  autoComplete,
  helper,
  minLength,
  maxLength,
  required = true,
  multiline = false,
  value,
  error,
  onChange,
}: {
  label: string;
  name: string;
  type?: string;
  placeholder: string;
  autoComplete?: string;
  helper?: string;
  minLength?: number;
  maxLength?: number;
  required?: boolean;
  multiline?: boolean;
  value: string;
  error?: string;
  onChange: (value: string) => void;
}) {
  const shared = {
    id: name,
    name,
    placeholder,
    maxLength,
    required,
    value,
    "aria-invalid": error ? true : undefined,
    "aria-describedby": error || helper ? `${name}-help` : undefined,
  };
  return (
    <div className="field">
      <label htmlFor={name}>{label}</label>
      {multiline ? (
        <textarea
          {...shared}
          className="input input--multiline"
          onChange={(event) => onChange(event.target.value)}
        />
      ) : (
        <input
          {...shared}
          className="input"
          type={type}
          autoComplete={autoComplete}
          minLength={minLength}
          onChange={(event) => onChange(event.target.value)}
        />
      )}
      {(error || helper) && (
        <p className={error ? "inline-error" : "meta"} id={`${name}-help`}>
          {error ?? helper}
        </p>
      )}
    </div>
  );
}

export default function AuthForm({ mode }: { mode: "login" | "signup" }) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { status } = useAuth();
  const [email, setEmail] = useState("");
  const [name, setName] = useState("");
  const [password, setPassword] = useState("");
  const [passwordConfirm, setPasswordConfirm] = useState("");
  const [bio, setBio] = useState("");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<FieldError[]>([]);

  const isSignup = mode === "signup";
  const nextParam = searchParams.get("next");
  const nextPath = safeNextPath(nextParam);

  // 이미 로그인했거나 방금 로그인에 성공하면 원래 보던 곳으로 이동합니다.
  useEffect(() => {
    if (status === "authenticated") router.replace(nextPath);
  }, [status, nextPath, router]);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    if (isSignup && password !== passwordConfirm) {
      setFieldErrors([{ field: "passwordConfirm", message: "비밀번호가 일치하지 않습니다." }]);
      return;
    }
    setFieldErrors([]);
    setPending(true);
    try {
      await (isSignup
        ? signup({ email, name: name.trim(), password, bio: bio.trim() || undefined })
        : login({ email, password }));
    } catch (caught) {
      const apiError = toApiError(caught);
      setError(apiError.message);
      setFieldErrors(apiError.details);
    } finally {
      // 페이지를 떠나도 상태가 보존되므로(Activity) 성공 시에도 비밀번호를 남기지 않습니다.
      setPassword("");
      setPasswordConfirm("");
      setPending(false);
    }
  }

  const otherHref = `${isSignup ? "/login" : "/signup"}${
    nextParam ? `?next=${encodeURIComponent(nextParam)}` : ""
  }`;

  return (
    // 스크립트가 로드되기 전에 제출돼도 비밀번호가 주소창에 남지 않도록 POST로 지정합니다.
    <form className="auth-form" method="post" onSubmit={handleSubmit}>
      <div className="auth-fields">
        <TextField
          label="이메일"
          name="email"
          type="email"
          placeholder="이메일을 입력하세요"
          autoComplete="email"
          maxLength={255}
          value={email}
          error={fieldMessage(fieldErrors, "email")}
          onChange={setEmail}
        />
        {isSignup && (
          <TextField
            label="이름"
            name="name"
            placeholder="이름을 입력하세요"
            autoComplete="name"
            maxLength={50}
            value={name}
            error={fieldMessage(fieldErrors, "name")}
            onChange={setName}
          />
        )}
        <TextField
          label="비밀번호"
          name="password"
          type="password"
          placeholder="비밀번호를 입력하세요"
          autoComplete={isSignup ? "new-password" : "current-password"}
          helper={isSignup ? `${MIN_PASSWORD_LENGTH}자 이상 입력하세요` : undefined}
          minLength={isSignup ? MIN_PASSWORD_LENGTH : undefined}
          value={password}
          error={fieldMessage(fieldErrors, "password")}
          onChange={setPassword}
        />
        {isSignup && (
          <>
            <TextField
              label="비밀번호 확인"
              name="passwordConfirm"
              type="password"
              placeholder="비밀번호를 한 번 더 입력하세요"
              autoComplete="new-password"
              value={passwordConfirm}
              error={fieldMessage(fieldErrors, "passwordConfirm")}
              onChange={setPasswordConfirm}
            />
            <TextField
              label="자기소개 (선택)"
              name="bio"
              placeholder="어떤 스터디나 프로젝트에 관심이 있나요?"
              required={false}
              multiline
              maxLength={200}
              value={bio}
              error={fieldMessage(fieldErrors, "bio")}
              onChange={setBio}
            />
          </>
        )}
      </div>
      {error && (
        <p className="inline-error" role="alert">
          {error}
        </p>
      )}
      <button className="button button--primary button--large" type="submit" disabled={pending}>
        {pending ? "처리 중…" : isSignup ? "가입하기" : "로그인"}
      </button>
      <p className="auth-switch">
        <span>{isSignup ? "이미 계정이 있으신가요?" : "계정이 없으신가요?"}</span>
        <Link href={otherHref}>{isSignup ? "로그인" : "회원가입"}</Link>
      </p>
    </form>
  );
}
