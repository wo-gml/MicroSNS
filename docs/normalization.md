# 정규화

각 테이블의 함수 종속성(FD)을 정리하고, 그 FD를 기준으로 1NF, 2NF, 3NF를 확인합니다.
DDL은 [`db/01_schema.sql`](../db/01_schema.sql)에 있습니다.

> 현재 정리된 테이블: member, follow, post, comment, post_like
> 아직 없음: recruitment, application, notification, hashtag, post_hashtag

## 테이블 구성

| 테이블 | 컬럼 | 기본키(PK) | 외래키(FK) |
| --- | --- | --- | --- |
| member | id, email, password_hash, name, bio, created_at, updated_at | id | 없음 |
| follow | follower_id, following_id, created_at | (follower_id, following_id) | follower_id → member.id, following_id → member.id |
| post | id, member_id, content, created_at, updated_at | id | member_id → member.id |
| comment | id, post_id, member_id, content, created_at | id | post_id → post.id, member_id → member.id |
| post_like | member_id, post_id, created_at | (member_id, post_id) | member_id → member.id, post_id → post.id |

## 함수 종속성(FD)

### member

```
id    → email, password_hash, name, bio, created_at, updated_at
email → id, password_hash, name, bio, created_at, updated_at
```

- 회원 id 하나로 이메일, 비밀번호 해시, 이름, 자기소개, 가입·수정 일시가 정해집니다.
- email에는 UNIQUE 제약이 있어 이메일로도 회원을 하나로 찾을 수 있습니다. 그래서 id와 email이 모두 후보키이고, id를 기본키로 씁니다.
- name은 중복될 수 있으므로 다른 속성을 결정하지 못합니다.
- password_hash는 암호화(복호화 가능)가 아니라 해시(되돌릴 수 없음)한 값입니다.

### follow

```
(follower_id, following_id) → created_at
```

- follower_id만으로는, following_id만으로는 팔로우한 시점을 정할 수 없습니다. 두 컬럼이 함께 있어야 "누가 누구를 언제 팔로우했는지"가 정해집니다.
- 두 컬럼을 복합 기본키로 두어 같은 회원 사이의 중복 팔로우를 막습니다.
- 자기 자신을 팔로우하지 못하도록 `CHECK (follower_id <> following_id)`를 둡니다.

### post

```
id → member_id, content, created_at, updated_at
```

- 게시글 id 하나로 작성자, 내용, 작성·수정 일시가 정해집니다.
- 한 회원이 여러 글을 쓸 수 있으므로 member_id는 게시글의 다른 속성을 결정하지 못합니다.

### comment

```
id → post_id, member_id, content, created_at
```

- 댓글 id 하나로 어느 글에 누가 무엇을 언제 썼는지가 정해집니다.
- 한 글에 댓글이 여러 개 달리고, 한 회원이 댓글을 여러 개 쓸 수 있으므로 post_id나 member_id는 다른 속성을 결정하지 못합니다.

### post_like

```
(member_id, post_id) → created_at
```

- member_id만으로는, post_id만으로는 좋아요를 누른 시점을 정할 수 없습니다. 두 컬럼이 함께 있어야 "누가 어느 글에 언제 좋아요를 눌렀는지"가 정해집니다.
- 두 컬럼을 복합 기본키로 두어 같은 글에 좋아요를 두 번 누르지 못하게 합니다.

## 1NF

모든 컬럼이 하나의 값(원자값)만 가지면 1NF입니다.

| 테이블 | 판단 |
| --- | --- |
| member | 컬럼마다 값이 하나입니다. |
| follow | 팔로우 관계 하나를 행 하나로 저장합니다. 팔로잉 목록을 한 컬럼에 몰아 넣지 않습니다. |
| post | 컬럼마다 값이 하나입니다. |
| comment | 댓글 하나를 행 하나로 저장합니다. 게시글에 댓글 목록 컬럼을 두지 않습니다. |
| post_like | 좋아요 하나를 행 하나로 저장합니다. 게시글에 좋아요한 회원 목록 컬럼을 두지 않습니다. |

다섯 테이블 모두 1NF를 만족합니다.

## 2NF

1NF이면서, 기본키가 아닌 속성이 기본키 **전체**에 종속되면(부분 함수 종속이 없으면) 2NF입니다.

| 테이블 | 기본키 | 판단 |
| --- | --- | --- |
| member | id (단일) | 기본키가 한 컬럼이므로 부분 종속이 생길 수 없습니다. |
| post | id (단일) | 위와 같습니다. |
| comment | id (단일) | 위와 같습니다. |
| follow | (follower_id, following_id) | created_at은 두 컬럼 전체에 종속되고, 한쪽만으로는 정해지지 않습니다. |
| post_like | (member_id, post_id) | created_at은 두 컬럼 전체에 종속되고, 한쪽만으로는 정해지지 않습니다. |

다섯 테이블 모두 2NF를 만족합니다.

## 3NF

2NF이면서, 기본키가 아닌 속성이 다른 비키 속성을 거쳐 결정되는 이행적 함수 종속이 없으면 3NF입니다.

| 테이블 | 판단 |
| --- | --- |
| member | 비키 속성끼리 결정하는 관계가 없습니다. `email → 나머지`는 email이 후보키이므로 3NF를 어기지 않습니다. |
| follow | 비키 속성이 created_at 하나뿐이라 이행 종속이 생길 수 없습니다. |
| post | 작성자 이름·이메일을 저장하지 않고 member_id로 참조합니다. 이름을 함께 저장했다면 `id → member_id → name`이 이행 종속이 됩니다. |
| comment | 작성자 이름과 게시글 내용을 저장하지 않고 member_id, post_id로 참조합니다. |
| post_like | 비키 속성이 created_at 하나뿐이라 이행 종속이 생길 수 없습니다. |

다섯 테이블 모두 3NF를 만족합니다.

### 설계 이유

- 회원과 회원 사이에는 "팔로우한다/팔로우된다"는 1:N 관계가 양쪽으로 있어 N:M이 됩니다. 이를 member에 컬럼으로 두지 않고 follow 테이블로 분리했습니다. 회원과 게시글 사이의 좋아요도 같은 이유로 post_like로 분리했습니다.
- follow, post, comment, post_like 어디에도 회원의 이름이나 이메일을 다시 저장하지 않고 member.id만 참조합니다. 회원 정보를 바꿀 때 member 한 곳만 고치면 되므로 갱신 이상이 생기지 않습니다.
- 좋아요 수와 댓글 수는 컬럼으로 저장하지 않고 post_like, comment에서 `COUNT`로 구합니다. 따로 저장하면 같은 정보가 두 곳에 생겨 서로 어긋날 수 있습니다.

## 정리

| 테이블 | 기본키(PK) | 외래키(FK) | 함수 종속성 | 결과 |
| --- | --- | --- | --- | --- |
| member | id | 없음 | id → 나머지, email → 나머지 | 3NF |
| follow | (follower_id, following_id) | follower_id, following_id | (follower_id, following_id) → created_at | 3NF |
| post | id | member_id | id → 나머지 | 3NF |
| comment | id | post_id, member_id | id → 나머지 | 3NF |
| post_like | (member_id, post_id) | member_id, post_id | (member_id, post_id) → created_at | 3NF |

### 삭제 시 동작

| 외래키 | 부모를 지우면 |
| --- | --- |
| follow → member | 팔로우 관계도 함께 삭제 (CASCADE) |
| comment.post_id → post | 댓글도 함께 삭제 (CASCADE) |
| post_like.post_id → post | 좋아요도 함께 삭제 (CASCADE) |
| post, comment, post_like의 member_id → member | 삭제 거부 (RESTRICT). 글·댓글·좋아요가 남은 회원은 지울 수 없습니다. |
