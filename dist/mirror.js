/* 本地页面只恢复阅读交互；真实测试和账号操作由官网完成，避免把参考快照当作业务客户端。 */
(() => {
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
    textarea.value = (window.shoplinkerSamples || [])[selector.selectedIndex - 1] || '暂无示例。';
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
  // 原介绍页的锚点使用 fullPage 名称；将名称对应到已存在的 section，保留导航含义。
  document.querySelectorAll('a[href^="#"]').forEach(anchor => anchor.addEventListener('click', event => {
    const hash = anchor.getAttribute('href').slice(1);
    const section = Array.from(document.querySelectorAll('[data-anchor]')).find(item => item.dataset.anchor === hash);
    if (section && !document.querySelector('#fullpage.fullpage-wrapper')) {event.preventDefault(); section.scrollIntoView({behavior:'smooth'}); history.replaceState(null,'','#'+hash);}
  }));
})();
