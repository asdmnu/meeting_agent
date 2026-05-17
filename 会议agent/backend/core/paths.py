import os


def get_project_root() -> str:
    current_file = os.path.abspath(__file__)
    current_dir = os.path.dirname(current_file)
    backend_dir = os.path.dirname(current_dir)
    project_root = os.path.dirname(backend_dir)
    return project_root


def get_abs_path(relative_path: str) -> str:
    return os.path.join(get_project_root(), relative_path)
