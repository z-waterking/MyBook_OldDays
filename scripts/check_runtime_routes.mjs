#!/usr/bin/env node

import assert from 'node:assert/strict';
import { existsSync, readFileSync, readdirSync } from 'node:fs';
import { join } from 'node:path';

await import('./site_runtime_helpers.js');

const root = process.cwd();
const helpers = globalThis.siteRuntimeHelpers;
assert.ok(helpers, 'siteRuntimeHelpers was not exposed');
const manifest = JSON.parse(readFileSync(join(root, 'book', 'reading-order.json'), 'utf8'));
const chapters = manifest.parts.flatMap((part) => part.chapters);
const articleNames = readdirSync(join(root, 'articles'), { withFileTypes: true })
  .filter((entry) => entry.isDirectory() && existsSync(join(root, 'articles', entry.name, 'index.md')))
  .map((entry) => entry.name);

for (const articleName of articleNames) {
  const category = articleName.startsWith('合集-') ? '合集' : '散篇';
  const cases = [
    [`#/articles/${encodeURI(articleName)}/index.md`, 'original'],
    [`#/articles/${encodeURI(articleName)}/review.md`, 'review'],
    [`#/ai-edited-articles/${encodeURI(category)}/${encodeURI(articleName)}/index.md`, 'edited'],
    [`#/ai-edited-articles/${encodeURI(category)}/${encodeURI(articleName)}/notes.md`, 'notes'],
  ];
  for (const [route, expectedPage] of cases) {
    const context = helpers.articleContextFromHash(route);
    assert.equal(context?.articleName, articleName, `article route mismatch: ${route}`);
    assert.equal(context?.category, category, `article category mismatch: ${route}`);
    assert.equal(context?.page, expectedPage, `article page mismatch: ${route}`);
  }
}

for (const chapter of chapters) {
  assert.ok(chapter.archivePath.startsWith('articles/'), `invalid archivePath: ${chapter.archivePath}`);
  assert.ok(chapter.readingPath.startsWith('ai-edited-articles/'), `invalid readingPath: ${chapter.readingPath}`);
  assert.ok(existsSync(join(root, decodeURI(chapter.archivePath))), `missing archivePath: ${chapter.archivePath}`);
  assert.ok(existsSync(join(root, decodeURI(chapter.readingPath))), `missing readingPath: ${chapter.readingPath}`);
}

assert.equal(helpers.articleContextFromHash('#/website/ranking.md'), null);
assert.equal(helpers.normalizeSiteHash('#/articles/a/index.md?id=section'), '#/articles/a/index');
console.log(`运行时路由契约通过（${articleNames.length} 篇 × 4 类页面，${chapters.length} 篇成书路径）`);
