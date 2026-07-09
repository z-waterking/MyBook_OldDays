# 旧日之书 Agent 指南

本文件是仓库的唯一详版协作指南。`CLAUDE.md` 只保留为兼容入口，具体规则以本文件为准。

## 仓库定位

这是一个微信公众号文章归档、文章评价、网页展示和成书整理仓库。维护时要区分四类内容：原文档案、AI 改稿、成书工作区、网站展示层。

## 目录结构与职责

- `articles/`：原始文章归档。每篇文章一个目录，通常包含 `index.md`、`images/`、`prompts/` 和若干 `review*.md`。正文原文尽量只追加和归档，不直接改写。
- `ai-edited-articles/`：AI 修改稿工作区。改稿不能覆盖 `articles/` 原文，目录关系记录在 `ai-edited-articles/mapping.md`。
- `book/`：成书工作区。可用于重排、删选、补写和分卷规划，但不替代原文归档。
- `website/`：Docsify 展示层内容目录。目录页、评分榜、佳句榜、趣味榜单等网页 Markdown 都放这里。
- `scripts/`：维护脚本。当前实际存在 `save_article.py` 和 `article_covers.mjs`。
- `tests/`：Python 单元测试，主要覆盖文章抓取、Markdown 转换和目录生成逻辑。
- 根目录 `index.html`：GitHub Pages / Docsify 正式入口。

## 关键路径约定

- 网站页面统一放在 `website/`，不要再把 `catalog.md`、`ranking.md`、`literary-gems.md`、`fun-rankings.md` 散放到根目录。
- `website/index.html` 只是旧 `/website/` 地址的兼容跳回页，正式入口不要放到 `website/` 下。
- 网站页里的文章链接按仓库根路径写，例如 `articles/合集-01-我在河津上幼儿园/index.md`。
- `website/catalog.md` 是自动生成目录，可由 `save_article.py` 或 `article_covers.mjs` 更新。
- `website/ranking.md`、`website/literary-gems.md`、`website/fun-rankings.md` 是人工整理榜单，新增文章后必须手动复评并同步。
- `website/maintenance-log.md` 是网站维护日志。凡影响网站结构、导航入口、目录生成、榜单统计、文章归档流程、AI 改稿入口或部署入口的大改动，都要追加一条 Log。
- 文章目录命名遵循 `合集-01-标题` 或 `散篇-01-标题`。新增文章不要随意改变已有编号体系。

## 常用命令

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

运行测试：

```bash
python -m unittest discover -s tests
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
11. 运行 `python -m unittest discover -s tests`。若只改了 Markdown，也至少检查相关链接、条目数和页面统计是否一致。
12. 最后询问用户是否需要 git commit；不要主动提交，除非用户明确要求。

## 文章评价规则

- 优先读正文，再看已有 `review*.md`。复评时通常以最新版本为参考，常见顺序是 `review_v4.md`、`review_v3.md`、`review_v2.md`、`review.md`。
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
- 榜单链接应指向实际存在的 `articles/.../index.md` 或 `review*.md`。
- 若榜单、站点导航、目录生成规则或文章入口发生大改动，同步更新 `website/maintenance-log.md`。

## AI 修改稿流程

- 接手 AI 改稿前必须先读 `ai-edited-articles/AI_EDITING_GUIDE.md`。
- 改稿只放在 `ai-edited-articles/合集/<文章目录>/` 或 `ai-edited-articles/散篇/<文章目录>/`。
- 每篇改稿至少包含 `index.md` 和 `notes.md`。
- 目录名必须与 `articles/` 中对应文章一致，并在 `ai-edited-articles/mapping.md` 中保持可追踪。
- `index.md` 放完整可读正文，不要只放建议。
- `notes.md` 记录改稿目标、主要改动、保留意见和下一轮建议。
- 改稿目标是向 `10/10` 靠近，但要保留作者原有语气：具体、嘴贫、自嘲、偶尔突然伤感，不要改成标准作文腔。
- 新增或补齐改稿后运行 `node scripts/article_covers.mjs --mode markdown`，让 `website/catalog.md` 自动出现 `AI改稿` 入口。
- 批量补齐缺失初稿可运行 `node scripts/generate_ai_edit_drafts.mjs`。该脚本默认只创建缺失稿件，不覆盖已有 `index.md`。
- 若需要刷新脚本生成的 v1 初稿，运行 `node scripts/generate_ai_edit_drafts.mjs --refresh-generated`；这会跳过不带 `edit_round: "v1"` 的手工精修稿。
- `--force` 会覆盖已有改稿，只能在用户明确要求或确认无手工稿价值时使用。

## 脚本说明

- `scripts/save_article.py` 负责抓取微信公众号文章、下载图片、转换 Markdown、生成 `website/catalog.md`。
- `scripts/article_covers.mjs --mode markdown` 会给每篇文章插入或刷新封面 `<img class="article-cover">` 块，并重建 `website/catalog.md`。
- `scripts/article_covers.mjs --mode generate` 会调用 Azure OpenAI 图片接口生成封面，需要 `AZURE_OPENAI_API_KEY` 或交互输入 API key；不要在日志或回复中暴露密钥。
- 两个脚本都可能改动 `website/catalog.md`，`article_covers.mjs --mode markdown` 还会改动多篇 `articles/*/index.md` 的封面块。

## 脚本失败时的备用方案

如果微信封锁、反爬或文章格式异常导致脚本无法抓取，可以：

1. 用网页抓取工具获取文章 HTML。
2. 手动提取标题、作者、日期、正文和图片。
3. 按现有 `articles/<文章目录>/index.md` 的 frontmatter 和正文格式写入。
4. 图片放入 `articles/<文章目录>/images/`，正文使用相对路径引用。
5. 完成后仍要补 `review.md`、更新三个榜单、重建目录并验证。

## 验证清单

- Python 逻辑改动后运行 `python -m unittest discover -s tests`。
- 目录、封面、AI 改稿入口变化后运行 `node scripts/article_covers.mjs --mode markdown`。
- 榜单改动后检查编号、排名、统计数字和链接目标。
- Markdown 页面链接使用仓库根路径，优先确认目标文件存在。
- 若工作区已有无关改动，不要回退；只说明自己改了什么、验证了什么。

## Git 与交付

- 不主动 `git commit`，除非用户明确要求。
- 不使用 `git reset --hard`、`git checkout --` 等破坏性命令。
- 保存文章或更新榜单后，最终回复应说明新增/修改了哪些文件、跑了哪些验证、是否有需要用户确认的遗留事项。
