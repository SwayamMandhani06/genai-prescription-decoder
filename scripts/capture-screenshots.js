import puppeteer from 'puppeteer-core';
import fs from 'node:fs';
import path from 'node:path';

const edgePath = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe';
const chromePath = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const executablePath = fs.existsSync(edgePath) ? edgePath : chromePath;

const outDir = process.env.SCREENSHOT_OUT_DIR || path.resolve(process.cwd(), 'screenshots');
if (!fs.existsSync(outDir)) {
  fs.mkdirSync(outDir, { recursive: true });
}

async function capture() {
  console.log(`Using browser executable: ${executablePath}`);
  const browser = await puppeteer.launch({
    executablePath,
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-gpu'],
  });

  const page = await browser.newPage();

  // 1. Desktop Light (1440x900)
  await page.setViewport({ width: 1440, height: 900, deviceScaleFactor: 2 });
  await page.goto('http://localhost:5173/', { waitUntil: 'networkidle0' });
  await new Promise((r) => setTimeout(r, 1200));

  await page.screenshot({ path: path.join(outDir, 'screenshot-home-light.png') });

  // 2. Desktop Dark Mode (evaluate theme switch)
  await page.evaluate(() => {
    document.documentElement.classList.add('dark');
  });
  await new Promise((r) => setTimeout(r, 500));
  await page.screenshot({ path: path.join(outDir, 'screenshot-home-dark.png') });

  // Reset to light
  await page.evaluate(() => {
    document.documentElement.classList.remove('dark');
  });

  // 3. Fullpage Light
  await page.screenshot({ path: path.join(outDir, 'screenshot-home-fullpage.png'), fullPage: true });

  // 4. Click "Analyze a prescription" to go to Workspace
  await page.evaluate(() => {
    const btns = Array.from(document.querySelectorAll('button'));
    const target = btns.find((b) => b.textContent && (b.textContent.includes('Analyze a prescription') || b.textContent.includes('Upload Script')));
    if (target) target.click();
  });
  await new Promise((r) => setTimeout(r, 1200));

  // Select a curated sample so document is mounted
  await page.evaluate(() => {
    const btns = Array.from(document.querySelectorAll('button'));
    const sampleBtn = btns.find((b) => b.textContent && b.textContent.includes('Standard Outpatient Script'));
    if (sampleBtn) sampleBtn.click();
  });
  await new Promise((r) => setTimeout(r, 800));
  await page.screenshot({ path: path.join(outDir, 'screenshot-workspace-upload.png') });

  // 5. Click "Continue to Review"
  await page.evaluate(() => {
    const btns = Array.from(document.querySelectorAll('button'));
    const target = btns.find((b) => b.textContent && b.textContent.includes('Continue to Review'));
    if (target) target.click();
  });
  await new Promise((r) => setTimeout(r, 800));
  await page.screenshot({ path: path.join(outDir, 'screenshot-workspace-review.png') });

  // 6. Click "Start Analysis" and wait for completion
  await page.evaluate(() => {
    const btns = Array.from(document.querySelectorAll('button'));
    const target = btns.find((b) => b.textContent && b.textContent.includes('Start Analysis'));
    if (target) target.click();
  });
  await new Promise((r) => setTimeout(r, 6500)); // wait for pipeline stages
  await page.screenshot({ path: path.join(outDir, 'screenshot-workspace-analyze-done.png') });

  // 7. Click "View Findings"
  await page.evaluate(() => {
    const btns = Array.from(document.querySelectorAll('button'));
    const target = btns.find((b) => b.textContent && (b.textContent.includes('View Findings') || b.textContent.includes('View Extracted Results')));
    if (target) target.click();
  });
  await new Promise((r) => setTimeout(r, 1200));
  await page.screenshot({ path: path.join(outDir, 'screenshot-workspace-findings.png') });

  // 8. Tablet (820x1180) & Mobile (390x844)
  await page.setViewport({ width: 820, height: 1180, deviceScaleFactor: 2 });
  await page.goto('http://localhost:5173/', { waitUntil: 'networkidle0' });
  await new Promise((r) => setTimeout(r, 800));
  await page.screenshot({ path: path.join(outDir, 'screenshot-tablet.png') });

  await page.setViewport({ width: 390, height: 844, deviceScaleFactor: 2 });
  await page.screenshot({ path: path.join(outDir, 'screenshot-mobile.png') });

  console.log('All baseline screenshots captured successfully!');
  await browser.close();
}

capture().catch((err) => {
  console.error('Capture error:', err);
  process.exit(1);
});
