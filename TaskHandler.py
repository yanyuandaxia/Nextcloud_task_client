# ---------------------------
# 任务操作处理类
# ---------------------------


from local_tasks import load_local_tasks, save_local_tasks
from nextcloudtasks import Todo


def pack_meta_into_note(task):
    """Return a visible Recurrence Info block (no hidden meta)."""
    meta = {}
    if task.get('is_recurring'):
        meta['is_recurring'] = bool(task.get('is_recurring', False))
    if task.get('recurrence_interval_minutes') is not None:
        meta['recurrence_interval_minutes'] = task.get('recurrence_interval_minutes')
    if task.get('recurrence_interval_days') is not None:
        meta['recurrence_interval_days'] = task.get('recurrence_interval_days')
    if task.get('due') is not None:
        dv = task.get('due')
        try:
            if isinstance(dv, str):
                meta['due'] = dv
            else:
                meta['due'] = dv.isoformat()
        except Exception:
            meta['due'] = str(dv)

    if not meta:
        return task.get('description', '')

    visible_lines = ["Recurrence Info"]
    if meta.get('due'):
        # show as `YYYY-MM-DD HH:MM`
        d = meta.get('due')
        try:
            if 'T' in d:
                d = d.replace('T', ' ')[:16]
            else:
                d = d[:16]
        except Exception:
            pass
        visible_lines.append(f"Deadline: {d}")

    mins = meta.get('recurrence_interval_minutes')
    if mins is None and meta.get('recurrence_interval_days') is not None:
        mins = meta.get('recurrence_interval_days') * 24 * 60
    if mins is not None:
        visible_lines.append(f"Recurrence: {int(mins)} Mins")

    return "\n".join(visible_lines)


def unpack_meta_from_note(note):
    """Parse visible Recurrence Info block from note.
    Return (clean_note, meta_dict). If note is only the block, clean_note will be ''.
    """
    if not note:
        return '', {}

    lines = [ln.strip() for ln in note.splitlines() if ln.strip()]
    if not lines:
        return note, {}

    # Look for 'Recurrence Info' as the first non-empty line
    try:
        idx = lines.index('Recurrence Info')
    except ValueError:
        return note, {}

    meta = {'is_recurring': True}
    # parse following lines
    for ln in lines[idx+1:]:
        if ln.startswith('Deadline:'):
            val = ln.split('Deadline:', 1)[1].strip()
            # convert to ISO-like 'YYYY-MM-DDTHH:MM:SS'
            try:
                if ' ' in val:
                    date_part = val
                else:
                    date_part = val
                # append seconds if missing
                if len(date_part) == 16:
                    iso = date_part.replace(' ', 'T') + ':00'
                elif 'T' in date_part and len(date_part) == 16:
                    iso = date_part + ':00'
                else:
                    iso = date_part.replace(' ', 'T')
                meta['due'] = iso
            except Exception:
                meta['due'] = val
        elif ln.startswith('Recurrence:'):
            val = ln.split('Recurrence:', 1)[1].strip()
            # expect like 'X Mins' or 'X'
            try:
                parts = val.split()
                num = int(parts[0])
                meta['recurrence_interval_minutes'] = num
            except Exception:
                pass

    # If the whole note is the block, return clean_note = ''
    # Otherwise, try to return any preceding text before the block
    # Find original note split position
    if 'Recurrence Info' in note:
        pre = note.split('Recurrence Info', 1)[0].strip()
        return pre, meta

    return note, {}


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
                    # 先从服务器返回的 description 中尝试解析元数据
                    desc, meta = unpack_meta_from_note(t.get('description', ''))
                    if desc != t.get('description', ''):
                        t['description'] = desc
                    # 如果 meta 中包含周期信息，则使用之
                    if meta.get('is_recurring') is not None:
                        t['is_recurring'] = meta.get('is_recurring')
                    if meta.get('recurrence_interval_minutes') is not None:
                        t['recurrence_interval_minutes'] = meta.get('recurrence_interval_minutes')
                    elif meta.get('recurrence_interval_days') is not None:
                        t['recurrence_interval_minutes'] = meta.get('recurrence_interval_days') * 24 * 60
                    # 如果元数据中包含 due 且服务器没有返回 due，则使用元数据中的 due
                    if meta.get('due') and not t.get('due'):
                        t['due'] = meta.get('due')

                    if t.get("uid") in local_recurring_map:
                        # 本地优先保留本地设置
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
                note = pack_meta_into_note(task_data)
                # 确保 due 为 datetime 对象
                due_value = task_data.get('due')
                try:
                    import datetime as _dt
                    if isinstance(due_value, str):
                        due_value = _dt.datetime.strptime(due_value, "%Y-%m-%dT%H:%M:%S")
                except Exception:
                    pass
                self.nc_client.updateTodo(uid,
                                          note=note,
                                          due=due_value,
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
                # 将周期元数据打包进 note 中
                note = pack_meta_into_note(task_data)
                self.nc_client.updateTodo(uid,
                                          summary=task_data["summary"],
                                          note=note,
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

