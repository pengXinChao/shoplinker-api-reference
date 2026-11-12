"""从同一份官方快照构建三语参考站，保留协议字段、表格和 XML 示例。"""
import json
import hashlib
import posixpath
import re
from pathlib import Path
from urllib.parse import urljoin, urlsplit
from lxml import etree, html

ROOT = Path(__file__).resolve().parent
SITE = ROOT.parent / 'dist'
KOREAN = re.compile('[가-힣]')
PROTECTED = {'script', 'style', 'pre', 'code'}


def output_path(url):
    """返回站内静态文件相对路径；无扩展名的官网介绍页使用 .html。"""
    path = urlsplit(url).path.lstrip('/')
    return path if Path(path).suffix else path.rstrip('/') + '.html'


def local_url(value, source_url, destination, routes, resource=False):
    """把已采集页面或本地资源改为相对链接，保留查询与锚点；未采集目标回到官网。"""
    if not value or value.startswith(('data:', 'mailto:', 'tel:', '#', 'about:')):
        return value
    absolute = urljoin(source_url, value)
    split = urlsplit(absolute)
    key = absolute.split('?')[0].split('#')[0]
    target = routes.get(key)
    # 官网同时使用 HTTP 与 HTTPS 导航；按相同主机与路径匹配，避免已复刻页面跳回韩文站。
    if not target and split.scheme == 'http':
        target = routes.get(urlsplit(key)._replace(scheme='https').geturl())
    # 官方 ERP-Dev 拼错 SkuInfo 文件名；中文入口复用已核验的 ERP 页面。
    if split.path.endswith('/SkuInifo.html'):
        target = routes.get('https://apiweb.shoplinker.co.kr/ShoplinkerApi/ver3/Product/SkuInfo.html')
    if resource and (SITE / split.path.lstrip('/')).is_file():
        target = split.path.lstrip('/')
    if target:
        relative = posixpath.relpath(target, posixpath.dirname(destination) or '.')
        return relative + ('?' + split.query if split.query else '') + ('#' + split.fragment if split.fragment else '')
    return absolute


def translate_text(value, dictionary):
    """保留空白边界以免改变行内节点拼接；缺译直接报错，避免交付混合正文。"""
    if not value or (not KOREAN.search(value) and value.strip() not in dictionary):
        return value
    key = value.strip()
    if key not in dictionary:
        raise ValueError('未翻译文本：' + key)
    leading = value[:len(value) - len(value.lstrip())]
    trailing = value[len(value.rstrip()):]
    return leading + dictionary[key] + trailing


def render_page(page, dictionary, routes, language='zh', prefix='', show_version_switch=False):
    """按指定语言生成参考页；路由保留语言，业务提交仍交由官方网站处理。"""
    tree = html.fromstring(page['html'])
    destination = localized_path(page['url'], language, prefix)
    is_public = '/service/api' in page['url']
    tree.set('lang', 'zh-CN' if language == 'zh' else language)
    for e in list(tree.iter()):
        if not isinstance(e.tag, str):
            continue
        if e.tag in ('script', 'noscript'):
            e.drop_tree()
            continue
        # XML 示例及 code 片段逐字保留，包括大小写、官方拼写和韩语示例数据。
        protected = e.tag in PROTECTED or any(a.tag in PROTECTED for a in e.iterancestors())
        if e.text and e.text.strip().startswith('-> 2<**>1_전기'):
            # 认证编号示例中的韩语是协议示例值，不能作为说明文字翻译。
            protected = True
            e.set('data-protocol-example', 'true')
        if not protected and language != 'ko':
            e.text = translate_text(e.text, dictionary)
            e.tail = translate_text(e.tail, dictionary)
            for attribute in ('title', 'alt', 'placeholder'):
                if e.get(attribute):
                    e.set(attribute, translate_text(e.get(attribute), dictionary))
            if e.tag == 'input' and e.get('type', '').lower() in ('button', 'submit'):
                e.set('value', translate_text(e.get('value'), dictionary) or '')
        onclick = e.get('onclick', '')
        if 'toggleUnitPrice' in onclick:
            e.set('data-local-action', 'unit-price')
        elif 'xmlget' in onclick:
            e.set('data-local-action', 'xml-sample')
        elif 'selectR' in onclick:
            e.set('data-local-action', 'xml-mode')
        elif 'ok()' in onclick:
            e.set('data-local-action', 'official-sandbox')
        elif 'acheck' in onclick or 'logOut' in onclick:
            e.set('data-local-action', 'official-login')
        elif 'window.open' in onclick:
            match = re.search(r'window\.open\([\'"]([^\'"]+)', onclick)
            if match:
                e.set('data-open-url', local_url(match.group(1), page['url'], destination, routes))
        for attribute in list(e.attrib):
            if attribute.lower().startswith('on'):
                del e.attrib[attribute]
        if e.tag == 'form':
            e.set('action', '#')
            e.set('data-local-form', 'true')
        if e.tag == 'input' and e.get('type') == 'password':
            e.set('value', '')
        if e.tag == 'a' and e.get('href'):
            value = e.get('href')
            e.set('href', '#' if value.startswith('javascript:') else local_url(value, page['url'], destination, routes))
        if e.tag in ('img', 'iframe', 'link', 'source'):
            attribute = 'href' if e.tag == 'link' else 'src'
            value = e.get(attribute)
            if e.tag == 'iframe':
                e.set('src', 'about:blank')
            elif value:
                e.set(attribute, local_url(value, page['url'], destination, routes, resource=True))
            # 1px 追踪图片与脚本不属于参考页面展示，不能在离线镜像继续执行。
            if e.tag == 'img' and any(s in (value or '') for s in ('logger.co.kr', 'facebook.com', 'ptbwa.com', 'doubleclick.net')):
                e.drop_tree()
        if e.tag == 'meta' and e.get('charset'):
            e.set('charset', 'utf-8')
        if e.tag == 'meta' and e.get('http-equiv', '').lower() == 'content-type':
            e.set('content', 'text/html; charset=utf-8')
    head, body = tree.find('head'), tree.find('body')
    if head is None:
        head = etree.Element('head'); tree.insert(0, head)
    etree.SubElement(head, 'meta', charset='utf-8')
    etree.SubElement(head, 'meta', name='viewport', content='width=device-width, initial-scale=1')
    # 三语页面共享官方快照；切换仅替换语言路径，查询条件和阅读位置由展示脚本保留。
    switch = etree.Element('nav', attrib={'class': 'language-switch', 'aria-label': {
        'zh': '页面语言', 'en': 'Page language', 'ko': '페이지 언어'}[language]})
    for code, label in [('zh', '中文'), ('en', 'English'), ('ko', '한국어')]:
        target = posixpath.relpath(localized_path(page['url'], code, prefix), posixpath.dirname(destination) or '.')
        link = etree.SubElement(switch, 'a', href=target, lang='zh-CN' if code == 'zh' else code,
                                attrib={'data-language': code, 'hreflang': 'zh-CN' if code == 'zh' else code})
        link.text = label
        if code == language:
            link.set('aria-current', 'page')
        etree.SubElement(head, 'link', rel='alternate', hreflang='zh-CN' if code == 'zh' else code, href=target)
    body.insert(0, switch)
    # 只在两套版本都有对应文档的 API 页提供切换，避免总览或通用专属页跳入不存在的 UA 路径。
    if show_version_switch:
        version_switch = etree.Element('nav', attrib={'class': 'version-switch', 'aria-label': {
            'zh': '文档版本', 'en': 'Document version', 'ko': '문서 버전'}[language]})
        versions = [('Under Armour', 'ua/', {'zh': 'Under Armour', 'en': 'Under Armour', 'ko': 'Under Armour'}[language]),
                    ('普通版', '', {'zh': '普通版', 'en': 'General', 'ko': '일반판'}[language])]
        for _, target_prefix, label in versions:
            target = posixpath.relpath(localized_path(page['url'], language, target_prefix), posixpath.dirname(destination) or '.')
            link = etree.SubElement(version_switch, 'a', href=target,
                                    attrib={'data-version': target_prefix or 'general'})
            link.text = label
            if target_prefix == prefix:
                link.set('aria-current', 'page')
        menu_title = tree.xpath('//*[contains(concat(" ", normalize-space(@class), " "), " menu-title ")]')
        if menu_title:
            menu_title[0].addprevious(version_switch)
        else:
            body.insert(1, version_switch)
    if not is_public:
        for name in ('jquery-1.8.1.min.js', 'jquery.color-2.1.2.min.js', 'common.js'):
            etree.SubElement(body, 'script', src=local_url('/ShoplinkerApi/ver3/js/' + name, page['url'], destination, routes, True))
    if '/introduce.html' in page['url'] or '/_customer.html' in page['url']:
        # fullPage 的动态包装不能重复初始化；先还原原始节点，再用官方展示库重新计算高度。
        for cell in tree.xpath('//*[contains(concat(" ", @class, " "), " fp-tableCell ")]'):
            cell.drop_tag()
        for section in tree.xpath('//*[@id="fullpage" or @id="fullpage2"]|//*[contains(concat(" ", @class, " "), " fp-section ")]'):
            section.attrib.pop('style', None)
            section.set('class', 'section' if section.get('data-anchor') else '')
        tree.attrib.pop('style', None)
        for name in ('jquery.easing.1.3.min.js', 'jquery.fullPage.min.js'):
            etree.SubElement(body, 'script', src=local_url('/ShoplinkerApi/ver3/js/' + name, page['url'], destination, routes, True))
        init = etree.SubElement(body, 'script')
        overview = '/_customer.html' in page['url']
        container, menu = ('#fullpage2', '#menu2') if overview else ('#fullpage', '#menu')
        anchors = [f'{i}rdPage' for i in range(18)] if overview else ['firstPage', 'secondPage', '3rdPage']
        # 原始 HTML 尚未执行 fullPage，先声明锚点，确保目录和语言切换使用同一章节标识。
        for section, anchor in zip(tree.xpath('//*[@id="' + container[1:] + '"]/*'), anchors):
            section.set('data-anchor', anchor)
            section.set('class', 'section')
        init.text = ("/* 使用官方展示库恢复介绍和总览分页；保留官方锚点及循环规则。 */ "
                     "jQuery(function(){jQuery('" + container + "').fullpage({anchors:" + json.dumps(anchors) +
                     ",menu:'" + menu + "',easingcss3:'cubic-bezier(0.175, 0.885, 0.320, 1.275)',loopTop:true,loopBottom:true});});")

    # 按内容更新展示资源版本，避免浏览器沿用上次部署的中文样式及交互脚本。
    def display_asset(name):
        revision = hashlib.sha256((SITE / name).read_bytes()).hexdigest()[:12]
        return local_url('/' + name + '?v=' + revision, page['url'], destination, routes, True)

    etree.SubElement(head, 'link', rel='stylesheet', href=display_asset('mirror.css'))
    if '/xml.html' in page['url']:
        etree.SubElement(body, 'script', src=display_asset('samples.js'))
    etree.SubElement(body, 'script', src=display_asset('mirror.js'))
    # 以等比例 HTML 标签覆盖说明文字，图形、商标与原始图片文件保持原样。
    labels = {
        'img_apiint_1.jpg': [(35, 106, 115, 25, '自有商城')],
        'img_customer0.jpg': [(35, 108, 116, 25, '自有商城')],
        'img_customer1.jpg': [(35, 99, 116, 24, '自有商城')],
        'img_customer2.jpg': [(48, 132, 91, 20, '自有商城'), (79, 24, 62, 21, '市价'), (79, 45, 62, 21, '售价'), (79, 67, 62, 20, '供货价')],
        'img_customer3.jpg': [(49, 132, 89, 21, '自有商城')],
        'img_customer4.jpg': [(35, 108, 116, 25, '自有商城'), (593, 129, 51, 38, '多家商城')],
        'img_customer5.jpg': [(48, 142, 90, 21, '自有商城')],
        'img_customer6.jpg': [(35, 98, 114, 25, '自有商城'), (505, 38, 125, 21, '选择销售期限'), (505, 59, 125, 22, '15天～90天')],
        'img_customer7.jpg': [(48, 132, 91, 22, '自有商城')],
        'img_customer8.jpg': [(49, 132, 92, 21, '自有商城')],
        'img_customer10.jpg': [(35, 108, 116, 25, '自有商城')],
        'img_customer11.jpg': [(35, 100, 114, 24, '自有商城')],
        'img_customer12.jpg': [(35, 100, 114, 24, '自有商城')],
        'img_customer2_1.jpg': [(35, 99, 113, 23, '自有商城'), (595, 130, 50, 35, '多家商城')],
        'img_customer2_2.jpg': [(35, 99, 113, 23, '自有商城'), (577, 128, 50, 35, '多家商城')],
        'img_customer2_3.jpg': [(35, 98, 113, 23, '自有商城'), (577, 128, 50, 35, '多家商城')],
        'img_customer2_4.jpg': [(35, 99, 114, 24, '自有商城')],
        'img_customer2_5.jpg': [(35, 99, 114, 23, '自有商城')],
        'img_customer2_6.jpg': [(35, 99, 114, 23, '自有商城')],
    }
    english_labels = {'自有商城': 'Own store', '市价': 'List price', '售价': 'Sale price',
                      '供货价': 'Supply price', '多家商城': 'Marketplaces',
                      '选择销售期限': 'Sales period', '15天～90天': '15–90 days'}
    for img in tree.xpath('//img[@src]') if language != 'ko' else []:
        filename = Path(urlsplit(img.get('src')).path).name
        if filename not in labels:
            continue
        # 图片尺寸仅用于把标签坐标转换为百分比，响应式缩放后仍与原图对应。
        from PIL import Image
        local_image = (SITE / posixpath.dirname(destination) / urlsplit(img.get('src')).path).resolve()
        with Image.open(local_image) as picture:
            width, height = picture.size
        wrapper = etree.Element('span', attrib={'class': 'zh-image-label'})
        img.addprevious(wrapper); wrapper.append(img)
        for x, y, w, h, text in labels[filename]:
            label = etree.SubElement(wrapper, 'span')
            label.set('style', f'left:{100*x/width}%;top:{100*y/height}%;width:{100*w/width}%;height:{100*h/height}%;')
            label.text = english_labels[text] if language == 'en' else text
    if language != 'ko':
        for img in tree.xpath('//img[contains(@src,"img_api05.png")]'):
            img.set('src', local_url('/images/new/service/img_api05_' + language + '.svg', page['url'], destination, routes, True))
    # 动态页面采集后的动画状态不应冻结在离线页面；恢复原布局中的可见内容。
    if is_public:
        tree.set('data-mirror-public', 'true')
    # 官方模板混用空格和制表符；只整理示例块外的缩进，协议示例内容逐字保留。
    for element in tree.iter():
        if not isinstance(element.tag, str) or element.tag in PROTECTED or any(a.tag in PROTECTED for a in element.iterancestors()):
            continue
        for field in ['text', 'tail']:
            value = getattr(element, field)
            if value and '\n' in value:
                setattr(element, field, '\n'.join(
                    re.sub(r'^[ \t]+', lambda m: m[0].expandtabs(4), line).rstrip(' \t')
                    for line in value.split('\n')))
    return '<!DOCTYPE html>\n' + html.tostring(tree, encoding='unicode')


def localized_path(url, language, prefix=''):
    """保留既有中文 URL，英文与韩文使用独立前缀，确保旧链接继续有效。"""
    return prefix + (language + '/' if language != 'zh' else '') + output_path(url)


def main():
    """离线构建三语页面并校验缺译，不访问真实业务 API。"""
    pages = [json.loads(p.read_text()) for p in sorted((ROOT / 'source').glob('*.json'))]
    ua_pages = [json.loads(p.read_text()) for p in sorted((ROOT / 'source-ua').glob('*.json'))]
    ua_urls = {page['url'].split('?')[0] for page in ua_pages}
    report = []
    for language in ['zh', 'en', 'ko']:
        dictionary = json.loads((ROOT / ('translations.' + language + '.json')).read_text()) if language != 'ko' else {}
        routes = {p['url'].split('?')[0]: localized_path(p['url'], language) for p in pages}
        for page in pages:
            target = SITE / localized_path(page['url'], language)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(render_page(page, dictionary, routes, language,
                                          show_version_switch=page['url'].split('?')[0] in ua_urls), encoding='utf-8')
            original = html.fromstring(page['html'])
            report.append({'source': page['url'], 'language': language, 'local': localized_path(page['url'], language),
                           'tables': len(original.xpath('//table')), 'examples': len(original.xpath('//pre'))})
        entry = 'ShoplinkerApi/ver3/Product/Attribute_Info.html?spec_135=ov&guTwo=t'
        title = {'zh': 'Shoplinker 中文参考', 'en': 'Shoplinker API Reference', 'ko': 'Shoplinker API 참고 문서'}[language]
        index = SITE / (language + '/' if language != 'zh' else '') / 'index.html'
        # 首页记住语言偏好；禁用 JavaScript 时仍可通过链接进入相应语言。
        script = ("let language='zh';try{language=localStorage.getItem('shoplinker-language')||'zh'}catch(e){};"
                  "location.replace((['en','ko'].includes(language)?language+'/':'')+" + json.dumps(entry) + ");") if language == 'zh' else 'location.replace(' + json.dumps(entry) + ');'
        index_target = ('ua/' if language == 'zh' else '../ua/' + language + '/') + entry
        index_script = "location.replace(" + json.dumps(index_target) + ");"
        index.write_text('<!doctype html><html lang="' + ('zh-CN' if language == 'zh' else language) + '"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta http-equiv="refresh" content="0;url=' + index_target + '"><title>' + title + '</title></head><body><script>' + index_script + '</script></body></html>')
        ua_routes = dict(routes)
        for page in ua_pages:
            ua_routes[page['url'].split('?')[0]] = localized_path(page['url'], language, 'ua/')
        for page in ua_pages:
            target = SITE / localized_path(page['url'], language, 'ua/')
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(render_page(page, dictionary, ua_routes, language, 'ua/',
                                          show_version_switch=True), encoding='utf-8')
        ua_page = next(p for p in ua_pages if '/Product/Attribute_Info.html?' in p['url'])
        ua_entry = output_path(ua_page['url']) + '?' + urlsplit(ua_page['url']).query
        ua_index = SITE / 'ua' / (language + '/' if language != 'zh' else '') / 'index.html'
        ua_index.parent.mkdir(parents=True, exist_ok=True)
        ua_title = {'zh': 'Shoplinker Under Armour 中文参考', 'en': 'Shoplinker Under Armour API Reference', 'ko': 'Shoplinker Under Armour API 참고 문서'}[language]
        ua_index.write_text('<!doctype html><html lang="' + ('zh-CN' if language == 'zh' else language) + '"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta http-equiv="refresh" content="0;url=' + ua_entry + '"><title>' + ua_title + '</title></head><body><script>location.replace(' + json.dumps(ua_entry) + ');</script></body></html>')
    (ROOT / 'coverage.json').write_text(json.dumps(report, ensure_ascii=False, indent=2))
    print('已生成普通版与 Under Armour 三语页面：', len(report), '；普通版每种语言：', len(pages), '；UA 每种语言：', len(ua_pages))


if __name__ == '__main__':
    main()
