# 网站文件夹

这里集中保存 Docsify 网站相关文件。

## 文件说明

- `index.html`：旧 `/website/` 地址的兼容跳回页，正式入口在根目录 `index.html`。
- `_sidebar.md`：侧边栏导航。
- `catalog.md`：文章目录，由脚本自动生成。
- `ranking.md`：评分排名。
- `literary-gems.md`：佳句榜。
- `fun-rankings.md`：趣味榜单。
- `image-index.md`：图片索引，由脚本自动生成。
- `maintenance-log.md`：网站维护日志，记录结构、导航、榜单、脚本和内容入口等重大改动。

## 路径约定

网站正式入口位于根目录 `index.html`，用于 GitHub Pages 原地址。站点页按仓库根目录写路径：链接到文章使用 `articles/...`，链接到成书工作区使用 `book/...`。

`website/index.html` 只负责把旧 `/website/` 地址跳回根入口，并保留 hash 路由。

## 生成目录

```bash
node scripts/article_covers.mjs --mode markdown
```

或：

```bash
python scripts/save_article.py --catalog-only
```

两个命令都应生成 `website/catalog.md`。

## 图片索引

```bash
node scripts/generate_image_index.mjs
```

该命令扫描 `assets/images/articles/` 和其他 `assets/images/` 子目录，生成 `website/image-index.md`。文章图片按文章目录分组，供原文和 AI 改稿共同引用。

## 维护日志

每次影响网站结构、导航入口、目录生成、榜单统计、文章归档流程或 AI 改稿入口的大改动，都要在 `website/maintenance-log.md` 追加一条 Log。
