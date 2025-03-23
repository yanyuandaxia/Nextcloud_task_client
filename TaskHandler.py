# ---------------------------
# 任务操作处理类
# ---------------------------


from local_tasks import load_local_tasks, save_local_tasks
from nextcloudtasks import Todo


class TaskHandler:
    def __init__(self, config, tasks_path, nc_client):
        self.config = config
        self.tasks_path = tasks_path
        self.nc_client = nc_client
        self.offline_mode = config["offline_mode"]

    def fetch_tasks(self):
        if self.offline_mode:
            tasks_list = load_local_tasks(self.tasks_path)
            tasks = [self._create_task_object(t) for t in tasks_list]
            return tasks
        else:
            try:
                self.nc_client.updateTodos()
                todos = self.nc_client.todos
                tasks = [Todo(t.data) for t in todos]
                tasks_dict_list = [task.to_dict() for task in tasks]
                save_local_tasks(tasks_dict_list, self.tasks_path)
                return tasks
            except Exception as e:
                tasks_list = load_local_tasks(self.tasks_path)
                tasks = [self._create_task_object(t) for t in tasks_list]
                return tasks

    def add_task(self, task_data):
        if self.offline_mode:
            tasks = load_local_tasks(self.tasks_path)
            tasks.append(task_data)
            save_local_tasks(tasks, self.tasks_path)
        else:
            try:
                self.nc_client.addTodo(task_data["summary"],
                                       priority=task_data["priority"],
                                       percent_complete=0)
                self.nc_client.updateTodos()
                uid = self.nc_client.getUidbySummary(task_data["summary"])
                self.nc_client.updateTodo(uid,
                                          note=task_data["description"],
                                          due=task_data["due"],
                                          priority=task_data["priority"])
            except Exception as e:
                tasks = load_local_tasks(self.tasks_path)
                tasks.append(task_data)
                save_local_tasks(tasks, self.tasks_path)

    def update_task(self, uid, task_data):
        if self.offline_mode:
            tasks = load_local_tasks(self.tasks_path)
            updated = False
            for t in tasks:
                if t.get("uid") == uid:
                    t.update(task_data)
                    updated = True
                    break
            if updated:
                save_local_tasks(tasks, self.tasks_path)
        else:
            try:
                self.nc_client.updateTodo(uid,
                                          summary=task_data["summary"],
                                          note=task_data["description"],
                                          due=task_data["due"],
                                          priority=task_data["priority"])
            except Exception as e:
                tasks = load_local_tasks(self.tasks_path)
                for t in tasks:
                    if t.get("uid") == uid:
                        t.update(task_data)
                        break
                save_local_tasks(tasks, self.tasks_path)

    def delete_task(self, uid, summary):
        if not self.offline_mode and uid:
            try:
                self.nc_client.deleteByUid(uid)
            except Exception as e:
                pass
        tasks = load_local_tasks(self.tasks_path)
        if uid:
            tasks = [t for t in tasks if t.get("uid") != uid]
        else:
            tasks = [t for t in tasks if t.get("summary") != summary]
        save_local_tasks(tasks, self.tasks_path)

    def update_status(self, uid, summary, new_status, percent_complete):
        tasks = load_local_tasks(self.tasks_path)
        for t in tasks:
            if (uid and t.get("uid") == uid) or (not uid and t.get("summary") == summary):
                t["status"] = new_status
                t["percent_complete"] = percent_complete
                break
        save_local_tasks(tasks, self.tasks_path)
        if not self.offline_mode and uid:
            try:
                self.nc_client.updateTodo(
                    uid, percent_complete=percent_complete)
            except Exception as e:
                pass

    def _create_task_object(self, t):
        task = type("LocalTask", (), {})()
        task.summary = t.get("summary", "")
        task.uid = t.get("uid", "")
        task.priority = t.get("priority", "")
        task.due = t.get("due", None)
        task.description = t.get("description", "")
        task.status = t.get("status", "NEEDS-ACTION")
        return task
