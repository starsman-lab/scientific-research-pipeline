# 知识库脚手架（Knowledge Base）

> 本目录是流水线的"长期记忆"：已读论文转 Markdown 存档，参考文献统一进 bibtex 库。
> 原则（R9 知识库优先 + R2 引用真实）：调研与写作只从本库取文献，新文献入库后才可被引用。

---

## 1. 结构

```
references/
├── README.md                 # 本文件
├── library.bib               # 统一 bibtex 库（所有可引用文献）
├── papers/                   # 单篇论文 Markdown 精读卡
│   └── <year>-<firstauthor>-<short-title>.md
└── templates/               # 模板
    ├── paper-card.md         # 论文精读卡模板
    └── citation.bib          # bibtex 条目模板
```

## 2. 论文精读卡模板 `papers/<year>-<firstauthor>-<short-title>.md`

每张卡必须带**来源锚点**（url / doi / arxiv id），便于审计与回链。复制 `templates/paper-card.md` 后填写：

```markdown
---
title: "<论文标题>"
authors: "<作者>"
venue: "<会议/期刊>"
year: <年>
url: "<来源链接>"
doi: "<DOI 或 arXiv ID>"
status: unread|skimmed|deep
tags: [<子领域>, <方法>]
---

## 一句话结论
<用一句大白话说清这篇干了什么>

## 主要做法
<2-4 句，方法核心>

## 数据集与设置
- 数据集：<名称>
- 指标：<核心指标>

## 关键数字
- <指标>: <数值>（来自原文，标注表格/段落出处）

## 与本项目的关系
<为什么存这张卡：支持/反驳/方法可复用>

## 可引用论断（claim anchors）
- "<可引用的具体论断>" -> 对应本文 <章节/图表>
```

## 3. bibtex 条目模板 `library.bib`

每条必须含真实 DOI / arXiv，禁止编造。字段缺失标 `note = {NEED-METADATA}`：

```bibtex
@article{<key>,
  title   = {<真实标题>},
  author  = {<真实作者>},
  journal = {<真实期刊>},
  year    = {<年>},
  doi     = {<真实DOI>},
  note    = {NEED-METADATA}   % 仅当确实缺失时
}
```

## 4. 入库流程

1. 文献调研 / 网络检索获得论文 → 写精读卡到 `papers/`（带来源锚点）。
2. 提取 bibtex 条目追加到 `library.bib`（优先用 Crossref / Semantic Scholar 校验元数据）。
3. 写作时只引用 `library.bib` 中已存在的 key；未确认的读者需求标 `[CITATION NEEDED]`（R2）。
4. 每周 `git commit` 一次知识库，保证可回溯。

## 5. 工具建议（可选增强）

- 学术搜索：Semantic Scholar API、OpenAlex、Crossref、arXiv、PubMed。
- 引用管理：Zotero / pandoc-citeproc，导出 bibtex 后并入 `library.bib`。
- 全文获取：通过机构 CARSI / OA 合法下载，存 `papers/pdf/` 并标注 license。
