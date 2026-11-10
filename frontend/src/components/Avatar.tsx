import type { UserSummary } from "@/api/types";

// 프로필 사진을 올리는 기능이 시안과 DB에 없어, 모든 회원에게 같은 기본 프로필을 보여 줍니다.
// user는 회원별 사진(member에 컬럼 추가)이 생기면 쓰려고 받아 둡니다.
export default function Avatar({ size = 40 }: { user: UserSummary; size?: number }) {
  return (
    <span className="avatar" style={{ width: size, height: size }} aria-hidden="true">
      <img src="/images/default-avatar.svg" alt="" />
    </span>
  );
}
