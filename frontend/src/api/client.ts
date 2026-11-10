// fetch 기본 설정. next.config.ts의 프록시를 거쳐 FastAPI로 전달됩니다.
export const API_BASE_URL = "/api";

export type FieldError = { field: string; message: string };

// 백엔드 공통 에러 형식 {"error": {"code", "message", "details"}}를 담습니다.
export class ApiError extends Error {
  constructor(
    readonly status: number,
    readonly code: string,
    message: string,
    readonly details: FieldError[] = [],
  ) {
    super(message);
    this.name = "ApiError";
  }
}

type RequestOptions = {
  method?: "GET" | "POST" | "PATCH" | "DELETE";
  body?: unknown;
  query?: Record<string, string | number | undefined>;
};

let onUnauthorized: (() => void) | null = null;

// 세션이 만료되면 어떤 요청에서든 401을 받습니다. useAuth가 여기에 등록해 상태를 맞춥니다.
export function setUnauthorizedHandler(handler: () => void) {
  onUnauthorized = handler;
}

function buildUrl(path: string, query: RequestOptions["query"]) {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(query ?? {})) {
    if (value !== undefined) params.set(key, String(value));
  }
  const search = params.toString();
  return `${API_BASE_URL}${path}${search ? `?${search}` : ""}`;
}

export async function apiFetch<T>(
  path: string,
  { method = "GET", body, query }: RequestOptions = {},
): Promise<T> {
  // 파일 업로드(FormData)는 브라우저가 boundary를 포함한 Content-Type을 직접 넣습니다.
  const isJson = body !== undefined && !(body instanceof FormData);
  let response: Response;
  try {
    response = await fetch(buildUrl(path, query), {
      method,
      headers: isJson ? { "Content-Type": "application/json" } : undefined,
      body: isJson ? JSON.stringify(body) : (body as FormData | undefined),
    });
  } catch {
    throw new ApiError(0, "NETWORK_ERROR", "서버에 연결할 수 없습니다.");
  }

  // 백엔드가 꺼져 있으면 프록시가 JSON이 아닌 응답을 돌려주므로 파싱 실패를 허용합니다.
  const payload: unknown = await response.json().catch(() => null);

  if (!response.ok) {
    if (response.status === 401) onUnauthorized?.();
    const error = (payload as { error?: { code?: string; message?: string; details?: FieldError[] } } | null)?.error;
    throw new ApiError(
      response.status,
      error?.code ?? "HTTP_ERROR",
      error?.message ?? "서버에 연결할 수 없습니다.",
      error?.details,
    );
  }
  return payload as T;
}

export function toApiError(error: unknown): ApiError {
  return error instanceof ApiError
    ? error
    : new ApiError(0, "UNKNOWN_ERROR", "알 수 없는 오류가 발생했습니다.");
}
