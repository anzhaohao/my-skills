import fs from 'node:fs/promises';
import path from 'node:path';

function arg(name, fallback = '') {
  const i = process.argv.indexOf(name);
  return i >= 0 && i + 1 < process.argv.length ? process.argv[i + 1] : fallback;
}

const url = arg('--url');
const out = arg('--out');
const waitMs = Number(arg('--wait', '800'));
const insecure = process.argv.includes('--allow-insecure-tls');
if (!url || !out) {
  console.error('Usage: node azf-ui-capture.mjs --url URL --out DIRECTORY [--wait MS]');
  process.exit(2);
}

let playwright;
try {
  playwright = await import('playwright');
} catch (error) {
  console.error(JSON.stringify({ status: 'BLOCKED', reason: 'Playwright is not available; install nothing automatically.', error: String(error) }));
  process.exit(2);
}

await fs.mkdir(out, { recursive: true });
const viewports = [
  { name: 'desktop-1440x900', width: 1440, height: 900 },
  { name: 'mobile-390x844', width: 390, height: 844 },
];
const result = { status: 'CAPTURE_READY', url, screenshots: [], console_errors: [], failed_requests: [], viewports: [] };
const browser = await playwright.chromium.launch({ headless: true });
try {
  for (const viewport of viewports) {
    const context = await browser.newContext({ viewport, ignoreHTTPSErrors: insecure });
    const page = await context.newPage();
    const consoleErrors = [];
    const failedRequests = [];
    page.on('console', message => { if (message.type() === 'error') consoleErrors.push(message.text()); });
    page.on('requestfailed', request => failedRequests.push({ url: request.url(), failure: request.failure()?.errorText ?? 'unknown' }));
    let navigation = 'PASS';
    try {
      await page.goto(url, { waitUntil: 'networkidle', timeout: 30000 });
      if (waitMs > 0) await page.waitForTimeout(waitMs);
    } catch (error) {
      navigation = `FAIL: ${String(error)}`;
    }
    const layout = await page.evaluate(() => ({
      scrollWidth: document.documentElement.scrollWidth,
      clientWidth: document.documentElement.clientWidth,
      bodyHeight: document.body?.scrollHeight ?? 0,
      title: document.title,
    })).catch(error => ({ error: String(error) }));
    const file = path.join(out, `${viewport.name}.png`);
    await page.screenshot({ path: file, fullPage: true });
    const item = { name: viewport.name, width: viewport.width, height: viewport.height, file, navigation, layout, console_errors: consoleErrors, failed_requests: failedRequests };
    result.screenshots.push(file);
    result.viewports.push(item);
    result.console_errors.push(...consoleErrors);
    result.failed_requests.push(...failedRequests);
    await context.close();
  }
} finally {
  await browser.close();
}
await fs.writeFile(path.join(out, 'ui-check.json'), JSON.stringify(result, null, 2), 'utf8');
console.log(JSON.stringify(result, null, 2));
