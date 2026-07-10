import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

from bs4 import BeautifulSoup

from scripts.save_article import ArticleData, clean_content_html, convert_to_markdown
from scripts.save_article import download_image, generate_catalog, parse_simple_frontmatter
from scripts.save_article import yaml_quote


class SaveArticleTests(unittest.TestCase):
    def test_frontmatter_values_are_escaped_and_read_back(self):
        article = ArticleData(
            url="https://example.test/a?x=1",
            raw_title='标题 "A"',
            author='作者\\名',
            publish_date="2026-06-24",
            content_html="<p>正文</p>",
        )

        markdown = convert_to_markdown(article, {})
        meta = parse_simple_frontmatter(markdown)

        self.assertIn('title: "标题 \\"A\\""', markdown)
        self.assertEqual(meta["title"], article.raw_title)
        self.assertEqual(meta["author"], article.author)

    def test_yaml_quote_handles_newlines(self):
        self.assertEqual(yaml_quote('a\nb"c'), '"a\\nb\\"c"')

    def test_monospace_code_is_not_reparsed_as_html(self):
        soup = BeautifulSoup(
            '<div><span style="font-family: Consolas">if a < b && c > d</span></div>',
            "lxml",
        )
        elem = soup.find("div")

        clean_content_html(elem)

        code = elem.find("code")
        self.assertIsNotNone(code)
        self.assertEqual(code.get_text(), "if a < b && c > d")

    def test_catalog_uses_actual_relative_article_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            articles = root / "custom_articles"
            article_dir = articles / "标题 A"
            article_dir.mkdir(parents=True)
            (article_dir / "index.md").write_text(
                "---\n"
                "title: \"标题 A\"\n"
                "author: \"作者|名\"\n"
                "date: \"2026-06-24\"\n"
                "---\n",
                encoding="utf-8",
            )
            edited_dir = root / "ai-edited-articles" / "其他" / "标题 A"
            edited_dir.mkdir(parents=True)
            (edited_dir / "index.md").write_text("# 标题 A 改稿\n", encoding="utf-8")
            (article_dir / "review.md").write_text("# 当前评价\n", encoding="utf-8")
            (article_dir / "review_v2.md").write_text("# 历史评价\n", encoding="utf-8")

            generate_catalog(root, articles)

            self.assertFalse((root / "catalog.md").exists())
            catalog = (root / "website" / "catalog.md").read_text(encoding="utf-8")
            self.assertIn("custom_articles/", catalog)
            self.assertIn("%E6%A0%87%E9%A2%98%20A/index.md", catalog)
            self.assertIn("article-cover-row", catalog)
            self.assertIn("其他 <small>1 篇</small>", catalog)
            self.assertIn("标题 A 封面", catalog)
            self.assertIn("ai-edited-articles/%E5%85%B6%E4%BB%96/%E6%A0%87%E9%A2%98%20A/index.md", catalog)
            self.assertIn("AI改稿", catalog)
            self.assertIn("review.md", catalog)
            self.assertIn(">评价</a>", catalog)
            self.assertNotIn("review_v2.md", catalog)
            self.assertNotIn("评价 v2", catalog)

    def test_download_image_rejects_html_response(self):
        session = Mock()
        response = Mock()
        response.headers = {"Content-Type": "text/html; charset=utf-8"}
        response.raise_for_status.return_value = None
        session.get.return_value = response

        with tempfile.TemporaryDirectory() as tmp:
            saved = download_image(session, "https://example.test/not-image", Path(tmp) / "x.jpg")

        self.assertFalse(saved)


if __name__ == "__main__":
    unittest.main()
