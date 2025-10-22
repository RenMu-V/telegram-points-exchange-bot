# 🤖 Telegram 积分兑换 Bot
一个功能强大、易于部署的 Telegram 机器人，用于在不同积分系统（例如积分A和积分B）之间进行无缝兑换，它拥有友好的交互界面和丰富的通知功能。

⚠️ **注意**：本项目仅适合使用花花 Emby 管理 Bot 的用户～  
👉 项目地址：[Sakura_embyboss](https://github.com/berry8838/Sakura_embyboss) 🌸

🛠 其他用户如需适配，请自行修改代码哦～  
💖 感谢理解与支持！

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
## ✨ 功能特性
- 🔄 **一键兑换**：通过内联键盘轻松选择兑换数量，操作简单直观。
- 📊 **实时查询**：兑换前自动显示当前积分，避免误操作。
- 🎉 **趣味通知**：兑换成功后，在群组中发送随机、有趣的文案，增加社区活跃度。
- 👥 **多群组支持**：可同时向多个 Telegram 群组发送兑换通知。
- 🔗 **可点击昵称**：通知中的用户昵称为蓝色链接，点击即可查看其个人资料。
- 🐳 **Docker 部署**：提供 `Dockerfile` 和 `docker-compose.yml`，实现一键部署。
- 🔒 **安全配置**：所有敏感信息通过配置文件管理，与代码分离。
## 🚀 快速开始
推荐使用 Docker 进行部署，这是最简单、最稳定的方式。
### 前置条件
- 安装 [Docker](https://www.docker.com/get-started)
- 安装 [Docker Compose](https://docs.docker.com/compose/install/)
### 1. 克隆项目
```bash
git clone https://github.com/yourusername/telegram-points-exchange-bot.git
cd telegram-points-exchange-bot
```
### 2. 配置文件
复制示例配置文件，并根据你的实际情况进行修改。
```bash
cp config.example.ini config.ini
```
使用你喜欢的编辑器打开 `config.ini` 文件，填入以下信息：
- `token`: 从 [@BotFather](https://t.me/BotFather) 获取的 Bot Token。
- `database_a` & `database_b`: 你的两个数据库连接信息。
- `exchange_rate`: 兑换比例（例如 `0.2` 表示 1 积分A = 0.2 积分B）。
- `admin`: 管理员的 Telegram User ID。
- `notification`: 接收通知的群组 ID。
### 3. 启动 Bot
在项目根目录下运行以下命令：
```bash
docker-compose up -d
```
Bot 将在后台启动并自动运行。你可以通过 `docker-compose logs -f` 查看实时日志。
## ⚙️ 配置说明
`config.ini` 文件是 Bot 的核心配置，以下是各配置项的详细说明：
```ini
[telegram]
# 从 @BotFather 获取的 Bot Token
token = YOUR_BOT_TOKEN_HERE
[database_a]
# 积分A的数据库连接信息
host = localhost
port = 3306
user = your_db_user
password = your_db_password
database = your_database_a
[database_b]
# 积分B的数据库连接信息
host = localhost
port = 3306
user = your_db_user
password = your_db_password
database = your_database_b
[settings]
# 兑换比例：1 积分A = ? 积分B
exchange_rate = 0.2
[admin]
# 管理员用户ID，多个用英文逗号分隔
user_ids = 123456789, 987654321
[notification]
# 接收兑换通知的 Telegram 群组 ID，多个用英文逗号分隔
group_ids = -1001234567890, -1000987654321
```
**如何获取群组 ID？**
1. 将机器人拉入群组。
2. 在群里发送任意消息。
3. 查看 Bot 的日志，或使用 [@userinfobot](https://t.me/userinfobot) 获取你的 ID 和群组 ID。
## 📁 项目结构
```
telegram-points-exchange-bot/
├── main.py                 # Bot 的核心逻辑代码
├── config.example.ini      # 配置文件模板
├── requirements.txt        # Python 依赖列表
├── Dockerfile             # Docker 镜像构建文件
├── docker-compose.yml     # Docker Compose 编排文件
├── .gitignore             # Git 忽略文件配置
└── README.md              # 项目说明文档 (本文件)
```
## 🛠️ 自定义与开发
本项目设计为易于扩展。你可以根据需要修改以下部分：
### 修改数据库逻辑
在 `main.py` 文件中，找到以下三个函数，并根据你的数据库表结构实现具体的查询和更新逻辑：
- `get_user_points_a(user_id)`: 查询用户积分A。
- `update_user_points_a(user_id, points_to_deduct)`: 扣除用户积分A。
- `add_user_points_b(user_id, points_to_add)`: 增加用户积分B。
### 自定义兑换文案
在 `send_group_notification` 函数中，修改 `congratulations` 列表，添加或修改你喜欢的通知文案。
### 修改兑换选项
在 `exchange_start` 函数中，修改 `InlineKeyboardButton` 的内容，以提供不同的兑换金额选项。
## 🤝 贡献
欢迎提交 Issue 来报告 Bug 或提出新功能建议！如果你想贡献代码，请 Fork 本项目，创建你的功能分支，然后提交 Pull Request。
## 📄 许可证
本项目采用 [MIT 许可证](LICENSE)。
## 🙏 致谢
感谢 [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) 库，让开发 Telegram Bot 变得如此简单！

感谢花花 [Sakura_embyboss](https://github.com/berry8838/Sakura_embyboss)
