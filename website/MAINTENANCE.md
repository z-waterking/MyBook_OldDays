# 网站维护手册

本手册是《旧日之书》网站层的权威维护入口。协作规范仍以根目录 `AGENTS.md` 为准；这里专门说明网站由什么组成、改动后运行什么命令、如何发布和排障。

## 一、维护边界

### 人工维护的源文件

- `website/home.md`：首页导览与推荐入口。
- `website/_sidebar.md`：全站主导航和文章导航。
- `website/ranking.md`：评分总榜及统计。
- `website/literary-gems.md`：佳句选读；插画块由脚本维护，文字与排序人工复核。
- `website/fun-rankings.md`：趣味榜单；插画块由脚本维护，榜单内容人工复核。
- `website/footprints.md`：足迹页结构和静态降级索引。
- `website/footprints-data.json`：足迹坐标、类型、故事和来源文章的唯一数据源。
- `book/reading-order.json`：成书选篇、分部和阅读顺序的唯一结构化数据源。
- `book/01-成书目录.md`、`book/部*.md`、`book/附录-别调与想象.md`：面向读者的成书目录与分部页。
- `index.html`：Docsify 配置、全站样式和交互插件。
- `website/maintenance-log.md`：影响读者入口、统计、生成流程或部署的变更记录。

### 脚本生成的文件

- `website/catalog.md`：文章目录。
- `website/image-index.md`：图片索引。
- `book/manuscript.md`：按阅读清单与当前 AI 修改稿拼合的连续工作书稿。
- `assets/images/_generated/catalog-covers/`：目录封面 WebP。
- `assets/images/_generated/illustrations/`：榜单插画 WebP。
- `assets/images/_generated/home-hero.webp` 和 `favicon.png`：首页主视觉与站点图标。

生成文件可以查看和提交，但不要把手工修改当成长期方案；应改源数据或生成脚本后重新生成。

## 二、命令速查

工具链基线为 Python 3.12+ 与 Node.js 20 LTS，分别记录在 `.python-version` 和 `.nvmrc`；文本编码与换行规则见 `.editorconfig`。
Python 依赖在 `requirements.txt` 中限定兼容主版本：日常安装获取兼容范围内的新修复，跨主版本升级必须单独验证后调整上限。

安装依赖：

```bash
python -m pip install -r requirements.txt
```

本地预览：

```bash
python -m http.server 4173
```

浏览器打开 `http://127.0.0.1:4173/`。不要直接双击 `index.html`，否则 Docsify 的 Markdown 请求和地图数据请求可能被浏览器拦截。

完整网站巡检：

```bash
python scripts/check_site.py
```

该命令检查：

- 每篇文章都有唯一的 `review.md`、六个规定章节和一个有效综合评分。
- 评分榜顺序、分类、分布和汇总统计与全部 `review.md` 一致。
- `website/catalog.md` 条目集合与文章集合一致，并带有规范生成声明。
- AI 改稿、`source_article`、`notes.md` 和 `mapping.md` 与原文一一对应。
- `website/*.md` 中的本地页面、图片和 Docsify 路由目标存在。
- `book/*.md` 本地链接有效，成书目录、八个分部页面与 `reading-order.json` 的章节集合和顺序一致。
- 足迹 JSON 结构、坐标范围、来源链接和路线有效。
- 插画清单、页面插画块、JPEG 原图和 WebP 派生图一一对应，并通过尺寸与像素差异检查确认派生图已同步。

同一检查由 `.github/workflows/site-check.yml` 在推送到 `main` 和 Pull Request 时自动执行。CI 还会检查全部 Python/Node.js 脚本语法，重建目录、图片索引和连续书稿，并要求生成结果无差异。新增约束时应优先扩展 `scripts/check_site.py`，让本地与 CI 使用同一套规则。

## 三、按改动类型维护

| 改动 | 必做维护 | 最低验证 |
| --- | --- | --- |
| 新增文章 | 补 `review.md`，复评三个榜单，刷新封面与目录 | `article_covers.mjs` + `check_site.py` |
| 修改评价或评分 | 同步评分榜、佳句榜和受影响的趣味榜 | `check_site.py` + 人工核对统计 |
| 新增或修改文章图片 | 更新共享图片路径，重建图片索引 | `generate_image_index.mjs` + `check_site.py` |
| 新增 AI 改稿 | 更新映射与说明，刷新目录中的 AI 改稿入口 | `article_covers.mjs` + `check_site.py` |
| 修改成书选篇、分部或顺序 | 同步阅读清单、公开目录和分部页，重建书稿 | `build_book_manuscript.py` + `check_site.py` |
| 修改首页、侧栏或 Docsify | 更新维护日志 | 六类页面浏览器冒烟检查 |
| 修改足迹 | 同步 JSON 与静态地点索引 | `check_site.py` + 地图双视图检查 |
| 修改佳句/趣味插画 | 更新 manifest，生成原图并准备 WebP | `prepare_site_illustrations.py` + `check_site.py` |

### 目录与封面

完整发布流程以 Node 命令为准：

```bash
node scripts/article_covers.mjs --mode markdown
```

它会刷新目录缩略图、首页派生图片和文章封面块，再调用 Python 的唯一目录渲染器更新 `website/catalog.md`。只有在明确不需要刷新图片和文章封面块时，才使用快速目录重建：

```bash
python scripts/save_article.py --catalog-only
```

### 图片索引

```bash
node scripts/generate_image_index.mjs
```

文章图片只存放在 `assets/images/articles/<文章目录>/`；AI 改稿直接引用同一份图片，不复制副本。

### 成书阅读与连续书稿

`book/reading-order.json` 控制七部、附录及全部入选章节的顺序。调整它时，必须同步检查 `book/01-成书目录.md`、对应分部页和网站侧栏；`scripts/check_site.py` 会核对这些入口是否一致。

从当前 AI 修改稿重建连续书稿并检查生成结果：

```bash
python scripts/build_book_manuscript.py
python scripts/build_book_manuscript.py --check
```

默认生成 `book/manuscript.md`。该文件只作为可重复构建的工作书稿，不直接手改，也不代替尚待作者补写的研究生阶段和全书收束。需要对照原文时，可用 `--source original --output <路径>` 生成单独文件。

### 佳句与趣味榜插画

```powershell
./scripts/generate_site_illustrations.ps1 -TimeoutSec 600
python scripts/prepare_site_illustrations.py
```

重做单张时使用 `-Id <条目ID> -Force`。不要直接修改 `_generated` 下的 WebP；先替换 JPEG 原图，再运行准备脚本。

## 四、新增文章发布闭环

1. 保存文章并确认标题、作者、日期、图片和目录名。
2. 阅读原文，创建唯一的 `articles/<文章目录>/review.md`。
3. 把评分插入 `website/ranking.md`，重算篇数、均分和分布。
4. 判断金句是否进入 `website/literary-gems.md`。
5. 检查人物、地点、食物、职业、考试等是否影响 `website/fun-rankings.md`。
6. 若出现新地点，更新 `website/footprints-data.json` 和 `website/footprints.md` 的静态地点索引。
7. 运行 `node scripts/article_covers.mjs --mode markdown`。
8. 若新增图片，运行 `node scripts/generate_image_index.mjs`。
9. 运行 `python scripts/check_site.py`。
10. 本地浏览核心页面，更新 `website/maintenance-log.md`，再提交推送。

## 五、发布前检查

### 自动检查

```bash
python -m py_compile scripts/save_article.py scripts/check_site.py scripts/build_book_manuscript.py scripts/generate_cover_thumbnails.py scripts/prepare_site_illustrations.py
node --check scripts/article_covers.mjs
node --check scripts/generate_ai_edit_drafts.mjs
node --check scripts/generate_image_index.mjs
node --check scripts/update_ai_edit_notes.mjs
python scripts/save_article.py --catalog-only
node scripts/generate_image_index.mjs
git diff --exit-code -- website/catalog.md website/image-index.md
python scripts/build_book_manuscript.py
python scripts/build_book_manuscript.py --check
git diff --exit-code -- book/manuscript.md
python scripts/check_site.py
git diff --check
```

### 浏览器冒烟检查

桌面和约 390px 移动宽度各检查一次：

1. 首页：主视觉、三个主操作、七部人生路径、地图专题和四篇入口。
2. 全部文章：目录、封面、评价与 AI 改稿入口。
3. 成书阅读：目录、七部与附录入口、章节进度、上一篇与下一篇跨部衔接。
4. 佳句选读：章节导航、插画和来源链接。
5. 趣味索引：全部榜单、章节导航和表格移动端宽度。
6. 足迹地图：中国/世界切换、筛选、标记弹窗、来源文章和静态索引。

同时用键盘 Tab 检查“跳到正文”、侧栏、表单控件与回到顶部的焦点是否可见，页面不应出现横向滚动。

## 六、故障降级

- **Leaflet 或地图底图失败：** 地点档案应先于地图出现并保持可读；页面显示明确提示。若连地点 JSON 也失败，静态地点索引应自动展开。
- **Docsify CDN 失败：** 这是全站级外部依赖。先确认 jsDelivr 状态和网络，再考虑锁定本地副本；不要把地图问题误判为 Docsify 问题。
- **微信抓取失败：** 按 `AGENTS.md` 的备用流程手动归档，仍需补评价、榜单、目录与验证。
- **生成图片失败：** 保留已有原图，不使用 `--force` 批量覆盖；按单个 ID 重试。
- **巡检报断链：** 先修源 Markdown 或数据文件，不要在生成文件中做无法复现的临时改动。

## 七、部署与回滚

GitHub Pages 从 `main` 分支的仓库根目录提供站点。推送后检查线上首页和本次涉及页面；CDN 或 Pages 可能有短暂缓存延迟。

发布前查看：

```bash
git status
git diff --check
```

发布后若出现回归，优先对问题提交执行 `git revert <commit>` 并重新推送，保留完整历史；不要使用 `git reset --hard` 覆盖已推送版本。历史稳定版本可通过仓库 tag 恢复。

## 八、定期维护

- 每次内容或网站变更：运行 `python scripts/check_site.py`。
- 每月：抽查线上六类核心页面、移动端布局和地图降级提示。
- 新增 5 篇文章或一次大规模复评后：重算榜单统计并检查首页推荐入口。
- 更换 Docsify、Leaflet 或地图服务版本时：记录版本、失败降级和桌面/移动端验证结果。
- 结构、导航、统计、生成流程或部署入口变化时：追加 `website/maintenance-log.md`。
