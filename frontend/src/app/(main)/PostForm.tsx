// 글 작성 폼
"use client";

import { useRef, useState, type ChangeEvent, type FormEvent } from "react";
import { toApiError } from "@/api/client";
import { createPost, MAX_POST_IMAGES, MAX_POST_LENGTH, uploadImage } from "@/api/posts";
import type { Post, UserSummary } from "@/api/types";
import Avatar from "@/components/Avatar";
import Icon from "@/components/Icon";

type Attachment = { file: File; previewUrl: string };

export default function PostForm({
  user,
  onCreated,
}: {
  user: UserSummary;
  onCreated: (post: Post) => void;
}) {
  const [content, setContent] = useState("");
  const [attachments, setAttachments] = useState<Attachment[]>([]);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInput = useRef<HTMLInputElement>(null);
  const textarea = useRef<HTMLTextAreaElement>(null);

  function handleFiles(event: ChangeEvent<HTMLInputElement>) {
    const files = Array.from(event.target.files ?? []);
    event.target.value = ""; // 같은 파일을 다시 고를 수 있게 비웁니다.
    if (attachments.length + files.length > MAX_POST_IMAGES) {
      setError(`사진은 ${MAX_POST_IMAGES}장까지 올릴 수 있습니다.`);
      return;
    }
    setError(null);
    setAttachments([
      ...attachments,
      ...files.map((file) => ({ file, previewUrl: URL.createObjectURL(file) })),
    ]);
  }

  function removeAttachment(target: Attachment) {
    URL.revokeObjectURL(target.previewUrl);
    setAttachments(attachments.filter((item) => item !== target));
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (pending) return;
    if (!content.trim()) {
      textarea.current?.focus();
      return;
    }
    setPending(true);
    setError(null);
    try {
      const imageUrls = await Promise.all(attachments.map(({ file }) => uploadImage(file)));
      onCreated(await createPost(content.trim(), imageUrls));
      attachments.forEach(({ previewUrl }) => URL.revokeObjectURL(previewUrl));
      setAttachments([]);
      setContent("");
    } catch (caught) {
      setError(toApiError(caught).message); // 작성한 내용은 지우지 않습니다.
    } finally {
      setPending(false);
    }
  }

  return (
    <form className="composer" onSubmit={handleSubmit}>
      <Avatar user={user} />
      <div className="composer-main">
        <div className="composer-row">
          <label className="sr-only" htmlFor="post-content">
            글 내용
          </label>
          <textarea
            ref={textarea}
            id="post-content"
            className="composer-input"
            rows={1}
            maxLength={MAX_POST_LENGTH}
            placeholder="어떤 스터디나 프로젝트를 모집하고 있나요?"
            value={content}
            onChange={(event) => setContent(event.target.value)}
          />
          <div className="composer-footer">
            <input
              ref={fileInput}
              className="sr-only"
              type="file"
              accept="image/*"
              multiple
              tabIndex={-1}
              aria-hidden="true"
              onChange={handleFiles}
            />
            <button
              className="icon-button"
              type="button"
              aria-label="사진 추가"
              onClick={() => fileInput.current?.click()}
            >
              <Icon name="image" />
            </button>
            <button className="button button--primary" type="submit" disabled={pending}>
              {pending ? "게시 중…" : "게시"}
            </button>
          </div>
        </div>
        {attachments.length > 0 && (
          <div className="composer-previews">
            {attachments.map((attachment) => (
              <div className="composer-preview" key={attachment.previewUrl}>
                <img src={attachment.previewUrl} alt={attachment.file.name} />
                <button
                  className="preview-remove"
                  type="button"
                  aria-label={`${attachment.file.name} 빼기`}
                  onClick={() => removeAttachment(attachment)}
                >
                  ×
                </button>
              </div>
            ))}
          </div>
        )}
        {error && (
          <p className="inline-error" role="alert">
            {error}
          </p>
        )}
      </div>
    </form>
  );
}
