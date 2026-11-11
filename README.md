# Shoplinker 三语参考站

现有中文 URL 保持不变；英文页面位于 `/en/`，韩文页面位于 `/ko/`。
每页右上方可切换语言，保留查询参数、章节锚点和滚动位置。
首页记住用户主动选择的语言；浏览器禁用存储时仍可正常使用语言链接。
普通版保留原目录；Under Armour 专属目录位于 `/ua/`，按历史 UA 目录提供 18 个页面。
页面右上方可在普通版与 Under Armour 版本之间切换；Under Armour 版本也提供三种语言。

## GitHub Pages

站点地址：https://pengxinchao.github.io/shoplinker-api-reference/

`.github/workflows/pages.yml` 直接部署 `dist/` 中已生成的静态页面。
更新文档后先运行下方构建和校验，再提交 `dist/`，push 到 `main` 即可自动发布。
也可在 GitHub 仓库的 **Actions → Deploy GitHub Pages → Run workflow** 手动部署。
仓库 **Settings → Pages → Source** 使用 **GitHub Actions**。
英文和韩文页面分别保留在站点目录下的 `en/`、`ko/`，支持仓库子路径部署。

## 内容来源与构建

- `tooling/source/`：2026-11-09 获取的 47 个官方文档原文快照。
- `tooling/translations.zh.json`：韩文原文到简体中文的说明文字字典。
- `tooling/translations.en.json`：韩文原文到英文的说明文字字典。
- `tooling/build.py`：使用同一份快照生成三语 HTML；不翻译协议字段或 XML 示例。
- `tooling/refresh-record.json`：本次更新范围及来源访问限制。
- `dist/`：静态部署目录，含共用资源和每种语言的 47 个文档页面。

```sh
python3 tooling/build.py
python3 -m unittest discover -s tooling/tests -v
node --check dist/mirror.js
python3 -m http.server 8786 --bind 127.0.0.1 --directory dist
```

构建需要本机已有的 Python `lxml` 和 `Pillow`。前端无新增依赖。
更新官方原文时需同时补齐字典；构建遇到未翻译韩文说明会失败。

## 本次接口文档更新

- 售后采集：响应表不再列出 `partner_product_id`、`order_seq`。
- SKU 新增：请求表不再列出 `ccategory_l`、`ccategory_m`、`ccategory_s`、`ccategory_d`。
- 库存同步：更新 `join_status` 的取值及联系 Shoplinker 开通商城库存同步的说明。
- 订单采集：`order_flag` 不再列出 `001`，同步文档行号。
- 价格同步：请求表不再列出 `market_price`，`join_status` 枚举不再列出 `003`；正文对 `003` 的备注仍按官方原文保留。
- 同步全部现有页面与导航，并补齐 11 个未收录的官方参考页面，其中一个为旧版页面。

官方响应包含登录、权限提示，但同时返回完整文档正文。本次按该正文更新，
不将文档差异解释为运行 API 一定删除字段或停用取值；未验证账户专属规范。
参考站只提供阅读和示例展示，业务测试、账号操作仍在官方网站完成。
