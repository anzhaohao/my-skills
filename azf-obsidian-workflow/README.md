# azf-obsidian-workflow

这个 skill 用来维护 An Zhaofeng 的 Obsidian 项目记录，把项目入口、进度交接、事件记录、稳定参考和补充笔记组织成可恢复的工作流。

## 什么时候触发

- 用户要求建立项目主笔记、整理项目笔记、记录实验/调试过程。
- 项目文件夹在 `01-Project` 下，需要更新状态、进度、材料或交接信息。
- 用户提供图片、实验结果、硬件信息或软件环境，需要写入 Obsidian。

## 当前关键规则

- 主笔记保持轻量，长细节放到链接记录或补充笔记中。
- 写作像清楚的实验交接：区分看到的事实和自己的判断，不把不确定内容写成已确认。
- 创建 Markdown note 时默认不在正文重复文件标题。
- 涉及深度学习实验归档时，使用 `azf-deep-learning-experiment-record` 作为证据写作层。

## 最近维护

- 2026-05-31：将深度学习实验记录引用更新为 `azf-deep-learning-experiment-record`，并补充中文 README。
