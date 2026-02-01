#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import caldav
import datetime
import json
import uuid
import re
import urllib3
# urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


todo_skeleton = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//TODOcli Nextcloud tasks 0.1
BEGIN:VTODO
CREATED;X-VOBJ-FLOATINGTIME-ALLOWED=TRUE:{}
DTSTAMP;X-VOBJ-FLOATINGTIME-ALLOWED=TRUE:{}
LAST-MODIFIED;X-VOBJ-FLOATINGTIME-ALLOWED=TRUE:{}
SUMMARY:{}
UID:{}
PRIORITY:{}
PERCENT-COMPLETE:{}
STATUS: {}
END:VTODO
END:VCALENDAR"""

# 异常定义


class SummaryNotFound(Exception):
    pass


class TaskNotFound(Exception):
    def __init__(self, task):
        super().__init__("Task \"%s\" not found." % task)


class ListNotFound(Exception):
    def __init__(self, list):
        super().__init__("List \"%s\" not found." % list)

# Todo 类：解析任务的 VTODO 数据

def make_rrule(freq, interval=1):
    """
    Create RRULE string from frequency type and interval.
    freq: 'DAILY', 'WEEKLY', 'MONTHLY', 'YEARLY', 'HOURLY', 'MINUTELY'
    interval: integer >= 1
    """
    if not freq:
        return None
    interval = max(1, int(interval))
    return f"FREQ={freq};INTERVAL={interval}"


def minutes_to_rrule(minutes):
    """
    Convert minutes integer to RRULE string (for custom intervals).
    Tries to find largest frequency (DAILY, HOURLY) for cleaner RRULE,
    otherwise defaults to MINUTELY.
    """
    if not minutes or minutes <= 0:
        return None
    
    # Check DAILY
    if minutes % 1440 == 0:
        days = minutes // 1440
        return f"FREQ=DAILY;INTERVAL={days}"
    
    # Check HOURLY
    if minutes % 60 == 0:
        hours = minutes // 60
        return f"FREQ=HOURLY;INTERVAL={hours}"
        
    return f"FREQ=MINUTELY;INTERVAL={minutes}"


def parse_rrule(rrule_str):
    """
    Parse RRULE string to (freq, interval) tuple.
    Returns (None, 1) if invalid.
    """
    if not rrule_str:
        return (None, 1)
    
    rrule_str = rrule_str.strip()
    parts = rrule_str.split(';')
    freq = None
    interval = 1
    
    for part in parts:
        kv = part.split('=')
        if len(kv) != 2:
            continue
        k, v = kv[0].strip(), kv[1].strip()
        
        if k == 'FREQ':
            freq = v
        elif k == 'INTERVAL':
            try:
                interval = int(v)
            except:
                interval = 1
    
    return (freq, interval)


def parse_rrule_to_minutes(rrule_str):
    """
    Parse RRULE string to minutes.
    Supports FREQ=DAILY, WEEKLY, MONTHLY, YEARLY, HOURLY, MINUTELY.
    For MONTHLY/YEARLY, returns approximate values.
    """
    freq, interval = parse_rrule(rrule_str)
    
    if not freq:
        return None
        
    minutes = 0
    if freq == 'MINUTELY':
        minutes = 1
    elif freq == 'HOURLY':
        minutes = 60
    elif freq == 'DAILY':
        minutes = 24 * 60
    elif freq == 'WEEKLY':
        minutes = 7 * 24 * 60
    elif freq == 'MONTHLY':
        minutes = 30 * 24 * 60  # Approximate
    elif freq == 'YEARLY':
        minutes = 365 * 24 * 60  # Approximate
    else:
        return None
        
    return minutes * interval


class Todo:
    def __init__(self, todo):
        self.todo = todo
        self.summary = re.search('SUMMARY:(.*?)\n', todo, re.DOTALL).group(1)
        self.created = datetime.datetime.strptime(
            re.search('CREATED(?:;X-VOBJ-FLOATINGTIME-ALLOWED=TRUE|):(.*?)(?:Z)?\n',
                      todo, re.DOTALL).group(1),
            '%Y%m%dT%H%M%S'
        )
        self.dtstamp = datetime.datetime.strptime(
            re.search('DTSTAMP(?:;X-VOBJ-FLOATINGTIME-ALLOWED=TRUE|):(.*?)(?:Z)?\n',
                      todo, re.DOTALL).group(1),
            '%Y%m%dT%H%M%S'
        )
        self.last_modified = datetime.datetime.strptime(
            re.search('LAST-MODIFIED(?:;X-VOBJ-FLOATINGTIME-ALLOWED=TRUE|):(.*?)(?:Z)?\n',
                      todo, re.DOTALL).group(1),
            '%Y%m%dT%H%M%S'
        )
        self.uid = re.search('UID:(.*?)\n', todo, re.DOTALL).group(1)
        try:
            # 修改这里，允许尾部 Z 可选
            self.due = datetime.datetime.strptime(
                re.search('DUE:(.*?)(?:Z)?\n', todo, re.DOTALL).group(1),
                '%Y%m%dT%H%M%S'
            )
        except Exception:
            self.due = None
        try:
            self.priority = re.search(
                'PRIORITY:(.*?)\n', todo, re.DOTALL).group(1)
        except:
            self.priority = None
        try:
            self.percent_complete = int(
                re.search('PERCENT-COMPLETE:(.*?)\n', todo, re.DOTALL).group(1))
        except:
            self.percent_complete = None
        try:
            self.status = re.search('STATUS:(.*?)\n', todo, re.DOTALL).group(1)
        except:
            self.status = None
        try:
            self.completed = datetime.datetime.strptime(
                re.search('COMPLETED:(.*?)\n', todo, re.DOTALL).group(1),
                '%Y%m%dT%H%M%S'
            )
        except:
            self.completed = None
        try:
            self.dtstart = datetime.datetime.strptime(
                re.search('DTSTART:(.*?)\n', todo, re.DOTALL).group(1),
                '%Y%m%dT%H%M%S'
            )
        except:
            self.dtstart = None
        try:
            self.description = re.search(
                'DESCRIPTION:(.*?)\n', todo, re.DOTALL).group(1)
        except:
            self.description = None
        try:
            self.related_to = re.search(
                'RELATED-TO:(.*?)\n', todo, re.DOTALL).group(1)
        except:
            self.related_to = None

        # 只解析 VTODO 组件内的 RRULE，避免匹配到 VTIMEZONE 中的 RRULE
        try:
            # 先提取 VTODO 部分
            vtodo_match = re.search(r'BEGIN:VTODO(.*?)END:VTODO', todo, re.DOTALL)
            if vtodo_match:
                vtodo_content = vtodo_match.group(1)
                rrule_match = re.search(r'RRULE:(.*?)\n', vtodo_content, re.DOTALL)
                self.rrule = rrule_match.group(1) if rrule_match else None
            else:
                self.rrule = None
        except:
            self.rrule = None

    def __str__(self):
        return "Todo(uid={}, summary={})".format(self.uid, self.summary)

    def to_dict(self):
        return {
            "summary": self.summary,
            "uid": self.uid,
            "priority": self.priority,
            "due": self.due.strftime("%Y-%m-%dT%H:%M:%S") if self.due else None,
            "status": self.status,
            "description": self.description,
            "percent_complete": self.percent_complete,
            "rrule": self.rrule,
            "last_modified": self.last_modified.strftime("%Y-%m-%dT%H:%M:%S") if hasattr(self, 'last_modified') and self.last_modified else None,
            # 根据需要可以加入其它字段
        }

# NextcloudTask 类：处理与 Nextcloud 的连接及任务增删改查


class NextcloudTask:
    def __init__(self, config, list_in=None):
        self.config = config
        self.url = config['url']
        if list_in is None:
            self.list = []
        else:
            self.list = list_in
        self.connected = False
        self.sort = ("priority",)

    def connect(self, username, password):
        try:
            url = self.url.split("://")[1]
        except IndexError:
            url = self.url
        self.client = caldav.DAVClient(
            "https://"+username+":"+password+"@"+url, ssl_verify_cert=self.config["ssl_verify_cert"])
        try:
            self.calendar = self.client.principal().calendar(self.list)
        except caldav.error.NotFoundError:
            raise ListNotFound(self.list)
        self.todos = self.client.principal().calendar(self.list).todos()
        self.connected = True

    def updateTodos(self):
        self.todos = self.client.principal().calendar(self.list).todos()

    def addTodo(self, summary, priority=0, percent_complete=0, rrule=None):
        if percent_complete == 100:
            status = "COMPLETED"
        elif percent_complete == 0:
            status = "NEEDS-ACTION"
        else:
            status = "IN-PROCESS"
        todo = todo_skeleton.format(
            datetime.datetime.now().strftime('%Y%m%dT%H%M%S'),
            datetime.datetime.now().strftime('%Y%m%dT%H%M%S'),
            datetime.datetime.now().strftime('%Y%m%dT%H%M%S'),
            summary, str(uuid.uuid4()), str(
                priority), str(percent_complete), status
        )
        if rrule:
            todo = todo.replace("END:VTODO", f"RRULE:{rrule}\nEND:VTODO")
        self.calendar.save_todo(todo)
        self.updateTodos()

    def updateTodo(self, uid, summary=None, start=None, due=None, note=None,
                   priority=None, percent_complete=None, categories=None, rrule=None):
        todo = self.getTodoByUid(uid)
        if summary is not None:
            todo.icalendar_component['SUMMARY'] = summary
        if note is not None:
            todo.icalendar_component['DESCRIPTION'] = note
        if categories is not None:
            todo.icalendar_component['CATEGORIES'] = categories
        if start is not None:
            todo.icalendar_component['DTSTART'] = start.strftime(
                '%Y%m%dT%H%M%S')
        if due is not None:
            todo.icalendar_component['DUE'] = due.strftime('%Y%m%dT%H%M%S')
        elif 'DUE' in todo.icalendar_component:
            del todo.icalendar_component['DUE']
        if priority is not None:
            todo.icalendar_component['PRIORITY'] = priority
        if percent_complete is not None:
            todo.icalendar_component['PERCENT-COMPLETE'] = percent_complete
            if percent_complete == 0:
                todo.icalendar_component['STATUS'] = "NEEDS-ACTION"
            elif percent_complete == 100:
                todo.icalendar_component['STATUS'] = "COMPLETED"
                todo.icalendar_component['COMPLETED'] = datetime.datetime.now().strftime(
                    '%Y%m%dT%H%M%S')
            else:
                todo.icalendar_component['STATUS'] = "IN-PROCESS"
        
        if rrule == "": # Explicit delete if empty string passed
            # 删除 VTODO 组件中的 RRULE
            if 'RRULE' in todo.icalendar_component:
                del todo.icalendar_component['RRULE']
        elif rrule is not None:
            from icalendar import vRecur
            # Set or Update RRULE
            # vRecur.from_ical returns a dict, we must wrap it in vRecur object for correct serialization
            todo.icalendar_component['RRULE'] = vRecur(vRecur.from_ical(rrule))
        
        todo.icalendar_component['LAST-MODIFIED'] = datetime.datetime.now().strftime(
            '%Y%m%dT%H%M%S')
        # 清除 _data 缓存，强制从 icalendar_instance 重新生成数据
        # 这确保对 icalendar_component 的修改会被正确保存到服务器
        todo._data = None
        todo.save()
        self.updateTodos()

    def getTodoByUid(self, uid):
        return self.client.principal().calendar(self.list).todo_by_uid(uid)

    def getUidbySummary(self, summary):
        output = ""
        for todo in self.todos:
            if todo.icalendar_component["SUMMARY"] == summary:
                output = todo.icalendar_component["UID"]
                break
        if output == "":
            raise SummaryNotFound
        else:
            return output

    def deleteByUid(self, uid):
        """
        根据任务 UID 删除服务器上的任务
        """
        try:
            # 获取对应的任务对象，然后调用其 delete() 方法
            todo = self.client.principal().calendar(self.list).todo_by_uid(uid)
            todo.delete()
        except caldav.error.NotFoundError:
            raise TaskNotFound(uid)
