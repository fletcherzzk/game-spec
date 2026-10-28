from html.parser import HTMLParser
from pathlib import Path
import unittest


class Assets(HTMLParser):
    def __init__(self):
        super().__init__()
        self.urls = []
        self.ids = set()

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if 'id' in attrs:
            self.ids.add(attrs['id'])
        if tag == 'script':
            self.urls.append(attrs['src'])
        if tag == 'link' and attrs.get('rel') == 'stylesheet':
            self.urls.append(attrs['href'])


class StaticFrontendTests(unittest.TestCase):
    def test_standalone_html_has_both_boards_and_resolvable_relative_assets(self):
        root = Path(__file__).resolve().parents[2] / 'frontend'
        html = (root / 'index.html').read_text(encoding='utf-8')
        self.assertNotIn('{{', html)
        self.assertNotIn('{%', html)
        parser = Assets()
        parser.feed(html)
        self.assertTrue({'board-a', 'board-b', 'join-form'}.issubset(parser.ids))
        for url in parser.urls:
            with self.subTest(url=url):
                self.assertTrue(url.startswith('./'))
                self.assertTrue((root / url).is_file())
        self.assertLess(parser.urls.index('./config.js'), parser.urls.index('./assets/app.js'))
