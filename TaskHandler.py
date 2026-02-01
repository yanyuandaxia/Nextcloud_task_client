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
                
                print(f"[DEBUG] fetch_tasks: received {len(tasks_dict_list)} tasks from server")
                
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
                note = task_data.get('description', '')
                # 确保 due 为 datetime 对象
                due_value = task_data.get('due')
                try:
                    import datetime as _dt
                    if isinstance(due_value, str):
                        due_value = _dt.datetime.strptime(due_value, "%Y-%m-%dT%H:%M:%S")
                except Exception:
                    pass
                
                # Extract RRULE - 如果没有 rrule 则传空字符串以清除服务器端的 RRULE
                rrule_val = task_data.get('rrule')
                if not rrule_val:
                      rrule_val = ""

                self.nc_client.updateTodo(uid,
                                          note=note,
                                          due=due_value,
                                          priority=task_data["priority"],
                                          rrule=rrule_val)
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
        print(f"[DEBUG] task_data: rrule={task_data.get('rrule')}")
        
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
                        pass # keep valid string? Or datetime? nc_client expects datetime mostly.

                # Get RRULE directly - 如果没有 rrule 则传空字符串以清除服务器端的 RRULE
                rrule_val = task_data.get("rrule")
                if not rrule_val:
                     rrule_val = ""

                # Note is just the user description
                note = task_data.get("description", "")

                print(f"[DEBUG] Calling nc_client.updateTodo with due={due_value}, rrule={rrule_val}")
                
                self.nc_client.updateTodo(uid,
                                          summary=task_data["summary"],
                                          note=note,
                                          due=due_value,
                                          priority=task_data["priority"],
                                          rrule=rrule_val)
                print(f"[DEBUG] Server update successful")

                # 保存到本地，并更新 last_modified
                now_str = dt.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
                tasks = load_local_tasks(self.tasks_path)
                for t in tasks:
                    if t.get("uid") == uid:
                        t.update(task_data)
                        t['last_modified'] = now_str
                        # 设置 rrule
                        t['rrule'] = rrule_val if rrule_val else None
                        print(f"[DEBUG] Updated local task: rrule={t.get('rrule')}")
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
        task.rrule = t.get("rrule", "")
        return task

