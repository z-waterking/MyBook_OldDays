# 网站维护日志

> 记录《旧日之书》网站层面的重大维护。凡影响站点结构、导航入口、目录生成、榜单统计、文章归档流程、AI 改稿入口或部署入口的大改动，都应在这里追加一条 Log。

## 记录规范

- 新记录放在最上方，按时间倒序排列。
- 每条记录建议包含：日期、类型、涉及范围、改动摘要、验证方式、关联提交。
- 小的错别字、单篇短评微调、普通文案润色可以不记；会影响读者入口、统计数字或维护流程的改动必须记。

---

## 2026-07-09 · 补齐 AI 改稿说明与图片索引规则

- **类型：** AI 改稿流程 / 图片资产管理 / 网站索引
- **关联提交：** 待提交

### 涉及范围

- `ai-edited-articles/**/notes.md`：补齐每篇改稿的 `本版实际改动`。
- `assets/images/`：新增跨文章共享图片库说明。
- `website/image-index.md`：新增全库图片索引。
- `scripts/update_ai_edit_notes.mjs` / `scripts/generate_image_index.mjs`：新增维护脚本。
- `AGENTS.md` / `README.md` / `ai-edited-articles/AI_EDITING_GUIDE.md` / `website/README.md` / `website/_sidebar.md`：同步协作规则与入口。

### 改动摘要

- 每篇 AI 改稿说明新增 `## 本版实际改动`，记录本版相对原文做了哪些清理、扩写、路径调整和结构处理。
- 建立 `assets/images/` 作为跨文章复用图片库；原文图片仍留在各自 `articles/<文章目录>/images/` 中，不为了复用而移动。
- 新增 `website/image-index.md`，集中列出原文图片和共享图片的预览、来源、类型、大小和引用路径。
- 新增维护命令：`node scripts/update_ai_edit_notes.mjs` 和 `node scripts/generate_image_index.mjs`。

### 验证

- `node scripts/update_ai_edit_notes.mjs`
- `node scripts/generate_image_index.mjs`
- `git diff --check`
- `python -m unittest discover -s tests`

---

## 2026-07-09 · 修复 GitHub Pages 根地址反复刷新

- **类型：** 部署入口修复 / 路由兼容
- **关联提交：** 待提交

### 涉及范围

- 根目录 `index.html`：改为 Docsify 正式入口。
- `website/index.html`：改为旧 `/website/` 地址的兼容跳回页。
- `README.md` / `AGENTS.md` / `website/README.md`：同步站点入口说明。

### 改动摘要

- 移除根目录 `index.html` 的 `meta refresh` 0 秒跳转，避免根地址和 `website/` 入口在 Docsify hash 路由下反复刷新。
- 将完整 Docsify 配置放回根目录 `index.html`，继续加载 `website/catalog.md`、`website/_sidebar.md` 等网站内容。
- `website/index.html` 只做单向跳回根入口，并保留当前 hash，兼容旧链接。

### 验证

- 本地静态服务访问根入口不再发生跳转循环。
- `/website/` 旧入口会跳回根入口并保留 hash。

---

## 2026-07-09 · 站点结构整理、丧尸指南入库与 AI 改稿工作区

- **类型：** 结构整理 / 内容更新 / 工作流完善
- **关联提交：** `64a1f54` · `chore: update archive site workflow and content`

### 涉及范围

- `website/`：集中 Docsify 入口、侧边栏、目录、评分榜、佳句榜、趣味榜单和网站说明。
- `articles/散篇-18-丧尸躲避指南/`：新增文章正文、图片、封面和评价。
- `ai-edited-articles/`：建立 AI 改稿工作区、映射表、协作指南，并补齐批量初稿。
- `scripts/`：更新文章保存、目录生成、封面插入和 AI 改稿草稿生成相关脚本。
- `AGENTS.md` / `CLAUDE.md`：统一 agent 协作规则，避免多份指南分叉。

### 改动摘要

- 将网站展示页从仓库根目录收敛到 `website/`，根目录 `index.html` 只保留跳转入口。
- 新增《丧尸暴发后，普通人该如何躲避》，补充 `review.md`、评分排名、佳句榜和趣味榜单条目。
- 为全部文章建立 AI 改稿工作区结构，新增 `AI_EDITING_GUIDE.md`、`mapping.md` 和批量初稿生成脚本。
- 更新 `article_covers.mjs` 与 `save_article.py`，让目录页使用 `website/catalog.md`，并自动识别 AI 改稿入口。
- 将 `AGENTS.md` 扩展为唯一详版协作指南，`CLAUDE.md` 收敛为兼容入口。

### 验证

- `git diff --check`
- `python -m unittest discover -s tests`
- 推送到 `origin/main` 成功：`6fead80..64a1f54`
