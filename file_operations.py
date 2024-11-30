import os
import re

# 新建文件操作相关的类
class FileOperations:
    @staticmethod
    def rename_files(file_list, mode, target=None, replacement=None):
        """执行文件重命名操作"""
        results = []
        for file_dir, filename in file_list:
            try:
                new_name = FileOperations._get_new_name(filename, mode, target, replacement, results)
                if new_name != filename:
                    results.append((file_dir, filename, new_name))
            except Exception as e:
                # 记录错误但继续处理其他文件
                print(f"处理文件 {filename} 时发生错误: {str(e)}")
        return results

    @staticmethod
    def _get_new_name(filename, mode, target, replacement, results=None):
        """根据不同模式生成新文件名"""
        name, ext = os.path.splitext(filename)
        if mode == "replace":
            return name.replace(target, replacement) + ext
        elif mode == "regex":
            return re.sub(target, replacement, name) + ext
        else:  # sequence mode
            return f"{name}_{len(results) if results else 0:03d}{ext}"