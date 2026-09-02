# 旧日之书 Agent 指南

本文件是仓库的唯一详版协作指南。`CLAUDE.md` 只保留为兼容入口，具体规则以本文件为准。

## 仓库定位

这是一个微信公众号文章归档、文章评价、网页展示和成书整理仓库。维护时要区分四类内容：原文档案、AI 改稿、成书工作区、网站展示层。

## 目录结构与职责

- `articles/`：原始文章归档。每篇文章一个目录，通常包含 `index.md`、`prompts/` 和唯一的规范评价文件 `review.md`。正文原文尽量只追加和归档，不直接改写。
- `assets/images/articles/`：文章图片统一存储区，按文章目录分组；原文和 AI 改稿引用同一份文件。
- `assets/images/`：除文章图片外的跨文章、成书区共用图片库。
- `ai-edited-articles/`：AI 修改稿工作区。改稿不能覆盖 `articles/` 原文，目录关系记录在 `ai-edited-articles/mapping.md`。
- `fan-submissions/`：粉丝投稿公开归档。每篇包含公众号正式稿 `index.md`、专栏评价 `review.md` 和编辑说明 `notes.md`；不混入作者个人文章、榜单或成书时间线。
- `book/`：成书工作区。维护七部时间主线、附录、补写计划、题目库和生成书稿，但不替代原文归档。
- `website/`：Docsify 展示层内容目录。目录页、评分榜、佳句榜、趣味榜单等网页 Markdown 都放这里。
- `scripts/`：文章抓取、封面、图片索引、插画和网站巡检脚本。
- 根目录 `index.html`：GitHub Pages / Docsify 正式入口。

## 关键路径约定

- 网站页面统一放在 `website/`，不要再把 `catalog.md`、`ranking.md`、`literary-gems.md`、`fun-rankings.md` 散放到根目录。
- `website/submissions.md` 是粉丝投稿专栏页，按连续编号手工维护；投稿正文与图片分别链接到 `fan-submissions/` 和 `assets/images/fan-submissions/`。
- `website/index.html` 只是旧 `/website/` 地址的兼容跳回页，正式入口不要放到 `website/` 下。
- 网站页里的文章链接按仓库根路径写，例如 `articles/合集-01-我在河津上幼儿园/index.md`。
- `website/catalog.md` 是自动生成目录，唯一渲染实现位于 `save_article.py`。完整发布以 `article_covers.mjs --mode markdown` 为准，该命令刷新图片后委托 Python 重建目录；`save_article.py --catalog-only` 只用于不刷新图片的快速重建。
- `website/ranking.md`、`website/literary-gems.md`、`website/fun-rankings.md` 是人工整理榜单，新增文章后必须手动复评并同步。
- `website/image-index.md` 是图片索引，由 `scripts/generate_image_index.mjs` 生成，记录文章图片和其他共享图片的引用路径。
- `website/maintenance-log.md` 是网站维护日志。凡影响网站结构、导航入口、目录生成、榜单统计、文章归档流程、AI 改稿入口或部署入口的大改动，都要追加一条 Log。
- `website/MAINTENANCE.md` 是网站生成、验证、发布、降级和回滚的权威操作手册。
- `book/reading-order.json` 是成书选篇、分部和阅读顺序的唯一结构化来源；公开目录、分部页、网站章节导航和生成书稿必须与其一致。
- `book/manuscript.md` 由 `scripts/build_book_manuscript.py` 生成，不做无法复现的手工修改。
- 文章目录命名遵循 `合集-01-标题` 或 `散篇-01-标题`。新增文章不要随意改变已有编号体系。

## 常用命令

工具链基线：Python 3.12+、Node.js 20 LTS；文本统一使用 UTF-8 与 LF，具体见 `.python-version`、`.nvmrc` 和 `.editorconfig`。

安装依赖：

```bash
python -m pip install -r requirements.txt
```

保存微信公众号文章：

```bash
python scripts/save_article.py URL1 [URL2 ...]
```

从文件批量保存：

```bash
python scripts/save_article.py -f urls.txt
```

强制覆盖已保存文章：

```bash
python scripts/save_article.py --force URL
```

仅重建网站目录：

```bash
python scripts/save_article.py --catalog-only
```

插入/刷新文章封面块并重建目录：

```bash
node scripts/article_covers.mjs --mode markdown
```

该命令会先运行 `scripts/generate_cover_thumbnails.py`，刷新目录缩略图和首页派生图片。

重建图片索引：

```bash
node scripts/generate_image_index.mjs
```

生成并检查当前连续书稿：

```bash
python scripts/build_book_manuscript.py
python scripts/build_book_manuscript.py --check
```

检查 Python 脚本语法：

```bash
python -m py_compile scripts/save_article.py scripts/check_site.py scripts/build_book_manuscript.py scripts/generate_cover_thumbnails.py scripts/prepare_site_illustrations.py
```

检查 Node.js 脚本语法：

```bash
node --check scripts/article_covers.mjs
node --check scripts/check_inline_scripts.mjs
node --check scripts/generate_ai_edit_drafts.mjs
node --check scripts/generate_image_index.mjs
node --check scripts/update_ai_edit_notes.mjs
node scripts/check_inline_scripts.mjs
```

检查网站完整性：

```bash
python scripts/check_site.py
```

## 新增文章完整流程

当用户提供微信公众号文章链接时，按下面闭环处理，不要只保存正文就结束。

1. 运行 `python scripts/save_article.py URL1 [URL2 ...]`。
2. 保存后向用户报告标题、作者、日期、图片数、保存路径，以及是否跳过或失败。
3. 若保存成功，阅读新文章 `articles/<文章目录>/index.md`，给出文章评价并创建或更新 `review.md`。
4. `review.md` 建议包含：总体印象、亮点分析、写作建议、金句摘录、综合评分、综合评价。
5. 评分使用 10 分制，可保留一位小数；评价要能解释该分数在全库中的相对位置。
6. 从文章中摘录 3-8 条金句。摘录应优先选择有文学性、记忆点、思想含量或人物/场景代表性的句子。
7. 更新 `website/ranking.md`：把新文章按综合评分插入总排名，更新文章总数、评分分布、平均分、最高/最低分等统计。
8. 更新 `website/literary-gems.md`：判断新金句是否进入佳句榜；若进入，补条目、点评、来源链接和底部总数。
9. 更新 `website/fun-rankings.md`：检查新文章是否影响美食榜、名场面榜、催泪榜、足迹榜、人物榜、文体榜、游戏榜、职业经历、预案榜、AI 焦虑榜、受伤榜、金句密度榜等。
10. 运行 `node scripts/article_covers.mjs --mode markdown`，让目录页和封面块保持最新。
11. 运行 `python scripts/check_site.py`，并检查相关链接、条目数和页面统计是否一致。
12. 最后询问用户是否需要 git commit；不要主动提交，除非用户明确要求。

## 文章评价规则

- 优先读正文，再看唯一的规范评价文件 `review.md`；复评时直接更新该文件，不创建其他评价版本文件。
- 评价要具体到文章的结构、场景、人物、语言、情感和主题，不要只写泛泛夸奖。
- 对回忆录，要关注时间线、场景密度、人物是否立住、结尾是否有回响。
- 对小说或虚构短篇，要关注人物动机、冲突推进、语体稳定和结尾力度。
- 对随笔、职场文、评论文，要关注核心问题是否清楚，材料是否服务主题。
- 金句摘录不是简单摘漂亮话，要说明句子为什么成立：意象、情绪、转折、节奏、哲思或叙事功能。

## 榜单维护规则

- `website/ranking.md` 是评分总榜。新增或复评文章后，要同步排名、分布和统计，不要只改表格单行。
- `website/literary-gems.md` 是佳句榜。只收真正能代表全书语言质量的句子；宁可少收，不要把普通总结句都放进去。
- `website/fun-rankings.md` 是人工趣味索引。新增文章若带来新城市、人物、食物、游戏、职业、受伤、名场面、预案或文体类型，要同步相关榜单。
- 修改榜单后检查底部“共 N 篇/共 N 句”等数字是否与正文一致。
- 榜单链接应指向实际存在的 `articles/.../index.md` 或 `articles/.../review.md`。
- 若榜单、站点导航、目录生成规则或文章入口发生大改动，同步更新 `website/maintenance-log.md`。

## AI 修改稿流程

- 接手 AI 改稿前必须先读 `ai-edited-articles/AI_EDITING_GUIDE.md`。
- 改稿只放在 `ai-edited-articles/合集/<文章目录>/` 或 `ai-edited-articles/散篇/<文章目录>/`。
- 每篇改稿至少包含 `index.md` 和 `notes.md`。
- 目录名必须与 `articles/` 中对应文章一致，并在 `ai-edited-articles/mapping.md` 中保持可追踪。
- `index.md` 放完整可读正文，不要只放建议。
- `index.md` 永远是唯一当前版本；历史版本使用 Git 保存，不创建 `index_v*.md` 平行入口。
- `notes.md` 记录改稿目标、主要改动、保留意见和下一轮建议，并必须包含 `## 本版实际改动`，写清本版到底改了哪些地方。
- 改稿目标是向 `10/10` 靠近，但要保留作者原有语气：具体、嘴贫、自嘲、偶尔突然伤感，不要改成标准作文腔。
- 新增或补齐改稿后运行 `node scripts/article_covers.mjs --mode markdown`，让 `website/catalog.md` 自动出现 `AI改稿` 入口。
- 批量补齐缺失初稿可运行 `node scripts/generate_ai_edit_drafts.mjs`。该脚本默认只创建缺失稿件，不覆盖已有 `index.md`。
- 批量补齐或刷新改稿说明可运行 `node scripts/update_ai_edit_notes.mjs`，该脚本会给每篇 `notes.md` 补齐 `## 本版实际改动`。
- 若需要刷新脚本生成的 v1 初稿，运行 `node scripts/generate_ai_edit_drafts.mjs --refresh-generated`；这会跳过不带 `edit_round: "v1"` 的手工精修稿。
- `--force` 会覆盖已有改稿，只能在用户明确要求或确认无手工稿价值时使用。

## 脚本说明

- `scripts/save_article.py` 负责抓取微信公众号文章、下载图片、转换 Markdown，并作为 `website/catalog.md` 的唯一渲染器。
- `scripts/article_covers.mjs --mode markdown` 会刷新轻量封面缩略图、给每篇文章插入或刷新封面 `<img class="article-cover">` 块，再调用 `save_article.py --catalog-only` 重建目录。
- `scripts/article_covers.mjs --mode generate` 会调用 Azure OpenAI 图片接口生成封面，需要 `AZURE_OPENAI_API_KEY` 或交互输入 API key；不要在日志或回复中暴露密钥。
- `scripts/generate_cover_thumbnails.py` 会从文章原始封面生成目录与正文 WebP、首页主视觉和 favicon；依赖 Pillow。
- `scripts/check_inline_scripts.mjs` 会解析根目录 `index.html` 中无 `src` 的脚本块，防止首页交互代码出现未被 CI 捕获的语法错误。
- `scripts/generate_image_index.mjs` 会扫描 `assets/images/articles/` 和其他 `assets/images/` 子目录，生成 `website/image-index.md`。
- `scripts/build_book_manuscript.py` 按 `book/reading-order.json` 从当前 AI 修改稿或原始档案稿生成连续书稿；默认输出为 `book/manuscript.md`。
- `scripts/update_ai_edit_notes.mjs` 会根据原文和 AI 改稿生成每篇 `notes.md` 的实际改动清单。
- `scripts/generate_site_illustrations.ps1` 按 `scripts/illustration_manifest.json` 调用全局 Azure GPT Image skill，生成佳句榜和趣味榜缺失插画；默认跳过已有文件。
- `scripts/prepare_site_illustrations.py` 将插画原图转为 960×640 WebP，并按清单把图片块注入 `website/literary-gems.md` 和 `website/fun-rankings.md`。
- `scripts/check_site.py` 检查唯一评价与六节结构、评分榜统计、文章/目录/AI 改稿映射、成书阅读顺序、本地链接、足迹数据和插画资产之间的一致性。
- `save_article.py` 和 `article_covers.mjs` 都可能触发 `website/catalog.md` 更新，但目录 HTML 只由前者渲染；后者在 `--mode markdown` 下还会改动多篇 `articles/*/index.md` 的封面块。

## 图片索引与复用规则

- 文章图片放在 `assets/images/articles/<文章目录>/`，目录名与 `articles/` 保持一致，文件默认不改名。
- 其他跨文章或成书区共用图片放在 `assets/images/<主题>/`。
- 所有 Markdown 使用仓库根路径，例如 `assets/images/articles/<文章目录>/001.jpg` 或 `assets/images/<主题>/name.png`。
- 新增、复制、移动图片后运行 `node scripts/generate_image_index.mjs`，并检查 `website/image-index.md`。
- AI 改稿直接引用 `assets/images/articles/<文章目录>/` 中的文章图片，不要把图片复制进 `ai-edited-articles/`。

## 脚本失败时的备用方案

如果微信封锁、反爬或文章格式异常导致脚本无法抓取，可以：

1. 用网页抓取工具获取文章 HTML。
2. 手动提取标题、作者、日期、正文和图片。
3. 按现有 `articles/<文章目录>/index.md` 的 frontmatter 和正文格式写入。
4. 文章图片放入 `assets/images/articles/<文章目录>/`；其他跨文章图片放入 `assets/images/<主题>/`；正文使用仓库根路径引用。
5. 完成后仍要补 `review.md`、更新三个榜单、重建目录并验证。

## 验证清单

- 网站或内容改动后运行 `python scripts/check_site.py`。
- Python 逻辑改动后检查全部 `scripts/*.py` 语法，并执行对应命令做行为验证。
- Node.js 逻辑改动后对全部 `scripts/*.mjs` 运行 `node --check`，并执行对应命令做行为验证。
- 目录、封面、AI 改稿入口变化后运行 `node scripts/article_covers.mjs --mode markdown`。
- 成书选篇、顺序、分部导言或入选 AI 改稿变化后运行 `python scripts/build_book_manuscript.py`，再运行 `python scripts/build_book_manuscript.py --check`。
- 图片新增、复制或路径规则变化后运行 `node scripts/generate_image_index.mjs`。
- 榜单改动后检查编号、排名、统计数字和链接目标。
- Markdown 页面链接使用仓库根路径，优先确认目标文件存在。
- 若工作区已有无关改动，不要回退；只说明自己改了什么、验证了什么。

## Git 与交付

- 不提交 API key、token、`.env` 或其他本地凭据；示例配置只能使用 `.env.example` 且不得包含真实值。
- 生成文件必须由权威脚本重建，不在生成结果里做无法复现的长期手工修改。
- 不主动 `git commit`，除非用户明确要求。
- 不使用 `git reset --hard`、`git checkout --` 等破坏性命令。
- 保存文章或更新榜单后，最终回复应说明新增/修改了哪些文件、跑了哪些验证、是否有需要用户确认的遗留事项。
