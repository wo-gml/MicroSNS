# 정규화

ERD의 테이블 11개마다 함수 종속성(FD)을 정리하고, 그 FD로 1NF, 2NF, 3NF를 확인합니다.
DDL은 [`db/01_schema.sql`](../db/01_schema.sql)에 있습니다.

## 테이블 구성

| 테이블 | 컬럼 | 기본키(PK) | 후보키(UNIQUE) | 외래키(FK) |
| --- | --- | --- | --- | --- |
| member | id, email, password_hash, name, bio, created_at, updated_at | id | email | 없음 |
| follow | follower_id, following_id, created_at | (follower_id, following_id) | | follower_id, following_id → member |
| post | id, member_id, content, created_at, updated_at | id | | member_id → member |
| comment | id, post_id, member_id, content, created_at | id | | post_id → post, member_id → member |
| post_image | id, post_id, url, sort_order, created_at | id | (post_id, sort_order) | post_id → post |
| post_like | member_id, post_id, created_at | (member_id, post_id) | | member_id → member, post_id → post |
| hashtag | id, name, created_at | id | name | 없음 |
| post_hashtag | post_id, hashtag_id | (post_id, hashtag_id) | | post_id → post, hashtag_id → hashtag |
| recruitment | id, post_id, type, capacity, deadline, status, created_at, updated_at | id | post_id | post_id → post |
| application | id, recruitment_id, member_id, message, status, created_at, updated_at | id | (recruitment_id, member_id) | recruitment_id → recruitment, member_id → member |
| notification | id, receiver_id, actor_id, type, post_id, content, is_read, created_at | id | | receiver_id, actor_id → member, post_id → post |

## 함수 종속성(FD)

### member

```
id    → email, password_hash, name, bio, created_at, updated_at
email → id, password_hash, name, bio, created_at, updated_at
```

- 회원 id 하나로 이메일, 비밀번호 해시, 이름, 자기소개, 가입·수정 일시가 정해집니다.
- email은 UNIQUE라서 이메일로도 회원을 하나로 찾을 수 있습니다. id와 email이 모두 후보키이고, id를 기본키로 씁니다.
- name은 중복될 수 있으므로 다른 속성을 결정하지 못합니다.
- password_hash는 되돌릴 수 있는 암호문이 아니라 되돌릴 수 없는 해시값입니다.

### follow

```
(follower_id, following_id) → created_at
```

- follower_id 하나만으로도, following_id 하나만으로도 팔로우한 시점을 정할 수 없습니다. 두 컬럼이 함께 있어야 "누가 누구를 언제 팔로우했는지"가 정해집니다.
- 두 컬럼을 복합 기본키로 두어 중복 팔로우를 막고, `CHECK (follower_id <> following_id)`로 자기 자신은 팔로우하지 못하게 합니다.

### post

```
id → member_id, content, created_at, updated_at
```

- 게시글 id 하나로 작성자, 내용, 작성·수정 일시가 정해집니다.
- 한 회원이 글을 여러 개 쓸 수 있으므로 member_id로는 글 하나를 정할 수 없습니다.

### comment

```
id → post_id, member_id, content, created_at
```

- 댓글 id 하나로 어느 글에 누가 무엇을 언제 썼는지가 정해집니다.
- 한 글에 댓글이 여러 개, 한 회원이 댓글을 여러 개 쓸 수 있으므로 post_id나 member_id로는 댓글 하나를 정할 수 없습니다.

### post_image

```
id                    → post_id, url, sort_order, created_at
(post_id, sort_order) → id, url, created_at
```

- 사진 id 하나로 어느 글의 몇 번째 사진인지와 주소가 정해집니다.
- 한 글 안에서 순서는 겹치지 않으므로(UNIQUE) (post_id, sort_order)도 후보키입니다.
- 사진을 post에 `image1`, `image2` 컬럼으로 두지 않고 행으로 나눴습니다. 그래야 사진 수가 바뀌어도 테이블 구조를 바꾸지 않습니다.

### post_like

```
(member_id, post_id) → created_at
```

- member_id 하나만으로도, post_id 하나만으로도 좋아요를 누른 시점을 정할 수 없습니다. 두 컬럼이 함께 있어야 정해집니다.
- 복합 기본키로 같은 글에 좋아요를 두 번 누르지 못하게 합니다.

### hashtag

```
id   → name, created_at
name → id, created_at
```

- 태그 이름은 UNIQUE이므로 id와 name이 모두 후보키입니다.
- 이름은 `#` 없이 저장하고, 대소문자를 구분하지 않는 정렬 규칙이라 `SQL`과 `sql`은 같은 태그입니다.

### post_hashtag

```
(post_id, hashtag_id) → (없음)
```

- 기본키 두 컬럼 말고 다른 속성이 없는 연결 테이블입니다. 글과 태그의 N:M 관계를 행 하나씩으로 나타냅니다.

### recruitment

```
id      → post_id, type, capacity, deadline, status, created_at, updated_at
post_id → id, type, capacity, deadline, status, created_at, updated_at
```

- 글 하나에 모집은 하나만 붙으므로(UNIQUE) post_id도 후보키입니다.
- status는 작성자가 직접 마감한 경우만 `closed`가 됩니다. 마감일이 지났는지, 정원이 찼는지는 저장하지 않고 deadline과 수락된 지원 수로 그때그때 계산합니다. 그래서 status는 deadline이나 capacity로 결정되는 값이 아닙니다.

### application

```
id                          → recruitment_id, member_id, message, status, created_at, updated_at
(recruitment_id, member_id) → id, message, status, created_at, updated_at
```

- 한 회원은 같은 모집에 한 번만 지원할 수 있으므로(UNIQUE) (recruitment_id, member_id)도 후보키입니다.
- 지원을 취소하면 상태를 바꾸지 않고 행을 지웁니다.

### notification

```
id → receiver_id, actor_id, type, post_id, content, is_read, created_at
```

- 알림 id 하나로 누가(actor) 누구에게(receiver) 어떤 알림을 보냈는지가 정해집니다.
- post_id로 receiver_id가 정해지지 않습니다. 같은 글이라도 좋아요·댓글·지원 알림은 글쓴이가, 지원 결과 알림은 지원자가 받기 때문입니다.
- 팔로우 알림은 글이 없으므로 post_id가 NULL입니다.

## 1NF

모든 컬럼이 하나의 값(원자값)만 가지면 1NF입니다.

- 컬럼마다 값이 하나이고, 목록을 한 컬럼에 몰아 넣지 않습니다.
- 여러 개가 붙을 수 있는 것은 모두 별도 테이블의 행으로 나눴습니다: 팔로우(follow), 댓글(comment), 사진(post_image), 좋아요(post_like), 글의 해시태그(post_hashtag), 지원(application).

11개 테이블 모두 1NF를 만족합니다.

## 2NF

1NF이면서, 기본키가 아닌 속성이 기본키 **전체**에 종속되면(부분 함수 종속이 없으면) 2NF입니다.

| 테이블 | 기본키 | 판단 |
| --- | --- | --- |
| member, post, comment, post_image, hashtag, recruitment, application, notification | id (단일) | 기본키가 한 컬럼이라 부분 종속이 생길 수 없습니다. |
| follow | (follower_id, following_id) | created_at은 두 컬럼 전체에 종속됩니다. |
| post_like | (member_id, post_id) | created_at은 두 컬럼 전체에 종속됩니다. |
| post_hashtag | (post_id, hashtag_id) | 기본키 외 속성이 없습니다. |

복합 후보키도 확인했습니다. post_image의 url은 post_id만으로 정해지지 않고, application의 status는 recruitment_id만으로 정해지지 않습니다.

11개 테이블 모두 2NF를 만족합니다.

## 3NF

2NF이면서, 기본키가 아닌 속성이 다른 비키 속성을 거쳐 결정되는 이행적 함수 종속이 없으면 3NF입니다.

| 테이블 | 판단 |
| --- | --- |
| member | `email → 나머지`는 email이 후보키라서 3NF를 어기지 않습니다. |
| follow, post_like | 비키 속성이 created_at 하나뿐입니다. |
| post_hashtag | 비키 속성이 없습니다. |
| post, comment, application | 작성자·지원자의 이름이나 이메일을 저장하지 않고 member_id로만 참조합니다. 이름을 함께 저장했다면 `id → member_id → name`이 이행 종속이 됩니다. |
| post_image, recruitment | 글 내용이나 작성자를 저장하지 않고 post_id로만 참조합니다. |
| hashtag | `name → 나머지`는 name이 후보키라서 3NF를 어기지 않습니다. |
| notification | 받는 사람·보낸 사람·글을 id로만 참조합니다. content는 아래 "알려진 중복"을 봅니다. |

11개 테이블 모두 3NF를 만족합니다.

### 알려진 중복: notification.content

notification.content에는 알림을 만들 때의 문장(`김민준님이 회원님의 글을 좋아합니다` 같은)을 저장합니다. 이 문장에 보낸 사람의 이름이 들어 있어, 회원 이름이 바뀌어도 이전 알림의 문장은 그대로 남습니다. 컬럼 사이의 FD는 아니지만, member.name과 같은 정보를 한 번 더 저장하는 셈입니다.

알림을 보낸 시점의 문장을 그대로 남기려는 의도라면 지금 구조로 둡니다. 항상 최신 이름을 보여 주려면 content를 저장하지 않고 type과 actor_id로 조회할 때 문장을 만듭니다.

## 설계 이유

- **N:M 관계는 연결 테이블로 나눴습니다.** 회원↔회원(follow), 회원↔글(post_like), 글↔태그(post_hashtag)입니다. 한쪽 테이블에 목록 컬럼을 두면 1NF를 어기고, 행을 추가하거나 지울 때 이상이 생깁니다.
- **회원 정보는 member 한 곳에만 둡니다.** 다른 테이블은 member.id만 참조하므로, 회원 정보를 바꿀 때 member만 고치면 됩니다(갱신 이상 방지).
- **계산할 수 있는 값은 저장하지 않습니다.** 좋아요 수, 댓글 수, 팔로워 수, 수락된 지원 수는 컬럼을 두지 않고 `COUNT`로 구합니다. 따로 저장하면 같은 정보가 두 곳에 생겨 서로 어긋날 수 있습니다.
- **글 하나에 모집 하나**는 recruitment.post_id의 UNIQUE로 지킵니다. 모집 정보를 post에 넣지 않은 이유는 모집이 없는 글이 대부분이라 NULL 컬럼이 많아지기 때문입니다.

## 정리

| 테이블 | 기본키(PK) | 함수 종속성 | 결과 |
| --- | --- | --- | --- |
| member | id | id → 나머지, email → 나머지 | 3NF |
| follow | (follower_id, following_id) | (follower_id, following_id) → created_at | 3NF |
| post | id | id → 나머지 | 3NF |
| comment | id | id → 나머지 | 3NF |
| post_image | id | id → 나머지, (post_id, sort_order) → 나머지 | 3NF |
| post_like | (member_id, post_id) | (member_id, post_id) → created_at | 3NF |
| hashtag | id | id → 나머지, name → 나머지 | 3NF |
| post_hashtag | (post_id, hashtag_id) | 비키 속성 없음 | 3NF |
| recruitment | id | id → 나머지, post_id → 나머지 | 3NF |
| application | id | id → 나머지, (recruitment_id, member_id) → 나머지 | 3NF |
| notification | id | id → 나머지 | 3NF |

## 삭제할 때의 동작

| 부모를 지우면 | 자식 |
| --- | --- |
| post | comment, post_image, post_like, post_hashtag, recruitment, notification(그 글의 알림)이 함께 지워집니다 (CASCADE). |
| recruitment | application이 함께 지워집니다 (CASCADE). |
| member | 회원을 참조하는 행(글, 댓글, 팔로우, 좋아요, 지원, 알림)이 하나라도 있으면 삭제를 막습니다 (RESTRICT). 회원 탈퇴 API는 없습니다. |
| hashtag | 글에 쓰인 태그는 지울 수 없습니다 (RESTRICT). |
