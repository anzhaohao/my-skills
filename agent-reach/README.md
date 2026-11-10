Agent Reach 用于只读搜索和读取多个平台的内容，以及管理已有渠道。

# 本机存放方式

- 真实文件只维护在 `E:\software\skills-manager\skills\agent-reach`。
- 原有客户端与共享技能目录通过链接读取这里，原先没有部署它的客户端不会额外获得它。
- 中央库的当前入口、认证边界和已有参考文档继续保留。
- Hana 的原有触发词、调研路由与全部分类参考文档保存在 `references/local-adapters/hana-original`；入口明确在 Hana 工作流中按需读取。
- 共享目录原有社交平台说明保存在 `references/local-adapters/shared-social-original.md`，方便核对和回溯定制。
- 原有参考文档有旧版命令；实际调用前按当前渠道能力核实，不因本次归并自动更新后端或改登录态。

# 最近维护

- 2026-11-10：接管 `.agents` 与 Hana 中的独立副本，保留原有定制，并统一从 E 盘部署。原件另存于本次其他客户端技能整理备份。
