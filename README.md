# 旧日之书

微信公众号文章归档、评价、网页展示与成书整理仓库。

在线阅读：[https://z-waterking.github.io/MyBook_OldDays/](https://z-waterking.github.io/MyBook_OldDays/)

## 目录结构

```text
articles/                 原始文章归档，每篇文章一个目录
assets/images/articles/   文章图片库，按文章目录分组
assets/images/            其他跨文章复用图片
ai-edited-articles/       AI 修改稿工作区，与 articles/ 一一对应
book/                     七部阅读结构、编辑规划与连续书稿
website/                  Docsify 网站入口、侧边栏、榜单和目录
scripts/                  抓取、目录生成、封面处理等脚本
index.html                GitHub Pages / Docsify 正式入口
requirements.txt          Python 依赖
.python-version           Python 版本基线（3.12）
.nvmrc                    Node.js 版本基线（20）
```

## 文章归档

保存微信公众号文章：

```bash
python scripts/save_article.py URL1 URL2 URL3
```

从文件批量导入：

```bash
python scripts/save_article.py -f urls.txt
```

强制覆盖已有文章：

```bash
python scripts/save_article.py --force URL
```

仅重建网站目录：

```bash
python scripts/save_article.py --catalog-only
```

封面与目录脚本：

```bash
node scripts/article_covers.mjs --mode markdown
```

该命令同时刷新轻量封面缩略图、文章封面块和网站目录。

## 网站目录

网页相关 Markdown 统一放在 `website/`：

- `website/home.md`：读者首页与阅读导览。
- `website/catalog.md`：文章目录，自动生成。
- `website/_sidebar.md`：Docsify 侧边栏。
- `website/ranking.md`：评分排名。
- `website/literary-gems.md`：佳句榜。
- `website/fun-rankings.md`：趣味榜单。
- `website/footprints.md`：中国与世界足迹地图、地点档案。
- `website/image-index.md`：图片索引，自动生成。
- `website/MAINTENANCE.md`：网站生成、验证、发布、降级与回滚手册。

完整 Docsify 站点入口是根目录 `index.html`，用于 GitHub Pages 原地址。网页相关 Markdown 仍统一放在 `website/`。`website/index.html` 只保留为旧 `/website/` 地址的兼容跳回页，并会保留当前 hash 路由。文章正文保留在 `articles/`，文章图片统一放在 `assets/images/articles/`。

## AI 修改稿

AI 修改后的文章放在 `ai-edited-articles/`，不要覆盖 `articles/` 中的作者原文。对应关系见：

```text
ai-edited-articles/mapping.md
```

建议每篇改稿使用同名目录：

```text
articles/合集-01-我在河津上幼儿园/index.md
ai-edited-articles/合集/合集-01-我在河津上幼儿园/index.md
```

每个改稿目录建议包含：

- `index.md`：AI 修改后的正文。
- `notes.md`：修改说明、保留意见、待作者确认的问题。

后续 AI 或协作者接手时，先读 `AGENTS.md` 和 `ai-edited-articles/AI_EDITING_GUIDE.md`。批量补缺失初稿可运行：

```bash
node scripts/generate_ai_edit_drafts.mjs
```

刷新脚本生成的 v1 初稿可运行：

```bash
node scripts/generate_ai_edit_drafts.mjs --refresh-generated
```

默认命令不会覆盖已有稿，`--refresh-generated` 也会跳过手工精修稿。

每篇 `notes.md` 应写清“本版实际改动”。批量补齐可运行：

```bash
node scripts/update_ai_edit_notes.mjs
```

## 图片索引

文章图片统一放在 `assets/images/articles/<文章目录>/`，原文和 AI 改稿引用同一份文件。其他跨文章或成书区共用图片放在 `assets/images/<主题>/`。新增、移动图片后运行：

```bash
node scripts/generate_image_index.mjs
```

生成结果在 `website/image-index.md`。正文使用仓库根路径，例如 `assets/images/articles/合集-05-我在康杰念高中（怀昔）/001.jpg`。

佳句榜和趣味榜插画由 `scripts/illustration_manifest.json` 统一描述。使用已配置的全局 Azure GPT Image skill 生成缺失原图，再生成网页 WebP 并注入对应标题：

```powershell
./scripts/generate_site_illustrations.ps1 -TimeoutSec 600
python scripts/prepare_site_illustrations.py
```

生成脚本默认跳过已有原图；需要重做单张时使用 `-Id <条目ID> -Force`。足迹坐标与来源说明维护在 `website/footprints-data.json`。

## 成书工作区

`book/` 维护《旧日之书》的七部时间主线、附录、时间线、题目库和出版规划。公开阅读顺序由 `book/reading-order.json` 统一控制，当前从 38 篇档案中选取 33 篇；这里可以重排、删选和规划补写，但不直接替代 `articles/` 的归档版本。

从当前 AI 修改稿生成连续工作书稿：

```bash
python scripts/build_book_manuscript.py
```

输出为 `book/manuscript.md`。检查已提交书稿是否与选篇清单、分部导言和文章源文件一致：

```bash
python scripts/build_book_manuscript.py --check
```

`book/manuscript.md` 不手工修改；应调整源文件后重新构建。需要临时对照原始归档稿时，可用 `--source original --output <路径>` 另行输出。

## 本地环境

工具链要求：

- Python 3.12 或更高版本；项目基线见 `.python-version`。
- Node.js 20 LTS 或兼容版本；项目基线见 `.nvmrc`。

安装 Python 依赖：

```bash
python -m pip install -r requirements.txt
```

Windows 如果没有 `python` 或 `node`，安装后重新打开终端并确认两个命令都在 `PATH` 中。

检查全部维护脚本语法：

```bash
python -m py_compile scripts/save_article.py scripts/check_site.py scripts/build_book_manuscript.py scripts/generate_cover_thumbnails.py scripts/prepare_site_illustrations.py
node --check scripts/article_covers.mjs
node --check scripts/generate_ai_edit_drafts.mjs
node --check scripts/generate_image_index.mjs
node --check scripts/update_ai_edit_notes.mjs
```

检查网站文章、成书阅读顺序、目录、链接、足迹和插画完整性：

```bash
python scripts/check_site.py
```

网站维护与发布的完整步骤见 [website/MAINTENANCE.md](website/MAINTENANCE.md)。

## 维护约定

1. `articles/` 是原文档案，尽量只追加，不直接改写正文。
2. `website/` 是网页展示层，目录和榜单可以维护。
3. `ai-edited-articles/` 是 AI 改稿区，保持与原文一一对应。
4. `book/` 是成书工作区，用于最终选稿、编排和补写。
5. `assets/images/articles/` 是文章图片的唯一存储区，原文和 AI 改稿共享引用。
6. 自动生成的网站目录、图片索引、`book/manuscript.md` 和 `_generated/` 派生图不直接手改，应修改源文件后重新运行生成脚本。
7. 本地密钥只通过环境变量或安全交互输入，不提交 `.env`；文本格式遵循 `.editorconfig`。
