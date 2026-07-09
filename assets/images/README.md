# 共享图片库

这里存放可被多篇文章、AI 改稿、成书区或网站页面共同引用的图片。

## 使用规则

1. `articles/<文章目录>/images/` 是原文档案图片，默认不移动。
2. 如果一张图片需要跨文章复用，复制一份到本目录下的主题子目录。
3. Markdown 中使用仓库根路径引用，例如：

```markdown
![](assets/images/topic/example.png)
```

4. 新增、移动或复制图片后，运行：

```bash
node scripts/generate_image_index.mjs
```

生成后的索引位于 `website/image-index.md`。
