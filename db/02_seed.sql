-- microSNS 예시 데이터. db/01_schema.sql로 테이블을 만든 뒤 실행합니다.
--   mysql -u root -p microsns < db/02_seed.sql
--
-- backend/app/mock/data.py(메모리 저장소)와 같은 데이터입니다.
-- - 로그인: admin@test.com(김민준, 회원 2) 또는 user1@test.com ~ user8@test.com, 비밀번호는 모두 test1234
-- - 시각은 넣는 시점(@now) 기준이라, 언제 넣어도 "2시간 전" 같은 표시가 시안과 같습니다.
-- - 메모리 저장소에서 시안 숫자를 맞추려고 더해 둔 값(좋아요 수, 댓글 수, 팔로워 수, 인기 해시태그 개수)은
--   실제 행이 아니므로 넣지 않았습니다. 그래서 화면의 숫자는 메모리 저장소보다 작습니다.

SET NAMES utf8mb4;
SET @now = NOW(6);

-- 회원 (비밀번호는 모두 test1234)

SET @pw = '$argon2id$v=19$m=65536,t=3,p=4$dxzdwC4wYVGjyfZ0rNi/Sg$LJUL3dhxdi89IiojMGQTDMscmrEjSu7Oey7OflhKdBw';

INSERT INTO member (id, email, password_hash, name, bio, created_at, updated_at) VALUES
    (1, 'user1@test.com', @pw, '이도윤', '쿼리 튜닝 스터디 운영 중', @now - INTERVAL 288000 MINUTE, @now - INTERVAL 288000 MINUTE),
    (2, 'admin@test.com', @pw, '김민준', '함께 공부할 사람을 찾고 있어요.', @now - INTERVAL 432000 MINUTE, @now - INTERVAL 432000 MINUTE),
    (3, 'user3@test.com', @pw, '정민재', '컴퓨터공학과 3학년이에요. 데이터베이스와 백엔드 개발에 관심이 많고, 함께 공부할 사람을 찾고 있어요.', '2026-03-10 10:00:00', '2026-03-10 10:00:00'),
    (4, 'user4@test.com', @pw, '서지안', NULL, @now - INTERVAL 144000 MINUTE, @now - INTERVAL 144000 MINUTE),
    (5, 'user5@test.com', @pw, '한유진', NULL, @now - INTERVAL 144000 MINUTE, @now - INTERVAL 144000 MINUTE),
    (6, 'user6@test.com', @pw, '강서준', NULL, @now - INTERVAL 144000 MINUTE, @now - INTERVAL 144000 MINUTE),
    (7, 'user7@test.com', @pw, '박지호', NULL, @now - INTERVAL 144000 MINUTE, @now - INTERVAL 144000 MINUTE),
    (8, 'user8@test.com', @pw, '최하은', NULL, @now - INTERVAL 144000 MINUTE, @now - INTERVAL 144000 MINUTE);

-- 팔로우

INSERT INTO follow (follower_id, following_id) VALUES
    (2, 1),
    (2, 4),
    (2, 5),
    (2, 6),
    (2, 7),
    (2, 8),
    (7, 2);

-- 게시글 (100번부터는 프로필의 "더 보기" 확인용)

INSERT INTO post (id, member_id, content, created_at, updated_at) VALUES
    (1, 1, 'MySQL 쿼리 튜닝 스터디 같이 하실 분 구해요. 매주 토요일 오전에 만나고, 실행 계획 읽는 법부터 시작합니다. 지금 3명이고 2명 더 모집해요.\n#스터디 #데이터베이스', @now - INTERVAL 120 MINUTE, @now - INTERVAL 120 MINUTE),
    (2, 8, '졸업 프로젝트로 일정 공유 웹앱을 만들고 있어요. 함께할 프론트엔드 개발자 1명을 찾습니다. Next.js 경험이 있으면 좋아요.\n#프로젝트 #프론트엔드', @now - INTERVAL 300 MINUTE, @now - INTERVAL 300 MINUTE),
    (3, 7, '알고리즘 스터디 4기를 모집합니다. 온라인으로 주 2회 진행하고, 풀이는 깃허브에 올려서 서로 리뷰해요.\n#스터디 #알고리즘', @now - INTERVAL 1500 MINUTE, @now - INTERVAL 1500 MINUTE),
    (4, 5, 'FastAPI 입문서 한 권을 같이 끝낼 분을 찾아요. 백엔드가 처음이어도 괜찮아요.\n#스터디 #백엔드', @now - INTERVAL 2940 MINUTE, @now - INTERVAL 2940 MINUTE),
    (5, 6, '스프링 부트로 게시판을 만드는 스터디를 시작해요. 자바 기초만 알면 돼요.\n#스터디 #백엔드', @now - INTERVAL 4380 MINUTE, @now - INTERVAL 4380 MINUTE),
    (6, 4, '해커톤에 같이 나갈 디자이너를 찾아요. 기획은 거의 끝났고, 개발자 2명이 함께하고 있어요.\n#프로젝트 #디자인', @now - INTERVAL 5820 MINUTE, @now - INTERVAL 5820 MINUTE),
    (7, 3, 'SQL 인덱스 스터디원을 찾습니다. 인덱스 설계와 실행 계획을 예제로 함께 공부해요.\n#스터디 #데이터베이스', @now - INTERVAL 180 MINUTE, @now - INTERVAL 180 MINUTE),
    (8, 3, '미니 SNS를 만드는 팀 프로젝트에서 백엔드를 맡을 분을 찾아요. FastAPI와 MySQL을 사용합니다.\n#프로젝트 #백엔드', @now - INTERVAL 5760 MINUTE, @now - INTERVAL 5760 MINUTE),
    (9, 3, '이번 학기 데이터베이스 수업을 같이 복습하실 분 있나요? 정규화부터 시작해요.\n#스터디 #데이터베이스', @now - INTERVAL 20160 MINUTE, @now - INTERVAL 20160 MINUTE),
    (10, 3, '백엔드 포트폴리오를 서로 리뷰할 분을 구해요. 매주 한 번 온라인으로 만나요.\n#스터디 #백엔드', @now - INTERVAL 44640 MINUTE, @now - INTERVAL 44640 MINUTE),
    (11, 2, '함께 사이드 프로젝트 하실 분을 찾아요. 주말에 온라인으로 만나요.\n#프로젝트', @now - INTERVAL 7200 MINUTE, @now - INTERVAL 7200 MINUTE),
    (100, 1, '지난 모집 글 1\n#지난글', @now - INTERVAL 28800 MINUTE, @now - INTERVAL 28800 MINUTE),
    (101, 1, '지난 모집 글 2\n#지난글', @now - INTERVAL 28900 MINUTE, @now - INTERVAL 28900 MINUTE),
    (102, 1, '지난 모집 글 3\n#지난글', @now - INTERVAL 29000 MINUTE, @now - INTERVAL 29000 MINUTE),
    (103, 1, '지난 모집 글 4\n#지난글', @now - INTERVAL 29100 MINUTE, @now - INTERVAL 29100 MINUTE),
    (104, 1, '지난 모집 글 5\n#지난글', @now - INTERVAL 29200 MINUTE, @now - INTERVAL 29200 MINUTE),
    (105, 1, '지난 모집 글 6\n#지난글', @now - INTERVAL 29300 MINUTE, @now - INTERVAL 29300 MINUTE),
    (106, 1, '지난 모집 글 7\n#지난글', @now - INTERVAL 29400 MINUTE, @now - INTERVAL 29400 MINUTE),
    (107, 1, '지난 모집 글 8\n#지난글', @now - INTERVAL 29500 MINUTE, @now - INTERVAL 29500 MINUTE),
    (108, 1, '지난 모집 글 9\n#지난글', @now - INTERVAL 29600 MINUTE, @now - INTERVAL 29600 MINUTE),
    (109, 1, '지난 모집 글 10\n#지난글', @now - INTERVAL 29700 MINUTE, @now - INTERVAL 29700 MINUTE),
    (110, 1, '지난 모집 글 11\n#지난글', @now - INTERVAL 29800 MINUTE, @now - INTERVAL 29800 MINUTE),
    (111, 1, '지난 모집 글 12\n#지난글', @now - INTERVAL 29900 MINUTE, @now - INTERVAL 29900 MINUTE),
    (112, 1, '지난 모집 글 13\n#지난글', @now - INTERVAL 30000 MINUTE, @now - INTERVAL 30000 MINUTE),
    (113, 1, '지난 모집 글 14\n#지난글', @now - INTERVAL 30100 MINUTE, @now - INTERVAL 30100 MINUTE),
    (114, 1, '지난 모집 글 15\n#지난글', @now - INTERVAL 30200 MINUTE, @now - INTERVAL 30200 MINUTE),
    (115, 1, '지난 모집 글 16\n#지난글', @now - INTERVAL 30300 MINUTE, @now - INTERVAL 30300 MINUTE),
    (116, 1, '지난 모집 글 17\n#지난글', @now - INTERVAL 30400 MINUTE, @now - INTERVAL 30400 MINUTE),
    (117, 1, '지난 모집 글 18\n#지난글', @now - INTERVAL 30500 MINUTE, @now - INTERVAL 30500 MINUTE),
    (118, 1, '지난 모집 글 19\n#지난글', @now - INTERVAL 30600 MINUTE, @now - INTERVAL 30600 MINUTE),
    (119, 1, '지난 모집 글 20\n#지난글', @now - INTERVAL 30700 MINUTE, @now - INTERVAL 30700 MINUTE),
    (120, 1, '지난 모집 글 21\n#지난글', @now - INTERVAL 30800 MINUTE, @now - INTERVAL 30800 MINUTE),
    (121, 1, '지난 모집 글 22\n#지난글', @now - INTERVAL 30900 MINUTE, @now - INTERVAL 30900 MINUTE),
    (122, 1, '지난 모집 글 23\n#지난글', @now - INTERVAL 31000 MINUTE, @now - INTERVAL 31000 MINUTE),
    (123, 1, '지난 모집 글 24\n#지난글', @now - INTERVAL 31100 MINUTE, @now - INTERVAL 31100 MINUTE);

-- 게시글 사진 (backend가 /api/mock-photos로 제공하는 frontend/mock/photos의 파일)

INSERT INTO post_image (post_id, url, sort_order, created_at) VALUES
    (1, '/api/mock-photos/laptop-cafe.jpg', 0, @now - INTERVAL 120 MINUTE),
    (2, '/api/mock-photos/whiteboard.jpg', 0, @now - INTERVAL 300 MINUTE),
    (2, '/api/mock-photos/calendar-app.jpg', 1, @now - INTERVAL 300 MINUTE),
    (7, '/api/mock-photos/book-desk.jpg', 0, @now - INTERVAL 180 MINUTE);

-- 좋아요

INSERT INTO post_like (member_id, post_id) VALUES
    (2, 1),
    (2, 8);

-- 댓글

INSERT INTO comment (id, post_id, member_id, content, created_at) VALUES
    (1, 1, 3, '실행 계획을 제대로 본 적이 없는데 저도 참여할 수 있을까요?', @now - INTERVAL 65 MINUTE),
    (2, 1, 8, '토요일 오전이면 저도 가능해요. 모임 시간은 몇 시인가요?', @now - INTERVAL 60 MINUTE),
    (3, 1, 5, '교재 정할 때 추천 목록도 같이 공유해 주시면 좋겠어요.', @now - INTERVAL 30 MINUTE),
    (4, 1, 7, '온라인으로 진행하면 저도 참여해 보고 싶어요.', @now - INTERVAL 20 MINUTE),
    (5, 1, 6, '스터디 기록은 어디에 남길 계획인가요?', @now - INTERVAL 10 MINUTE);

-- 해시태그 (글 내용의 #단어)

INSERT INTO hashtag (id, name) VALUES
    (1, '스터디'),
    (2, '데이터베이스'),
    (3, '프로젝트'),
    (4, '프론트엔드'),
    (5, '알고리즘'),
    (6, '백엔드'),
    (7, '디자인'),
    (8, '지난글');

INSERT INTO post_hashtag (post_id, hashtag_id) VALUES
    (1, 1),
    (1, 2),
    (2, 3),
    (2, 4),
    (3, 1),
    (3, 5),
    (4, 1),
    (4, 6),
    (5, 1),
    (5, 6),
    (6, 3),
    (6, 7),
    (7, 1),
    (7, 2),
    (8, 3),
    (8, 6),
    (9, 1),
    (9, 2),
    (10, 1),
    (10, 6),
    (11, 3),
    (100, 8),
    (101, 8),
    (102, 8),
    (103, 8),
    (104, 8),
    (105, 8),
    (106, 8),
    (107, 8),
    (108, 8),
    (109, 8),
    (110, 8),
    (111, 8),
    (112, 8),
    (113, 8),
    (114, 8),
    (115, 8),
    (116, 8),
    (117, 8),
    (118, 8),
    (119, 8),
    (120, 8),
    (121, 8),
    (122, 8),
    (123, 8);

-- 모집

INSERT INTO recruitment (id, post_id, type, capacity, deadline, status, created_at, updated_at) VALUES
    (1, 1, 'study', 5, @now + INTERVAL 10080 MINUTE, 'open', @now - INTERVAL 120 MINUTE, @now - INTERVAL 120 MINUTE),
    (2, 2, 'project', 1, @now + INTERVAL 4320 MINUTE, 'open', @now - INTERVAL 300 MINUTE, @now - INTERVAL 300 MINUTE),
    (3, 3, 'study', 4, @now - INTERVAL 60 MINUTE, 'open', @now - INTERVAL 1500 MINUTE, @now - INTERVAL 1500 MINUTE),
    (4, 11, 'project', 2, @now + INTERVAL 7200 MINUTE, 'open', @now - INTERVAL 7200 MINUTE, @now - INTERVAL 7200 MINUTE);

-- 지원

INSERT INTO application (id, recruitment_id, member_id, message, status, created_at, updated_at) VALUES
    (1, 1, 3, '실행 계획을 배우고 싶어요.', 'accepted', @now - INTERVAL 60 MINUTE, @now - INTERVAL 30 MINUTE),
    (2, 2, 2, 'Next.js 경험이 있어요.', 'pending', @now - INTERVAL 60 MINUTE, @now - INTERVAL 60 MINUTE),
    (3, 4, 8, '프론트엔드를 맡고 싶어요.', 'pending', @now - INTERVAL 12 MINUTE, @now - INTERVAL 12 MINUTE),
    (4, 4, 3, NULL, 'pending', @now - INTERVAL 60 MINUTE, @now - INTERVAL 60 MINUTE),
    (5, 4, 5, '기획도 도울 수 있어요.', 'pending', @now - INTERVAL 90 MINUTE, @now - INTERVAL 90 MINUTE);

-- 알림 (모두 김민준 계정이 받은 알림)

INSERT INTO notification (id, receiver_id, actor_id, type, post_id, content, is_read, created_at) VALUES
    (1, 2, 1, 'like', 1, '이도윤님이 회원님의 글을 좋아합니다.', FALSE, @now - INTERVAL 3 MINUTE),
    (2, 2, 8, 'application', 11, '최하은님이 회원님의 모집에 지원했습니다.', FALSE, @now - INTERVAL 12 MINUTE),
    (3, 2, 7, 'follow', NULL, '박지호님이 회원님을 팔로우하기 시작했습니다.', FALSE, @now - INTERVAL 60 MINUTE),
    (4, 2, 5, 'comment', 1, '한유진님이 회원님의 글에 댓글을 남겼습니다.', TRUE, @now - INTERVAL 180 MINUTE),
    (5, 2, 1, 'application_result', 1, '이도윤님이 회원님의 지원을 수락했습니다.', TRUE, @now - INTERVAL 1500 MINUTE);
