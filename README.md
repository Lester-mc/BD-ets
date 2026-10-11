# E听说 智能提取工具

> 一款自动解析 E听说 缓存、提取最新套题答案并支持导出 PDF 的桌面小工具。

![版本](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

---

## ✨ 功能特性

- 🎯 **自动识别最新套题** — 扫描 ETS 缓存目录，自动找出最近一次做过的套题
- 📅 **当天题目优先** — 优先展示今天生成的套题，非当天会给出提示
- 📝 **智能题型分组** — 按「模仿朗读 / 听选信息 / 回答问题 / 信息转述 / 询问信息」等环节依次展示
- 💡 **只取最优答案** — 每道小题只显示前 3 个参考答案，简洁不冗余
- 🎧 **支持听力原文** — 模仿朗读等题型可查看完整听力材料
- 📄 **一键导出 PDF** — 支持将整套题导出为排版精美的 PDF 文件
- 🖥️ **现代化 GUI** — 基于 Tkinter，界面清爽，无需浏览器

---

## 📸 界面预览

> 首次运行会自动扫描并展示最新套题

<!-- 替换成你自己的截图 -->
![界面截图](screenshots/preview.png)

---

## 🚀 快速开始

### 方式一：直接下载 exe（推荐普通用户）

1. 前往 [Releases](../../releases) 页面
2. 下载最新版本的 `E听说提取工具.exe`
3. 双击运行即可，无需安装 Python

> ⚠️ 首次运行如遇 Windows Defender 拦截，请点击「更多信息」→「仍要运行」

### 方式二：从源码运行（推荐开发者）

#### 环境要求

- Python 3.10 或更高版本
- Windows 10 / 11

#### 安装依赖

```bash
pip install reportlab
```

#### 运行

```bash
python BD-ets.py
```

---

## 📖 使用说明

### 第一步：确认缓存目录

程序默认读取以下路径：

```
C:\Users\<你的用户名>\AppData\Roaming\ETS
```

如果你的 E听说 安装在别的位置，点击 **📁 浏览** 手动选择 ETS 目录。

### 第二步：一键提取

点击 **🚀 一键提取**，程序会：

1. 扫描 ETS 目录下所有套题文件夹
2. 找出**最新**的一套（优先当天的）
3. 按环节顺序解析题目和答案
4. 在窗口中展示结果

### 第三步：导出 PDF（可选）

确认内容无误后，点击 **📄 导出 PDF**，选择保存位置，即可生成 PDF 文件。

---

## 🗂️ 支持的题型

| 题型 | 说明 |
|---|---|
| 模仿朗读 | 展示听力原文 |
| 听选信息 1/2/3 | 展示题目和 3 个参考答案 |
| 回答问题 | 展示题目和 3 个参考答案 |
| 信息转述 | 展示题目和 3 个参考答案 |
| 询问信息 | 展示题目和 3 个参考答案 |

---

## 🛠️ 技术栈

- **界面**：Tkinter（Python 内置）
- **PDF 导出**：ReportLab
- **打包**：PyInstaller
- **数据解析**：JSON + 正则表达式

---

## 📁 项目结构

```
BD-ets/
├── BD-ets.py          # 主程序
├── requirements.txt   # 依赖列表
├── LICENSE            # 开源协议
├── README.md          # 说明文档
└── screenshots/       # 截图目录
    └── preview.png
```

---

## 📦 打包成 exe

如果你想自己打包：

```bash
pip install pyinstaller
pyinstaller --onefile --noconsole --collect-all reportlab --name "E听说提取工具" BD-ets.py
```

生成的 exe 位于 `dist/` 目录下。

---

## ❓ 常见问题

<details>
<summary><b>Q1：提示「未找到任何套题文件夹」怎么办？</b></summary>

请确认：
- ETS 目录路径是否正确
- 是否已经在 E听说 中完成过至少一套题目
- 可以点击「浏览」手动选择目录
</details>

<details>
<summary><b>Q2：题目显示为「非当天」怎么办？</b></summary>

说明缓存中最新的一套不是今天的。请先在 E听说 中完成今天的作业，然后重新点击「一键提取」。
</details>

<details>
<summary><b>Q3：导出 PDF 时提示缺少 reportlab？</b></summary>

在命令行运行：
```bash
pip install reportlab
```
如果清华源找不到，试试官方源：
```bash
pip install reportlab -i https://pypi.org/simple/
```
</details>

<details>
<summary><b>Q4：exe 被杀毒软件误报怎么办？</b></summary>

这是 PyInstaller 打包程序的常见问题，添加信任即可。你也可以直接使用源码运行。
</details>

---

## ⚠️ 免责声明

本工具**仅供个人学习研究使用**，请勿用于任何商业用途或作弊行为。使用本工具产生的一切后果由使用者自行承担。

请尊重 E听说 官方版权，支持正版学习。

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建新分支 `git checkout -b feature/xxx`
3. 提交更改 `git commit -m 'feat: xxx'`
4. 推送分支 `git push origin feature/xxx`
5. 提交 Pull Request

---

## 📄 License

本项目基于 [MIT License](LICENSE) 开源。

---

## ⭐ Star History

如果这个项目对你有帮助，欢迎点个 ⭐ Star 支持一下！

---

**Made with ❤️ by [你的GitHub用户名]**
