// Figma 시안에서 내려받은 아이콘(public/icons). 시안 크기 그대로 표시합니다.
const SIZES = {
  home: 24,
  bell: 24,
  user: 24,
  "arrow-left": 24,
  heart: 20,
  "heart-filled": 20,
  message: 20,
  image: 20,
  "unread-dot": 8,
} as const;

export type IconName = keyof typeof SIZES;

export default function Icon({ name }: { name: IconName }) {
  const size = SIZES[name];
  return <img className="icon" src={`/icons/${name}.svg`} width={size} height={size} alt="" />;
}
