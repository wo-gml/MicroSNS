"use client";

import { useParams } from "next/navigation";
import { getHashtag, getPostsByHashtag } from "@/api/hashtags";
import PageHeader from "@/components/PageHeader";
import PostList from "@/components/PostList";
import { useResource } from "@/hooks/useResource";
import { decodeParam } from "@/lib/format";

function HashtagPosts({ tag }: { tag: string }) {
  const { data } = useResource(() => getHashtag(tag));
  return (
    <>
      <PageHeader title={`#${tag}`} back>
        {data && <span className="meta">{data.post_count}개의 글</span>}
      </PageHeader>
      <PostList
        fetchPage={(page) => getPostsByHashtag(tag, page)}
        empty={{ title: `#${tag} 태그가 달린 글이 없습니다.` }}
      />
    </>
  );
}

export default function HashtagView() {
  const tag = decodeParam(useParams().tag);
  return <HashtagPosts key={tag} tag={tag} />;
}
