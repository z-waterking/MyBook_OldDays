# Claude 工作流说明

## 保存公众号文章
当用户提供微信公众号文章链接时，运行：
```bash
python scripts/save_article.py URL1 [URL2 ...]
```

## 保存后
- 报告：标题、作者、日期、图片数、保存路径
- 询问用户是否需要 git commit

## 重建目录
```bash
python scripts/save_article.py --catalog-only
```

## 脚本失败时的备用方案
如果脚本无法抓取（如微信封锁），可以：
1. 用 WebFetch 获取文章 HTML
2. 手动提取内容并写入文件
