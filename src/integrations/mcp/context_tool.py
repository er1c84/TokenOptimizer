from pathlib import Path

from ...config import Settings
from ...core.scanner import scan_project 
from ...core.optimizer import select_context

def build_context(project_path, task, budget=4000):
    settings = Settings(token_budget=budget)
    project = Path(project_path)
    scan = scan_project(project, settings)
    return select_context(scan, 
budget=settings.token_budget, task=task)