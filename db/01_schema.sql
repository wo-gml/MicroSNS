-- microSNS 스키마 (MySQL 8.0.16 이상, CHECK 제약 사용)
--
-- 실행: 레포 루트에서
--   mysql -u root -p microsns < db/01_schema.sql
--
-- 규칙
-- - 시각은 모두 DATETIME(6)이고, 연결 시간대(DB_TIME_ZONE, 기본 +09:00) 기준으로 저장합니다.
-- - enum 값은 API와 프론트엔드가 쓰는 소문자 문자열과 같습니다. (app/schemas/)
-- - 글을 지우면 댓글, 사진, 좋아요, 해시태그 연결, 모집과 지원, 글에 딸린 알림이 함께 지워집니다.
-- - 회원을 지우는 API는 없으므로, 회원을 참조하는 행이 있으면 삭제를 막습니다(기본 RESTRICT, API는 409).
-- - 지원 취소, 언팔로우, 좋아요 취소는 상태를 바꾸지 않고 행을 지웁니다.

SET NAMES utf8mb4;

DROP TABLE IF EXISTS notification;
DROP TABLE IF EXISTS application;
DROP TABLE IF EXISTS recruitment;
DROP TABLE IF EXISTS post_hashtag;
DROP TABLE IF EXISTS hashtag;
DROP TABLE IF EXISTS post_like;
DROP TABLE IF EXISTS post_image;
DROP TABLE IF EXISTS comment;
DROP TABLE IF EXISTS follow;
DROP TABLE IF EXISTS post;
DROP TABLE IF EXISTS member;

CREATE TABLE member (
    id            BIGINT       NOT NULL AUTO_INCREMENT,
    email         VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name          VARCHAR(50)  NOT NULL,
    bio           VARCHAR(200) NULL,
    created_at    DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at    DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    CONSTRAINT uq_member_email UNIQUE (email)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci;

CREATE TABLE post (
    id         BIGINT       NOT NULL AUTO_INCREMENT,
    member_id  BIGINT       NOT NULL,
    content    VARCHAR(500) NOT NULL,
    created_at DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    -- 프로필의 작성 글 목록(작성자별 최신순)
    INDEX idx_post_member_created (member_id, created_at),
    -- 피드와 해시태그 글 목록(전체 최신순)
    INDEX idx_post_created (created_at),
    CONSTRAINT fk_post_member FOREIGN KEY (member_id) REFERENCES member (id)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci;

CREATE TABLE follow (
    follower_id  BIGINT      NOT NULL,
    following_id BIGINT      NOT NULL,
    created_at   DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    PRIMARY KEY (follower_id, following_id),
    -- 팔로워 목록(나를 팔로우하는 사람)
    INDEX idx_follow_following (following_id, follower_id),
    CONSTRAINT fk_follow_follower  FOREIGN KEY (follower_id)  REFERENCES member (id),
    CONSTRAINT fk_follow_following FOREIGN KEY (following_id) REFERENCES member (id),
    CONSTRAINT ck_follow_not_self CHECK (follower_id <> following_id)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci;

CREATE TABLE comment (
    id         BIGINT       NOT NULL AUTO_INCREMENT,
    post_id    BIGINT       NOT NULL,
    member_id  BIGINT       NOT NULL,
    content    VARCHAR(300) NOT NULL,
    created_at DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    -- 글의 댓글 목록(작성순)
    INDEX idx_comment_post_created (post_id, created_at),
    INDEX idx_comment_member (member_id),
    CONSTRAINT fk_comment_post   FOREIGN KEY (post_id)   REFERENCES post (id) ON DELETE CASCADE,
    CONSTRAINT fk_comment_member FOREIGN KEY (member_id) REFERENCES member (id)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci;

CREATE TABLE post_image (
    id         BIGINT       NOT NULL AUTO_INCREMENT,
    post_id    BIGINT       NOT NULL,
    url        VARCHAR(500) NOT NULL,
    sort_order INT          NOT NULL,
    created_at DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    -- 한 글 안에서 사진 순서가 겹치지 않게 합니다. 글의 사진 조회에도 쓰입니다.
    CONSTRAINT uq_post_image_order UNIQUE (post_id, sort_order),
    CONSTRAINT fk_post_image_post FOREIGN KEY (post_id) REFERENCES post (id) ON DELETE CASCADE,
    CONSTRAINT ck_post_image_order CHECK (sort_order >= 0)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci;

CREATE TABLE post_like (
    member_id  BIGINT      NOT NULL,
    post_id    BIGINT      NOT NULL,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    PRIMARY KEY (member_id, post_id),
    -- 글의 좋아요 수
    INDEX idx_post_like_post (post_id),
    CONSTRAINT fk_post_like_member FOREIGN KEY (member_id) REFERENCES member (id),
    CONSTRAINT fk_post_like_post   FOREIGN KEY (post_id)   REFERENCES post (id) ON DELETE CASCADE
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci;

CREATE TABLE hashtag (
    id         BIGINT      NOT NULL AUTO_INCREMENT,
    -- '#' 없이 저장합니다. 대소문자를 구분하지 않는 정렬 규칙이라 'SQL'과 'sql'은 같은 태그입니다.
    name       VARCHAR(50) NOT NULL,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    CONSTRAINT uq_hashtag_name UNIQUE (name)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci;

CREATE TABLE post_hashtag (
    post_id    BIGINT NOT NULL,
    hashtag_id BIGINT NOT NULL,
    PRIMARY KEY (post_id, hashtag_id),
    -- 태그별 글 목록과 인기 태그 집계
    INDEX idx_post_hashtag_hashtag (hashtag_id, post_id),
    CONSTRAINT fk_post_hashtag_post    FOREIGN KEY (post_id)    REFERENCES post (id) ON DELETE CASCADE,
    CONSTRAINT fk_post_hashtag_hashtag FOREIGN KEY (hashtag_id) REFERENCES hashtag (id)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci;

CREATE TABLE recruitment (
    id         BIGINT                     NOT NULL AUTO_INCREMENT,
    post_id    BIGINT                     NOT NULL,
    type       ENUM ('study', 'project')  NOT NULL,
    capacity   INT                        NOT NULL,
    deadline   DATETIME(6)                NOT NULL,
    status     ENUM ('open', 'closed')    NOT NULL DEFAULT 'open',
    created_at DATETIME(6)                NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6)                NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    -- 글 하나에 모집은 하나만 붙습니다.
    CONSTRAINT uq_recruitment_post UNIQUE (post_id),
    CONSTRAINT fk_recruitment_post FOREIGN KEY (post_id) REFERENCES post (id) ON DELETE CASCADE,
    CONSTRAINT ck_recruitment_capacity CHECK (capacity >= 1)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci;

CREATE TABLE application (
    id             BIGINT                                      NOT NULL AUTO_INCREMENT,
    recruitment_id BIGINT                                      NOT NULL,
    member_id      BIGINT                                      NOT NULL,
    message        VARCHAR(300)                                NULL,
    status         ENUM ('pending', 'accepted', 'rejected')    NOT NULL DEFAULT 'pending',
    created_at     DATETIME(6)                                 NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at     DATETIME(6)                                 NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    -- 같은 모집에 두 번 지원할 수 없습니다. 모집별 지원자 목록 조회에도 쓰입니다.
    CONSTRAINT uq_application_recruitment_member UNIQUE (recruitment_id, member_id),
    -- 수락 인원 집계
    INDEX idx_application_recruitment_status (recruitment_id, status),
    INDEX idx_application_member (member_id),
    CONSTRAINT fk_application_recruitment FOREIGN KEY (recruitment_id) REFERENCES recruitment (id) ON DELETE CASCADE,
    CONSTRAINT fk_application_member      FOREIGN KEY (member_id)      REFERENCES member (id)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci;

CREATE TABLE notification (
    id          BIGINT       NOT NULL AUTO_INCREMENT,
    receiver_id BIGINT       NOT NULL,
    actor_id    BIGINT       NOT NULL,
    type        ENUM ('like', 'comment', 'follow', 'application', 'application_result') NOT NULL,
    -- 팔로우 알림은 글이 없으므로 NULL입니다.
    post_id     BIGINT       NULL,
    content     VARCHAR(255) NOT NULL,
    is_read     BOOLEAN      NOT NULL DEFAULT FALSE,
    created_at  DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    -- 알림 목록(최신순)과 안 읽은 알림 수
    INDEX idx_notification_receiver_created (receiver_id, created_at),
    INDEX idx_notification_receiver_read (receiver_id, is_read),
    INDEX idx_notification_actor (actor_id),
    CONSTRAINT fk_notification_receiver FOREIGN KEY (receiver_id) REFERENCES member (id),
    CONSTRAINT fk_notification_actor    FOREIGN KEY (actor_id)    REFERENCES member (id),
    CONSTRAINT fk_notification_post     FOREIGN KEY (post_id)     REFERENCES post (id) ON DELETE CASCADE,
    -- 본인의 행동은 본인에게 알리지 않습니다.
    -- post_id는 ON DELETE CASCADE가 있어 MySQL이 CHECK에 쓰지 못하므로, 팔로우만 NULL인지는 앱에서 지킵니다.
    CONSTRAINT ck_notification_not_self CHECK (receiver_id <> actor_id)
)ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci;
