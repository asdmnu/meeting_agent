import os


def get_project_root() -> str:
    """Return the repository root based on this file location."""
    current_file = os.path.abspath(__file__)
    current_dir = os.path.dirname(current_file)
    backend_dir = os.path.dirname(current_dir)
    return os.path.dirname(backend_dir)


def get_abs_path(relative_path: str) -> str:
    """Resolve a repository-relative path to an absolute path."""
    return os.path.join(get_project_root(), relative_path)
