import os


def get_project_root() -> str:
    """根据当前文件位置返回仓库根目录。"""
    current_file = os.path.abspath(__file__)
    current_dir = os.path.dirname(current_file)
    backend_dir = os.path.dirname(current_dir)
    return os.path.dirname(backend_dir)


def get_abs_path(relative_path: str) -> str:
    """将仓库相对路径解析为绝对路径。"""
    return os.path.join(get_project_root(), relative_path)
