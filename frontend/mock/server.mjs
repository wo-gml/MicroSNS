// 백엔드 없이 화면을 확인하기 위한 개발용 목 API입니다. 배포에 사용하지 않습니다.
// 데이터는 Figma 시안의 예시 내용이고 메모리에만 있어, 서버를 끄면 처음 상태로 돌아갑니다.
// 인증은 흉내만 내므로 이 컴퓨터(127.0.0.1)에서만 접속할 수 있게 합니다.
// API 형식은 src/api의 타입과 맞춥니다. src/api가 바뀌면 이 파일도 함께 고칩니다.
import fs from "node:fs";
import http from "node:http";
import path from "node:path";
import { fileURLToPath } from "node:url";

export const SAMPLE_ACCOUNT = { email: "minjun@example.com", password: "test1234" };

const PHOTOS_DIR = path.join(path.dirname(fileURLToPath(import.meta.url)), "photos");
const HOUR = 60;
const DAY = 1440;

const photo = (name) => `/api/mock-photos/${name}.jpg`;
const ago = (minutes) => new Date(Date.now() - minutes * 60_000).toISOString();
const later = (minutes) => new Date(Date.now() + minutes * 60_000).toISOString();
const now = () => new Date().toISOString();

// id % 8이 시안의 아바타 위치와 맞도록 정했습니다.
const users = [
  { id: 1, name: "이도윤", bio: "쿼리 튜닝 스터디 운영 중", base: {}, created_at: ago(200 * DAY) },
  { id: 2, ...SAMPLE_ACCOUNT, name: "김민준", bio: "함께 공부할 사람을 찾고 있어요.", base: {}, created_at: ago(300 * DAY) },
  { id: 3, name: "정민재", bio: "컴퓨터공학과 3학년이에요. 데이터베이스와 백엔드 개발에 관심이 많고, 함께 공부할 사람을 찾고 있어요.", base: { posts: 8, followers: 128, following: 64 }, created_at: "2026-03-10T10:00:00" },
  { id: 4, name: "서지안", bio: null, base: {}, created_at: ago(100 * DAY) },
  { id: 5, name: "한유진", bio: null, base: {}, created_at: ago(100 * DAY) },
  { id: 6, name: "강서준", bio: null, base: {}, created_at: ago(100 * DAY) },
  { id: 7, name: "박지호", bio: null, base: {}, created_at: ago(100 * DAY) },
  { id: 8, name: "최하은", bio: null, base: {}, created_at: ago(100 * DAY) },
];
const follows = new Set(["2:1", "2:8", "2:7", "2:5", "2:6", "2:4", "7:2"]);

// likes와 commentBase는 시안의 숫자를 맞추기 위한 초깃값입니다.
const makePost = (id, author_id, content, minutes, likes, commentBase, image_urls = [], liked = false) => ({
  id,
  author_id,
  content,
  created_at: ago(minutes),
  likes,
  commentBase,
  image_urls,
  likedBy: new Set(liked ? [2] : []),
});

let posts = [
  makePost(1, 1, "MySQL 쿼리 튜닝 스터디 같이 하실 분 구해요. 매주 토요일 오전에 만나고, 실행 계획 읽는 법부터 시작합니다. 지금 3명이고 2명 더 모집해요.\n#스터디 #데이터베이스", 2 * HOUR, 23, 0, [photo("laptop-cafe")], true),
  makePost(2, 8, "졸업 프로젝트로 일정 공유 웹앱을 만들고 있어요. 함께할 프론트엔드 개발자 1명을 찾습니다. Next.js 경험이 있으면 좋아요.\n#프로젝트 #프론트엔드", 5 * HOUR, 12, 5, [photo("whiteboard"), photo("calendar-app")]),
  makePost(3, 7, "알고리즘 스터디 4기를 모집합니다. 온라인으로 주 2회 진행하고, 풀이는 깃허브에 올려서 서로 리뷰해요.\n#스터디 #알고리즘", 25 * HOUR, 37, 8),
  makePost(4, 5, "FastAPI 입문서 한 권을 같이 끝낼 분을 찾아요. 백엔드가 처음이어도 괜찮아요.\n#스터디 #백엔드", 2 * DAY + 60, 9, 2),
  makePost(5, 6, "스프링 부트로 게시판을 만드는 스터디를 시작해요. 자바 기초만 알면 돼요.\n#스터디 #백엔드", 3 * DAY + 60, 21, 6),
  makePost(6, 4, "해커톤에 같이 나갈 디자이너를 찾아요. 기획은 거의 끝났고, 개발자 2명이 함께하고 있어요.\n#프로젝트 #디자인", 4 * DAY + 60, 15, 3),
  makePost(7, 3, "SQL 인덱스 스터디원을 찾습니다. 인덱스 설계와 실행 계획을 예제로 함께 공부해요.\n#스터디 #데이터베이스", 3 * HOUR, 18, 4, [photo("book-desk")]),
  makePost(8, 3, "미니 SNS를 만드는 팀 프로젝트에서 백엔드를 맡을 분을 찾아요. FastAPI와 MySQL을 사용합니다.\n#프로젝트 #백엔드", 4 * DAY, 30, 6, [], true),
  makePost(9, 3, "이번 학기 데이터베이스 수업을 같이 복습하실 분 있나요? 정규화부터 시작해요.\n#스터디 #데이터베이스", 14 * DAY, 7, 1),
  makePost(10, 3, "백엔드 포트폴리오를 서로 리뷰할 분을 구해요. 매주 한 번 온라인으로 만나요.\n#스터디 #백엔드", 31 * DAY, 11, 2),
  makePost(11, 2, "함께 사이드 프로젝트 하실 분을 찾아요. 주말에 온라인으로 만나요.\n#프로젝트", 5 * DAY, 0, 0),
  // "더 보기" 확인용
  ...Array.from({ length: 24 }, (_, i) => makePost(100 + i, 1, `지난 모집 글 ${i + 1}\n#지난글`, 20 * DAY + i * 100, 0, 0)),
];

let comments = [
  [1, 3, "실행 계획을 제대로 본 적이 없는데 저도 참여할 수 있을까요?", HOUR + 5],
  [2, 8, "토요일 오전이면 저도 가능해요. 모임 시간은 몇 시인가요?", HOUR],
  [3, 5, "교재 정할 때 추천 목록도 같이 공유해 주시면 좋겠어요.", 30],
  [4, 7, "온라인으로 진행하면 저도 참여해 보고 싶어요.", 20],
  [5, 6, "스터디 기록은 어디에 남길 계획인가요?", 10],
].map(([id, author_id, content, minutes]) => ({ id, post_id: 1, author_id, content, created_at: ago(minutes) }));

const notifications = [
  [1, "like", 1, 1, "이도윤님이 회원님의 글을 좋아합니다.", false, 3],
  [2, "application", 8, 11, "최하은님이 회원님의 모집에 지원했습니다.", false, 12],
  [3, "follow", 7, null, "박지호님이 회원님을 팔로우하기 시작했습니다.", false, HOUR],
  [4, "comment", 5, 1, "한유진님이 회원님의 글에 댓글을 남겼습니다.", true, 3 * HOUR],
  [5, "application_result", 1, 1, "이도윤님이 회원님의 지원을 수락했습니다.", true, 25 * HOUR],
].map(([id, type, actor_id, post_id, content, is_read, minutes]) => ({ id, user_id: 2, type, actor_id, post_id, content, is_read, created_at: ago(minutes) }));

const recruitments = [
  { id: 1, post_id: 1, type: "study", capacity: 5, deadline: later(7 * DAY), status: "open", created_at: ago(2 * HOUR), updated_at: ago(2 * HOUR) },
  { id: 2, post_id: 2, type: "project", capacity: 1, deadline: later(3 * DAY), status: "open", created_at: ago(5 * HOUR), updated_at: ago(5 * HOUR) },
  { id: 3, post_id: 3, type: "study", capacity: 4, deadline: ago(HOUR), status: "open", created_at: ago(25 * HOUR), updated_at: ago(25 * HOUR) },
  { id: 4, post_id: 11, type: "project", capacity: 2, deadline: later(5 * DAY), status: "open", created_at: ago(5 * DAY), updated_at: ago(5 * DAY) },
];

let applications = [
  { id: 1, recruitment_id: 1, member_id: 3, message: "실행 계획을 배우고 싶어요.", status: "accepted", created_at: ago(HOUR), updated_at: ago(30) },
  { id: 2, recruitment_id: 2, member_id: 2, message: "Next.js 경험이 있어요.", status: "pending", created_at: ago(HOUR), updated_at: ago(HOUR) },
  { id: 3, recruitment_id: 4, member_id: 8, message: "프론트엔드를 맡고 싶어요.", status: "pending", created_at: ago(12), updated_at: ago(12) },
  { id: 4, recruitment_id: 4, member_id: 3, message: null, status: "pending", created_at: ago(60), updated_at: ago(60) },
  { id: 5, recruitment_id: 4, member_id: 5, message: "기획도 도울 수 있어요.", status: "pending", created_at: ago(90), updated_at: ago(90) },
];

const TRENDING = [["스터디", 128], ["프로젝트", 96], ["데이터베이스", 54], ["프론트엔드", 41], ["알고리즘", 37]];
let nextId = 1000;

const summary = (id) => {
  const { name } = users.find((user) => user.id === id);
  return { id, name };
};
const isFollowing = (me, id) => (me ? follows.has(`${me.id}:${id}`) : false);

function recruitmentOut(recruitment, me) {
  if (!recruitment) return null;
  const mine = me
    ? applications.find((a) => a.recruitment_id === recruitment.id && a.member_id === me.id)
    : null;
  return {
    ...recruitment,
    accepted_count: applications.filter((a) => a.recruitment_id === recruitment.id && a.status === "accepted").length,
    my_application: mine ? { id: mine.id, message: mine.message, status: mine.status } : null,
  };
}

const applicationOut = ({ member_id, ...application }) => ({ ...application, applicant: summary(member_id) });

const postOut = (post, me) => ({
  id: post.id,
  author: { ...summary(post.author_id), is_following: isFollowing(me, post.author_id) },
  content: post.content,
  image_urls: post.image_urls,
  created_at: post.created_at,
  like_count: post.likes + post.likedBy.size,
  comment_count: post.commentBase + comments.filter((c) => c.post_id === post.id).length,
  liked_by_me: me ? post.likedBy.has(me.id) : false,
  recruitment: recruitmentOut(recruitments.find((r) => r.post_id === post.id), me),
});

const userItem = (user, me) => ({ id: user.id, name: user.name, bio: user.bio, is_following: isFollowing(me, user.id) });
const publicMe = ({ id, email, name, bio, created_at }) => ({ id, email, name, bio, created_at });

function page(rows, url) {
  const limit = Number(url.searchParams.get("limit") ?? 20);
  const offset = Number(url.searchParams.get("offset") ?? 0);
  return { items: rows.slice(offset, offset + limit), limit, offset, has_more: rows.length > offset + limit };
}

const newestFirst = (a, b) => new Date(b.created_at) - new Date(a.created_at);
const fail = (status, code, message) => ({ status, body: { error: { code, message } } });
const hasTag = (post, tag) => post.content.split(/\s+/).includes(`#${tag}`);
const postsPage = (rows, url, me) => ({ body: page(rows.sort(newestFirst).map((post) => postOut(post, me)), url) });

function route(method, pathname, url, body, me, setCookie) {
  const needLogin = () => (me ? null : fail(401, "UNAUTHORIZED", "로그인이 필요합니다."));
  const logIn = (user) => setCookie(`access_token=${user.id}; HttpOnly; Path=/; SameSite=Lax`);
  let m;

  if (method === "GET" && pathname === "/auth/me") return needLogin() ?? { body: publicMe(me) };
  if (method === "POST" && pathname === "/auth/login") {
    const user = users.find((u) => u.email && u.email === body.email && u.password === body.password);
    if (!user) return fail(401, "UNAUTHORIZED", "이메일 또는 비밀번호가 올바르지 않습니다.");
    logIn(user);
    return { body: publicMe(user) };
  }
  if (method === "POST" && pathname === "/auth/signup") {
    if (users.some((u) => u.email === body.email)) return fail(409, "CONFLICT", "이미 가입된 이메일입니다.");
    const user = { id: ++nextId, email: body.email, password: body.password, name: body.name, bio: body.bio ?? null, base: {}, created_at: now() };
    users.push(user);
    logIn(user);
    return { status: 201, body: publicMe(user) };
  }
  if (method === "POST" && pathname === "/auth/logout") {
    setCookie("access_token=; Max-Age=0; Path=/");
    return { status: 204 };
  }

  // 업로드한 파일은 저장하지 않고 예시 사진 주소를 돌려줍니다.
  if (method === "POST" && pathname === "/uploads") {
    return needLogin() ?? { status: 201, body: { url: `${photo("calendar-app")}?u=${++nextId}` } };
  }

  if (method === "GET" && pathname === "/posts/feed") {
    return needLogin() ?? postsPage(posts.filter((p) => p.author_id === me.id || isFollowing(me, p.author_id)), url, me);
  }
  if (method === "POST" && pathname === "/posts") {
    if (needLogin()) return needLogin();
    const post = makePost(++nextId, me.id, body.content, 0, 0, 0, body.image_urls ?? []);
    posts.push(post);
    if (body.recruitment) {
      recruitments.push({ id: ++nextId, post_id: post.id, ...body.recruitment, status: "open", created_at: now(), updated_at: now() });
    }
    return { status: 201, body: postOut(post, me) };
  }
  if ((m = pathname.match(/^\/posts\/(\d+)$/))) {
    const post = posts.find((p) => p.id === Number(m[1]));
    if (!post) return fail(404, "NOT_FOUND", "게시글을 찾을 수 없습니다.");
    if (method === "GET") return { body: postOut(post, me) };
    if (method === "DELETE") {
      if (needLogin()) return needLogin();
      if (post.author_id !== me.id) return fail(403, "FORBIDDEN", "권한이 없습니다.");
      posts = posts.filter((p) => p !== post);
      return { status: 204 };
    }
  }
  if ((m = pathname.match(/^\/posts\/(\d+)\/like$/))) {
    if (needLogin()) return needLogin();
    const post = posts.find((p) => p.id === Number(m[1]));
    if (!post) return fail(404, "NOT_FOUND", "게시글을 찾을 수 없습니다.");
    if (method === "POST") post.likedBy.add(me.id);
    else post.likedBy.delete(me.id);
    return { status: 204 };
  }

  if ((m = pathname.match(/^\/posts\/(\d+)\/comments$/))) {
    const postId = Number(m[1]);
    if (method === "GET") {
      const rows = comments.filter((c) => c.post_id === postId).map((c) => ({ ...c, author: summary(c.author_id) }));
      return { body: page(rows, url) };
    }
    if (needLogin()) return needLogin();
    const comment = { id: ++nextId, post_id: postId, author_id: me.id, content: body.content, created_at: now() };
    comments.push(comment);
    return { status: 201, body: { ...comment, author: summary(me.id) } };
  }
  if ((m = pathname.match(/^\/comments\/(\d+)$/)) && method === "DELETE") {
    if (needLogin()) return needLogin();
    comments = comments.filter((c) => c.id !== Number(m[1]));
    return { status: 204 };
  }

  if ((m = pathname.match(/^\/recruitments\/(\d+)$/)) && method === "PATCH") {
    if (needLogin()) return needLogin();
    const recruitment = recruitments.find((r) => r.id === Number(m[1]));
    if (!recruitment) return fail(404, "NOT_FOUND", "모집을 찾을 수 없습니다.");
    recruitment.status = body.status;
    recruitment.updated_at = now();
    return { body: recruitmentOut(recruitment, me) };
  }
  if ((m = pathname.match(/^\/recruitments\/(\d+)\/applications$/))) {
    if (needLogin()) return needLogin();
    const id = Number(m[1]);
    if (method === "GET") {
      return { body: page(applications.filter((a) => a.recruitment_id === id).map(applicationOut), url) };
    }
    const application = { id: ++nextId, recruitment_id: id, member_id: me.id, message: body.message, status: "pending", created_at: now(), updated_at: now() };
    applications.push(application);
    return { status: 201, body: applicationOut(application) };
  }
  if ((m = pathname.match(/^\/applications\/(\d+)$/))) {
    if (needLogin()) return needLogin();
    const application = applications.find((a) => a.id === Number(m[1]));
    if (!application) return fail(404, "NOT_FOUND", "지원을 찾을 수 없습니다.");
    if (method === "PATCH") {
      application.status = body.status;
      application.updated_at = now();
      return { body: applicationOut(application) };
    }
    if (method === "DELETE") {
      applications = applications.filter((a) => a !== application);
      return { status: 204 };
    }
  }

  if ((m = pathname.match(/^\/users\/(\d+)$/)) && method === "GET") {
    const user = users.find((u) => u.id === Number(m[1]));
    if (!user) return fail(404, "NOT_FOUND", "회원을 찾을 수 없습니다.");
    return {
      body: {
        ...userItem(user, me),
        created_at: user.created_at,
        post_count: (user.base.posts ?? 0) + posts.filter((p) => p.author_id === user.id).length,
        follower_count: (user.base.followers ?? 0) + [...follows].filter((k) => k.endsWith(`:${user.id}`)).length,
        following_count: (user.base.following ?? 0) + [...follows].filter((k) => k.startsWith(`${user.id}:`)).length,
      },
    };
  }
  if ((m = pathname.match(/^\/users\/(\d+)\/posts$/))) return postsPage(posts.filter((p) => p.author_id === Number(m[1])), url, me);
  if ((m = pathname.match(/^\/users\/(\d+)\/likes$/))) return postsPage(posts.filter((p) => p.likedBy.has(Number(m[1]))), url, me);
  if ((m = pathname.match(/^\/users\/(\d+)\/followers$/))) return { body: page(users.filter((u) => follows.has(`${u.id}:${m[1]}`)).map((u) => userItem(u, me)), url) };
  if ((m = pathname.match(/^\/users\/(\d+)\/following$/))) return { body: page(users.filter((u) => follows.has(`${m[1]}:${u.id}`)).map((u) => userItem(u, me)), url) };
  if ((m = pathname.match(/^\/users\/(\d+)\/follow$/))) {
    if (needLogin()) return needLogin();
    const key = `${me.id}:${m[1]}`;
    if (method === "POST") follows.add(key);
    else follows.delete(key);
    return { status: 204 };
  }

  if (pathname === "/hashtags/trending") return { body: TRENDING.map(([name, post_count]) => ({ name, post_count })) };
  if ((m = pathname.match(/^\/hashtags\/([^/]+)\/posts$/))) {
    const tag = decodeURIComponent(m[1]);
    return postsPage(posts.filter((p) => hasTag(p, tag)), url, me);
  }
  if ((m = pathname.match(/^\/hashtags\/([^/]+)$/))) {
    const tag = decodeURIComponent(m[1]);
    const seeded = TRENDING.find(([name]) => name === tag);
    return { body: { name: tag, post_count: seeded ? seeded[1] : posts.filter((p) => hasTag(p, tag)).length } };
  }

  if (pathname === "/notifications" && method === "GET") {
    if (needLogin()) return needLogin();
    const rows = notifications
      .filter((n) => n.user_id === me.id)
      .sort(newestFirst)
      .map(({ actor_id, user_id, ...n }) => ({ ...n, actor: summary(actor_id) }));
    return { body: page(rows, url) };
  }
  if (pathname === "/notifications/unread-count") {
    return needLogin() ?? { body: { count: notifications.filter((n) => n.user_id === me.id && !n.is_read).length } };
  }
  if ((m = pathname.match(/^\/notifications\/(\d+)\/read$/)) && method === "POST") {
    if (needLogin()) return needLogin();
    const notification = notifications.find((n) => n.id === Number(m[1]));
    if (notification) notification.is_read = true;
    return { status: 204 };
  }

  return fail(404, "NOT_FOUND", "Not Found");
}

function handleRequest(req, res) {
  const chunks = [];
  req.on("data", (chunk) => chunks.push(chunk));
  req.on("end", () => {
    const url = new URL(req.url, "http://mock");

    // 파일 이름은 영문, 숫자, 하이픈만 허용합니다.
    const photoMatch = url.pathname.match(/^\/mock-photos\/([0-9a-z-]+\.jpg)$/);
    if (photoMatch) {
      fs.readFile(path.join(PHOTOS_DIR, photoMatch[1]), (error, data) => {
        res.writeHead(error ? 404 : 200, { "Content-Type": "image/jpeg" });
        res.end(error ? "" : data);
      });
      return;
    }

    const token = /access_token=(\d+)/.exec(req.headers.cookie ?? "")?.[1];
    const me = users.find((user) => String(user.id) === token) ?? null;
    const headers = { "Content-Type": "application/json" };
    const isJson = (req.headers["content-type"] ?? "").includes("application/json");
    const body = isJson ? JSON.parse(Buffer.concat(chunks).toString()) : {};
    const result = route(req.method, url.pathname, url, body, me, (cookie) => {
      headers["Set-Cookie"] = cookie;
    });
    res.writeHead(result.status ?? 200, headers);
    res.end(result.body === undefined ? "" : JSON.stringify(result.body));
  });
}

export function startMockServer(port) {
  return new Promise((resolve, reject) => {
    const server = http.createServer(handleRequest);
    server.once("error", reject);
    server.listen(port, "127.0.0.1", () => resolve(server));
  });
}
