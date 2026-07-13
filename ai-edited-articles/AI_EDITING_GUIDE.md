# AI 改稿协作规矩

这个目录用于保存 AI 参与修改后的文章版本。目标是让每篇文章都朝着 `10/10` 靠近，但不能把作者原本的声音磨掉。

## 基本原则

1. 不覆盖 `articles/` 原文。原文是档案，AI 改稿只放在 `ai-edited-articles/`。
2. 每篇文章目录名必须与 `articles/` 中对应目录一致。
3. 每篇至少包含 `index.md` 和 `notes.md`。
4. `index.md` 放可阅读的改稿正文，不要只放建议。
5. `notes.md` 记录改稿目标、主要改动、保留意见和下一轮可继续处理的点。
6. `notes.md` 必须包含 `## 本版实际改动`，逐条写清这版相对原文做了什么。
7. `index.md` 是唯一当前版本；历史版本依赖 Git，不创建 `index_v*.md` 平行稿。

## 改稿前必须读

按优先级阅读：

1. `articles/<文章目录>/index.md`
2. 唯一的规范评价文件 `articles/<文章目录>/review.md`
3. `website/ranking.md` 中对应文章的评分和核心评价
4. 已存在的 `ai-edited-articles/<分类>/<文章目录>/notes.md`

## 写作风格

保留作者的核心风格：

- 具体场景优先，不写空泛总结。
- 可以嘴贫，可以自嘲，可以突然落下一句伤感。
- 不要把句子改成标准作文腔。
- 不要堆“时光荏苒、青春无悔、人生旅途”这类模板词。
- 重要人名缩写可以保留，但关键人物首次出现时最好补一句身份或性格标签。
- 结尾尽量落到具体物件、动作或一句作者式玩笑，不要只靠鸡汤升华。

## 10 分方向

不同类型文章的改法不同：

- 回忆录：收紧时间线，保留高光细节，让结尾回到开头的核心意象。
- 职场文：减少流水账，突出一个主问题，比如选择、权力、成长、幻灭。
- 散文随笔：减少素材罗列，把情绪和主题扣紧。
- 小说：优先保证人物动机、冲突推进和语体稳定。
- 段子短文：可以扩写，但不要解释到不好笑。

## 文件约定

`index.md` frontmatter 建议包含：

```yaml
---
title: "原标题"
author: "凡复思忖"
source_article: "../../../articles/.../index.md"
target_score: "10/10"
status: "AI 修改稿"
edit_round: "v1"
edited: "YYYY-MM-DD"
---
```

`notes.md` 建议包含：

- 选择/改稿理由
- 本版实际改动
- 本轮主要改动
- 保留的原文亮点
- 下一轮继续精修建议

批量补齐实际改动清单可运行：

```bash
node scripts/update_ai_edit_notes.mjs
```

## 更新网站入口

改稿生成后运行：

```bash
node scripts/article_covers.mjs --mode markdown
```

目录页会自动检测 `ai-edited-articles/<分类>/<文章目录>/index.md`，并在文章卡片右侧加 `AI改稿` 入口。

每篇改稿底部保留 `ai-edit-links` 导航块，提供“返回原文”和“查看改稿说明”。Docsify 的站内 hash 路由必须写成 HTML `href="#/..."`，不要写成 Markdown 的 `](#/...)`；后者会被解析为当前页面的标题锚点。批量修复已有导航可运行：

```bash
node scripts/generate_ai_edit_drafts.mjs --refresh-navigation
```

## 批量生成初稿

如果需要给缺失文章补第一版改稿，可运行：

```bash
node scripts/generate_ai_edit_drafts.mjs
```

这个脚本只补缺失稿件，默认不覆盖已有 `index.md`。已有稿件应人工精修或显式使用脚本参数处理。

刷新机器生成的 v1 初稿时，使用：

```bash
node scripts/generate_ai_edit_drafts.mjs --refresh-generated
```

该参数只覆盖带 `edit_round: "v1"` 的脚本初稿，会跳过手工精修稿。`--force` 会覆盖所有已有稿件，只有在明确确认后才使用。

## 图片引用

- AI 改稿不要复制图片到 `ai-edited-articles/`。
- 文章图片使用仓库根路径引用，例如 `assets/images/articles/<文章目录>/001.jpg`。
- 其他跨文章共用图片放到 `assets/images/<主题>/`，再在正文中引用。
- 图片索引位于 `website/image-index.md`，由下面命令生成：

```bash
node scripts/generate_image_index.mjs
```
