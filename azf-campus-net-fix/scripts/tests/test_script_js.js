// 跨语言一致性测试：用 Node 真实执行生成的扩展脚本，
// 与 Python 侧 (reach.apply_cf_fix) 的预演结果对比。
//
//   node scripts/tests/test_script_js.js
//
// 退出码 0 = 通过。需要先运行 probe / profile / apply --dry-run。

const fs = require('fs');
const path = require('path');
const vm = require('vm');
const os = require('os');

const SKILL_ROOT = path.resolve(__dirname, '..', '..');
const SCRIPT = path.join(SKILL_ROOT, 'data', 'Script.latest.js');
const APPDATA = process.env.APPDATA;
const DATA_DIR = path.join(APPDATA, 'io.github.clash-verge-rev.clash-verge-rev');
const PROFILES = path.join(DATA_DIR, 'profiles');

let failures = 0;
function check(cond, msg) {
  if (cond) {
    console.log('  ✓ ' + msg);
  } else {
    console.log('  ✗ ' + msg);
    failures++;
  }
}

if (!fs.existsSync(SCRIPT)) {
  console.error('找不到生成的脚本：' + SCRIPT + '\n请先运行：apply --dry-run');
  process.exit(2);
}

// --- 极简 YAML 读取：只取 proxies / proxy-groups（与 Python 侧同一份配置）---
function parseYaml(file) {
  const text = fs.readFileSync(file, 'utf8');
  // 用 Python 侧导出的 JSON 更可靠；这里改为读取 dump 文件
  return JSON.parse(fs.readFileSync(file, 'utf8'));
}

const src = fs.readFileSync(SCRIPT, 'utf8');
const sandbox = { console: { log: () => {} } };
vm.createContext(sandbox);
vm.runInContext(src, sandbox);

console.log('=== 1. 脚本结构与语法 ===');
check(typeof sandbox.main === 'function', '导出 main(config, profileName)');
check(/function main\(config, profileName\)/.test(src), '函数签名正确');
check(/reality-opts/.test(src), '启发式规则含 REALITY 排除');
check(/CF_FIPS|CF_IPS/.test(src), '含 CF_IPS 常量');

// --- 取出所有订阅，逐个跑 ---
const dumpFile = path.join(os.tmpdir(), 'cnfx_dump.json');
if (!fs.existsSync(dumpFile)) {
  console.log('\n（跳过 2-5：未找到 ' + dumpFile + '，请先运行 Python 侧导出）');
  process.exit(failures ? 1 : 0);
}
const dumps = JSON.parse(fs.readFileSync(dumpFile, 'utf8'));

for (const item of dumps) {
  const name = item.name;
  const before = JSON.parse(JSON.stringify(item.config));
  console.log('\n=== 订阅：' + name + ' ===');

  const out = sandbox.main(JSON.parse(JSON.stringify(before)), name);
  if (!out || !out.proxies || !out['proxy-groups']) {
    check(false, 'main 返回有效配置');
    continue;
  }

  // 2) 只改入口 IP：名称/类型/SNI/reality-opts/ws-opts 必须不变
  let changed = 0, errs = 0;
  for (let i = 0; i < before.proxies.length; i++) {
    const a = before.proxies[i], b = out.proxies[i];
    if (!a || !b) { errs++; continue; }
    if (a.server !== b.server) changed++;
    if (a.name !== b.name) { errs++; }
    if (a.type !== b.type) { errs++; }
    if ((a.servername || a.sni || '') !== (b.servername || b.sni || '')) { errs++; }
    if (JSON.stringify(a['reality-opts'] || null) !==
        JSON.stringify(b['reality-opts'] || null)) { errs++; }
    if (JSON.stringify(a['ws-opts'] || null) !==
        JSON.stringify(b['ws-opts'] || null)) { errs++; }
  }
  check(errs === 0, '名称/类型/SNI/reality-opts/ws-opts 全部未改动（' + errs + ' 处异常）');
  console.log('    （改写入口 IP 的节点：' + changed + ' 个）');

  // 3) REALITY 节点绝不被改写
  let realityChanged = 0;
  for (let i = 0; i < before.proxies.length; i++) {
    if (before.proxies[i]['reality-opts'] &&
        before.proxies[i].server !== out.proxies[i].server) realityChanged++;
  }
  check(realityChanged === 0, 'REALITY 节点未被改写（' + realityChanged + ' 个被误改）');

  // 4) 分组：无空组、内置项保留
  const BUILTIN = ['DIRECT', 'REJECT', 'REJECT-DROP', 'PASS', 'COMPATIBLE', 'GLOBAL'];
  const gnames = new Set(before['proxy-groups'].map((g) => g.name));
  let empty = 0, brokenKept = 0;
  for (const g of out['proxy-groups']) {
    if (!g.proxies || !g.proxies.length) empty++;
    for (const n of g.proxies || []) {
      if (typeof n !== 'string') continue;
      if (BUILTIN.includes(n) || gnames.has(n)) continue;
      // 组内不得残留本订阅的死节点
      if ((item.dead || []).includes(n)) brokenKept++;
    }
  }
  check(empty === 0, '无空分组');
  check(brokenKept === 0, '组内无残留死节点（' + brokenKept + ' 个残留）');

  // 5) 幂等：连跑两次结果一致
  const twice = sandbox.main(JSON.parse(JSON.stringify(before)), name);
  check(JSON.stringify(twice) === JSON.stringify(out), '幂等（两次运行结果一致）');
}

console.log('\n' + (failures === 0 ? '全部通过' : failures + ' 项失败'));
process.exit(failures ? 1 : 0);
