#!/usr/bin/env python3
"""
微信公众号文章归档工具
用法:
    python save_article.py URL1 [URL2 ...]
    python save_article.py -f urls.txt
    python save_article.py --catalog-only
"""

import argparse
import ast
import hashlib
import html
import io
import os
import re
import sys
import time

# Windows 控制台 UTF-8 支持
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from urllib.parse import quote, urlparse, parse_qs

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup, Tag
import markdownify


# ─── 配置 ────────────────────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).resolve().parent.parent
ARTICLES_DIR = REPO_ROOT / "articles"
AI_EDITED_DIR = REPO_ROOT / "ai-edited-articles"
WEBSITE_DIR = REPO_ROOT / "website"
CATALOG_FILE = WEBSITE_DIR / "catalog.md"

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

WECHAT_REFERER = "https://mp.weixin.qq.com/"

# Windows 文件名非法字符
UNSAFE_CHARS = re.compile(r'[\\/:*?"<>|\r\n\t]')
WINDOWS_RESERVED = {
    "CON", "PRN", "AUX", "NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
}

IMAGE_DELAY = 0.2  # 图片下载间隔(秒)
ARTICLE_DELAY = 1.0  # 文章抓取间隔(秒)


# ─── 数据模型 ─────────────────────────────────────────────────────────────────

@dataclass
class ImageInfo:
    original_url: str
    local_filename: str
    alt_text: str = ""
    downloaded: bool = False


@dataclass
class ArticleData:
    url: str
    raw_title: str = ""
    author: str = ""
    original_author: str = ""
    publish_date: str = ""
    content_html: str = ""
    images: list[ImageInfo] = field(default_factory=list)

    @property
    def safe_title(self) -> str:
        return sanitize_filename(self.raw_title)


# ─── 异常 ─────────────────────────────────────────────────────────────────────

class WeChatArchiverError(Exception):
    pass

class FetchError(WeChatArchiverError):
    pass

class ParseError(WeChatArchiverError):
    pass


# ─── 工具函数 ─────────────────────────────────────────────────────────────────

def sanitize_filename(title: str) -> str:
    """生成 Windows 安全的文件名，保留中文"""
    if not title:
        return "untitled"
    safe = UNSAFE_CHARS.sub("_", title)
    safe = re.sub(r"_+", "_", safe).strip(". _")
    # 处理 Windows 保留名
    if safe.upper() in WINDOWS_RESERVED:
        safe = safe + "_article"
    return safe[:100] or "untitled"


def get_image_extension(img_tag=None, url="", content_type=""):
    """从多个来源推断图片扩展名"""
    # 1. 从标签 data-type 属性
    if img_tag and img_tag.get("data-type"):
        ext = img_tag["data-type"].lower().strip()
        if ext in ("jpeg", "jpg", "png", "gif", "svg", "webp", "bmp"):
            return ".jpg" if ext == "jpeg" else f".{ext}"

    # 2. 从 URL 参数 wx_fmt
    if url:
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        if "wx_fmt" in params:
            fmt = params["wx_fmt"][0].lower()
            if fmt in ("jpeg", "jpg", "png", "gif", "svg", "webp"):
                return ".jpg" if fmt == "jpeg" else f".{fmt}"

    # 3. 从 Content-Type
    if content_type:
        ct = content_type.lower()
        if "jpeg" in ct or "jpg" in ct:
            return ".jpg"
        elif "png" in ct:
            return ".png"
        elif "gif" in ct:
            return ".gif"
        elif "svg" in ct:
            return ".svg"
        elif "webp" in ct:
            return ".webp"

    # 4. 从 URL 路径
    if url:
        path = urlparse(url).path
        _, ext = os.path.splitext(path)
        if ext.lower() in (".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp", ".bmp"):
            return ".jpg" if ext.lower() == ".jpeg" else ext.lower()

    return ".jpg"  # 默认


def url_hash(url: str) -> str:
    """URL 短哈希，用于处理同名文章"""
    return hashlib.md5(url.encode()).hexdigest()[:6]


def yaml_quote(value: str) -> str:
    """将字符串写成安全的 YAML 双引号标量"""
    escaped = str(value).replace("\\", "\\\\").replace('"', '\\"')
    escaped = escaped.replace("\r", "\\r").replace("\n", "\\n")
    return f'"{escaped}"'


def parse_simple_frontmatter(content: str) -> dict:
    """解析本工具生成的简单 YAML frontmatter"""
    meta = {}
    if not content.startswith("---"):
        return meta

    parts = content.split("---", 2)
    if len(parts) < 3:
        return meta

    for line in parts[1].strip().splitlines():
        if ":" not in line:
            continue
        key, val = line.split(":", 1)
        val = val.strip()
        if len(val) >= 2 and val[0] == val[-1] == '"':
            try:
                val = ast.literal_eval(val)
            except (SyntaxError, ValueError):
                val = val.strip('"')
        meta[key.strip()] = val
    return meta


def markdown_table_cell(value: str) -> str:
    """转义 Markdown 表格单元格内容"""
    return str(value).replace("|", "\\|").replace("\r", " ").replace("\n", " ")


def markdown_link_target(path: str) -> str:
    """为 Markdown 链接编码路径，同时保留斜杠"""
    return quote(path.replace("\\", "/"), safe="/()_-.")


def markdown_excerpt(content: str, limit: int = 150) -> str:
    """从文章 Markdown 中提取目录摘要"""
    body = re.sub(r"^---\r?\n[\s\S]*?\r?\n---", "", content)
    body = re.sub(r"\*原文链接:[\s\S]*$", "", body, flags=re.MULTILINE)
    body = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", body)
    body = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", body)
    body = re.sub(r"<[^>]+>", "", body)
    body = re.sub(r"^#.*$", "", body, flags=re.MULTILINE)
    body = re.sub(r"^>.*$", "", body, flags=re.MULTILINE)
    body = re.sub(r"^---$", "", body, flags=re.MULTILINE)
    body = re.sub(r"[*_`~]", "", body)
    text = re.sub(r"\s+", " ", body).strip()
    return text if len(text) <= limit else f"{text[:limit]}..."


def catalog_group(dir_name: str) -> str:
    """根据目录名归入网站目录分组"""
    if dir_name.startswith("散篇-"):
        return "散篇"
    match = re.match(r"^合集-(\d{2})-", dir_name)
    if not match:
        return "其他"
    order = int(match.group(1))
    if order <= 5:
        return "合集 · 少年时代"
    if order <= 10:
        return "合集 · 大学四年"
    return "合集 · 工作与考试"


def group_order(group: str) -> int:
    """网站目录分组顺序，与侧边栏保持一致"""
    groups = ["合集 · 少年时代", "合集 · 大学四年", "合集 · 工作与考试", "散篇", "其他"]
    try:
        return groups.index(group)
    except ValueError:
        return len(groups)


def dir_order(dir_name: str) -> int:
    """从文章目录名提取编号，用于同组内排序"""
    match = re.match(r"^(?:合集|散篇)-(\d{2})-", dir_name)
    return int(match.group(1)) if match else 999


def ai_edited_group(dir_name: str) -> str:
    if dir_name.startswith("散篇-"):
        return "散篇"
    if dir_name.startswith("合集-"):
        return "合集"
    return "其他"


def ai_edited_path(repo_root: Path, dir_name: str) -> Path:
    return repo_root / AI_EDITED_DIR.relative_to(REPO_ROOT) / ai_edited_group(dir_name) / dir_name / "index.md"


# ─── HTTP 层 ──────────────────────────────────────────────────────────────────

def create_session() -> requests.Session:
    """创建带重试机制的 HTTP 会话"""
    session = requests.Session()
    session.headers.update({
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate",
    })
    retry = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[500, 502, 503, 504],
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def fetch_article_html(session: requests.Session, url: str) -> str:
    """抓取文章 HTML"""
    try:
        resp = session.get(url, timeout=30, allow_redirects=True)
        resp.raise_for_status()
        resp.encoding = "utf-8"
        html = resp.text

        if "#js_content" not in html and "rich_media_content" not in html:
            # 可能是需要登录或已删除
            if "环境异常" in html or "访问过于频繁" in html:
                raise FetchError("微信反爬触发，请稍后重试")
            if "该内容已被发布者删除" in html:
                raise FetchError("文章已被删除")
            if "此内容因违规无法查看" in html:
                raise FetchError("文章因违规被屏蔽")
            raise ParseError("未找到文章内容，可能需要登录或文章格式异常")

        return html

    except requests.RequestException as e:
        raise FetchError(f"HTTP 请求失败: {e}")


def download_image(session: requests.Session, image_url: str, save_path: Path) -> bool:
    """下载单张图片"""
    if save_path.exists() and save_path.stat().st_size > 0:
        return True  # 已存在，跳过

    try:
        headers = {
            "Referer": WECHAT_REFERER,
            "Accept": "image/*,*/*;q=0.8",
        }
        resp = session.get(image_url, headers=headers, timeout=30, stream=True)
        resp.raise_for_status()
        content_type = resp.headers.get("Content-Type", "").lower()
        if content_type and not content_type.startswith("image/"):
            raise FetchError(f"响应不是图片: {content_type}")

        save_path.parent.mkdir(parents=True, exist_ok=True)
        with open(save_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)

        return True

    except Exception as e:
        print(f"      ⚠️  图片下载失败: {e}")
        # 删除可能的不完整文件
        if save_path.exists():
            save_path.unlink()
        return False


# ─── 解析层 ───────────────────────────────────────────────────────────────────

def parse_article(html: str, url: str) -> ArticleData:
    """解析文章 HTML，提取元信息和内容"""
    soup = BeautifulSoup(html, "lxml")
    article = ArticleData(url=url)

    # 标题
    for selector in ["#activity-name", ".rich_media_title"]:
        elem = soup.select_one(selector)
        if elem and elem.get_text(strip=True):
            article.raw_title = elem.get_text(strip=True)
            break
    if not article.raw_title:
        title_tag = soup.find("title")
        if title_tag:
            article.raw_title = title_tag.get_text(strip=True)

    # 作者/公众号名
    for selector in ["#js_name", ".rich_media_meta_nickname"]:
        elem = soup.select_one(selector)
        if elem and elem.get_text(strip=True):
            article.author = elem.get_text(strip=True)
            break

    # 原作者
    elem = soup.select_one("#js_author_name")
    if elem:
        article.original_author = elem.get_text(strip=True)

    # 发布日期
    elem = soup.select_one("#publish_time")
    if elem and elem.get_text(strip=True):
        article.publish_date = elem.get_text(strip=True)
    else:
        # 尝试从 JS 变量中提取
        for pattern in [
            r'var\s+ct\s*=\s*"(\d+)"',
            r'"publish_time"\s*:\s*"([^"]+)"',
            r'n="(\d{4}-\d{2}-\d{2})"',
        ]:
            match = re.search(pattern, html)
            if match:
                val = match.group(1)
                if val.isdigit() and len(val) == 10:
                    article.publish_date = datetime.fromtimestamp(int(val)).strftime("%Y-%m-%d")
                else:
                    article.publish_date = val
                break

    # 正文内容
    content_elem = None
    for selector in ["#js_content", ".rich_media_content"]:
        content_elem = soup.select_one(selector)
        if content_elem:
            break

    if not content_elem:
        raise ParseError("未找到文章正文内容")

    # 提取图片信息
    img_counter = 0
    for img in content_elem.find_all("img"):
        src = img.get("data-src") or img.get("src") or ""
        if not src or src.startswith("data:"):
            continue

        # 过滤 1x1 追踪像素
        width = img.get("width", "")
        height = img.get("height", "")
        if width == "1" or height == "1":
            continue
        if "tp=webp" in src and ("width=1" in src or "height=1" in src):
            continue

        img_counter += 1
        ext = get_image_extension(img_tag=img, url=src)
        filename = f"{img_counter:03d}{ext}"

        article.images.append(ImageInfo(
            original_url=src,
            local_filename=filename,
            alt_text=img.get("alt", ""),
        ))

        # 将 data-src 复制到 src 以便后续转换
        img["src"] = src

    # 清理 HTML
    clean_content_html(content_elem)
    article.content_html = str(content_elem)

    return article


def clean_content_html(elem: Tag):
    """清理微信文章 HTML"""
    soup = elem if isinstance(elem, BeautifulSoup) else elem.find_parent()
    while soup and soup.parent:
        soup = soup.parent
    if soup is None:
        soup = BeautifulSoup("", "lxml")

    # 删除脚本、样式、iframe
    for tag in elem.find_all(["script", "style", "iframe"]):
        tag.decompose()

    # 删除空的 mpvoice (音频占位) 和 mpvideosnap (视频占位)
    for tag in elem.find_all(["mpvoice", "mpvideosnap", "mp-miniprogram"]):
        tag_type = tag.name
        replacement = BeautifulSoup("<p></p>", "lxml").find("p")
        if tag_type == "mpvoice":
            replacement.string = "[音频内容]"
        elif tag_type == "mpvideosnap":
            replacement.string = "[视频内容]"
        else:
            replacement.string = "[小程序]"
        tag.replace_with(replacement)

    # 处理内联样式转语义标签
    for span in list(elem.find_all("span", style=True)):
        style = span.get("style", "")
        text_content = span.decode_contents()

        tag_name = None
        if re.search(r"font-weight\s*:\s*(bold|[6-9]00)", style):
            tag_name = "strong"
        elif re.search(r"font-style\s*:\s*italic", style):
            tag_name = "em"
        elif re.search(r"text-decoration\s*:\s*line-through", style):
            tag_name = "del"

        if tag_name:
            new_html = f"<{tag_name}>{text_content}</{tag_name}>"
            new_tag = BeautifulSoup(new_html, "lxml").find(tag_name)
            if new_tag:
                span.replace_with(new_tag)

    # 检测代码块：含 monospace 字体的元素
    for tag in list(elem.find_all(style=True)):
        style = tag.get("style", "")
        if re.search(r"font-family\s*:.*?(monospace|Consolas|Courier|Source Code)", style, re.I):
            if tag.name not in ("pre", "code"):
                code_text = tag.get_text()
                pre_tag = soup.new_tag("pre")
                code_tag = soup.new_tag("code")
                code_tag.string = code_text
                pre_tag.append(code_tag)
                tag.replace_with(pre_tag)

    # 去除所有剩余的 style, class, data-* 属性（保留 src, alt, href）
    KEEP_ATTRS = {"src", "href", "alt", "colspan", "rowspan"}
    for tag in elem.find_all(True):
        attrs_to_remove = [
            attr for attr in list(tag.attrs.keys())
            if attr not in KEEP_ATTRS
        ]
        for attr in attrs_to_remove:
            del tag[attr]


# ─── Markdown 转换 ────────────────────────────────────────────────────────────

class WeChatMarkdownConverter(markdownify.MarkdownConverter):
    """针对微信公众号文章的自定义 Markdown 转换器"""

    def __init__(self, image_map=None, **kwargs):
        self.image_map = image_map or {}
        super().__init__(**kwargs)

    def convert_img(self, el, text, convert_as_inline=False, **kwargs):
        src = el.get("src", "")
        alt = el.get("alt", "")
        safe_alt = alt.replace("\n", " ").replace("]", "\\]")

        # 替换为本地路径
        if src in self.image_map:
            local_path = self.image_map[src]
            return f"\n\n![{safe_alt}]({local_path})\n\n"

        return f"\n\n![{safe_alt}]({src})\n\n"

    def convert_section(self, el, text, convert_as_inline=False, **kwargs):
        """section 当作段落处理，前后加空行确保分段"""
        text = text.strip()
        if not text:
            return ""
        return f"\n\n{text}\n\n"

    def convert_p(self, el, text, convert_as_inline=False, **kwargs):
        """段落标签，确保前后有空行"""
        text = text.strip()
        if not text:
            return ""
        return f"\n\n{text}\n\n"

    def convert_pre(self, el, text, convert_as_inline=False, **kwargs):
        """代码块"""
        code = el.find("code")
        content = code.get_text() if code else el.get_text()
        content = content.rstrip("\n")
        lang = ""
        if code and code.get("class"):
            classes = code.get("class", [])
            for cls in classes:
                if cls.startswith("language-") or cls.startswith("lang-"):
                    lang = cls.split("-", 1)[1]
                    break
        return f"\n\n```{lang}\n{content}\n```\n\n"


def convert_to_markdown(article: ArticleData, image_map: dict) -> str:
    """将文章转换为 Markdown"""

    # YAML frontmatter
    lines = [
        "---",
        f"title: {yaml_quote(article.raw_title)}",
        f"author: {yaml_quote(article.author)}",
    ]
    if article.original_author and article.original_author != article.author:
        lines.append(f"original_author: {yaml_quote(article.original_author)}")
    if article.publish_date:
        lines.append(f"date: {yaml_quote(article.publish_date)}")
    lines.append(f"source: {yaml_quote(article.url)}")
    lines.append(f"archived: {yaml_quote(datetime.now().strftime('%Y-%m-%d %H:%M'))}")
    lines.append("---")
    lines.append("")

    # 标题
    lines.append(f"# {article.raw_title}")
    lines.append("")

    # 元信息
    meta_parts = []
    if article.author:
        meta_parts.append(f"作者: {article.author}")
    if article.publish_date:
        meta_parts.append(f"日期: {article.publish_date}")
    if meta_parts:
        lines.append(f"> {' | '.join(meta_parts)}")
        lines.append("")

    # 正文转换
    converter = WeChatMarkdownConverter(
        image_map=image_map,
        heading_style="ATX",
        bullets="-",
        strong_em_symbol="*",
        wrap=False,
        strip=["script", "style"],
    )
    body = converter.convert(article.content_html)

    # 清理多余空行
    body = re.sub(r"\n{4,}", "\n\n\n", body)
    body = body.strip()
    lines.append(body)

    # 尾部
    lines.append("")
    lines.append("---")
    lines.append(f"*原文链接: [查看原文]({article.url})*")
    lines.append("")

    return "\n".join(lines)


# ─── 文件操作 ─────────────────────────────────────────────────────────────────

def save_article_to_disk(
    session: requests.Session,
    article: ArticleData,
    articles_dir: Path,
    force: bool = False,
    no_images: bool = False,
) -> str:
    """保存文章到磁盘，返回保存路径"""
    safe_title = article.safe_title

    # 检查同名冲突
    article_dir = articles_dir / safe_title
    if article_dir.exists():
        existing_md = article_dir / "index.md"
        if existing_md.exists() and not force:
            # 检查是否是同一篇文章
            content = existing_md.read_text(encoding="utf-8")
            if article.url in content:
                return ""  # 已存在，跳过
            else:
                # 不同文章同名，加哈希后缀
                safe_title = f"{safe_title}_{url_hash(article.url)}"
                article_dir = articles_dir / safe_title

    article_dir.mkdir(parents=True, exist_ok=True)

    # 下载图片
    image_map = {}
    if article.images and not no_images:
        images_dir = article_dir / "images"
        images_dir.mkdir(exist_ok=True)

        for i, img in enumerate(article.images):
            save_path = images_dir / img.local_filename
            success = download_image(session, img.original_url, save_path)
            img.downloaded = success

            if success:
                image_map[img.original_url] = f"images/{img.local_filename}"
            else:
                image_map[img.original_url] = img.original_url  # 保留原始 URL

            if i < len(article.images) - 1:
                time.sleep(IMAGE_DELAY)

    # 转换 Markdown
    markdown = convert_to_markdown(article, image_map)

    # 写入文件
    md_path = article_dir / "index.md"
    md_path.write_text(markdown, encoding="utf-8")

    return str(article_dir)


def generate_catalog(repo_root: Path, articles_dir: Path):
    """生成文章目录索引"""
    entries = []

    if not articles_dir.exists():
        return

    for article_dir in sorted(articles_dir.iterdir()):
        if not article_dir.is_dir():
            continue
        md_file = article_dir / "index.md"
        if not md_file.exists():
            continue

        content = md_file.read_text(encoding="utf-8")
        meta = parse_simple_frontmatter(content)

        title = meta.get("title", article_dir.name)
        author = meta.get("author", "")
        date = meta.get("date", "")
        try:
            rel_path = md_file.relative_to(repo_root).as_posix()
        except ValueError:
            rel_path = md_file.resolve().as_posix()
        cover_path = article_dir / "images" / "cover.png"
        try:
            cover_rel_path = cover_path.relative_to(repo_root).as_posix()
        except ValueError:
            cover_rel_path = cover_path.resolve().as_posix()
        excerpt = markdown_excerpt(content)
        group = catalog_group(article_dir.name)
        reviews = ["review.md"] if (article_dir / "review.md").is_file() else []

        entries.append((date, title, author, rel_path, cover_rel_path, excerpt, group, reviews, article_dir))

    entries.sort(key=lambda x: (group_order(x[6]), dir_order(x[8].name), x[8].name))

    # 生成网站目录页
    lines = [
        "# 文章目录",
        "",
        f"> 共 {len(entries)} 篇文章，更新于 {datetime.now().strftime('%Y-%m-%d')}",
        "",
    ]

    groups = ["合集 · 少年时代", "合集 · 大学四年", "合集 · 工作与考试", "散篇", "其他"]
    for group in groups:
        grouped_entries = [entry for entry in entries if entry[6] == group]
        if not grouped_entries:
            continue
        lines.append(f'<div class="article-cover-group">')
        lines.append(f'<h2>{html.escape(group)} <small>{len(grouped_entries)} 篇</small></h2>')
        lines.append('<div class="article-cover-list">')
        for date, title, author, rel_path, cover_rel_path, excerpt, _, reviews, article_dir in grouped_entries:
            safe_rel_path = markdown_link_target(rel_path)
            safe_cover_path = markdown_link_target(cover_rel_path)
            safe_title = html.escape(title)
            safe_date = html.escape(date)
            safe_excerpt = html.escape(excerpt)
            lines.append('<div class="article-cover-row">')
            lines.append(f'<a class="article-cover-thumb" href="#/{safe_rel_path}"><img src="{safe_cover_path}" alt="{safe_title} 封面"></a>')
            lines.append('<span class="article-cover-info">')
            review_links = []
            for filename in reviews:
                review_path = article_dir / filename
                try:
                    review_rel_path = review_path.relative_to(repo_root).as_posix()
                except ValueError:
                    review_rel_path = review_path.resolve().as_posix()
                review_links.append(f'<a href="#/{markdown_link_target(review_rel_path)}">评价</a>')
            action_links = [f'<a href="#/{safe_rel_path}">正文</a>', *review_links]
            edited_path = ai_edited_path(repo_root, article_dir.name)
            if edited_path.exists():
                try:
                    edited_rel_path = edited_path.relative_to(repo_root).as_posix()
                except ValueError:
                    edited_rel_path = edited_path.resolve().as_posix()
                action_links.append(f'<a href="#/{markdown_link_target(edited_rel_path)}">AI改稿</a>')
            lines.append('<span class="article-cover-head">')
            lines.append('<span class="article-cover-main">')
            lines.append(f'<a class="article-cover-title" href="#/{safe_rel_path}"><strong>{safe_title}</strong></a>')
            lines.append(f'<em>{safe_date}</em>')
            lines.append('</span>')
            if len(action_links) > 1:
                lines.append(f'<span class="article-cover-actions">{"".join(action_links)}</span>')
            lines.append('</span>')
            lines.append(f'<span class="article-cover-excerpt">{safe_excerpt}</span>')
            lines.append('</span>')
            lines.append('</div>')
        lines.append('</div>')
        lines.append('</div>')
        lines.append("")

    lines.append("<!-- 此文件由 save_article.py 自动更新，也可手动编辑 -->")
    lines.append("")

    catalog_path = repo_root / CATALOG_FILE.relative_to(REPO_ROOT)
    catalog_path.parent.mkdir(parents=True, exist_ok=True)
    catalog_path.write_text("\n".join(lines), encoding="utf-8")
    return len(entries)


# ─── 主流程 ───────────────────────────────────────────────────────────────────

def process_url(session: requests.Session, url: str, articles_dir: Path,
                force: bool = False, no_images: bool = False, verbose: bool = False) -> dict:
    """处理单个 URL，返回结果信息"""
    result = {"url": url, "status": "failed", "title": "", "path": "", "images": 0, "images_ok": 0}

    try:
        # 抓取
        html = fetch_article_html(session, url)

        # 解析
        article = parse_article(html, url)
        result["title"] = article.raw_title
        result["author"] = article.author
        result["date"] = article.publish_date
        result["images"] = len(article.images)

        print(f"      📄 {article.raw_title}")
        if article.author or article.publish_date:
            parts = []
            if article.author:
                parts.append(f"👤 {article.author}")
            if article.publish_date:
                parts.append(f"📅 {article.publish_date}")
            print(f"      {' | '.join(parts)}")

        # 检查是否已存在
        safe_title = article.safe_title
        existing_dir = articles_dir / safe_title
        existing_md = existing_dir / "index.md"
        if existing_md.exists() and not force:
            existing_content = existing_md.read_text(encoding="utf-8")
            if article.url in existing_content:
                print(f"      ⏭️  已保存过 (用 --force 覆盖)")
                result["status"] = "skipped"
                result["path"] = str(existing_dir)
                return result

        # 保存
        saved_path = save_article_to_disk(session, article, articles_dir, force, no_images)
        if saved_path:
            images_ok = sum(1 for img in article.images if img.downloaded)
            result["images_ok"] = images_ok
            if article.images:
                print(f"      🖼️  图片: {images_ok}/{len(article.images)} ✓")
            print(f"      ✅ 保存 → {Path(saved_path).name}/")
            result["status"] = "saved"
            result["path"] = saved_path
        else:
            print(f"      ⏭️  已保存过 (用 --force 覆盖)")
            result["status"] = "skipped"

    except FetchError as e:
        print(f"      ❌ 抓取失败: {e}")
        result["error"] = str(e)
    except ParseError as e:
        print(f"      ❌ 解析失败: {e}")
        result["error"] = str(e)
    except Exception as e:
        print(f"      ❌ 未知错误: {e}")
        if verbose:
            import traceback
            traceback.print_exc()
        result["error"] = str(e)

    return result


def main():
    parser = argparse.ArgumentParser(
        description="微信公众号文章归档工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python save_article.py https://mp.weixin.qq.com/s/xxxxx
  python save_article.py URL1 URL2 URL3
  python save_article.py -f urls.txt
  python save_article.py --catalog-only
        """
    )
    parser.add_argument("urls", nargs="*", help="微信公众号文章链接")
    parser.add_argument("-f", "--file", help="从文件读取链接 (每行一个)")
    parser.add_argument("--force", action="store_true", help="强制覆盖已保存的文章")
    parser.add_argument("--no-images", action="store_true", help="不下载图片")
    parser.add_argument("--catalog-only", action="store_true", help="仅重建目录索引")
    parser.add_argument("-v", "--verbose", action="store_true", help="显示详细信息")
    parser.add_argument("--articles-dir", default=str(ARTICLES_DIR), help="文章存储目录")

    args = parser.parse_args()
    articles_dir = Path(args.articles_dir)
    articles_dir.mkdir(parents=True, exist_ok=True)

    # 仅重建目录
    if args.catalog_only:
        count = generate_catalog(REPO_ROOT, articles_dir)
        print(f"📋 目录已更新: website/catalog.md ({count} 篇文章)")
        return

    # 收集 URL
    urls = list(args.urls)
    if args.file:
        file_path = Path(args.file)
        if not file_path.exists():
            print(f"❌ 文件不存在: {args.file}")
            sys.exit(1)
        with open(file_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    urls.append(line)

    if not urls:
        parser.print_help()
        sys.exit(1)

    # 去重
    seen = set()
    unique_urls = []
    for u in urls:
        if u not in seen:
            seen.add(u)
            unique_urls.append(u)
    urls = unique_urls

    print(f"\n处理 {len(urls)} 篇文章...\n")

    session = create_session()
    results = {"saved": 0, "skipped": 0, "failed": 0}

    for i, url in enumerate(urls, 1):
        print(f"[{i}/{len(urls)}] {url}")
        result = process_url(session, url, articles_dir, args.force, args.no_images, args.verbose)

        if result["status"] == "saved":
            results["saved"] += 1
        elif result["status"] == "skipped":
            results["skipped"] += 1
        else:
            results["failed"] += 1

        # 文章间延迟
        if i < len(urls):
            time.sleep(ARTICLE_DELAY)
        print()

    # 更新目录
    count = generate_catalog(REPO_ROOT, articles_dir)

    # 总结
    print("━" * 40)
    parts = []
    if results["saved"]:
        parts.append(f"{results['saved']} 篇已保存")
    if results["skipped"]:
        parts.append(f"{results['skipped']} 篇已跳过")
    if results["failed"]:
        parts.append(f"{results['failed']} 篇失败")
    print(f"📊 完成: {', '.join(parts)}")
    if count is not None:
        print(f"📋 目录已更新: website/catalog.md ({count} 篇文章)")


if __name__ == "__main__":
    main()
