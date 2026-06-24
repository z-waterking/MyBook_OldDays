# MyBook_OldDays

微信公众号文章归档仓库，自动抓取并保存为 Markdown 格式，保留图片。

## 使用方式

### 通过 Claude Code（推荐）
直接把公众号文章链接发给 Claude，自动保存。

### 命令行
```bash
# 安装依赖
pip install -r requirements.txt

# 保存文章（支持多个链接）
python scripts/save_article.py URL1 URL2 URL3

# 从文件批量导入
python scripts/save_article.py -f urls.txt

# 强制覆盖已有文章
python scripts/save_article.py --force URL

# 仅重建目录索引
python scripts/save_article.py --catalog-only
```

### Windows 环境
如果命令行里没有 `python`，先安装 Python 3.12+，并在安装器里勾选
`Add python.exe to PATH`。安装后重新打开终端，再执行：

```bash
python --version
python -m pip install -r requirements.txt
```

### 测试
```bash
python -m unittest discover -s tests
```

## 目录结构
```
articles/
├── 文章标题1/
│   ├── index.md        # Markdown 正文 + YAML 元信息
│   └── images/         # 本地图片
│       ├── 001.jpg
│       └── 002.png
└── 文章标题2/
    └── ...
catalog.md              # 文章总目录（自动生成）
```
