import json
import os
import tkinter as tk
from datetime import datetime
from tkinter import filedialog, simpledialog, messagebox, ttk
import re
from config import COMMON_EXTENSIONS, REGEX_TEMPLATES


class RenameTools:
    def __init__(self, root):
        self.root = root
        self.setup_window()
        self.init_variables()
        self.create_widgets()

    def setup_window(self):
        """设置窗口基本属性"""
        self.root.title("批量重命名工具")
        self.root.geometry("800x600")
        #self.root.attributes('-topmost', True)
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

    def init_variables(self):
        """初始化变量"""
        self.history_file = "rename_history.json"
        self.history = []
        self.load_history()
        self.common_extensions = COMMON_EXTENSIONS
        self.regex_templates = REGEX_TEMPLATES

        # 添加缺失的变量
        self.filter_entry = ttk.Entry(self.main_frame)
        self.include_subfolders = tk.BooleanVar(value=False)

    def create_widgets(self):
        """创建所有UI组件"""
        self._create_mode_selection()
        self._create_extension_selection()
        self._create_buttons()
        self._create_history_display()
        self._create_preview_tree()
        self._create_regex_frame()

    def _create_mode_selection(self):
        """创建模式选择部分"""
        modes = [
            ("普通替换", "replace"),
            ("正则替换", "regex"),
            ("添加序号", "sequence")
        ]

        self.mode_var = tk.StringVar(value="replace")
        for text, value in modes:
            ttk.Radiobutton(self.main_frame, text=text, value=value,
                            variable=self.mode_var).pack(anchor=tk.W)

    def _create_extension_selection(self):
        """创建文件扩展名选择部分"""
        # 添加文件扩展名选择框架
        ext_frame = ttk.LabelFrame(self.main_frame, text="文件类型", padding="5")
        ext_frame.pack(fill=tk.X, pady=10)

        # 创建扩展名选择变量
        self.selected_extensions = []
        self.extension_vars = []

        # 创建网格布局
        row = 0
        col = 0
        for ext in self.common_extensions:
            var = tk.BooleanVar(value=(ext == '.pdf'))  # 默认选择 PDF
            self.extension_vars.append(var)
            cb = ttk.Checkbutton(ext_frame, text=ext, variable=var)
            cb.grid(row=row, column=col, padx=5, pady=2, sticky=tk.W)
            col += 1
            if col > 3:  # 每行4个选项
                col = 0
                row += 1

        # 添加自定义扩展名选项
        self.custom_ext_var = tk.BooleanVar()
        self.custom_ext_frame = ttk.Frame(ext_frame)
        self.custom_ext_frame.grid(row=row + 1, column=0, columnspan=4, pady=5, sticky=tk.W)

        ttk.Checkbutton(self.custom_ext_frame, text="自定义扩展名",
                        variable=self.custom_ext_var,
                        command=self.toggle_custom_entry).pack(side=tk.LEFT)

        self.custom_ext_entry = ttk.Entry(self.custom_ext_frame, width=20)
        self.custom_ext_entry.pack(side=tk.LEFT, padx=5)
        self.custom_ext_entry.config(state='disabled')

    def _create_buttons(self):
        """创建按钮部分"""
        # 按钮框架
        btn_frame = ttk.Frame(self.main_frame)
        btn_frame.pack(pady=10)

        ttk.Button(btn_frame, text="选择文件夹",
                   command=self.rename_files).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="撤销上次操作",
                   command=self.undo_last_operation).pack(side=tk.LEFT, padx=5)

    def _create_history_display(self):
        """创建历史记录显示部分"""
        # 历史记录显示
        ttk.Label(self.main_frame, text="操作历史：").pack(anchor=tk.W)
        self.history_text = tk.Text(self.main_frame, height=10, width=60)
        self.history_text.pack(pady=10)
        self.update_history_display()

    def _create_preview_tree(self):
        """创建重命名预览树部分"""
        # 添加预览列表
        preview_frame = ttk.LabelFrame(self.main_frame, text="重命名预览", padding="5")
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        self.preview_tree = ttk.Treeview(preview_frame, columns=('原文件名', '新文件名'), show='headings')
        self.preview_tree.heading('原文件名', text='原文件名',
                                  command=lambda: self.sort_preview_tree('原文件名'))
        self.preview_tree.heading('新文件名', text='新文件名',
                                  command=lambda: self.sort_preview_tree('新文件名'))
        self.preview_tree.pack(fill=tk.BOTH, expand=True)

        # 添加滚动条
        scrollbar = ttk.Scrollbar(preview_frame, orient=tk.VERTICAL, command=self.preview_tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.preview_tree.configure(yscrollcommand=scrollbar.set)

    def _create_regex_frame(self):
        """创建正则表达式框架部分"""
        # 添加正则表达式框架
        self.regex_frame = ttk.LabelFrame(self.main_frame, text="正则表达式选项", padding="5")

        # 创建并配置正则表达式模板选择器
        ttk.Label(self.regex_frame, text="常用模板：").pack(anchor=tk.W)
        self.template_var = tk.StringVar()
        self.template_combobox = ttk.Combobox(
            self.regex_frame,
            textvariable=self.template_var,
            values=list(self.regex_templates.keys()),
            state='readonly',
            width=30
        )
        self.template_combobox.pack(fill=tk.X, pady=5)
        self.template_combobox.bind('<<ComboboxSelected>>', self.on_template_selected)

        # 添加模式说明标签
        self.template_desc = ttk.Label(self.regex_frame, text="", wraplength=400)
        self.template_desc.pack(fill=tk.X, pady=5)

        # 添加正则表达式输入框
        pattern_frame = ttk.Frame(self.regex_frame)
        pattern_frame.pack(fill=tk.X, pady=5)
        ttk.Label(pattern_frame, text="匹配模式：").pack(side=tk.LEFT)
        self.pattern_entry = ttk.Entry(pattern_frame)
        self.pattern_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # 添加替换文本输入框
        replace_frame = ttk.Frame(self.regex_frame)
        replace_frame.pack(fill=tk.X, pady=5)
        ttk.Label(replace_frame, text="替换文本：").pack(side=tk.LEFT)
        self.replace_entry = ttk.Entry(replace_frame)
        self.replace_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # 添加测试按钮
        ttk.Button(self.regex_frame, text="测试正则表达式",
                   command=self.test_regex).pack(pady=5)

        # 在模式为正则替换时显示正则框架
        self.mode_var.trace('w', self.toggle_regex_frame)

    def toggle_custom_entry(self):
        """切换自定义扩展名输入框的状态"""
        if self.custom_ext_var.get():
            self.custom_ext_entry.config(state='normal')
        else:
            self.custom_ext_entry.config(state='disabled')

    def get_selected_extensions(self):
        """获取所有选中的扩展名"""
        extensions = []

        # 获取选中的常用扩展名
        for var, ext in zip(self.extension_vars, self.common_extensions):
            if var.get():
                extensions.append(ext)

        # 获取自定义扩展名
        if self.custom_ext_var.get():
            custom_exts = self.custom_ext_entry.get().strip()
            if custom_exts:
                # 处理用户输入的自定义扩展名
                custom_list = [ext.strip() for ext in custom_exts.split(',')]
                # 确保所有扩展名都以点开头
                custom_list = [ext if ext.startswith('.') else f'.{ext}' for ext in custom_list]
                extensions.extend(custom_list)

        return extensions

    def get_all_files(self, directory):
        files_list = []
        filter_text = self.filter_entry.get().strip()

        if self.include_subfolders.get():
            for root, _, files in os.walk(directory):
                for file in files:
                    if not filter_text or filter_text in file:
                        files_list.append((root, file))
        else:
            for file in os.listdir(directory):
                if os.path.isfile(os.path.join(directory, file)):
                    files_list.append((directory, file))
        return files_list

    def rename_files(self):
        directory = filedialog.askdirectory()
        if not directory:
            return

        extensions = self.get_selected_extensions()
        if not extensions:
            messagebox.showwarning("警告", "请至少选择一个文件类型")
            return

        if self.mode_var.get() in ["replace", "regex"]:
            target = simpledialog.askstring("输入",
                                            "请输入要替换的" + (
                                                "正则表达式" if self.mode_var.get() == "regex" else "字段") + "：")
            if target is None:
                return
            replacement = simpledialog.askstring("输入", "请输入替换后的内容：",
                                                 initialvalue="")
            if replacement is None:
                return

            if self.mode_var.get() == "regex":
                try:
                    # 测试正则表达式是否有效
                    re.compile(target)
                except re.error:
                    messagebox.showerror("错误", "无效的正则表达式")
                    return

        # 预览更改
        preview = []
        files_list = self.get_all_files(directory)

        for file_dir, filename in files_list:
            if any(filename.endswith(ext) for ext in extensions):
                name, ext = os.path.splitext(filename)
                if self.mode_var.get() == "replace":
                    newname = name.replace(target, replacement) + ext
                elif self.mode_var.get() == "regex":
                    try:
                        newname = re.sub(target, replacement, name) + ext
                    except re.error as e:
                        messagebox.showerror("错误", f"正则表达式替换失败：{str(e)}")
                        return
                else:  # sequence mode
                    newname = f"{name}_{len(preview):03d}{ext}"

                if filename != newname:
                    preview.append((file_dir, filename, newname))

        if not preview:
            messagebox.showinfo("提示", "没有找到需要重命名的文件")
            return

        # 检查文件名冲突
        new_names = set()
        for _, _, new_name in preview:
            if new_name in new_names:
                messagebox.showerror("错误", f"检测到重复的新文件名: {new_name}")
                return
            new_names.add(new_name)

        preview_text = "\n".join([f"{os.path.join(d, old)} -> {os.path.join(d, new)}"
                                  for d, old, new in preview])
        if messagebox.askyesno("预览", f"将进行以下重命名：\n\n{preview_text}\n\n是否继续？"):
            # 创建进度条
            progress = ttk.Progressbar(self.main_frame, length=300, mode='determinate')
            progress.pack(pady=10)

            # 保存操作记录用于撤销
            operation_record = {
                'timestamp': datetime.now().isoformat(),
                'changes': []
            }

            # 执行重命名
            for i, (file_dir, old, new) in enumerate(preview):
                old_path = os.path.join(file_dir, old)
                new_path = os.path.join(file_dir, new)

                # 备份原始文件信息
                operation_record['changes'].append({
                    'old_path': old_path,
                    'new_path': new_path
                })

                os.rename(old_path, new_path)
                progress['value'] = (i + 1) / len(preview) * 100
                self.root.update()

            # 保存操作记录
            self.history.append(operation_record)
            self.save_history()
            self.update_history_display()

            progress.destroy()
            messagebox.showinfo("完成", f"完成 {len(preview)} 个文件的重命名")

            # 更新预览树
            self.preview_tree.delete(*self.preview_tree.get_children())
            for file_dir, old, new in preview:
                self.preview_tree.insert('', tk.END, values=(old, new))

    def undo_last_operation(self):
        if not self.history:
            messagebox.showinfo("提示", "没有可撤销的操作")
            return

        last_operation = self.history[-1]
        if messagebox.askyesno("确认", "确定要撤销上次重命名操作吗？"):
            try:
                # 反向执行重命名操作
                for change in reversed(last_operation['changes']):
                    if os.path.exists(change['new_path']):
                        os.rename(change['new_path'], change['old_path'])

                # 从历史记录中删除该操作
                self.history.pop()
                self.save_history()
                self.update_history_display()

                # 更新预览树
                self.preview_tree.delete(*self.preview_tree.get_children())
                for change in last_operation['changes']:
                    self.preview_tree.insert('', tk.END, values=(
                    os.path.basename(change['new_path']), os.path.basename(change['old_path'])))

                messagebox.showinfo("完成", "撤销操作完成")
            except Exception as e:
                messagebox.showerror("错误", f"撤销操作失败：{str(e)}")

    def load_history(self):
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    self.history = json.load(f)
        except Exception:
            self.history = []

    def save_history(self):
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            messagebox.showerror("错误", f"保存历史记录失败：{str(e)}")

    def update_history_display(self):
        self.history_text.delete(1.0, tk.END)
        for operation in reversed(self.history[-5:]):  # 只显示最近5次操作
            time_str = datetime.fromisoformat(operation['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
            self.history_text.insert(tk.END, f"操作时间：{time_str}\n")
            for change in operation['changes']:
                self.history_text.insert(tk.END,
                                         f"  {os.path.basename(change['old_path'])} -> {os.path.basename(change['new_path'])}\n")
            self.history_text.insert(tk.END, "-" * 50 + "\n")

    def sort_preview_tree(self, col):
        """排序预览树的内容"""
        items = [(self.preview_tree.set(item, col), item) for item in self.preview_tree.get_children('')]
        items.sort()

        for index, (_, item) in enumerate(items):
            self.preview_tree.move(item, '', index)

    def toggle_regex_frame(self, *args):
        """根据选择的模式显示或隐藏正则表达式框架"""
        if self.mode_var.get() == "regex":
            self.regex_frame.pack(fill=tk.X, pady=10, after=self.main_frame.winfo_children()[2])
        else:
            self.regex_frame.pack_forget()

    def on_template_selected(self, event):
        """当选择模板时更新界面"""
        template_name = self.template_var.get()
        if template_name in self.regex_templates:
            template = self.regex_templates[template_name]
            self.pattern_entry.delete(0, tk.END)
            self.pattern_entry.insert(0, template['pattern'])
            self.replace_entry.delete(0, tk.END)
            self.replace_entry.insert(0, template['replacement'])
            self.template_desc.config(text=template['description'])

    def test_regex(self):
        """测试正则表达式"""
        pattern = self.pattern_entry.get()
        replacement = self.replace_entry.get()

        if not pattern:
            messagebox.showwarning("警告", "请输入正则表达式")
            return

        # 创建测试对话框
        test_dialog = tk.Toplevel(self.root)
        test_dialog.title("正则表达式测试")
        test_dialog.geometry("400x300")

        # 添加测试输入框
        ttk.Label(test_dialog, text="测试文本：").pack(pady=5)
        test_input = ttk.Entry(test_dialog)
        test_input.pack(fill=tk.X, padx=5)

        # 添加结果显示
        ttk.Label(test_dialog, text="匹配结果：").pack(pady=5)
        result_text = tk.Text(test_dialog, height=5)
        result_text.pack(fill=tk.BOTH, expand=True, padx=5)

        def update_result(*args):
            """更新测试结果"""
            try:
                test_str = test_input.get()
                if test_str:
                    result = re.sub(pattern, replacement, test_str)
                    result_text.delete(1.0, tk.END)
                    result_text.insert(tk.END, f"原文本：{test_str}\n")
                    result_text.insert(tk.END, f"替换后：{result}")
            except re.error as e:
                result_text.delete(1.0, tk.END)
                result_text.insert(tk.END, f"正则表达式错误：{str(e)}")

        # 绑定输入事件
        test_input.bind('<KeyRelease>', update_result)


# 创建主窗口
root = tk.Tk()
app = RenameTools(root)
root.mainloop()