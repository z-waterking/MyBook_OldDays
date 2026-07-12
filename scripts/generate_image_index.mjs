#!/usr/bin/env node

import { mkdir, readFile, readdir, stat, writeFile } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { basename, extname, join, relative } from 'node:path';

const ROOT = process.cwd();
const ARTICLES_DIR = join(ROOT, 'articles');
const SHARED_IMAGES_DIR = join(ROOT, 'assets', 'images');
const ARTICLE_IMAGES_DIR = join(SHARED_IMAGES_DIR, 'articles');
const WEBSITE_DIR = join(ROOT, 'website');
const OUTPUT = join(WEBSITE_DIR, 'image-index.md');
const IMAGE_EXTS = new Set(['.png', '.jpg', '.jpeg', '.webp', '.gif']);

function encodePath(path) {
  return encodeURI(path).replace(/#/g, '%23');
}

function escapeCell(value) {
  return String(value || '').replace(/\|/g, '\\|').replace(/\r?\n/g, ' ');
}

function decodeYamlScalar(value) {
  const trimmed = value.trim();
  if (trimmed.startsWith('"') && trimmed.endsWith('"')) {
    return trimmed.slice(1, -1).replace(/\\"/g, '"').replace(/\\n/g, '\n').replace(/\\r/g, '\r').replace(/\\\\/g, '\\');
  }
  return trimmed;
}

function parseMeta(content, fallbackTitle) {
  const meta = {};
  const fm = content.match(/^---\r?\n([\s\S]*?)\r?\n---/);
  if (fm) {
    for (const line of fm[1].split(/\r?\n/)) {
      const m = line.match(/^([^:]+):\s*(.*)$/);
      if (m) meta[m[1].trim()] = decodeYamlScalar(m[2]);
    }
  }
  return {
    title: meta.title || content.match(/^#\s+(.+)$/m)?.[1]?.trim() || fallbackTitle,
    date: meta.date || '',
  };
}

async function walkImages(dir) {
  if (!existsSync(dir)) return [];
  const out = [];
  for (const entry of await readdir(dir, { withFileTypes: true })) {
    const full = join(dir, entry.name);
    if (entry.isDirectory()) out.push(...await walkImages(full));
    else if (entry.isFile() && IMAGE_EXTS.has(extname(entry.name).toLowerCase())) out.push(full);
  }
  return out;
}

async function listArticleImages() {
  const dirs = (await readdir(ARTICLES_DIR, { withFileTypes: true }))
    .filter((entry) => entry.isDirectory())
    .map((entry) => entry.name)
    .sort((a, b) => a.localeCompare(b, 'zh-Hans-CN'));
  const rows = [];
  for (const dirName of dirs) {
    const articlePath = join(ARTICLES_DIR, dirName, 'index.md');
    const imagesDir = join(ARTICLE_IMAGES_DIR, dirName);
    if (!existsSync(articlePath) || !existsSync(imagesDir)) continue;
    const meta = parseMeta(await readFile(articlePath, 'utf8'), dirName.replace(/^(合集|散篇)-\d{2}-/, ''));
    const images = (await walkImages(imagesDir)).sort((a, b) => a.localeCompare(b, 'zh-Hans-CN'));
    for (const imagePath of images) {
      const stats = await stat(imagePath);
      const rel = relative(ROOT, imagePath).replace(/\\/g, '/');
      rows.push({
        scope: 'article',
        articleDir: dirName,
        title: meta.title,
        date: meta.date,
        file: basename(imagePath),
        rel,
        size: stats.size,
        role: basename(imagePath).toLowerCase() === 'cover.png' ? 'cover' : 'inline',
      });
    }
  }
  return rows;
}

async function listSharedImages() {
  const rows = [];
  const entries = existsSync(SHARED_IMAGES_DIR)
    ? await readdir(SHARED_IMAGES_DIR, { withFileTypes: true })
    : [];
  const imagePaths = [];
  for (const entry of entries) {
    if (entry.name === 'articles' || entry.name === '_generated') continue;
    const full = join(SHARED_IMAGES_DIR, entry.name);
    if (entry.isDirectory()) imagePaths.push(...await walkImages(full));
    else if (entry.isFile() && IMAGE_EXTS.has(extname(entry.name).toLowerCase())) imagePaths.push(full);
  }
  for (const imagePath of imagePaths) {
    const stats = await stat(imagePath);
    const rel = relative(ROOT, imagePath).replace(/\\/g, '/');
    rows.push({
      scope: 'shared',
      articleDir: '',
      title: '共享图片库',
      date: '',
      file: basename(imagePath),
      rel,
      size: stats.size,
      role: 'shared',
    });
  }
  rows.sort((a, b) => a.rel.localeCompare(b.rel, 'zh-Hans-CN'));
  return rows;
}

function formatSize(bytes) {
  if (bytes >= 1024 * 1024) return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
  if (bytes >= 1024) return `${Math.round(bytes / 1024)} KB`;
  return `${bytes} B`;
}

function renderRows(rows) {
  return rows.map((row) => {
    const preview = `<img src="${encodePath(row.rel)}" alt="${escapeCell(row.title)} ${escapeCell(row.file)}" width="96">`;
    const path = `\`${row.rel}\``;
    const source = row.articleDir ? `[${escapeCell(row.title)}](#/${encodePath(`articles/${row.articleDir}/index.md`)})` : escapeCell(row.title);
    return `| ${preview} | ${source} | ${escapeCell(row.role)} | ${escapeCell(row.file)} | ${formatSize(row.size)} | ${path} |`;
  });
}

async function main() {
  const articleRows = await listArticleImages();
  const sharedRows = await listSharedImages();
  const lines = [
    '# 图片索引',
    '',
    `> 共 ${articleRows.length + sharedRows.length} 张图片，更新于 ${new Date().toISOString().slice(0, 10)}。`,
    '',
    '## 引用规则',
    '',
    '- 所有文章图片统一存放在 `assets/images/articles/<文章目录>/`，原文和 AI 改稿引用同一份文件。',
    '- 其他跨文章、成书区共用图片放入 `assets/images/<主题>/`。',
    '- Markdown 使用仓库根路径，例如 `![](assets/images/articles/合集-05-我在康杰念高中（怀昔）/001.jpg)`。',
    '',
    '## 共享图片库',
    '',
  ];

  if (sharedRows.length) {
    lines.push('| 预览 | 来源 | 类型 | 文件 | 大小 | 引用路径 |');
    lines.push('|------|------|------|------|------|----------|');
    lines.push(...renderRows(sharedRows));
  } else {
    lines.push('暂无共享图片。新增跨文章复用图片时，放入 `assets/images/` 后重新运行 `node scripts/generate_image_index.mjs`。');
  }

  lines.push('', '## 文章图片', '', '| 预览 | 来源 | 类型 | 文件 | 大小 | 引用路径 |', '|------|------|------|------|------|----------|');
  lines.push(...renderRows(articleRows));
  lines.push('', '<!-- 此文件由 scripts/generate_image_index.mjs 自动生成。 -->', '');

  await mkdir(WEBSITE_DIR, { recursive: true });
  await writeFile(OUTPUT, lines.join('\n'), 'utf8');
  console.log(`indexed ${articleRows.length} article images, ${sharedRows.length} shared images`);
}

main().catch((error) => {
  console.error(error.stack || error.message);
  process.exit(1);
});
