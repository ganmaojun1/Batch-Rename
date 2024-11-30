# 新建配置文件存储常量
COMMON_EXTENSIONS = [
    '.txt', '.doc', '.docx', '.pdf',
    '.jpg', '.jpeg', '.png', '.gif',
    '.mp3', '.mp4', '.avi', '.mkv'
]

REGEX_TEMPLATES = {
    '删除括号及内容': {
        'pattern': r'\(.*?\)',
        'replacement': '',
        'description': '删除文件名中的括号及括号内的所有内容'
    },
    '提取数字': {
        'pattern': r'.*?(\d+).*',
        'replacement': r'文件\1',
        'description': '提取文件名中的数字作为新文件名'
    },
    '删除多余空格': {
        'pattern': r'\s+',
        'replacement': ' ',
        'description': '将多个连续空格替换为单个空格'
    },
    '删除特殊字符': {
        'pattern': r'[^\w\s\.]',
        'replacement': '',
        'description': '删除除字母、数字、空格和点之外的所有特殊字符'
    },
    '日期格式化': {
        'pattern': r'(\d{4})-(\d{2})-(\d{2})',
        'replacement': r'\1年\2月\3日',
        'description': '将YYYY-MM-DD格式转换为中文日期格式'
    }
}