-- 게시글 시드(db/seed/posts.sql) 내용의 #태그를 hashtag, post_hashtag에 넣습니다.
-- 앱에서 글을 쓰면 API가 내용에서 #태그를 뽑아 저장하지만, 시드는 SQL로 바로 넣으므로 따로 넣어야 합니다.
-- posts.sql 다음에 실행합니다. 게시글 id는 1~10이라고 가정합니다(빈 테이블에 넣었을 때).
-- 글 내용을 바꾸면 이 파일의 태그도 같이 맞춰야 합니다.

INSERT INTO hashtag (name, created_at) VALUES
('백엔드',       '2026-11-01 10:00:00'),
('SpringBoot',   '2026-11-01 10:00:00'),
('알고리즘',     '2026-11-01 11:00:00'),
('스터디',       '2026-11-01 11:00:00'),
('Python',       '2026-11-02 09:30:00'),
('프론트엔드',   '2026-11-02 13:00:00'),
('React',        '2026-11-02 13:00:00'),
('프로젝트',     '2026-11-03 10:00:00'),
('데이터베이스', '2026-11-03 14:00:00'),
('Git',          '2026-11-04 15:30:00');

-- 태그 id는 이름으로 찾습니다.
INSERT INTO post_hashtag (post_id, hashtag_id)
SELECT tagged.post_id, h.id
FROM (
    SELECT 1 AS post_id, '백엔드' AS name
    UNION ALL SELECT 1, 'SpringBoot'
    UNION ALL SELECT 2, '알고리즘'
    UNION ALL SELECT 2, '스터디'
    UNION ALL SELECT 3, '알고리즘'
    UNION ALL SELECT 3, 'Python'
    UNION ALL SELECT 4, '프론트엔드'
    UNION ALL SELECT 4, 'React'
    UNION ALL SELECT 5, '프로젝트'
    UNION ALL SELECT 5, '프론트엔드'
    UNION ALL SELECT 5, '백엔드'
    UNION ALL SELECT 6, '데이터베이스'
    UNION ALL SELECT 6, '스터디'
    UNION ALL SELECT 7, '알고리즘'
    UNION ALL SELECT 7, '스터디'
    UNION ALL SELECT 8, 'Git'
    UNION ALL SELECT 8, '프로젝트'
    UNION ALL SELECT 9, '프로젝트'
    UNION ALL SELECT 9, '프론트엔드'
    UNION ALL SELECT 10, '프로젝트'
) AS tagged
JOIN hashtag h ON h.name = tagged.name;
