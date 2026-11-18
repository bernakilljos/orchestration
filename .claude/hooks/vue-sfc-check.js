// vue-sfc-check.js — .vue 단일 파일 구문 검사 (check-js-syntax.sh 가 호출 · 2026-11-13 R249)
// 새 도구를 설치하지 않고 그 프로젝트에 이미 있는 Vue 컴파일러를 쓴다:
//   프로젝트 Vue 와 짝인 'vue/compiler-sfc' (Vue 2.7·3 모두 제공) 우선 → 없으면 '@vue/compiler-sfc' → 둘 다 없으면 검사 생략 (exit 0).
//   Vue 2 프로젝트에 호이스팅된 Vue 3 컴파일러를 먼저 쓰면 정상 Vue 2 템플릿(필터 등)을 오류로 잘못 잡는다.
// 검사: SFC 구조 오류 · 템플릿 컴파일 오류 · <script setup> 은 compileScript · 일반 JS <script> 는 node --check.
// 결과: 오류 있으면 stderr 에 내용 + exit 1 · 없으면 exit 0.
// 별도 파일인 이유: Git Bash → Windows node 에 여러 줄 `node -e` 인자를 넘기면 첫 줄만 실행된다 [확인 2026-11-13].
"use strict";
const fs = require("fs"), os = require("os"), path = require("path"), cp = require("child_process");

const file = process.argv[2];
if (!file || !fs.existsSync(file)) process.exit(0);
const req = require("module").createRequire(path.resolve(file));
let sfc = null;
for (const m of ["vue/compiler-sfc", "@vue/compiler-sfc"]) {
  try { sfc = req(m); break; } catch (e) { /* 다음 후보 */ }
}
if (!sfc || typeof sfc.parse !== "function") process.exit(0);

const msg = (e) => String((e && (e.message || e.msg)) || e);
const errs = [];
const src = fs.readFileSync(file, "utf8");
// 호출 형식이 버전마다 다르다 — Vue 3: parse(source, {filename}) · Vue 2.7: parse({source, filename}).
//   Vue 2.7 에 Vue 3 형식으로 부르면 오류 없이 빈 descriptor 를 돌려줘 아무것도 검사하지 않고 통과했다 [확인 2026-11-13].
const empty = (x) => { const dd = x.descriptor || x; return !dd.template && !dd.script && !dd.scriptSetup; };
let r = sfc.parse(src, { filename: file });
let vue2 = false;
if (empty(r) && /<(template|script)[\s>]/.test(src)) { r = sfc.parse({ source: src, filename: file }); vue2 = true; }
const d = r.descriptor || r;
if (empty(r) && /<(template|script)[\s>]/.test(src)) {
  fs.writeSync(2, "sfc: 블록을 읽지 못함 (컴파일러 형식 불일치 · 검사 미수행)");
  process.exit(0);   // 검사 못 함 = 통과 아님 — 차단도 하지 않고 사유만 남긴다 (오탐 방지)
}
// Vue 2.7 의 SFC 구조 단계 errors 는 경고 성격 — 실제로 빌드되는 IFRS 파일 285개 중 10개가 «<br>·<input> 닫는 태그 없음»
//   으로 걸렸다 (빈 요소 · 템플릿 컴파일은 통과) [확인 2026-11-13] → Vue 2 는 템플릿 컴파일·스크립트 구문 오류만 차단 근거.
if (!vue2) for (const e of (r.errors || d.errors || [])) errs.push("sfc: " + msg(e));

if (d.template && !d.template.src && (!d.template.lang || d.template.lang === "html") && sfc.compileTemplate) {
  const t = sfc.compileTemplate({ source: d.template.content, filename: file, id: "chk", compilerOptions: { outputSourceRange: true } });
  for (const e of (t.errors || [])) errs.push("template: " + msg(e));
}

const s = d.scriptSetup || d.script;
if (s && !s.src) {
  if (d.scriptSetup && sfc.compileScript) {
    try { sfc.compileScript(d, { id: "chk" }); } catch (e) { errs.push("script: " + msg(e)); }
  } else if (!s.lang || s.lang === "js") {
    const tmp = path.join(os.tmpdir(), "vuechk-" + process.pid + ".mjs");
    fs.writeFileSync(tmp, s.content);
    const p = cp.spawnSync(process.execPath, ["--check", tmp], { encoding: "utf8" });
    try { fs.unlinkSync(tmp); } catch (e) { /* 무시 */ }
    if (p.status !== 0) {
      errs.push("script: " + String(p.stderr || "").split(tmp).join(path.basename(file) + " <script>")
        .trim().split("\n").slice(0, 6).join("\n"));
    }
  }
}

if (errs.length) {
  fs.writeSync(2, errs.join("\n").slice(0, 3000));   // 동기 쓰기 — Windows 파이프에서 exit 전 출력 유실 방지
  process.exit(1);
}
process.exit(0);
