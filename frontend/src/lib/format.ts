const MINUTE = 60_000;
const HOUR = 60 * MINUTE;
const DAY = 24 * HOUR;

export function formatRelativeTime(value: string, now = Date.now()) {
  const date = new Date(value);
  const elapsed = now - date.getTime();
  if (elapsed < MINUTE) return "방금";
  if (elapsed < HOUR) return `${Math.floor(elapsed / MINUTE)}분 전`;
  if (elapsed < DAY) return `${Math.floor(elapsed / HOUR)}시간 전`;
  if (elapsed < 2 * DAY) return "어제";
  if (elapsed < 7 * DAY) return `${Math.floor(elapsed / DAY)}일 전`;
  if (elapsed < 30 * DAY) return `${Math.floor(elapsed / (7 * DAY))}주 전`;
  if (elapsed < 365 * DAY) return `${Math.floor(elapsed / (30 * DAY))}개월 전`;
  return date.toLocaleDateString("ko-KR", { dateStyle: "long" });
}

// 예: 2026년 11월 5일 오전 10:24
export function formatFullDate(value: string) {
  return new Date(value).toLocaleString("ko-KR", { dateStyle: "long", timeStyle: "short" });
}

// 예: 2026년 3월
export function formatYearMonth(value: string) {
  return new Date(value).toLocaleDateString("ko-KR", { year: "numeric", month: "long" });
}

// URL의 id가 숫자가 아니면 null을 돌려줍니다.
export function parseId(value: string | string[] | undefined) {
  const id = Number(value);
  return Number.isInteger(id) && id > 0 ? id : null;
}

export function decodeParam(value: string | string[] | undefined) {
  const text = Array.isArray(value) ? value.join("/") : (value ?? "");
  try {
    return decodeURIComponent(text);
  } catch {
    return text;
  }
}

// 외부 사이트로 이동하지 않도록 같은 사이트 경로만 허용합니다.
export function safeNextPath(value: string | null) {
  return value && /^\/(?![/\\])/.test(value) ? value : "/";
}
