# 图片库

这里集中存放文章、AI 改稿、成书区和网站页面引用的图片。

## 使用规则

1. 文章图片放在 `assets/images/articles/<文章目录>/`，目录名与 `articles/` 一致。
1. 原文和 AI 改稿直接引用同一份文章图片，不创建重复副本。
1. 其他跨文章或成书区共用图片放在主题子目录。
1. Markdown 中使用仓库根路径引用，例如：

```markdown
![](assets/images/articles/合集-05-我在康杰念高中（怀昔）/001.jpg)
```

1. 新增、移动或复制图片后，运行：

```bash
node scripts/generate_image_index.mjs
```

生成后的索引位于 `website/image-index.md`。

## 子目录职责

- `articles/`：文章原始图片和文章封面，按文章目录分组，是原文与 AI 改稿共用的源文件。
- `illustrations/`：佳句榜和趣味榜插画的高质量 JPEG 源文件。
- `_generated/catalog-covers/`：目录使用的轻量 WebP，由 `scripts/generate_cover_thumbnails.py` 生成。
- `_generated/illustrations/`：榜单使用的 960×640 WebP，由 `scripts/prepare_site_illustrations.py` 生成。
- `_generated/home-hero.webp` 与 `_generated/favicon.png`：首页和站点图标派生物。

`_generated/` 会随 GitHub Pages 一起发布，因此需要提交到仓库，但不要直接编辑。需要调整时先修改对应源文件，再运行生成脚本并提交源文件与派生物。
