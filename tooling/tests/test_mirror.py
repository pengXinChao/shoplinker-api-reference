"""验证中文镜像保留接口契约与原始表格，不检查无意义的实现细节。"""
import json
import re
import sys
import unittest
from pathlib import Path
from urllib.parse import urlsplit
from lxml import html

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from build import render_page, output_path, local_url, localized_path, SITE


def protocol_tokens(cell):
    """必填徽标是本地化说明；协议校验只比较字段名和类型，避免把英文徽标误判为字段。"""
    copy = html.fromstring(html.tostring(cell))
    for badge in copy.xpath('.//span[contains(@class,"ico-css")]'):
        badge.drop_tree()
    return re.findall(r'[A-Za-z_][A-Za-z_0-9]*', copy.text_content())


class MirrorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pages = [json.loads(p.read_text()) for p in (ROOT / 'source').glob('*.json')]
        cls.dictionary = json.loads((ROOT / 'translations.zh.json').read_text())
        cls.routes = {p['url'].split('?')[0]: output_path(p['url']) for p in cls.pages}

    def test_source_count(self):
        self.assertGreaterEqual(len(self.pages), 46)

    def test_http_and_https_document_links_share_local_target(self):
        source = 'https://apiweb.shoplinker.co.kr/ShoplinkerApi/ver3/_customer.html'
        for scheme in ('http', 'https'):
            self.assertEqual(local_url(source.replace('https', scheme) + '#4rdPage', source,
                                      output_path(source), self.routes), '_customer.html#4rdPage')

    def test_overview_chapters_have_working_navigation(self):
        page = next(p for p in self.pages if '/_customer.html' in p['url'])
        tree = html.fromstring(render_page(page, self.dictionary, self.routes))
        chapters = tree.xpath('//*[@id="fullpage2"]/*[@data-anchor]/@data-anchor')
        self.assertEqual(chapters, [f'{i}rdPage' for i in range(18)])
        self.assertEqual(tree.xpath('//*[@id="menu2"]//a[starts-with(@href,"#")]/@href'),
                         ['#' + a for a in chapters])
        # 捕获后的分页容器需要重新计算布局，否则目录存在但不能切换正文。
        self.assertTrue(tree.xpath('//script[contains(@src,"jquery.fullPage.min.js")]'))
        self.assertTrue(any("'#fullpage2'" in (s.text or '') and '.fullpage(' in (s.text or '')
                            for s in tree.xpath('//script')))

    def test_tables_contracts_and_examples_preserved(self):
        for page in self.pages:
            with self.subTest(url=page['url']):
                original = html.fromstring(page['html'])
                mirrored = html.fromstring(render_page(page, self.dictionary, self.routes))
                ot, mt = original.xpath('//table'), mirrored.xpath('//table')
                self.assertEqual(len(ot), len(mt))
                for a, b in zip(ot, mt):
                    self.assertEqual([len(r.xpath('./td|./th')) for r in a.xpath('.//tr')],
                                     [len(r.xpath('./td|./th')) for r in b.xpath('.//tr')])
                    self.assertEqual(a.xpath('.//@rowspan|.//@colspan'), b.xpath('.//@rowspan|.//@colspan'))
                    # 参数名及类型位于第二、第三列，中文必填标识不影响协议标识符。
                    for ra, rb in zip(a.xpath('.//tbody/tr'), b.xpath('.//tbody/tr')):
                        ca, cb = ra.xpath('./td'), rb.xpath('./td')
                        if len(ca) == 6:
                            for i in (1, 2):
                                self.assertEqual(protocol_tokens(ca[i]), protocol_tokens(cb[i]))
                self.assertEqual([e.text_content() for e in original.xpath('//pre')],
                                 [e.text_content() for e in mirrored.xpath('//pre')])
                # 只对 URL 的韩语占位说明做翻译；真实端点路径和参数键必须完全一致。
                pattern = r'https://apiweb\.shoplinker\.co\.kr/ShoplinkerApi/[^\s<]*?\.(?:php|html)'
                self.assertEqual(re.findall(pattern, original.text_content()), re.findall(pattern, mirrored.text_content()))

    def test_translation_coverage(self):
        for page in self.pages:
            tree = html.fromstring(render_page(page, self.dictionary, self.routes))
            for e in tree.iter():
                if not isinstance(e.tag, str) or e.tag in ('script', 'style', 'pre', 'code') or e.get('data-protocol-example'):
                    continue
                if any(a.tag in ('pre', 'code', 'script', 'style') or a.get('class') == 'language-switch' for a in e.iterancestors()):
                    continue
                for value in [e.text, e.tail, e.get('title'), e.get('alt'), e.get('placeholder')]:
                    self.assertFalse(value and re.search('[가-힣]', value), (page['url'], value))

    def test_internal_navigation_localized(self):
        known_paths = {urlsplit(url).path for url in self.routes}
        for page in self.pages:
            tree = html.fromstring(render_page(page, self.dictionary, self.routes))
            for href in tree.xpath('//a/@href|//*[@data-open-url]/@data-open-url'):
                self.assertFalse(href.startswith('javascript:'), href)
                target = urlsplit(href)
                self.assertFalse(target.hostname == 'apiweb.shoplinker.co.kr'
                                 and target.path in known_paths, (page['url'], href))

    def test_all_languages_preserve_contracts_and_examples(self):
        # 校验构建结果而非翻译实现，防止语言切换意外改动协议或丢失页面。
        for page in self.pages:
            source = html.fromstring(page['html'])
            for language in ['zh', 'en', 'ko']:
                with self.subTest(url=page['url'], language=language):
                    target = SITE / localized_path(page['url'], language)
                    translated = html.fromstring(target.read_text())
                    self.assertEqual([p.text_content() for p in source.xpath('//pre')],
                                     [p.text_content() for p in translated.xpath('//pre')])
                    original_rows = source.xpath('//table//tr')
                    translated_rows = translated.xpath('//table//tr')
                    self.assertEqual(len(original_rows), len(translated_rows))
                    for a, b in zip(original_rows, translated_rows):
                        ca, cb = a.xpath('./td'), b.xpath('./td')
                        if len(ca) == 6:
                            for i in [1, 2]:
                                self.assertEqual(protocol_tokens(ca[i]), protocol_tokens(cb[i]))
                    links = translated.xpath('//nav[@class="language-switch"]/a')
                    self.assertEqual([a.get('data-language') for a in links], ['zh', 'en', 'ko'])
                    for a in links:
                        self.assertTrue((target.parent / a.get('href')).resolve().is_file())
                    self.assertEqual(translated.xpath('//nav[@class="language-switch"]/a[@aria-current]/@data-language'), [language])

    def test_english_has_no_untranslated_prose(self):
        for page in self.pages:
            tree = html.fromstring((SITE / localized_path(page['url'], 'en')).read_text())
            for e in tree.iter():
                if not isinstance(e.tag, str) or e.tag in ('script', 'style', 'pre', 'code') or e.get('data-protocol-example'):
                    continue
                if any(a.tag in ('pre', 'code', 'script', 'style', 'nav') for a in e.iterancestors()):
                    continue
                for value in [e.text, e.tail, e.get('title'), e.get('alt'), e.get('placeholder')]:
                    self.assertFalse(value and re.search('[가-힣\u4e00-\u9fff]', value), (page['url'], value))


if __name__ == '__main__':
    unittest.main()
