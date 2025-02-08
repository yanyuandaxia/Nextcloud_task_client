# Nextcloud Task 同步客户端

## 简介

**Nextcloud Task 同步客户端** 是一款基于 PyQt5 开发的桌面应用程序，旨在帮助用户在 Windows 和 Linux 平台上管理和同步 Nextcloud 上的任务。其中nextcloudtasks.py使用了[nextcloud-tasks](https://github.com/Sinkmanu/nextcloud-tasks)项目。图标来自 [iconfinder.com](https://www.iconfinder.com/search?q=todo&price=free)。该客户端具有以下特点：

* **任务管理** ：支持添加、编辑、删除任务，并可将任务同步至 Nextcloud 服务器。
* **离线模式** ：当网络异常或处于离线模式时，仍能通过本地 JSON 文件保存任务数据，待网络恢复后进行同步。
* **多语言支持** ：内置中英文界面切换，方便不同语言用户使用。
* **系统托盘通知** ：任务截止前自动弹出托盘提醒，确保用户不错过重要事项。

## 使用 conda 安装

为了方便管理项目依赖，我们建议使用 conda 来创建独立的 Python 环境。请按照以下步骤进行安装和配置：

### 1. 创建 conda 环境

在终端或命令提示符中执行以下命令以创建一个新的 conda 环境（例如，命名为 `nextcloud_task`）并指定 Python 版本（建议 Python 3.11 或更高版本）：

> conda create -n nextcloud_task python=3.11

### 2. 激活环境

创建完成后，激活该环境：

> conda activate nextcloud_task

### 3. 安装依赖

> pip install pyqt5

### 4. 填写配置文件

在conf.json中填写以下内容，请删除#后的注释

> {

    "language": "zh", # zh/en

    "url": "xxx/nextcloud/remote.php/dav/calendars/xxx/x/", # without http

    "username": "user",

    "password": "passwd",

    "check_interval": 60, # in seconds

    "ssl_verify_cert": false, # check cert or not

    "offline_mode": false # on-line or off-line mode

}

### 5. 运行程序

在激活的 conda 环境中运行主程序（例如 `main.py`）：

python main.py
