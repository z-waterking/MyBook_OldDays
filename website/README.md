# 网站文件夹

这里集中保存 Docsify 网站相关文件。

## 文件说明

- `index.html`：Docsify 网站入口。
- `_sidebar.md`：侧边栏导航。
- `catalog.md`：文章目录，由脚本自动生成。
- `ranking.md`：评分排名。
- `literary-gems.md`：佳句榜。
- `fun-rankings.md`：趣味榜单。

## 路径约定

网站入口位于 `website/index.html`，页面里设置了 `<base href="../">`，因此站点页仍按仓库根目录写路径：链接到文章使用 `articles/...`，链接到成书工作区使用 `book/...`。

根目录的 `index.html` 只是跳转入口，用来保持 GitHub Pages 原地址可用。

## 生成目录

```bash
node scripts/article_covers.mjs --mode markdown
```

或：

```bash
python scripts/save_article.py --catalog-only
```

两个命令都应生成 `website/catalog.md`。
