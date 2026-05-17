import os


def get_project_root() -> str:
    current_file = os.path.abspath(__file__)
    current_dir = os.path.dirname(current_file)
    backend_dir = os.path.dirname(current_dir)
    return os.path.dirname(backend_dir)


def get_abs_path(relative_path: str) -> str:
    return os.path.join(get_project_root(), relative_path)
