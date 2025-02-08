import os
import json
import datetime

SERVER_TASKS_FILE = "server_tasks.json"


def load_server_tasks():
    """
    从 server_tasks.json 中加载任务列表，每个任务为一个字典。
    如果存在截止时间字段，将其从字符串转换为 datetime 对象。
    """
    if os.path.exists(SERVER_TASKS_FILE):
        with open(SERVER_TASKS_FILE, "r", encoding="utf-8") as f:
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


def save_server_tasks(tasks):
    """
    将任务列表保存到 server_tasks.json 中。
    如果任务中包含 datetime 类型的截止时间，则转换为字符串保存。
    """
    tasks_to_save = []
    for task in tasks:
        new_task = task.copy()
        if new_task.get("due") and isinstance(new_task["due"], datetime.datetime):
            new_task["due"] = new_task["due"].strftime("%Y-%m-%dT%H:%M:%S")
        tasks_to_save.append(new_task)
    with open(SERVER_TASKS_FILE, "w", encoding="utf-8") as f:
        json.dump(tasks_to_save, f, ensure_ascii=False, indent=4)
