import sys
import json
import re
import datetime
import threading
from pathlib import Path
from html import unescape

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext

# ---------- PDF 库（可选） ----------
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.cidfonts import UnicodeCIDFont
    from reportlab.lib.units import mm
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False

# ---------- 配色 ----------
C_BG        = "#f5f6fa"
C_HEADER    = "#2c3e50"
C_TOOLBAR   = "#ecf0f1"
C_CARD      = "#ffffff"
C_TEXT      = "#2c3e50"
C_TEXT_LT   = "#7f8c8d"
C_ACCENT    = "#3498db"
C_ACCENT_H  = "#2980b9"
C_SUCCESS   = "#27ae60"
C_SUCCESS_H = "#229954"
C_GRAY      = "#7f8c8d"
C_GRAY_H    = "#95a5a6"
C_DIVIDER   = "#dcdde1"

# ---------- 固定环节顺序 ----------
STAGE_NAMES = [
    '模仿朗读', '听选信息1', '听选信息2', '听选信息3',
    '回答问题', '信息转述', '询问信息',
]

# ================= 数据处理逻辑 =================
def clean_html(text):
    if not isinstance(text, str):
        return text
    text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'</br>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'<p>', '', text, flags=re.IGNORECASE)
    text = re.sub(r'</p>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'<[^>]+>', '', text)
    text = unescape(text)
    text = re.sub(r'\n\s*\n', '\n', text)
    return text.strip()

def parse_collector_role(data):
    results = []
    if data.get('structure_type') != 'collector.role':
        return results
    info = data.get('info', {})
    questions = info.get('question', [])
    for q in questions:
        ask = clean_html(q.get('ask', ''))
        std_list = q.get('std', [])
        answers = []
        for std_item in std_list[:3]:
            val = std_item.get('value', '')
            if val:
                answers.append(clean_html(val))
        results.append({
            'xh': q.get('xh', ''),
            'ask': ask,
            'answers': answers
        })
    return results

def parse_collector_read(data):
    if data.get('structure_type') != 'collector.read':
        return None
    info = data.get('info', {})
    value = info.get('value', '')
    return clean_html(value)

def find_latest_exam_folder(root_dir):
    root = Path(root_dir)
    if not root.exists():
        return None

    today = datetime.date.today()
    exam_folders = []

    for item in root.iterdir():
        if not item.is_dir() or not item.name.isdigit():
            continue

        latest_mtime = 0
        has_today_file = False

        for f in item.rglob('*'):
            if f.is_file():
                mtime = f.stat().st_mtime
                if mtime > latest_mtime:
                    latest_mtime = mtime
                file_date = datetime.date.fromtimestamp(mtime)
                if file_date == today:
                    has_today_file = True

        if latest_mtime == 0:
            latest_mtime = item.stat().st_mtime

        exam_folders.append((latest_mtime, item, has_today_file))

    if not exam_folders:
        return None

    today_folders = [f for f in exam_folders if f[2]]
    if today_folders:
        today_folders.sort(key=lambda x: x[0], reverse=True)
        return today_folders[0][1], True

    exam_folders.sort(key=lambda x: x[0], reverse=True)
    return exam_folders[0][1], False

def wrap_text(text, max_width_chars):
    """按显示宽度换行，中文按 2 计算，英文按 1 计算"""
    lines = []
    for paragraph in text.split('\n'):
        if not paragraph.strip():
            lines.append('')
            continue
        current = ''
        width = 0
        for ch in paragraph:
            w = 2 if ord(ch) > 127 else 1
            if width + w > max_width_chars:
                lines.append(current)
                current = ch
                width = w
            else:
                current += ch
                width += w
        if current:
            lines.append(current)
    return lines

# ================= Tkinter GUI =================
class App:
    def __init__(self, root):
        self.root = root
        self.root.title("E听说 智能提取工具")
        self.root.geometry("1050x820")
        self.root.configure(bg=C_BG)

        self.default_path = r"C:\Users\35217\AppData\Roaming\ETS"

        # 数据缓存（用于导出 PDF）
        self.current_stages = None
        self.current_exam_name = ""
        self.current_mtime = ""

        self.setup_ui()
        self.root.after(200, self.start_extract)

    # ---------- 按钮工具：创建带 hover 的扁平按钮 ----------
    def _make_button(self, parent, text, bg, bg_hover, command):
        btn = tk.Button(
            parent, text=text, bg=bg, fg="white",
            font=("Microsoft YaHei", 10, "bold"),
            relief=tk.FLAT, bd=0, padx=16, pady=6,
            cursor="hand2", activebackground=bg_hover,
            activeforeground="white",
            command=command,
        )
        btn.bind("<Enter>", lambda e, b=btn, c=bg_hover: b.config(bg=c))
        btn.bind("<Leave>", lambda e, b=btn, c=bg: b.config(bg=c))
        return btn

    def setup_ui(self):
        # ---------- 顶部标题栏 ----------
        header = tk.Frame(self.root, bg=C_HEADER, height=60)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        tk.Label(
            header, text="📚  E听说 智能提取工具",
            bg=C_HEADER, fg="white",
            font=("Microsoft YaHei", 15, "bold"),
        ).pack(side=tk.LEFT, padx=22, pady=15)

        tk.Label(
            header, text="v2.0  ·  自动识别最新套题",
            bg=C_HEADER, fg="#95a5a6",
            font=("Microsoft YaHei", 9),
        ).pack(side=tk.RIGHT, padx=22, pady=15)

        # ---------- 工具条 ----------
        toolbar = tk.Frame(self.root, bg=C_TOOLBAR, padx=18, pady=14)
        toolbar.pack(fill=tk.X)

        tk.Label(
            toolbar, text="ETS 目录:", bg=C_TOOLBAR,
            font=("Microsoft YaHei", 10), fg=C_TEXT,
        ).pack(side=tk.LEFT)

        self.path_var = tk.StringVar(value=self.default_path)
        self.path_entry = tk.Entry(
            toolbar, textvariable=self.path_var,
            font=("Microsoft YaHei", 10), relief=tk.FLAT, bd=0,
            bg="white", fg=C_TEXT, insertbackground=C_TEXT,
            highlightthickness=1, highlightbackground="#bdc3c7",
            highlightcolor=C_ACCENT,
        )
        self.path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True,
                             padx=10, ipady=7, ipadx=8)

        self.browse_btn = self._make_button(
            toolbar, "📁 浏览", C_GRAY, C_GRAY_H, self.browse_folder)
        self.browse_btn.pack(side=tk.LEFT, padx=3)

        self.extract_btn = self._make_button(
            toolbar, "🚀 一键提取", C_ACCENT, C_ACCENT_H, self.start_extract)
        self.extract_btn.pack(side=tk.LEFT, padx=3)

        self.export_btn = self._make_button(
            toolbar, "📄 导出 PDF", C_SUCCESS, C_SUCCESS_H, self.export_pdf)
        self.export_btn.pack(side=tk.LEFT, padx=3)
        self.export_btn.config(state=tk.DISABLED)

        # ---------- 内容区 ----------
        content_frame = tk.Frame(self.root, bg=C_BG, padx=16, pady=14)
        content_frame.pack(fill=tk.BOTH, expand=True)

        self.result_area = scrolledtext.ScrolledText(
            content_frame, wrap=tk.WORD,
            font=("Microsoft YaHei", 11),
            bg=C_CARD, fg=C_TEXT,
            padx=24, pady=20, relief=tk.FLAT, bd=0,
            highlightthickness=1, highlightbackground=C_DIVIDER,
        )
        self.result_area.pack(fill=tk.BOTH, expand=True)

        # ---------- 文本样式标签 ----------
        self.result_area.tag_config(
            "exam_title",
            font=("Microsoft YaHei", 16, "bold"),
            foreground="#8e44ad", spacing1=8, spacing3=8)
        self.result_area.tag_config(
            "info",
            font=("Microsoft YaHei", 10), foreground=C_TEXT_LT, spacing1=4)
        self.result_area.tag_config(
            "stage",
            font=("Microsoft YaHei", 15, "bold"),
            foreground=C_ACCENT, spacing1=26, spacing3=10)
        self.result_area.tag_config(
            "question",
            font=("Microsoft YaHei", 12, "bold"),
            foreground=C_TEXT, spacing1=12, spacing3=6)
        self.result_area.tag_config(
            "answer_label",
            font=("Microsoft YaHei", 11, "bold"),
            foreground=C_SUCCESS, spacing1=10, spacing3=6)
        self.result_area.tag_config(
            "answer",
            font=("Microsoft YaHei", 11),
            foreground="#16a085", lmargin1=30, lmargin2=30, spacing1=4)
        self.result_area.tag_config(
            "read_text",
            font=("Microsoft YaHei", 11), foreground="#34495e",
            lmargin1=20, lmargin2=20, spacing1=5, spacing3=5)
        self.result_area.tag_config(
            "divider",
            font=("Microsoft YaHei", 8), foreground=C_DIVIDER,
            spacing1=8, spacing3=8)
        self.result_area.tag_config(
            "warning",
            font=("Microsoft YaHei", 11), foreground="#e67e22", spacing1=5)

        # ---------- 状态栏 ----------
        self.status_var = tk.StringVar(value="准备就绪")
        status_bar = tk.Label(
            self.root, textvariable=self.status_var,
            bg=C_HEADER, fg="#bdc3c7",
            font=("Microsoft YaHei", 9), anchor=tk.W,
            padx=22, pady=6)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    # ---------- 事件 ----------
    def browse_folder(self):
        folder = filedialog.askdirectory(
            title="选择 ETS 缓存目录", initialdir=self.path_var.get())
        if folder:
            self.path_var.set(folder)

    def start_extract(self):
        path = self.path_var.get().strip()
        if not path:
            messagebox.showwarning("警告", "请输入或选择 ETS 缓存目录！")
            return

        self.extract_btn.config(state=tk.DISABLED)
        self.browse_btn.config(state=tk.DISABLED)
        self.export_btn.config(state=tk.DISABLED)
        self.result_area.delete(1.0, tk.END)
        self.status_var.set("正在扫描目录...")

        thread = threading.Thread(target=self.worker_logic, args=(path,))
        thread.daemon = True
        thread.start()

    # ---------- 后台提取 ----------
    def worker_logic(self, path):
        try:
            result = find_latest_exam_folder(path)
            if result is None:
                self.root.after(0, lambda: self.on_error(
                    "在指定目录下未找到任何套题文件夹。\n"
                    "请确认路径是否正确，或先在 E听说 中完成一套题目。"))
                return

            latest_folder, is_today = result
            latest_mtime = max(
                (f.stat().st_mtime for f in latest_folder.rglob('*') if f.is_file()),
                default=latest_folder.stat().st_mtime,
            )
            mtime_str = datetime.datetime.fromtimestamp(latest_mtime).strftime('%Y-%m-%d %H:%M:%S')

            self.root.after(0, lambda: self.status_var.set(f"解析套题: {latest_folder.name} ..."))

            content_folders = []
            for sub in sorted(latest_folder.iterdir()):
                if sub.is_dir() and sub.name.startswith('content_'):
                    content_folders.append(sub)

            stages = []
            for idx, folder in enumerate(content_folders):
                stage_name = STAGE_NAMES[idx] if idx < len(STAGE_NAMES) else folder.name
                json_file = folder / 'content.json'
                if not json_file.exists():
                    continue

                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                except Exception:
                    try:
                        with open(json_file, 'r', encoding='gbk') as f:
                            data = json.load(f)
                    except Exception:
                        continue

                stage_data = {'name': stage_name, 'items': []}
                st = data.get('structure_type', '')

                if st == 'collector.role':
                    qa_list = parse_collector_role(data)
                    for qa in qa_list:
                        stage_data['items'].append(('qa', qa))
                elif st == 'collector.read':
                    text = parse_collector_read(data)
                    if text:
                        stage_data['items'].append(('read', text))
                else:
                    if isinstance(data, dict):
                        info = data.get('info', {})
                        value = info.get('value', '')
                        if value:
                            text = clean_html(value)
                            if text:
                                stage_data['items'].append(('read', text))

                if stage_data['items']:
                    stages.append(stage_data)

            self.root.after(0, lambda: self.render_data(
                stages, latest_folder.name, mtime_str, is_today))

        except Exception as e:
            err_msg = f"发生错误: {str(e)}"
            self.root.after(0, lambda msg=err_msg: self.on_error(msg))

    # ---------- 渲染 ----------
    def render_data(self, stages, exam_name, mtime_str, is_today):
        # 缓存数据供导出 PDF 使用
        self.current_stages = stages
        self.current_exam_name = exam_name
        self.current_mtime = mtime_str

        self.result_area.delete(1.0, tk.END)

        if not is_today:
            self.result_area.insert(
                tk.END,
                "⚠️ 提示：当前套题不是今天生成的，可能显示的是历史题目。\n", "warning")
            self.result_area.insert(
                tk.END,
                "   请先在 E听说 中完成今天的作业，再重新打开本工具。\n\n", "info")

        if not stages:
            self.result_area.insert(tk.END, "未提取到任何题目数据。\n", "exam_title")
            self.export_btn.config(state=tk.DISABLED)
            self.on_finished()
            return

        self.result_area.insert(tk.END, f"🎯 套题编号：{exam_name}\n", "exam_title")
        self.result_area.insert(tk.END, f"🕒 最后修改时间：{mtime_str}\n", "info")
        self.result_area.insert(tk.END, "─" * 70 + "\n", "divider")

        for stage in stages:
            self.result_area.insert(tk.END, f"\n▶  {stage['name']}\n", "stage")
            self.result_area.insert(tk.END, "─" * 70 + "\n", "divider")

            for typ, content in stage['items']:
                if typ == 'qa':
                    xh = content.get('xh', '')
                    xh_str = f" {xh}" if xh else ""
                    self.result_area.insert(tk.END, f"\n【题目{xh_str}】\n", "question")
                    self.result_area.insert(tk.END, f"{content['ask']}\n", "read_text")
                    self.result_area.insert(
                        tk.END, "\n✨ 参考答案（前 3 个）：\n", "answer_label")
                    for i, ans in enumerate(content['answers'], 1):
                        self.result_area.insert(tk.END, f"  {i}. {ans}\n", "answer")
                    self.result_area.insert(tk.END, "\n" + "─" * 50 + "\n", "divider")
                elif typ == 'read':
                    self.result_area.insert(tk.END, "\n🎧 听力材料原文：\n", "question")
                    self.result_area.insert(tk.END, f"{content}\n", "read_text")
                    self.result_area.insert(tk.END, "\n" + "─" * 50 + "\n", "divider")

        self.export_btn.config(state=tk.NORMAL)
        self.on_finished()

    # ---------- 状态 ----------
    def on_finished(self):
        self.status_var.set("✅ 提取完成！")
        self.extract_btn.config(state=tk.NORMAL)
        self.browse_btn.config(state=tk.NORMAL)

    def on_error(self, err_msg):
        messagebox.showerror("错误", err_msg)
        self.status_var.set("❌ 提取失败")
        self.extract_btn.config(state=tk.NORMAL)
        self.browse_btn.config(state=tk.NORMAL)
        self.export_btn.config(state=tk.DISABLED)

    # ---------- 导出 PDF ----------
    def export_pdf(self):
        if not self.current_stages:
            messagebox.showwarning("提示", "请先点击“一键提取”，成功提取后再导出 PDF。")
            return

        if not HAS_REPORTLAB:
            messagebox.showerror(
                "缺少依赖",
                "导出 PDF 需要 reportlab 库。\n\n"
                "请在命令行执行：\n    pip install reportlab\n\n"
                "安装后重启本程序即可。")
            return

        file_path = filedialog.asksaveasfilename(
            title="导出 PDF",
            defaultextension=".pdf",
            filetypes=[("PDF 文件", "*.pdf")],
            initialfile=f"E听说_{self.current_exam_name}.pdf",
        )
        if not file_path:
            return

        try:
            pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'))
            c = canvas.Canvas(file_path, pagesize=A4)
            width, height = A4
            left = 18 * mm
            right = width - 18 * mm
            y = height - 22 * mm
            bottom_limit = 22 * mm

            def new_page_if_needed(y, needed=15 * mm):
                if y < bottom_limit + needed:
                    c.showPage()
                    return height - 22 * mm
                return y

            # 标题
            c.setFont('STSong-Light', 20)
            c.setFillColorRGB(0.17, 0.24, 0.31)
            c.drawString(left, y, f"E听说 套题：{self.current_exam_name}")
            y -= 8 * mm

            c.setFont('STSong-Light', 10)
            c.setFillColorRGB(0.5, 0.5, 0.5)
            c.drawString(left, y, f"最后修改时间：{self.current_mtime}")
            y -= 6 * mm

            c.setStrokeColorRGB(0.8, 0.8, 0.85)
            c.line(left, y, right, y)
            y -= 8 * mm

            for stage in self.current_stages:
                y = new_page_if_needed(y, 30 * mm)

                # 环节标题
                c.setFont('STSong-Light', 15)
                c.setFillColorRGB(0.16, 0.5, 0.72)
                c.drawString(left, y, f"▶  {stage['name']}")
                y -= 3 * mm

                c.setStrokeColorRGB(0.85, 0.9, 0.95)
                c.line(left, y, right, y)
                y -= 7 * mm

                for typ, content in stage['items']:
                    if typ == 'qa':
                        y = new_page_if_needed(y, 20 * mm)
                        xh = content.get('xh', '')
                        xh_str = f" [{xh}]" if xh else ""

                        # 题目
                        c.setFont('STSong-Light', 12)
                        c.setFillColorRGB(0.17, 0.24, 0.31)
                        for line in wrap_text(f"题目{xh_str}：{content['ask']}", 52):
                            y = new_page_if_needed(y)
                            c.drawString(left, y, line)
                            y -= 6 * mm

                        y -= 2 * mm
                        # 答案标签
                        c.setFont('STSong-Light', 11)
                        c.setFillColorRGB(0.15, 0.68, 0.38)
                        c.drawString(left, y, "参考答案（前 3 个）：")
                        y -= 6 * mm

                        # 答案
                        for i, ans in enumerate(content['answers'], 1):
                            for line in wrap_text(f"{i}. {ans}", 50):
                                y = new_page_if_needed(y)
                                c.setFont('STSong-Light', 11)
                                c.setFillColorRGB(0.09, 0.5, 0.4)
                                c.drawString(left + 6 * mm, y, line)
                                y -= 5.5 * mm
                        y -= 5 * mm

                    elif typ == 'read':
                        y = new_page_if_needed(y, 20 * mm)
                        c.setFont('STSong-Light', 12)
                        c.setFillColorRGB(0.17, 0.24, 0.31)
                        c.drawString(left, y, "听力材料原文：")
                        y -= 6 * mm

                        c.setFont('STSong-Light', 11)
                        c.setFillColorRGB(0.2, 0.2, 0.2)
                        for line in wrap_text(content, 52):
                            y = new_page_if_needed(y)
                            c.drawString(left + 6 * mm, y, line)
                            y -= 5.5 * mm
                        y -= 5 * mm

                y -= 3 * mm

            c.save()
            messagebox.showinfo("导出成功", f"PDF 已保存至：\n{file_path}")

        except Exception as e:
            err = str(e)
            messagebox.showerror("导出失败", f"发生错误：\n{err}")


if __name__ == '__main__':
    root = tk.Tk()
    app = App(root)
    root.mainloop()