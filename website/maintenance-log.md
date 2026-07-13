# 网站维护日志

> 记录《旧日之书》网站层面的重大维护。凡影响站点结构、导航入口、目录生成、榜单统计、文章归档流程、AI 改稿入口或部署入口的大改动，都应在这里追加一条 Log。

## 记录规范

- 新记录放在最上方，按时间倒序排列。
- 每条记录建议包含：日期、类型、涉及范围、改动摘要、验证方式、关联提交。
- 小的错别字、单篇短评微调、普通文案润色可以不记；会影响读者入口、统计数字或维护流程的改动必须记。

---

## 2026-07-13 · 全库 38 篇 AI 改稿升级为 v2

- **类型：** AI 改稿 / 成书生成 / 内容安全与可信度
- **关联提交：** 本条所在提交；标签 `ai-edits-v2-2026-07-13`

### 涉及范围

- AI 改稿区：覆盖 20 篇合集与 18 篇散篇的唯一当前改稿，并同步修改说明。
- 生成脚本：将全库定向精修规则与 v2 说明纳入可复现流程。
- 成书脚本与连续书稿：支持章节正文内部二级分节。

### 改动摘要

- 38 篇改稿统一升级为 v2，不创建平行版本，不覆盖原始档案。
- 长篇依据规范评价重建主轴、分节、素材取舍和专属结尾；短篇由图片梗或清单扩写为可独立阅读的微型叙事。
- 《请出示证件》补写第五、六天，完成父亲逃亡原因、小闪动机和小牛最终选择的闭环。
- 公共人物死亡随笔删除无法由本地档案核实的健康与死因传言；丧尸指南增加虚构声明、点位淘汰标准和现实安全警示。
- 书稿生成器只统计阅读顺序中的正式章节，不再把文章内部二级分节误算为新章节。

### 验证

- 全量重建 AI 改稿与改稿说明。
- 重建网站目录与连续书稿，并验证书稿可重复生成。
- 网站巡检通过：38 篇文章、38 个目录项、38 个评分项、38 篇 AI 改稿。
- 全部 Python / Node.js 维护脚本语法检查通过。

---

## 2026-07-13 · 全站审计与构建、加载体验加固

- **类型：** 全站审计 / 生成流程 / 可访问性 / 加载韧性 / 持续集成
- **状态：** 已完成
- **关联提交：** 待提交

### 涉及范围

- `scripts/save_article.py`：文章正文与网站目录统一以 LF 写入；纯本地目录重建不再强制加载抓取依赖。
- `scripts/generate_cover_thumbnails.py` / `scripts/article_covers.mjs`：生成并引用轻量正文封面。
- `scripts/check_site.py`：校验文章封面、目录/正文 WebP、首页主视觉和 favicon 的格式、尺寸及同步状态。
- `index.html`：改善粗指针设备触控区域，补充常青元信息、CDN 预连接、无脚本说明和 Docsify 加载失败提示。
- `scripts/check_inline_scripts.mjs` / `.github/workflows/site-check.yml`：将首页内联脚本语法纳入本地和 CI 检查。

### 改动摘要

- 修复 Windows 上运行 `--catalog-only` 时，内容没有变化但 `website/catalog.md` 因 CRLF 换行而显示为已修改的问题。
- `--catalog-only` 只使用标准库即可运行；缺少抓取依赖时，真正归档远程文章仍会给出明确安装提示。
- 新归档文章也显式遵循仓库 `.editorconfig` 与 `.gitattributes` 的 LF 约定，避免平台相关差异进入后续构建。
- 文章页改用 1200×800 WebP 封面并声明尺寸，降低原始 PNG 传输量和布局偏移；巡检会捕获缺失、多余或过期的封面派生图。
- 移动端触控目标按输入设备能力增大，桌面端继续保持紧凑布局。Docsify 或 JavaScript 不可用时，读者会看到明确说明和 GitHub 内容入口。
- Docsify 渲染前会把仓库根图片路径补成站点根路径，修复深层文章路由下正文图片被错误拼接为 `articles/.../assets/...` 的问题。
- CI 现在会实际编译检查 `index.html` 的内联脚本，覆盖此前只检查 `scripts/*.mjs` 的盲区。

### 验证

- Windows 上连续运行两次 `python scripts/save_article.py --catalog-only`，`website/catalog.md` 保持无差异。
- `node scripts/article_covers.mjs --mode markdown`。
- `node scripts/check_inline_scripts.mjs`。
- `python -m py_compile scripts/save_article.py`。
- `python scripts/check_site.py`。
- 桌面与 390px 移动宽度浏览器冒烟检查。

---

## 2026-07-12 · 七部成书结构与连续阅读

- **类型：** 成书编排 / 读者导航 / 生成流程 / 持续集成
- **状态：** 已完成
- **关联提交：** 本条所在提交 · `feat: structure seven-part book edition`

### 涉及范围

- `book/reading-order.json`：新增七部、附录及 33 篇入选文章的唯一结构化阅读顺序。
- `book/01-成书目录.md` / `book/部*.md` / `book/附录-别调与想象.md`：重建面向读者的成书目录、分部导言与章节入口。
- `book/02-时间线.md` / `book/03-写作规划.md` / `book/04-候选题目库.md`：整理阶段覆盖、关键缺章、出版路径及各阶段备选题目。
- `scripts/build_book_manuscript.py` / `book/manuscript.md`：新增可重复构建的连续工作书稿。
- `index.html` / `website/home.md` / `website/_sidebar.md`：新增七部人生路径、章节进度及跨分部上一篇/下一篇导航。
- `scripts/check_site.py` / `.github/workflows/site-check.yml`：校验阅读清单、公开入口和连续书稿的一致性。

### 改动摘要

- 成书结构由旧有规划卷目收敛为七部时间主线与一组附录，网站文章档案仍保留全部 38 篇，纸书当前精选 33 篇。
- 公开阅读页与内部编辑规划分离；研究生阶段的关键缺章和全书结尾明确留给作者补写，不用生成内容替代真实经历。
- 删除重复且相互冲突的旧卷目页，所有公开章节顺序统一由 `reading-order.json` 驱动并接受机器校验。
- 文章页显示全书进度和相邻章节，跨分部阅读保持连续；桌面首页使用七列时间线，移动端自动收为单列。
- `book/manuscript.md` 从当前 AI 修改稿拼合，修改选篇、分部导言或入选稿件后必须重新生成，不做长期手工修改。

### 验证

- `python scripts/build_book_manuscript.py` 与 `python scripts/build_book_manuscript.py --check`：33 篇连续书稿可重复生成。
- `python scripts/check_site.py`：成书目录、八个分部页面、章节顺序、站内链接及原有文章数据检查通过。
- 桌面与 390px 移动端检查：首页七部时间线无横向溢出，文章页进度与上一篇/下一篇正确衔接。
- 全部 Python/Node.js 脚本语法检查及 `git diff --check`。

## 2026-07-12 · 工程原则收敛与全库自动校验

- **类型：** 仓库规范 / 生成流程 / 持续集成 / 数据一致性
- **状态：** 已完成
- **关联提交：** 本条所在提交 · `chore: consolidate repository engineering rules`

### 涉及范围

- `scripts/save_article.py` / `scripts/article_covers.mjs`：目录 HTML 收敛为唯一 Python 实现，Node 封面流程改为委托调用。
- `scripts/check_site.py`：新增评价结构与唯一性、评分榜顺序和统计、AI 改稿与映射、页面固定统计等校验。
- `.github/workflows/site-check.yml`：覆盖全部 Python 与 Node.js 脚本，并验证目录和图片索引可重复生成。
- `.python-version` / `.nvmrc` / `.editorconfig` / `.gitattributes` / `.gitignore`：明确工具链、编码换行、缩进和本地密钥规则。
- `AGENTS.md` / `README.md` / `website/MAINTENANCE.md` / 各子目录 README：统一生成物、AI 当前版本和验证约定。

### 改动摘要

- `website/catalog.md` 只由 `save_article.py` 渲染；完整封面命令保留原用法，但不再维护第二套目录模板。
- 生成目录和图片索引不再写入运行日期，相同源文件始终产生相同结果；生成文件明确禁止长期手工编辑。
- AI 改稿统一以 `index.md` 作为唯一当前版本，历史由 Git 保存，不再允许 `index_v*.md` 平行入口。
- CI 使用 Python 3.12 和 Node.js 20，安装完整 Python 依赖、检查全部 8 个脚本并重建索引。
- Python 依赖限定兼容主版本，允许安全更新但不静默跨越破坏性大版本。
- 巡检把 38 篇规范评价、排名/分布/均值、38 个 AI 改稿及 mapping、地点和榜单统计纳入机器约束。
- 首页和常青维护文档移除容易过期的文章/榜单固定总数；成书规模保留为带日期快照。

### 验证

- 完整运行 `article_covers.mjs --mode markdown`，文章正文无变化，目录由唯一 Python 渲染器重建。
- 两次重建 `website/catalog.md` 与 `website/image-index.md`，文件哈希保持一致。
- 全部 4 个 Python 和 4 个 Node.js 脚本语法检查。
- `python scripts/check_site.py`：文章、目录、排名、AI 改稿均为 38，567 个本地目标、31+4 个足迹记录和 50 张插画全部通过。
- `git diff --check` 与首页桌面/移动端冒烟检查。

## 2026-07-12 · 全站审阅、故障降级与维护体系

- **类型：** 全站审阅 / 可访问性 / 性能与韧性 / 维护自动化
- **状态：** 已完成
- **关联提交：** 本条所在提交 · `feat: harden site and document maintenance`

### 涉及范围

- `index.html` / `website/footprints.md`：经典蓝色地图视觉、按路由加载、地点档案优先渲染、双层失败降级、键盘焦点、跳到正文和减少动效支持。
- `scripts/check_site.py`：新增文章、评价、目录、本地链接、足迹与插画的一体化巡检。
- `.github/workflows/site-check.yml`：在主分支推送和 Pull Request 上自动运行巡检。
- `website/MAINTENANCE.md`：新增网站维护、生成、验证、发布、降级和回滚的权威操作手册。
- `README.md` / `AGENTS.md` / `website/README.md` / `website/_sidebar.md`：统一维护入口和目录生成职责。

### 审阅结论与改动

- 修复地图数据或 Leaflet 失败时地点列表可能为空的问题；地点 JSON 成功后先渲染档案，再异步加载地图库。
- Leaflet CSS/JS 不再由所有页面无条件加载，只在首次进入足迹页时请求。
- 足迹页从棕灰地图配色切换为经典蓝；范围按钮、路线、六类蓝色标记、图例、弹窗与地点档案使用统一的地图色阶。
- 地图范围切换改用带 `aria-pressed` 的原生按钮组；数据失败时自动展开带来源文章的静态地点索引。
- 增加首个键盘焦点“跳到正文”、统一 `focus-visible` 轮廓、搜索框标签及 `prefers-reduced-motion` 支持。
- 明确 `article_covers.mjs --mode markdown` 是目录与封面的完整发布命令，`save_article.py --catalog-only` 仅用于快速目录重建。
- 网站维护从人工清单升级为本地脚本与 CI 共用的一套可执行规则。

### 验证

- `python -m py_compile scripts/save_article.py scripts/check_site.py`
- `python scripts/check_site.py`：38 篇文章/目录、567 个本地链接与图片、31+4 个足迹记录、50 张插画全部通过。
- Playwright 主动阻断 Leaflet：31 条动态地点档案仍可读；主动阻断足迹 JSON：静态索引自动展开。
- 桌面和 390px 移动端检查蓝色地图；中国/世界按钮、31/4 个标记、路线、图例和地点列表同步切换。
- 六个核心路由桌面冒烟检查；首页、目录、地图和维护手册 390px 移动端及减少动效检查。
- 键盘 Tab 首焦点、跳到正文、断图、空白页面、横向溢出、内联 JavaScript 语法和 `git diff --check` 检查。

## 2026-07-12 · 强化足迹入口与长页导航

- **类型：** 读者入口 / 地图体验 / 长页导航
- **状态：** 已完成
- **关联提交：** 本条所在提交 · `feat: improve map discovery and long-page navigation`

### 涉及范围

- `website/home.md`：将足迹地图提升为首屏操作，并新增地图专题入口与地点统计。
- `website/footprints.md`：为交互地图增加操作提示浮层。
- `index.html`：放宽并增高地图、突出侧栏地图入口，为两张长榜单自动生成章节选择器，并新增回到顶部控件。

### 改动摘要

- 地图不再只藏在首页底部，而是同时出现在 Hero 主操作和独立专题区；侧栏入口增加视觉提示。
- 地图桌面宽度提升至 1120px、高度提升至 620px，移动端保持 430px 操作区和可读的点击提示。
- 佳句榜按 5 个主题、趣味榜按 18 个榜单自动生成吸顶章节导航，滚动时同步当前章节。
- 长页滚动超过 700px 后显示回到顶部控件；移动端加强 Hero 文字对比度并保证导航无横向溢出。

### 验证

- 桌面及 390px 移动端 Playwright 检查：首页入口、地图标记与筛选、章节跳转、滚动同步、回到顶部和横向溢出。
- 中国视图 31 个标记、世界视图 4 个总览/地点标记与本地档案列表同步。
- 内联 JavaScript 语法检查与 `git diff --check`。

## 2026-07-12 · 佳句与趣味榜插画、足迹地图

- **类型：** 视觉内容 / 专题页面 / 地图交互
- **状态：** 已完成
- **关联提交：** 本条所在提交 · `feat: illustrate curated pages and add footprint map`

### 涉及范围

- `website/literary-gems.md` / `website/fun-rankings.md`：为 32 条佳句和 18 个趣味榜单分别加入场景插画。
- `assets/images/illustrations/` / `assets/images/_generated/illustrations/`：保存 1536×1024 JPEG 原图与 960×640 WebP 网页派生图。
- `scripts/illustration_manifest.json` / `scripts/generate_site_illustrations.ps1` / `scripts/prepare_site_illustrations.py`：维护场景清单、断点续生、压缩和页面注入。
- `website/footprints.md` / `website/footprints-data.json`：新增中国与世界足迹地图、地点列表和来源说明。
- `index.html` / `website/_sidebar.md` / `website/home.md`：新增 Leaflet 地图、响应式插画样式和读者入口。

### 改动摘要

- 50 张插画使用统一的 3:2 纪实电影感方向，但按每条佳句或榜单主题分别还原具体场景。
- 页面只加载约 2.39 MB 的 WebP 派生图，使用懒加载；高质量 JPEG 原图保留用于后续再加工。
- 足迹页包含 31 个中国地点、3 个西班牙地点和 6 类足迹；坐标、路线与文章来源由本地 JSON 驱动。
- 地图使用 Leaflet 和 Esri 世界街道底图；底图不可用时仍展示本地点档案列表。

### 验证

- 50 张原图均为 1536×1024 JPEG，50 张派生图均为 960×640 WebP，文件哈希无重复。
- `python scripts/prepare_site_illustrations.py` 重复运行无重复插入。
- 地点 JSON、坐标范围、35 条地点记录与来源链接检查。
- 桌面及 390px 移动端 Playwright 检查：插画比例、地图瓦片、标记、筛选、列表和横向溢出。

## 2026-07-12 · 新增书籍首页并优化目录性能

- **类型：** 读者入口 / 信息架构 / 页面性能
- **状态：** 已完成
- **关联提交：** 本条所在提交 · `feat: add reader-oriented book homepage`

### 涉及范围

- `website/home.md`：新增书籍扉页式首页、人生路径、推荐阅读与专题入口。
- `website/_sidebar.md`：改用“首页、全部文章、按卷阅读、编辑精选、佳句选读、趣味索引”等读者语言。
- `index.html`：根路由切换到首页，新增主页样式、分享元信息、canonical 和 favicon。
- `scripts/generate_cover_thumbnails.py` / `scripts/article_covers.mjs`：生成并使用轻量 WebP 缩略图。

### 改动摘要

- 根地址不再直接展示 38 篇全目录；全部文章保留为二级页。
- 首页以总序已有文字和代表性封面为核心，提供从头阅读、编辑精选、全部文章及按人生阶段进入的路径。
- 目录封面从 38 张原图约 86.6 MB，改为 38 张 480×320 WebP 并启用懒加载；全部网站派生图片约 0.87 MB。
- 更新成书工作区中过时的文章、评价和 AI 改稿统计。

### 验证

- `python scripts/generate_cover_thumbnails.py`
- `node scripts/article_covers.mjs --mode markdown`
- 桌面与移动端 Playwright 截图、布局和断链检查
- 目录图片请求量与资源大小检查

## 2026-07-12 · 文章图片集中迁移到共享资产目录

- **类型：** 图片资产结构 / 归档流程 / AI 改稿引用
- **状态：** 已完成
- **关联提交：** 本条所在提交 · `chore: centralize article image assets`

### 涉及范围

- `assets/images/articles/`：按文章目录集中存放全部文章图片。
- `articles/*/index.md` / `ai-edited-articles/**/index.md`：统一改用共享资产路径。
- `scripts/save_article.py` / `scripts/article_covers.mjs` / `scripts/generate_image_index.mjs` / `scripts/generate_ai_edit_drafts.mjs`：统一图片写入、封面生成、索引和改稿路径规则。

### 改动摘要

- 将原 `articles/<文章目录>/images/` 中的图片迁移至 `assets/images/articles/<文章目录>/`，原文与 AI 改稿引用同一份文件。
- 新保存文章和新生成封面直接写入共享资产目录。
- 清理四个内容完全重复且未引用的图片副本、两个失去作用的 `.gitkeep`、`tests/` 和本地缓存。

### 验证

- `node scripts/article_covers.mjs --mode markdown`
- `node scripts/generate_image_index.mjs`
- `python -m py_compile scripts/save_article.py`
- 全库图片引用目标检查与 `git diff --check`

## 2026-07-11 · 全库统一复评与评价入口收敛

- **类型：** 全库复评 / 榜单重建 / 目录与维护流程更新
- **关联提交：** 待提交

### 涉及范围

- `articles/*/review.md`：重新阅读并评价全部 38 篇原文。
- `articles/*/review_v*.md`：删除 132 个历史评价版本。
- `website/ranking.md` / `website/literary-gems.md` / `website/fun-rankings.md`：按本轮评价和原文重新整理。
- `website/catalog.md`：重建目录，所有文章统一只保留一个“评价”入口。
- `scripts/article_covers.mjs` / `scripts/save_article.py` / `scripts/generate_ai_edit_drafts.mjs`：统一只识别规范评价文件 `review.md`。
- `AGENTS.md` / `ai-edited-articles/AI_EDITING_GUIDE.md` / `ai-edited-articles/**/notes.md`：同步唯一评价文件约定。

### 改动摘要

- 每篇评价统一包含“总体印象、亮点分析、写作建议、金句摘录、综合评分、综合评价”，评分重新按 38 篇全库横向校准。
- 新评分总榜覆盖 38 篇文章；全库平均分为 7.83，合集平均分为 8.21，散篇平均分为 7.41。
- 佳句榜重新核验原文并精选 32 句；趣味榜复核事实、人物出场、近期文章和金句密度统计。
- 目录生成和文章抓取脚本不再展示或寻找 `review_v1.md`、`review_v2.md` 等历史版本；封面块已存在时不再无意义重写原文。

### 验证

- 38 篇文章均恰有一个 `review.md`，六个规定章节完整，且不存在 `review_v*.md`。
- `node scripts/article_covers.mjs --mode markdown`
- `python -m unittest discover -s tests`
- `git diff --check`

---

## 2026-07-09 · 补齐 AI 改稿说明与图片索引规则

- **类型：** AI 改稿流程 / 图片资产管理 / 网站索引
- **关联提交：** 待提交

### 涉及范围

- `ai-edited-articles/**/notes.md`：补齐每篇改稿的 `本版实际改动`。
- `assets/images/`：新增跨文章共享图片库说明。
- `website/image-index.md`：新增全库图片索引。
- `scripts/update_ai_edit_notes.mjs` / `scripts/generate_image_index.mjs`：新增维护脚本。
- `AGENTS.md` / `README.md` / `ai-edited-articles/AI_EDITING_GUIDE.md` / `website/README.md` / `website/_sidebar.md`：同步协作规则与入口。

### 改动摘要

- 每篇 AI 改稿说明新增 `## 本版实际改动`，记录本版相对原文做了哪些清理、扩写、路径调整和结构处理。
- 建立 `assets/images/` 作为跨文章复用图片库；原文图片仍留在各自 `articles/<文章目录>/images/` 中，不为了复用而移动。
- 新增 `website/image-index.md`，集中列出原文图片和共享图片的预览、来源、类型、大小和引用路径。
- 新增维护命令：`node scripts/update_ai_edit_notes.mjs` 和 `node scripts/generate_image_index.mjs`。

### 验证

- `node scripts/update_ai_edit_notes.mjs`
- `node scripts/generate_image_index.mjs`
- `git diff --check`
- `python -m unittest discover -s tests`

---

## 2026-07-09 · 修复 GitHub Pages 根地址反复刷新

- **类型：** 部署入口修复 / 路由兼容
- **关联提交：** 待提交

### 涉及范围

- 根目录 `index.html`：改为 Docsify 正式入口。
- `website/index.html`：改为旧 `/website/` 地址的兼容跳回页。
- `README.md` / `AGENTS.md` / `website/README.md`：同步站点入口说明。

### 改动摘要

- 移除根目录 `index.html` 的 `meta refresh` 0 秒跳转，避免根地址和 `website/` 入口在 Docsify hash 路由下反复刷新。
- 将完整 Docsify 配置放回根目录 `index.html`，继续加载 `website/catalog.md`、`website/_sidebar.md` 等网站内容。
- `website/index.html` 只做单向跳回根入口，并保留当前 hash，兼容旧链接。

### 验证

- 本地静态服务访问根入口不再发生跳转循环。
- `/website/` 旧入口会跳回根入口并保留 hash。

---

## 2026-07-09 · 站点结构整理、丧尸指南入库与 AI 改稿工作区

- **类型：** 结构整理 / 内容更新 / 工作流完善
- **关联提交：** `64a1f54` · `chore: update archive site workflow and content`

### 涉及范围

- `website/`：集中 Docsify 入口、侧边栏、目录、评分榜、佳句榜、趣味榜单和网站说明。
- `articles/散篇-18-丧尸躲避指南/`：新增文章正文、图片、封面和评价。
- `ai-edited-articles/`：建立 AI 改稿工作区、映射表、协作指南，并补齐批量初稿。
- `scripts/`：更新文章保存、目录生成、封面插入和 AI 改稿草稿生成相关脚本。
- `AGENTS.md` / `CLAUDE.md`：统一 agent 协作规则，避免多份指南分叉。

### 改动摘要

- 将网站展示页从仓库根目录收敛到 `website/`，根目录 `index.html` 只保留跳转入口。
- 新增《丧尸暴发后，普通人该如何躲避》，补充 `review.md`、评分排名、佳句榜和趣味榜单条目。
- 为全部文章建立 AI 改稿工作区结构，新增 `AI_EDITING_GUIDE.md`、`mapping.md` 和批量初稿生成脚本。
- 更新 `article_covers.mjs` 与 `save_article.py`，让目录页使用 `website/catalog.md`，并自动识别 AI 改稿入口。
- 将 `AGENTS.md` 扩展为唯一详版协作指南，`CLAUDE.md` 收敛为兼容入口。

### 验证

- `git diff --check`
- `python -m unittest discover -s tests`
- 推送到 `origin/main` 成功：`6fead80..64a1f54`
