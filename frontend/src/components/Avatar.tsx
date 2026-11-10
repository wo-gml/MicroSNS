import type { UserSummary } from "@/api/types";

const COLUMNS = 4;
const ROWS = 2;

// 프로필 사진을 올리는 기능이 시안과 DB에 없어, 시안의 이미지 8개(public/images/avatars.jpg)를
// 회원 id별로 나눠 씁니다. 위치와 크기 비율은 Figma 값입니다.
export default function Avatar({ user, size = 40 }: { user: UserSummary; size?: number }) {
  const index = user.id % (COLUMNS * ROWS);
  const column = index % COLUMNS;
  const row = Math.floor(index / COLUMNS);
  return (
    <span className="avatar" style={{ width: size, height: size }} aria-hidden="true">
      <img
        src="/images/avatars.jpg"
        alt=""
        style={{ left: `${-5.56 - 111.11 * column}%`, top: `${-12.02 - 124.03 * row}%` }}
      />
    </span>
  );
}
