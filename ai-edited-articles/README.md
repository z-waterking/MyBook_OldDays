# AI 修改稿目录

这里用于保存 AI 参与修改后的文章版本。`articles/` 是作者原文归档，本目录是改稿工作区，二者应保持一一对应。

## 命名规则

- 每篇文章使用与 `articles/` 下相同的目录名。
- 合集文章放在 `ai-edited-articles/合集/`。
- 散篇文章放在 `ai-edited-articles/散篇/`。
- 每篇改稿建议至少包含：
  - `index.md`：AI 修改后的正文。
  - `notes.md`：修改说明、保留意见、待作者确认的问题。

## 对应关系

对应关系记录在 [mapping.md](mapping.md)。例如：

```text
articles/合集-01-我在河津上幼儿园/index.md
ai-edited-articles/合集/合集-01-我在河津上幼儿园/index.md
```

## 使用原则

1. `articles/` 只保存原始归档和评价，不直接覆盖作者原文。
2. AI 修改稿可以调整结构、措辞、删改段落，但应在 `notes.md` 记录较大的改动。
3. 如果一篇文章有多个修改方向，可增加 `index_v2.md`、`index_v3.md`，不要覆盖已有版本。
4. 最终要合入成书稿时，再从这里挑选确认后的版本进入 `book/`。

## 协作规矩

后续 AI 接手改稿前，先读 [AI_EDITING_GUIDE.md](AI_EDITING_GUIDE.md)。里面记录了改稿目标、风格边界、文件约定和目录入口更新方式。
