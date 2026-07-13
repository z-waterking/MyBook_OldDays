#!/usr/bin/env node

import { readFileSync } from 'node:fs';
import vm from 'node:vm';

const indexUrl = new URL('../index.html', import.meta.url);
const html = readFileSync(indexUrl, 'utf8');
const scriptPattern = /<script\b([^>]*)>([\s\S]*?)<\/script>/gi;
const inlineScripts = [...html.matchAll(scriptPattern)]
  .filter(([, attributes]) => !/\bsrc\s*=/.test(attributes));

if (inlineScripts.length === 0) {
  throw new Error('index.html 中没有找到可检查的内联脚本。');
}

let checked = 0;
for (const [, , source] of inlineScripts) {
  if (!source.trim()) continue;
  checked += 1;
  new vm.Script(source, { filename: `index.html:inline-script-${checked}` });
}

console.log(`index.html 内联脚本语法通过（${checked} 个）`);
