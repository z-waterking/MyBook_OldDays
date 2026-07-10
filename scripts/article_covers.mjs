#!/usr/bin/env node

import { mkdir, readFile, readdir, writeFile } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { basename, dirname, join, relative } from 'node:path';
import { stdin, stdout } from 'node:process';

const ROOT = process.cwd();
const ARTICLES_DIR = join(ROOT, 'articles');
const AI_EDITED_DIR = join(ROOT, 'ai-edited-articles');
const WEBSITE_DIR = join(ROOT, 'website');
const CATALOG = join(WEBSITE_DIR, 'catalog.md');
const DEFAULT_REST_ENDPOINT = 'https://41626-me2j04fd-eastus2.cognitiveservices.azure.com/openai/deployments/gpt-image-2/images/generations';
const DEFAULT_API_VERSION = '2024-02-01';

function parseArgs(argv) {
  const args = {};
  for (let i = 0; i < argv.length; i += 1) {
    const key = argv[i];
    if (!key.startsWith('--')) continue;
    const value = argv[i + 1];
    if (!value || value.startsWith('--')) args[key.slice(2)] = true;
    else {
      args[key.slice(2)] = value;
      i += 1;
    }
  }
  return args;
}

async function promptHidden(label) {
  if (!stdin.isTTY) return (await readAllStdin()).trim();
  stdout.write(label);
  stdin.setRawMode(true);
  stdin.resume();
  stdin.setEncoding('utf8');
  let value = '';
  try {
    for await (const chunk of stdin) {
      for (const key of chunk) {
        if (key === '\u0003') throw new Error('Input cancelled.');
        if (key === '\r' || key === '\n') {
          stdout.write('\n');
          return value.trim();
        }
        if (key === '\u007f' || key === '\b') value = value.slice(0, -1);
        else value += key;
      }
    }
  } finally {
    stdin.setRawMode(false);
    stdin.pause();
  }
  return value.trim();
}

async function readAllStdin() {
  let text = '';
  for await (const chunk of stdin) text += chunk.toString('utf8');
  return text;
}

function decodeYamlScalar(value) {
  const trimmed = value.trim();
  if (trimmed.startsWith('"') && trimmed.endsWith('"')) {
    return trimmed.slice(1, -1).replace(/\\"/g, '"').replace(/\\n/g, '\n').replace(/\\r/g, '\r').replace(/\\\\/g, '\\');
  }
  return trimmed;
}

function parseArticle(content, dirName) {
  content = String(content).replace(/^\uFEFF/, '');
  const meta = {};
  const fm = content.match(/^---\r?\n([\s\S]*?)\r?\n---/);
  if (fm) {
    for (const line of fm[1].split(/\r?\n/)) {
      const m = line.match(/^([^:]+):\s*(.*)$/);
      if (m) meta[m[1].trim()] = decodeYamlScalar(m[2]);
    }
  }
  const h1 = content.match(/^#\s+(.+)$/m)?.[1]?.trim();
  const title = meta.title || h1 || dirName.replace(/^(合集|散篇)-\d{2}-/, '');
  const author = meta.author || '凡复思忖';
  const date = meta.date || '';
  const body = content
    .replace(/^---\r?\n[\s\S]*?\r?\n---/, '')
    .replace(/\*原文链接:[\s\S]*$/m, '')
    .replace(/!\[[^\]]*\]\([^)]*\)/g, '')
    .replace(/\[([^\]]+)\]\([^)]*\)/g, '$1')
    .replace(/<[^>]+>/g, '')
    .replace(/^#.*$/gm, '')
    .replace(/^>.*$/gm, '')
    .replace(/^---$/gm, '')
    .replace(/[*_`~]/g, '')
    .replace(/\s+/g, ' ')
    .trim();
  return { title, author, date, excerpt: body.slice(0, 650) };
}

function catalogExcerpt(value) {
  const text = String(value || '').replace(/\s+/g, ' ').trim();
  if (text.length <= 150) return text;
  return `${text.slice(0, 150)}...`;
}

function localDate() {
  const date = new Date();
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

function coverPrompt(article, dirName) {
  return `Create a bright, premium editorial cover illustration for a Chinese personal essay.\n` +
    `Title: ${article.title}\n` +
    `Series folder: ${dirName}\n` +
    `Essay excerpt for emotional context: ${article.excerpt}\n` +
    `Composition: 1536x1024 landscape cover, cinematic magazine/editorial illustration, one clear focal scene, readable at thumbnail size, enough calm negative space for a title overlay but do not render any text.\n` +
    `Style: polished painterly realism, warm human detail, subtle literary atmosphere, not corporate stock art, not a poster collage.\n` +
    `Lighting and color: natural daylight or warm evening light, clean contrast, nuanced palette with sky blue, warm gold, soft green or muted red accents as appropriate to the story, no muddy colors.\n` +
    `Details: concrete objects and places suggested by the essay, Chinese life texture, personal memory, restrained symbolism.\n` +
    `Avoid: readable text, logos, watermarks, celebrity likenesses, copyrighted character likenesses, gore, explicit violence, distorted hands, extra limbs, clutter.`;
}

async function generateImage({ apiKey, prompt, output, size, endpoint, apiVersion, timeoutMs }) {
  const response = await fetch(`${endpoint}?api-version=${apiVersion}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'api-key': apiKey },
    body: JSON.stringify({ prompt, n: 1, size }),
    signal: AbortSignal.timeout(timeoutMs),
  });
  const text = await response.text();
  if (!response.ok) throw new Error(`HTTP ${response.status}: ${text}`);
  const body = JSON.parse(text);
  const b64 = body.data?.[0]?.b64_json;
  if (!b64) throw new Error('Response did not include b64_json image data.');
  await mkdir(dirname(output), { recursive: true });
  await writeFile(output, Buffer.from(b64, 'base64'));
}

async function listArticles() {
  const dirs = await readdir(ARTICLES_DIR, { withFileTypes: true });
  const articles = [];
  for (const dir of dirs) {
    if (!dir.isDirectory()) continue;
    const mdPath = join(ARTICLES_DIR, dir.name, 'index.md');
    if (!existsSync(mdPath)) continue;
    const content = await readFile(mdPath, 'utf8');
    const parsed = parseArticle(content, dir.name);
    const files = await readdir(join(ARTICLES_DIR, dir.name), { withFileTypes: true });
    const reviews = files
      .filter((file) => file.isFile() && file.name === 'review.md')
      .map((file) => file.name);
    articles.push({ dir: dir.name, mdPath, content, reviews, ...parsed });
  }
  articles.sort(articleNavSort);
  return articles;
}

function articleNavSort(a, b) {
  const groupA = groupOrder(catalogGroup(a));
  const groupB = groupOrder(catalogGroup(b));
  if (groupA !== groupB) return groupA - groupB;

  const orderA = dirOrder(a.dir);
  const orderB = dirOrder(b.dir);
  if (orderA !== orderB) return orderA - orderB;

  return a.dir.localeCompare(b.dir, 'zh-Hans-CN');
}

function groupOrder(group) {
  const groups = ['合集 · 少年时代', '合集 · 大学四年', '合集 · 工作与考试', '散篇', '其他'];
  const index = groups.indexOf(group);
  return index >= 0 ? index : groups.length;
}

function dirOrder(dirName) {
  const match = dirName.match(/^(?:合集|散篇)-(\d{2})-/);
  return match ? Number(match[1]) : 999;
}

function websiteArticleHref(article) {
  return relative(ROOT, article.mdPath).replace(/\\/g, '/');
}

function websiteImageHref(article) {
  return relative(ROOT, join(ARTICLES_DIR, article.dir, 'images', 'cover.png')).replace(/\\/g, '/');
}

function websiteReviewHref(article, filename) {
  return relative(ROOT, join(ARTICLES_DIR, article.dir, filename)).replace(/\\/g, '/');
}

function aiEditedGroup(dirName) {
  if (dirName.startsWith('散篇-')) return '散篇';
  if (dirName.startsWith('合集-')) return '合集';
  return '其他';
}

function aiEditedPath(article) {
  return join(AI_EDITED_DIR, aiEditedGroup(article.dir), article.dir, 'index.md');
}

function websiteAiEditedHref(article) {
  return relative(ROOT, aiEditedPath(article)).replace(/\\/g, '/');
}

function articleLocalCover(article) {
  return relative(ROOT, join(ARTICLES_DIR, article.dir, 'images', 'cover.png')).replace(/\\/g, '/');
}

function ensureArticleCover(content, article) {
  const coverBlock = `<p><img class="article-cover" src="${articleLocalCover(article)}" alt="${escapeHtml(article.title)} 封面"></p>`;
  if (content.includes(coverBlock)) return content;
  let next = content.replace(/\n?<p><img class="article-cover"[\s\S]*?<\/p>\n?/m, '\n');
  const metaLine = next.match(/^> .*$/m);
  if (metaLine) {
    const idx = metaLine.index + metaLine[0].length;
    next = `${next.slice(0, idx)}\n\n${coverBlock}${next.slice(idx)}`;
  } else {
    const h1 = next.match(/^#\s+.*$/m);
    if (h1) {
      const idx = h1.index + h1[0].length;
      next = `${next.slice(0, idx)}\n\n${coverBlock}${next.slice(idx)}`;
    }
  }
  return next.replace(/(?:\r?\n){4,}/g, '\n\n\n');
}

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function encodePath(path) {
  return encodeURI(path).replace(/#/g, '%23');
}

function catalogGroup(article) {
  if (article.dir.startsWith('散篇-')) return '散篇';
  const match = article.dir.match(/^合集-(\d{2})-/);
  if (!match) return '其他';
  const order = Number(match[1]);
  if (order <= 5) return '合集 · 少年时代';
  if (order <= 10) return '合集 · 大学四年';
  return '合集 · 工作与考试';
}

async function updateCatalog(articles) {
  const lines = [
    '# 文章目录',
    '',
    `> 共 ${articles.length} 篇文章，更新于 ${localDate()}`,
    '',
  ];
  const groups = ['合集 · 少年时代', '合集 · 大学四年', '合集 · 工作与考试', '散篇', '其他'];
  const byGroup = new Map(groups.map((group) => [group, []]));
  for (const article of articles) {
    const group = catalogGroup(article);
    if (!byGroup.has(group)) byGroup.set(group, []);
    byGroup.get(group).push(article);
  }
  for (const group of groups) {
    const groupedArticles = byGroup.get(group) || [];
    if (!groupedArticles.length) continue;
    lines.push(`<div class="article-cover-group">`);
    lines.push(`<h2>${escapeHtml(group)} <small>${groupedArticles.length} 篇</small></h2>`);
    lines.push('<div class="article-cover-list">');
    for (const article of groupedArticles) {
      lines.push('<div class="article-cover-row">');
      lines.push(`<a class="article-cover-thumb" href="#/${encodePath(websiteArticleHref(article))}"><img src="${encodePath(websiteImageHref(article))}" alt="${escapeHtml(article.title)} 封面"></a>`);
      lines.push('<span class="article-cover-info">');
      const actionLinks = [
        `<a href="#/${encodePath(websiteArticleHref(article))}">正文</a>`,
        ...article.reviews.map((filename) => `<a href="#/${encodePath(websiteReviewHref(article, filename))}">评价</a>`),
      ];
      if (existsSync(aiEditedPath(article))) {
        actionLinks.push(`<a href="#/${encodePath(websiteAiEditedHref(article))}">AI改稿</a>`);
      }
      lines.push('<span class="article-cover-head">');
      lines.push('<span class="article-cover-main">');
      lines.push(`<a class="article-cover-title" href="#/${encodePath(websiteArticleHref(article))}"><strong>${escapeHtml(article.title)}</strong></a>`);
      lines.push(`<em>${escapeHtml(article.date || '')}</em>`);
      lines.push('</span>');
      if (actionLinks.length > 1) lines.push(`<span class="article-cover-actions">${actionLinks.join('')}</span>`);
      lines.push('</span>');
      lines.push(`<span class="article-cover-excerpt">${escapeHtml(catalogExcerpt(article.excerpt))}</span>`);
      lines.push('</span>');
      lines.push('</div>');
    }
    lines.push('</div>');
    lines.push('</div>');
    lines.push('');
  }
  lines.push('<!-- 此文件由 scripts/article_covers.mjs 自动更新，也可手动编辑 -->');
  lines.push('');
  await mkdir(WEBSITE_DIR, { recursive: true });
  await writeFile(CATALOG, lines.join('\n'), 'utf8');
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const mode = args.mode || 'all';
  const size = args.size || '1536x1024';
  const endpoint = args['rest-endpoint'] || process.env.AZURE_OPENAI_IMAGE_REST_ENDPOINT || DEFAULT_REST_ENDPOINT;
  const apiVersion = args['api-version'] || process.env.AZURE_OPENAI_API_VERSION || DEFAULT_API_VERSION;
  const timeoutMs = Number(args['timeout-ms'] || 300000);
  const force = Boolean(args.force);
  const articles = await listArticles();

  if (mode === 'generate' || mode === 'all') {
    const apiKey = process.env.AZURE_OPENAI_API_KEY || await promptHidden('Azure OpenAI API key: ');
    if (!apiKey) throw new Error('Missing API key.');
    for (const [index, article] of articles.entries()) {
      const coverPath = join(ARTICLES_DIR, article.dir, 'images', 'cover.png');
      const promptPath = join(ARTICLES_DIR, article.dir, 'prompts', 'cover.txt');
      const prompt = coverPrompt(article, article.dir);
      await mkdir(dirname(promptPath), { recursive: true });
      await writeFile(promptPath, prompt, 'utf8');
      if (!force && existsSync(coverPath)) {
        console.log(`[${index + 1}/${articles.length}] skip ${article.dir}`);
        continue;
      }
      console.log(`[${index + 1}/${articles.length}] generate ${article.dir}`);
      await generateImage({ apiKey, prompt, output: coverPath, size, endpoint, apiVersion, timeoutMs });
    }
  }

  if (mode === 'markdown' || mode === 'all') {
    for (const article of articles) {
      const fresh = await readFile(article.mdPath, 'utf8');
      await writeFile(article.mdPath, ensureArticleCover(fresh, article), 'utf8');
    }
    await updateCatalog(articles);
  }
}

main().catch((err) => {
  console.error(err.stack || err.message);
  process.exit(1);
});
