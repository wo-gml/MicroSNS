import Link from "next/link";

// 앞이 글자가 아닌 #단어만 해시태그로 봅니다. (abc#def는 제외)
const HASHTAG = /(?<![\p{L}\p{N}_])#([\p{L}\p{N}_]+)/gu;
const TRAILING_HASHTAGS = /^([\s\S]*?)\s*((?:(?:^|\s)#[\p{L}\p{N}_]+)+)\s*$/u;

export default function RichText({ text }: { text: string }) {
  const parts: React.ReactNode[] = [];
  let lastIndex = 0;
  for (const match of text.matchAll(HASHTAG)) {
    parts.push(text.slice(lastIndex, match.index));
    parts.push(
      <Link className="hashtag" key={match.index} href={`/hashtags/${encodeURIComponent(match[1])}`}>
        {match[0]}
      </Link>,
    );
    lastIndex = match.index + match[0].length;
  }
  parts.push(text.slice(lastIndex));
  return <>{parts}</>;
}

// 시안처럼 글 끝의 해시태그는 본문 아래 별도 줄로 표시합니다.
export function PostText({ content }: { content: string }) {
  const match = TRAILING_HASHTAGS.exec(content);
  const body = match ? match[1] : content;
  const tags = match?.[2].trim();
  return (
    <>
      {body && (
        <p className="post-text">
          <RichText text={body} />
        </p>
      )}
      {tags && (
        <p className="post-tags">
          <RichText text={tags} />
        </p>
      )}
    </>
  );
}
