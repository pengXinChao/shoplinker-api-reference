/* 本地页面只恢复阅读交互；真实测试和账号操作由官网完成，避免把参考快照当作业务客户端。 */
(() => {
  const language = document.documentElement.lang.startsWith('zh') ? 'zh' : document.documentElement.lang;
  // 存储可能被浏览器禁用，语言切换和站内链接仍应正常工作。
  document.querySelectorAll('[data-language]').forEach(link => {
    const target = new URL(link.href);
    target.search = location.search; target.hash = location.hash;
    link.href = target.href;
    link.addEventListener('click', () => {
      try {
        localStorage.setItem('shoplinker-language', link.dataset.language);
        sessionStorage.setItem('shoplinker-scroll:' + target.pathname, String(window.scrollY));
      } catch (e) { /* 浏览器禁用存储时使用链接中的语言路径。 */ }
    });
  });
  try {
    const key = 'shoplinker-scroll:' + location.pathname;
    const scroll = sessionStorage.getItem(key);
    if (scroll !== null) {
      sessionStorage.removeItem(key);
      window.addEventListener('load', () => requestAnimationFrame(() => window.scrollTo(0, Number(scroll))));
    }
  } catch (e) { /* 未启用存储时保留浏览器默认的锚点定位。 */ }
  const officialSandbox = 'https://apiweb.shoplinker.co.kr/ShoplinkerApi/ver3/xml.html?type_gubun=003';
  const officialHome = 'https://apiweb.shoplinker.co.kr/ShoplinkerApi/ver3/index.html';
  const byId = id => document.getElementById(id);
  const show = (id, visible) => { const node = byId(id); if (node) node.style.display = visible ? '' : 'none'; };
  function selectMode() {
    const selected = document.querySelector('input[name="select"]:checked');
    if (!selected) return;
    const mode = selected.value;
    show('urlName', mode !== 'sample'); show('urlNameXml', mode === 'sample');
    show('xmlSend', mode !== 'urlXml'); show('xmlUrl2', mode === 'urlXml'); show('xmlB', mode === 'sample');
  }
  function loadSample() {
    const selector = byId('urlNameXml');
    const textarea = byId('xmlSend');
    if (!selector || !textarea) return;
    textarea.value = (window.shoplinkerSamples || [])[selector.selectedIndex - 1] ||
      ({zh: '暂无示例。', en: 'No sample available.', ko: '예제가 없습니다.'}[language]);
  }
  document.querySelectorAll('form').forEach(form => form.addEventListener('submit', e => {
    e.preventDefault(); window.open(byId('xmlSend') ? officialSandbox : officialHome, '_blank', 'noopener');
  }));
  document.addEventListener('click', event => {
    const node = event.target.closest('[data-local-action], [data-open-url], .bn-top a');
    if (!node) return;
    const action = node.dataset.localAction;
    if (node.dataset.openUrl) {event.preventDefault(); window.open(node.dataset.openUrl, '_blank', 'noopener');}
    if (action === 'xml-mode') selectMode();
    if (action === 'xml-sample') {event.preventDefault(); loadSample();}
    if (action === 'official-sandbox' || action === 'official-login') {
      event.preventDefault(); window.open(action === 'official-sandbox' ? officialSandbox : officialHome, '_blank', 'noopener');
    }
    if (action === 'unit-price') {
      const rows = Array.from(document.querySelectorAll('.unit_price_child'));
      const isOpen = rows.some(row => row.style.display !== 'none');
      rows.forEach(row => row.style.display = isOpen ? 'none' : 'table-row');
      const arrow = byId('unit_price_arrow'); if (arrow) arrow.textContent = isOpen ? '▼' : '▲';
    }
    if (node.matches('.bn-top a')) {event.preventDefault(); window.scrollTo({top:0,behavior:'smooth'});}
  });
  selectMode();
  // 官网 FAQ 使用高度动画和 open 类，按相同规则一次只展开一个答案。
  const faqItems = Array.from(document.querySelectorAll('.cs_faq .cb_wrap > ul > li'));
  faqItems.forEach(item => item.addEventListener('click', () => {
    const isOpen = item.classList.contains('open');
    faqItems.forEach(other => {
      other.classList.remove('open');
      const paragraph = other.querySelector('p'); if (paragraph) paragraph.style.height = '0px';
    });
    const paragraph = item.querySelector('p');
    if (!isOpen && paragraph) {
      item.classList.add('open'); paragraph.style.height = paragraph.scrollHeight + 'px';
    }
  }));
  // 官方分页已初始化时由 fullPage 接管锚点，避免总览页被普通滚动逻辑打断。
  document.querySelectorAll('a[href^="#"]').forEach(anchor => anchor.addEventListener('click', event => {
    const hash = anchor.getAttribute('href').slice(1);
    const section = Array.from(document.querySelectorAll('[data-anchor]')).find(item => item.dataset.anchor === hash);
    if (section && !section.closest('.fullpage-wrapper')) {event.preventDefault(); section.scrollIntoView({behavior:'smooth'}); history.replaceState(null,'','#'+hash);}
  }));
})();
