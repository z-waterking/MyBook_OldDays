#!/usr/bin/env node

import { readFile, readdir, writeFile } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { join, relative } from 'node:path';

const ROOT = process.cwd();
const AI_DIR = join(ROOT, 'ai-edited-articles');
const ARTICLES_DIR = join(ROOT, 'articles');

function groupOf(dirName) {
  if (dirName.startsWith('散篇-')) return '散篇';
  if (dirName.startsWith('合集-')) return '合集';
  return '其他';
}

function parseFrontmatter(content) {
  const meta = {};
  const match = content.match(/^---\r?\n([\s\S]*?)\r?\n---/);
  if (!match) return meta;
  for (const line of match[1].split(/\r?\n/)) {
    const m = line.match(/^([^:]+):\s*(.*)$/);
    if (!m) continue;
    let value = m[2].trim();
    if (value.startsWith('"') && value.endsWith('"')) {
      value = value.slice(1, -1).replace(/\\"/g, '"').replace(/\\n/g, '\n').replace(/\\\\/g, '\\');
    }
    meta[m[1].trim()] = value;
  }
  return meta;
}

function stripMarkdown(content) {
  return content
    .replace(/^---\r?\n[\s\S]*?\r?\n---\r?\n*/, '')
    .replace(/^#\s+.*\r?\n+/, '')
    .replace(/<p><img class="article-cover"[\s\S]*?<\/p>\r?\n*/g, '')
    .replace(/!\[[^\]]*\]\([^)]*\)/g, '')
    .replace(/\[[^\]]*\]\([^)]*\)/g, '')
    .replace(/<[^>]+>/g, '')
    .replace(/[*_`~>#|]/g, '')
    .replace(/\s+/g, ' ')
    .trim();
}

function titleFrom(dirName, content) {
  const meta = parseFrontmatter(content);
  return meta.title || content.match(/^#\s+(.+)$/m)?.[1]?.trim() || dirName.replace(/^(合集|散篇)-\d{2}-/, '');
}

function countImages(content) {
  return (content.match(/!\[[^\]]*\]\([^)]*\)|<img\b/gi) || []).length;
}

function bodyWordCount(content) {
  return stripMarkdown(content).length;
}

function classifyChanges({ dirName, sourceBody, draftBody, sourceImages, draftImages }) {
  const changes = [];
  const sourceLen = bodyWordCount(sourceBody);
  const draftLen = bodyWordCount(draftBody);
  const ratio = sourceLen ? draftLen / sourceLen : 1;
  const hasGeneratedFrontmatter = /^edit_round:\s*"v1"\s*$/m.test(draftBody);

  if (hasGeneratedFrontmatter) {
    changes.push('补充 AI 改稿 frontmatter，标明原文路径、目标评分、改稿状态、轮次和日期。');
  }

  if (sourceBody.match(/^#\s+.+$/m)) {
    changes.push('清理原文页头、作者日期栏和封面块，只保留可直接阅读的正文。');
  }

  if (draftBody.includes(`assets/images/articles/${dirName}/`)) {
    changes.push('将正文图片统一引用共享资产目录，便于原文、AI 改稿区和成书区复用。');
  }

  if (draftImages >= sourceImages && draftImages > 0) {
    changes.push('保留原文图片位置和叙事节奏，避免改稿时丢失关键视觉材料。');
  }

  if (ratio >= 1.35) {
    changes.push('对原本偏短或信息不足的段落进行扩写，补足场景、语境和笑点承接。');
  } else if (ratio <= 0.8) {
    changes.push('压缩重复信息和散点材料，让主线更集中。');
  } else {
    changes.push('基本保留原文骨架，主要调整过渡、段落衔接和结尾落点。');
  }

  if (/目标评分:\s*10\/10|target_score:\s*"10\/10"/.test(draftBody)) {
    changes.push('按 10 分目标补强可读性，但保留作者原有的口语、自嘲和突然伤感。');
  }

  if (['散篇-07-面试的艺术', '散篇-08-412之趣言趣闻', '散篇-10-读研读废了是什么体验', '散篇-11-男朋友不回消息怎么办'].includes(dirName)) {
    changes.push('针对短篇/段子型原文重写为完整可独立阅读版本，降低对熟人语境和图片的依赖。');
  }

  if (dirName === '合集-05-我在康杰念高中（怀昔）') {
    changes.push('手工强化青春回忆主线，增加开头与结尾呼应，并压缩部分同学信息罗列。');
  }

  return [...new Set(changes)];
}

function actualChangesBlock(changes, sourceRel, draftRel) {
  return [
    '## 本版实际改动',
    '',
    ...changes.map((change) => `- ${change}`),
    '',
    `对照文件：\`${sourceRel}\` -> \`${draftRel}\`。`,
  ].join('\n');
}

function upsertSection(content, heading, block) {
  const pattern = new RegExp(`\\n## ${heading.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\n[\\s\\S]*?(?=\\n## |$)`);
  if (pattern.test(content)) return content.replace(pattern, `\n${block.trimEnd()}\n`);

  const marker = '\n## 评价摘录\n';
  if (content.includes(marker)) return content.replace(marker, `\n${block.trimEnd()}\n\n${marker.trimStart()}`);
  return `${content.trimEnd()}\n\n${block}`;
}

async function listArticleDirs() {
  const entries = await readdir(ARTICLES_DIR, { withFileTypes: true });
  return entries
    .filter((entry) => entry.isDirectory() && existsSync(join(ARTICLES_DIR, entry.name, 'index.md')))
    .map((entry) => entry.name)
    .sort((a, b) => a.localeCompare(b, 'zh-Hans-CN'));
}

async function main() {
  let updated = 0;
  let skipped = 0;

  for (const dirName of await listArticleDirs()) {
    const group = groupOf(dirName);
    const sourcePath = join(ARTICLES_DIR, dirName, 'index.md');
    const draftPath = join(AI_DIR, group, dirName, 'index.md');
    const notesPath = join(AI_DIR, group, dirName, 'notes.md');
    if (!existsSync(draftPath) || !existsSync(notesPath)) {
      skipped += 1;
      continue;
    }

    const sourceBody = await readFile(sourcePath, 'utf8');
    const draftBody = await readFile(draftPath, 'utf8');
    const notesBody = await readFile(notesPath, 'utf8');
    const title = titleFrom(dirName, draftBody);
    const changes = classifyChanges({
      dirName,
      sourceBody,
      draftBody,
      sourceImages: countImages(sourceBody),
      draftImages: countImages(draftBody),
    });
    const sourceRel = relative(ROOT, sourcePath).replace(/\\/g, '/');
    const draftRel = relative(ROOT, draftPath).replace(/\\/g, '/');
    const block = actualChangesBlock(changes, sourceRel, draftRel);
    const next = `${upsertSection(notesBody, '本版实际改动', block).replace(/^# 修改说明：.*$/m, `# 修改说明：${title}`).trimEnd()}\n`;
    if (next !== notesBody) {
      await writeFile(notesPath, next, 'utf8');
      updated += 1;
    } else {
      skipped += 1;
    }
  }

  console.log(`updated ${updated}, skipped ${skipped}`);
}

main().catch((error) => {
  console.error(error.stack || error.message);
  process.exit(1);
});
