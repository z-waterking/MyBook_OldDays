# 图片库

这里集中存放文章、AI 改稿、成书区和网站页面引用的图片。

## 使用规则

1. 文章图片放在 `assets/images/articles/<文章目录>/`，目录名与 `articles/` 一致。
2. 原文和 AI 改稿直接引用同一份文章图片，不创建重复副本。
3. 其他跨文章或成书区共用图片放在主题子目录。
4. Markdown 中使用仓库根路径引用，例如：

```markdown
![](assets/images/articles/合集-05-我在康杰念高中（怀昔）/001.jpg)
```

5. 新增、移动或复制图片后，运行：

```bash
node scripts/generate_image_index.mjs
```

生成后的索引位于 `website/image-index.md`。
