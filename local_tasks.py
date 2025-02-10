import os
import json
import datetime


def load_local_tasks(path_tasks):
    """
    从 tasks.json 中加载任务列表，每个任务为一个字典。
    如果存在截止时间字段，将其从字符串转换为 datetime 对象。
    """
    if os.path.exists(path_tasks):
        with open(path_tasks, "r", encoding="utf-8") as f:
            try:
                tasks = json.load(f)
            except json.JSONDecodeError:
                tasks = []
    else:
        tasks = []
    for task in tasks:
        if task.get("due"):
            try:
                task["due"] = datetime.datetime.strptime(
                    task["due"], "%Y-%m-%dT%H:%M:%S")
            except Exception:
                task["due"] = None
    return tasks


def save_local_tasks(tasks, path_tasks):
    """
    将任务列表保存到 tasks.json 中。
    如果任务中包含 datetime 类型的截止时间，则转换为字符串保存。
    """
    tasks_to_save = []
    for task in tasks:
        new_task = task.copy()
        if new_task.get("due") and isinstance(new_task["due"], datetime.datetime):
            new_task["due"] = new_task["due"].strftime("%Y-%m-%dT%H:%M:%S")
        tasks_to_save.append(new_task)
    with open(path_tasks, "w", encoding="utf-8") as f:
        json.dump(tasks_to_save, f, ensure_ascii=False, indent=4)
