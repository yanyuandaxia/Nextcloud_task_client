# Nextcloud Tasks 同步客户端

## 简介

**Nextcloud Tasks 同步客户端** 是一款基于 PyQt5 开发的桌面应用程序，旨在帮助用户在 Windows 和 Linux 平台上管理和同步 Nextcloud 上的任务。其中nextcloudtasks.py使用了[nextcloud-tasks](https://github.com/Sinkmanu/nextcloud-tasks)项目。图标来自 [iconfinder.com](https://www.iconfinder.com/search?q=todo&price=free)。该客户端具有以下特点：

* **任务管理** ：支持添加、编辑、删除任务，并可将任务同步至 Nextcloud 服务器。
* **周期任务** ：支持设置周期性任务，可自定义重复间隔。当周期任务到期时，自动标记为已完成并创建下一周期的新任务。
* **离线模式** ：当网络异常或处于离线模式时，仍能通过本地 JSON 文件保存任务数据，待网络恢复后进行同步。
* **多语言支持** ：内置中英文界面切换，方便不同语言用户使用。
* **系统托盘通知** ：任务截止前自动弹出托盘提醒，确保用户不错过重要事项。

## 安装与运行

### 1. 安装依赖

> pip install pyqt5 caldav

### 2. 填写配置文件

在conf.json中填写以下内容，请删除#后的注释，或者在程序的设置菜单中填写以下内容

> {
>
> "language": "zh", # zh/en,
>
> "tasks_json_path": "/path/tasks.json",
>
> "icon_path": "/path/icon.png",
>
> "url": "xxx/nextcloud/remote.php/dav/calendars/xxx/x/", # without http
>
> "username": "user",
>
> "password": "passwd",
>
> "check_interval": 60, # in seconds
>
> "show_ddl_message_box": true, # if show ddl warning box
>
> "ssl_verify_cert": false, # check cert or not
>
> "offline_mode": false # on-line or off-line mode
>
> }

### 3. 运行程序

运行主程序（例如 `main.py`）：

> python main.py

或者

> python main.py conf.json

或者直接运行可执行文件。
