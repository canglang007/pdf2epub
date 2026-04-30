# pdf2epub

将 PDF 文档转换为 EPUB 电子书格式，保留文字排版和图片。

## 功能

- 文字 PDF 转换为 EPUB，保留段落结构和标题层级
- 自动提取并嵌入图片
- 支持中文（CJK）文字排版
- CLI 命令行 + 桌面 GUI 双模式
- 跨平台（macOS / Windows）

## 下载

从 [Releases](https://github.com/canglang007/pdf2epub/releases) 页面下载对应平台的版本：

- **macOS**: 下载 `pdf2epub.dmg`，双击安装后拖入 Applications
- **Windows**: 下载 `pdf2epub.exe`，双击运行

无需安装 Python 或任何依赖。

## 使用方法

### 桌面版（推荐）

双击 `pdf2epub`，选择 PDF 文件，点击 Convert 即可。

### 命令行

```bash
# 安装
pip install pdf2epub

# 转换
pdf2epub input.pdf -o output.epub
```

## 技术栈

- PDF 解析: [PyMuPDF](https://pymupdf.readthedocs.io/)
- EPUB 生成: [EbookLib](https://github.com/aerkalov/ebooklib)
- 桌面 GUI: [CustomTkinter](https://customtkinter.tomschimansky.com/)
- 打包分发: [PyInstaller](https://pyinstaller.org/)

## 构建

```bash
pip install -e .
# macOS
scripts/build_macos.sh
# Windows
.\scripts\build_windows.ps1
```

## License

MIT
