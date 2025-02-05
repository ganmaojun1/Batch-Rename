import os
import re
import json
import tkinter as tk
from datetime import datetime
from tkinter import filedialog, messagebox, ttk

# 配置常量
COMMON_EXTENSIONS = [".txt", ".doc", ".docx", ".pdf", ".jpg", ".png", ".mp3", ".mp4"]

REGEX_TEMPLATES = {
    "删除括号(英文)及内容": {
        "pattern": r"\(.*?\)",
        "replacement": "",
        "description": "删除文件名中的括号及括号内的所有内容",
    },
    "删除括号（中文）及内容": {
        "pattern": r"\（.*?\）",
        "replacement": "",
        "description": "删除文件名中的括号及括号内的所有内容",
    },
    "删除多余空格": {
        "pattern": r"\s+",
        "replacement": " ",
        "description": "将多个连续空格替换为单个空格",
    },
}


class FileOperations:
    """
    文件操作相关封装
    """

    @staticmethod
    def rename_files(file_list, mode, target=None, replacement=None):
        """
        根据指定模式批量生成新的文件名列表

        :param file_list: [(目录, 文件名), ...]
        :param mode: "replace" 或 "regex"
        :param target: 替换目标或正则表达式模式
        :param replacement: 替换字符串
        :return: [(目录, 原文件名, 新文件名), ...]
        """
        results = []
        for file_dir, filename in file_list:
            try:
                new_name = FileOperations._get_new_name(filename, mode, target, replacement)
                if new_name != filename:
                    results.append((file_dir, filename, new_name))
            except Exception as e:
                print(f"处理文件 {filename} 时发生错误: {e}")
        return results

    @staticmethod
    def _get_new_name(filename, mode, target, replacement):
        name, ext = os.path.splitext(filename)
        if mode == "replace":
            return name.replace(target, replacement) + ext
        elif mode == "regex":
            return re.sub(target, replacement, name) + ext
        else:
            raise ValueError("无效的重命名模式")


class RenameTools:
    """
    批量重命名工具主界面
    """

    def __init__(self, root):
        self.root = root
        self.history_file = "rename_history.json"
        self.history = []
        self.common_extensions = COMMON_EXTENSIONS
        self.regex_templates = REGEX_TEMPLATES
        self.load_history()
        self.setup_window()
        self.init_variables()
        self.create_widgets()

    def setup_window(self):
        """设置主窗口基本属性"""
        self.root.title("批量重命名工具")
        self.root.geometry("800x600")
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

    def init_variables(self):
        """初始化操作时需要使用的变量"""
        # 默认选择普通替换
        self.mode_var = tk.StringVar(value="replace")
        self.include_subfolders = tk.BooleanVar(value=False)

        # 用于文件名过滤（后续可扩展）
        self.filter_entry = ttk.Entry(self.main_frame)

    def create_widgets(self):
        """构建所有UI组件"""
        self._create_mode_selection()
        self._create_replacement_frame()  # 新增替换设置区域
        self._create_extension_selection()
        self._create_buttons()
        self._create_history_display()
        self._create_regex_frame()
        # 根据初始模式调整正则表达式区域显示
        self.toggle_regex_frame()

    def _create_mode_selection(self):
        """创建重命名模式选择区域"""
        mode_frame = ttk.LabelFrame(self.main_frame, text="重命名模式", padding="5")
        mode_frame.pack(fill=tk.X, pady=5)

        # 普通替换与正则替换
        modes = [
            ("普通替换", "replace"),
            ("正则替换", "regex"),
        ]
        for text, value in modes:
            ttk.Radiobutton(mode_frame, text=text, value=value, variable=self.mode_var).pack(
                side=tk.LEFT, padx=5
            )
        # 是否包含子文件夹
        ttk.Checkbutton(
            mode_frame, text="包含子文件夹", variable=self.include_subfolders
        ).pack(side=tk.LEFT, padx=20)

    def _create_replacement_frame(self):
        """创建替换文本输入区域（仅用于普通替换模式）"""
        self.replacement_frame = ttk.LabelFrame(self.main_frame, text="替换设置", padding="5")
        self.replacement_frame.pack(fill=tk.X, pady=5)

        # 原文本输入
        target_frame = ttk.Frame(self.replacement_frame)
        target_frame.pack(fill=tk.X, pady=2)
        ttk.Label(target_frame, text="原文本：").pack(side=tk.LEFT, padx=5)
        self.replace_target_entry = ttk.Entry(target_frame)
        self.replace_target_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # 替换后文本输入
        replace_frame = ttk.Frame(self.replacement_frame)
        replace_frame.pack(fill=tk.X, pady=2)
        ttk.Label(replace_frame, text="替换文本：").pack(side=tk.LEFT, padx=5)
        self.replace_with_entry = ttk.Entry(replace_frame)
        self.replace_with_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

    def _create_extension_selection(self):
        """创建文件扩展名选择区域"""
        ext_frame = ttk.LabelFrame(self.main_frame, text="文件类型", padding="5")
        ext_frame.pack(fill=tk.X, pady=10)

        self.extension_vars = []
        row, col = 0, 0
        for ext in self.common_extensions:
            var = tk.BooleanVar(value=(ext == ".pdf"))  # 默认选中 PDF
            self.extension_vars.append(var)
            cb = ttk.Checkbutton(ext_frame, text=ext, variable=var)
            cb.grid(row=row, column=col, padx=5, pady=2, sticky=tk.W)
            col += 1
            if col > 3:
                col = 0
                row += 1

        # 自定义扩展名
        self.custom_ext_var = tk.BooleanVar()
        custom_frame = ttk.Frame(ext_frame)
        custom_frame.grid(row=row + 1, column=0, columnspan=4, pady=5, sticky=tk.W)
        ttk.Checkbutton(custom_frame, text="自定义扩展名", variable=self.custom_ext_var, command=self.toggle_custom_entry
                       ).pack(side=tk.LEFT)
        self.custom_ext_entry = ttk.Entry(custom_frame, width=20)
        self.custom_ext_entry.pack(side=tk.LEFT, padx=5)
        self.custom_ext_entry.config(state="disabled")

    def _create_buttons(self):
        """创建操作按钮区域"""
        btn_frame = ttk.Frame(self.main_frame)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="选择文件夹并重命名", command=self.rename_files).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(btn_frame, text="撤销上次操作", command=self.undo_last_operation).pack(
            side=tk.LEFT, padx=5
        )

    def _create_history_display(self):
        """创建操作历史显示区域"""
        ttk.Label(self.main_frame, text="操作历史：").pack(anchor=tk.W)
        self.history_text = tk.Text(self.main_frame, height=10, width=60)
        self.history_text.pack(pady=10)
        self.update_history_display()

    def _create_regex_frame(self):
        """创建正则表达式配置区域（包含实时测试功能）"""
        self.regex_frame = ttk.LabelFrame(self.main_frame, text="正则表达式选项", padding="5")
        # 默认先隐藏，只有在正则替换模式下显示
        # 注意这里采用 pack_forget 后再 pack
        self.regex_frame.pack(fill=tk.X, pady=10)

        # 常用模板选择
        ttk.Label(self.regex_frame, text="常用模板：").pack(anchor=tk.W)
        self.template_var = tk.StringVar()
        self.template_combobox = ttk.Combobox(
            self.regex_frame,
            textvariable=self.template_var,
            values=list(self.regex_templates.keys()),
            state="readonly",
            width=30,
        )
        self.template_combobox.pack(fill=tk.X, pady=5)
        self.template_combobox.bind("<<ComboboxSelected>>", self.on_template_selected)

        self.template_desc = ttk.Label(self.regex_frame, text="", wraplength=400)
        self.template_desc.pack(fill=tk.X, pady=5)

        # 匹配模式输入
        pattern_frame = ttk.Frame(self.regex_frame)
        pattern_frame.pack(fill=tk.X, pady=5)
        ttk.Label(pattern_frame, text="匹配模式：").pack(side=tk.LEFT)
        self.pattern_entry = ttk.Entry(pattern_frame)
        self.pattern_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.pattern_entry.bind("<KeyRelease>", self.update_regex_preview)

        # 替换文本输入
        replace_frame = ttk.Frame(self.regex_frame)
        replace_frame.pack(fill=tk.X, pady=5)
        ttk.Label(replace_frame, text="替换文本：").pack(side=tk.LEFT)
        self.replace_entry = ttk.Entry(replace_frame)
        self.replace_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.replace_entry.bind("<KeyRelease>", self.update_regex_preview)

        # 测试文本输入
        test_frame = ttk.Frame(self.regex_frame)
        test_frame.pack(fill=tk.X, pady=5)
        ttk.Label(test_frame, text="测试文本：").pack(side=tk.LEFT)
        self.test_input = ttk.Entry(test_frame)
        self.test_input.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.test_input.bind("<KeyRelease>", self.update_regex_preview)

        # 匹配结果预览区域
        result_frame = ttk.Frame(self.regex_frame)
        result_frame.pack(fill=tk.BOTH, pady=5, expand=True)
        ttk.Label(result_frame, text="匹配结果：").pack(anchor=tk.W)
        self.result_text = tk.Text(result_frame, height=5)
        self.result_text.pack(fill=tk.BOTH, expand=True)

        # 根据模式切换显示/隐藏正则配置区域
        self.mode_var.trace_add("write", self.toggle_regex_frame)

    def toggle_custom_entry(self):
        """切换自定义扩展名输入框状态"""
        state = "normal" if self.custom_ext_var.get() else "disabled"
        self.custom_ext_entry.config(state=state)

    def get_selected_extensions(self):
        """获取所有选中的扩展名"""
        extensions = [ext for var, ext in zip(self.extension_vars, self.common_extensions) if var.get()]

        if self.custom_ext_var.get():
            custom_exts = self.custom_ext_entry.get().strip()
            if custom_exts:
                custom_list = [ext.strip() for ext in custom_exts.split(",") if ext.strip()]
                # 确保以点开头
                custom_list = [ext if ext.startswith(".") else f".{ext}" for ext in custom_list]
                extensions.extend(custom_list)
        return extensions

    def get_all_files(self, directory):
        """获取指定目录下（可包含子目录）的所有文件（可按过滤条件）"""
        files_list = []
        filter_text = self.filter_entry.get().strip()

        if self.include_subfolders.get():
            for root_dir, _, files in os.walk(directory):
                for file in files:
                    if not filter_text or filter_text in file:
                        files_list.append((root_dir, file))
        else:
            for file in os.listdir(directory):
                full_path = os.path.join(directory, file)
                if os.path.isfile(full_path):
                    if not filter_text or filter_text in file:
                        files_list.append((directory, file))
        return files_list

    def rename_files(self):
        """选择文件夹，预览并执行文件重命名操作"""
        directory = filedialog.askdirectory()
        if not directory:
            return

        extensions = self.get_selected_extensions()
        if not extensions:
            messagebox.showwarning("警告", "请至少选择一个文件类型")
            return

        mode = self.mode_var.get()
        # 根据选择模式获取替换参数
        if mode == "replace":
            target = self.replace_target_entry.get()
            replacement = self.replace_with_entry.get()
            if target == "":
                messagebox.showwarning("警告", "请在替换设置中输入要替换的原文本")
                return
        elif mode == "regex":
            target = self.pattern_entry.get()
            replacement = self.replace_entry.get()
            if target == "":
                messagebox.showwarning("警告", "请在正则表达式区域输入匹配模式")
                return
            try:
                re.compile(target)
            except re.error:
                messagebox.showerror("错误", "无效的正则表达式")
                return
        else:
            messagebox.showerror("错误", "未知的重命名模式")
            return

        # 筛选并预览需要处理的文件
        all_files = self.get_all_files(directory)
        filtered_files = [(d, f) for d, f in all_files if any(f.endswith(ext) for ext in extensions)]
        preview = FileOperations.rename_files(filtered_files, mode, target, replacement)

        if not preview:
            messagebox.showinfo("提示", "没有找到需要重命名的文件")
            return

        # 检查新文件名是否存在重复
        new_names = set()
        for _, _, new_name in preview:
            if new_name in new_names:
                messagebox.showerror("错误", f"检测到重复的新文件名: {new_name}")
                return
            new_names.add(new_name)

        # 生成预览文本
        preview_lines = []
        for file_dir, old, new in preview:
            full_old = os.path.join(file_dir, old)
            full_new = os.path.join(file_dir, new)
            preview_lines.append(f"{full_old}\n  -> {full_new}\n")

        preview_text = "\n".join(preview_lines)
        # 弹出确认对话框
        if not messagebox.askyesno("预览", f"将进行以下重命名：\n\n{preview_text}\n\n是否继续？"):
            return

        # 创建进度条
        progress = ttk.Progressbar(self.main_frame, length=300, mode="determinate")
        progress.pack(pady=10)
        self.root.update()

        # 保存操作记录，便于撤销
        operation_record = {"timestamp": datetime.now().isoformat(), "changes": []}

        try:
            for i, (file_dir, old, new) in enumerate(preview):
                old_path = os.path.join(file_dir, old)
                new_path = os.path.join(file_dir, new)
                operation_record["changes"].append({"old_path": old_path, "new_path": new_path})
                os.rename(old_path, new_path)
                progress["value"] = (i + 1) / len(preview) * 100
                self.root.update()
        except Exception as e:
            messagebox.showerror("错误", f"重命名过程中出现异常：{e}")
            progress.destroy()
            return

        # 保存历史记录
        self.history.append(operation_record)
        self.save_history()
        self.update_history_display()

        progress.destroy()
        messagebox.showinfo("完成", f"完成 {len(preview)} 个文件的重命名")

    def undo_last_operation(self):
        """撤销上次的重命名操作"""
        if not self.history:
            messagebox.showinfo("提示", "没有可撤销的操作")
            return

        last_operation = self.history[-1]
        if not messagebox.askyesno("确认", "确定要撤销上次重命名操作吗？"):
            return

        try:
            for change in reversed(last_operation["changes"]):
                if os.path.exists(change["new_path"]):
                    os.rename(change["new_path"], change["old_path"])
            self.history.pop()
            self.save_history()
            self.update_history_display()
            messagebox.showinfo("完成", "撤销操作完成")
        except Exception as e:
            messagebox.showerror("错误", f"撤销操作失败：{e}")

    def load_history(self):
        """加载历史记录"""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, "r", encoding="utf-8") as f:
                    self.history = json.load(f)
            except Exception as e:
                print(f"加载历史记录失败：{e}")
                self.history = []

    def save_history(self):
        """保存历史记录到文件"""
        try:
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump(self.history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            messagebox.showerror("错误", f"保存历史记录失败：{e}")

    def update_history_display(self):
        """更新历史记录文本显示，仅显示最近 5 次操作"""
        self.history_text.delete("1.0", tk.END)
        for operation in reversed(self.history[-5:]):
            time_str = datetime.fromisoformat(operation["timestamp"]).strftime("%Y-%m-%d %H:%M:%S")
            self.history_text.insert(tk.END, f"操作时间：{time_str}\n")
            for change in operation["changes"]:
                self.history_text.insert(
                    tk.END,
                    f"  {os.path.basename(change['old_path'])} -> {os.path.basename(change['new_path'])}\n"
                )
            self.history_text.insert(tk.END, "-" * 50 + "\n")

    def toggle_regex_frame(self, *args):
        """根据选择模式显示或隐藏正则表达式配置区域"""
        if self.mode_var.get() == "regex":
            # 正则模式下显示正则配置区域，同时隐藏普通替换设置区域
            self.regex_frame.pack(fill=tk.X, pady=10)
            self.replacement_frame.pack_forget()
        else:
            # 普通替换时显示替换设置区域，隐藏正则区域
            self.replacement_frame.pack(fill=tk.X, pady=5)
            self.regex_frame.pack_forget()

    def on_template_selected(self, event):
        """当选择常用模板时自动填充正则表达式相关内容"""
        template_name = self.template_var.get()
        if template_name in self.regex_templates:
            template = self.regex_templates[template_name]
            self.pattern_entry.delete(0, tk.END)
            self.pattern_entry.insert(0, template["pattern"])
            self.replace_entry.delete(0, tk.END)
            self.replace_entry.insert(0, template["replacement"])
            self.template_desc.config(text=template["description"])
            self.update_regex_preview()

    def update_regex_preview(self, event=None):
        """实时更新正则表达式测试预览结果"""
        pattern = self.pattern_entry.get()
        replacement = self.replace_entry.get()
        test_str = self.test_input.get()
        try:
            result = re.sub(pattern, replacement, test_str)
            self.result_text.delete("1.0", tk.END)
            self.result_text.insert(tk.END, f"原文本：{test_str}\n替换后：{result}")
        except re.error as e:
            self.result_text.delete("1.0", tk.END)
            self.result_text.insert(tk.END, f"正则表达式错误：{e}")


# 主程序入口
if __name__ == "__main__":
    root = tk.Tk()
    app = RenameTools(root)
    root.mainloop()