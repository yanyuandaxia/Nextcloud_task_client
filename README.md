# Nextcloud Task Synchronization Client

## Introduction

The **Nextcloud Task Synchronization Client** is a desktop application developed with PyQt5, designed to help users manage and synchronize tasks on Nextcloud across Windows and Linux platforms. The script *nextcloudtasks.py* utilizes the **[nextcloud-tasks](https://github.com/Sinkmanu/nextcloud-tasks)** project. The icon is from [iconfinder.com](https://www.iconfinder.com/search?q=todo&price=free). This client features:

* **Task Management**: Supports adding, editing, and deleting tasks, with the ability to synchronize them to the Nextcloud server.
* **Offline Mode**: In the event of network issues or when in offline mode, task data is saved locally in a JSON file and synchronized once the network is restored.
* **Multi-language Support**: Comes with built-in Chinese and English interfaces, making it convenient for users of different languages.
* **System Tray Notifications**: Automatically pops up tray reminders before task deadlines to ensure users do not miss important tasks.

## Installing with conda

To facilitate dependency management, it is recommended to use conda to create an isolated Python environment. Please follow the steps below for installation and configuration:

### 1. Create a conda Environment

Open a terminal or command prompt and execute the following command to create a new conda environment (for example, named `nextcloud_task`) and specify the Python version (Python 3.11 or higher is recommended):

> conda create -n nextcloud_task python=3.11

### 2. Activate the Environment

Once the environment is created, activate it:

> conda activate nextcloud_task

### 3. Install Dependencies

> pip install pyqt5 caldav

### 4. Configure the Configuration File

Fill in the following content in the **conf.json** file, and please remove the comments (the text following `#`):

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

### 5. Run the Program

Within the activated conda environment, run the main program (for example, `main.py`):

> python main.py conf.json

---
