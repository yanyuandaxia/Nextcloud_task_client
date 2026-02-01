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
                server_tasks = [Todo(t.data) for t in todos]
                tasks_dict_list = [task.to_dict() for task in server_tasks]
                
                # 保留本地存储的周期任务设置
                local_tasks = load_local_tasks(self.tasks_path)
                local_recurring_map = {}
                for lt in local_tasks:
                    if lt.get("uid"):
                        # 兼容旧版 recurrence_interval_days
                        interval_minutes = lt.get("recurrence_interval_minutes")
                        if interval_minutes is None and lt.get("recurrence_interval_days"):
                            interval_minutes = lt.get("recurrence_interval_days") * 24 * 60
                        local_recurring_map[lt["uid"]] = {
                            "is_recurring": lt.get("is_recurring", False),
                            "recurrence_interval_minutes": interval_minutes
                        }
                
                print(f"[DEBUG] fetch_tasks: local_recurring_map = {local_recurring_map}")
                
                for t in tasks_dict_list:
                    if t.get("uid") in local_recurring_map:
                        t["is_recurring"] = local_recurring_map[t["uid"]]["is_recurring"]
                        t["recurrence_interval_minutes"] = local_recurring_map[t["uid"]]["recurrence_interval_minutes"]
                        print(f"[DEBUG] fetch_tasks: Preserved recurring for uid={t.get('uid')}: is_recurring={t['is_recurring']}, interval_minutes={t.get('recurrence_interval_minutes')}")
                    else:
                        print(f"[DEBUG] fetch_tasks: No local recurring data for uid={t.get('uid')}")
                
                save_local_tasks(tasks_dict_list, self.tasks_path)
                # 返回包含周期字段的任务对象
                tasks = [self._create_task_object(t) for t in tasks_dict_list]
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
                # 保存周期任务设置到本地
                task_data["uid"] = uid
                tasks = load_local_tasks(self.tasks_path)
                # 更新或添加任务
                found = False
                for t in tasks:
                    if t.get("uid") == uid:
                        t.update(task_data)
                        found = True
                        break
                if not found:
                    tasks.append(task_data)
                save_local_tasks(tasks, self.tasks_path)
            except Exception as e:
                tasks = load_local_tasks(self.tasks_path)
                tasks.append(task_data)
                save_local_tasks(tasks, self.tasks_path)

    def update_task(self, uid, task_data):
        import datetime as dt
        print(f"[DEBUG] update_task called with uid={uid}")
        print(f"[DEBUG] task_data: is_recurring={task_data.get('is_recurring')}, interval={task_data.get('recurrence_interval_days')}")
        
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
                print(f"[DEBUG] Saved to local (offline mode)")
        else:
            try:
                # 确保 due 是 datetime 对象
                due_value = task_data.get("due")
                if isinstance(due_value, str):
                    try:
                        due_value = dt.datetime.strptime(due_value, "%Y-%m-%dT%H:%M:%S")
                    except Exception:
                        due_value = None
                
                print(f"[DEBUG] Calling nc_client.updateTodo with due={due_value}")
                self.nc_client.updateTodo(uid,
                                          summary=task_data["summary"],
                                          note=task_data.get("description", ""),
                                          due=due_value,
                                          priority=task_data["priority"])
                print(f"[DEBUG] Server update successful")
                
                # 保存周期任务设置到本地
                tasks = load_local_tasks(self.tasks_path)
                for t in tasks:
                    if t.get("uid") == uid:
                        t.update(task_data)
                        print(f"[DEBUG] Updated local task: is_recurring={t.get('is_recurring')}")
                        break
                save_local_tasks(tasks, self.tasks_path)
                print(f"[DEBUG] Saved to local file")
            except Exception as e:
                print(f"[DEBUG] Server update failed: {e}")
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
        task.is_recurring = t.get("is_recurring", False)
        # 兼容旧版 recurrence_interval_days
        interval_minutes = t.get("recurrence_interval_minutes")
        if interval_minutes is None and t.get("recurrence_interval_days"):
            interval_minutes = t.get("recurrence_interval_days") * 24 * 60
        task.recurrence_interval_minutes = interval_minutes
        # 保持向后兼容
        task.recurrence_interval_days = t.get("recurrence_interval_days")
        return task

