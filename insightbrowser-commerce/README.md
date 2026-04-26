# 🏪 InsightBrowser — Commerce Bridge (端口 7004)

> 🏢 [InsightLabs](https://github.com/chenshuai9101/insightbrowser) — Agent 原生互联网基础设施  
> MIT 开源 · 免费

商家转换器。传统商家贴 URL → 自动生成 agent.json → 注册到 Agent 互联网。

**不需要懂技术。不需要懂 agent.json。贴链接就行。**

## 流程

```
商家填写店铺信息 + URL
       ↓
InsightLens 提取网页内容
       ↓
InsightSee 分析行业/关键词
       ↓
自动生成 agent.json（含能力、产品列表、定价）
       ↓
自动注册到 Registry + Hosting
       ↓
Agent 可以发现你的店铺了 🎉
```

## 使用

打开浏览器访问 `http://localhost:7004`

填写：
- 店铺名称
- 官网/商品链接
- 行业分类
- 店铺描述

点击确认 → 自动完成入驻。

## API

| 端点 | 方法 | 说明 |
|:----|:---:|:----|
| `/` | GET | 商家入驻表单页 |
| `/convert` | POST | 提交商家信息（自动转换+注册） |
| `/sites/{id}` | GET | 查看已入驻商家详情 |
| `/health` | GET | 健康检查 |

## 依赖

```bash
pip install -r requirements.txt
python3 main.py
```

---

**Made with ❤️ by InsightLabs**

<p align="center">
  <img src="https://raw.githubusercontent.com/chenshuai9101/insightbrowser/main/assets/wechat_pay.jpg" width="150" alt="微信" />
  <img src="https://raw.githubusercontent.com/chenshuai9101/insightbrowser/main/assets/alipay.jpg" width="150" alt="支付宝" />
  <br/><i>如果本项目有帮助，欢迎捐赠支持持续发展 ☕</i>
</p>
