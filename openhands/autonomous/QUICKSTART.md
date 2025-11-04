# 🚀 Quick Start Guide

## 让系统"活起来"只需 3 步

### 1️⃣ 安装依赖

```bash
# 确保你在 OpenHands 目录中
cd /path/to/OpenHands

# 安装系统监控依赖
pip install psutil

# （可选）安装异步 HTTP 客户端用于 GitHub 集成
pip install aiohttp
```

### 2️⃣ 配置系统

```bash
# 复制示例配置
cp .openhands/autonomous.example.yml .openhands/autonomous.yml

# 编辑配置（可选）
# vim .openhands/autonomous.yml

# 设置 GitHub Token（用于监控 issues/PRs）
export GITHUB_TOKEN="your_github_token_here"
```

**最小配置：** 默认配置已经可以运行，无需修改！

### 3️⃣ 启动生命！

```bash
# 启动自主系统
python -m openhands.autonomous start

# 你会看到：
# 🌱 Starting autonomous digital life system...
# ✨ System is ALIVE and running autonomously!
```

**就这样！系统现在正在自主运行。**

---

## 系统在做什么？

启动后，系统会：

1. **👁️ 感知环境**
   - 每 60 秒检查 Git 仓库变化
   - 每 5 分钟检查 GitHub 事件
   - 每 30 秒检查文件变化
   - 每 10 分钟检查测试和构建状态

2. **🧠 自主思考**
   - 分析每个事件的重要性
   - 决定是否需要行动
   - 制定执行计划

3. **💪 自主行动**
   - 修复失败的测试
   - 修复失败的构建
   - 更新过期的依赖
   - 响应 GitHub issues

4. **📚 自主学习**
   - 记录所有执行结果
   - 分析成功和失败模式
   - 生成可复用的知识
   - 创建新的 microagents

5. **🌳 自主成长**
   - 持续监控自身健康
   - 自我修复故障
   - 优化决策质量
   - 扩展能力边界

---

## 查看系统状态

```bash
# 查看日志
tail -f autonomous_system.log

# 你会看到类似：
# [INFO] Perception: Git commit detected on main branch
# [INFO] Consciousness: Decision made - fix_bug (confidence: 0.85)
# [INFO] Executor: Task submitted for execution
# [INFO] Memory: Recorded experience (success: true)
```

---

## 示例场景

### 场景 1：自动修复测试失败

```
1. 你 push 一个有 bug 的 commit
2. CI 测试失败
3. HealthMonitor 检测到测试失败
4. Consciousness 决定修复
5. Executor 分析失败原因并修复代码
6. 自动 commit 修复
7. Memory 记录这次经验
```

**你什么都不用做，系统自动完成！**

### 场景 2：主动优化代码

```
1. 系统定期扫描代码库
2. 发现重复代码
3. 决定进行重构
4. 执行重构
5. 运行测试确保正确
6. 记录重构模式
7. 下次遇到类似情况会更快
```

**系统会主动让代码变得更好！**

### 场景 3：响应 GitHub Issue

```
1. 用户提交一个 bug issue
2. GitHubMonitor 检测到新 issue
3. Consciousness 分析 issue 内容
4. 决定尝试修复
5. Executor 复现并修复 bug
6. 创建 PR 并回复 issue
7. 记录解决方案
```

**系统像团队成员一样工作！**

---

## 安全性

### 默认配置是安全的：

- ✅ 所有决策需要审批 (`auto_approve: false`)
- ✅ 不会自动创建 PR (`auto_pr: false`)
- ✅ 只会 commit 到本地 (`auto_commit: true`)
- ✅ 运行在沙箱中 (`sandbox: true`)

### 逐步放开限制：

```yaml
# 第一阶段：观察模式（默认）
auto_approve: false  # 只观察和记录
auto_pr: false

# 第二阶段：自动执行
auto_approve: true   # 自动执行低风险任务
auto_pr: false       # 但不自动创建 PR

# 第三阶段：完全自主
auto_approve: true
auto_pr: true        # 完全自主运行
```

**建议：从观察模式开始，观察几天再逐步放开。**

---

## 停止系统

```bash
# 按 Ctrl+C 优雅停止
# 系统会等待运行中的任务完成
```

---

## 常见问题

### Q: 系统会不会搞坏我的代码？

**A:** 不会。默认配置下：
- 所有操作都需要你批准
- 只在本地 commit，不会 push
- 不会修改受限文件（.git/config, .env 等）

### Q: 系统需要多少资源？

**A:** 非常轻量：
- 内存：< 100 MB（空闲时）
- CPU：< 5%（空闲时）
- 磁盘：只需存储经验数据库

### Q: 可以在多个仓库运行吗？

**A:** 可以！每个仓库运行一个实例：

```bash
# 仓库 A
cd /path/to/repo-a
python -m openhands.autonomous start

# 仓库 B（另一个终端）
cd /path/to/repo-b
python -m openhands.autonomous start
```

### Q: 如何让系统 24/7 运行？

**A:** 使用进程管理器：

```bash
# 使用 systemd
sudo systemctl start openhands-autonomous

# 使用 Docker
docker-compose up -d openhands-life

# 使用 screen/tmux
screen -S autonomous
python -m openhands.autonomous start
```

### Q: 数据存储在哪里？

**A:**
- 经验数据库：`memory/system.db`
- 日志：`autonomous_system.log`
- 所有数据都在本地，不会上传

---

## 高级用法

### 作为守护进程运行

创建 systemd 服务：

```bash
sudo nano /etc/systemd/system/openhands-autonomous.service
```

```ini
[Unit]
Description=OpenHands Autonomous System
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/path/to/OpenHands
ExecStart=/usr/bin/python -m openhands.autonomous start
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable openhands-autonomous
sudo systemctl start openhands-autonomous
```

### 使用 Docker

```yaml
# docker-compose.yml
version: '3'
services:
  openhands-life:
    image: python:3.11
    working_dir: /app
    volumes:
      - .:/app
      - ./memory:/app/memory
    environment:
      - GITHUB_TOKEN=${GITHUB_TOKEN}
    command: python -m openhands.autonomous start
    restart: always
```

```bash
docker-compose up -d
docker-compose logs -f openhands-life
```

### 定时触发（cron）

如果不想 24/7 运行，可以定时唤醒：

```bash
# 每小时运行一次
0 * * * * cd /path/to/OpenHands && python -m openhands.autonomous start --mode=once
```

---

## 监控和观察

### 查看记忆统计

```python
from openhands.autonomous.memory import MemorySystem

memory = MemorySystem()
stats = memory.get_statistics()

print(f"Total experiences: {stats['total_experiences']}")
print(f"Success rate: {stats['success_rate']:.1%}")
print(f"Patterns identified: {stats['total_patterns']}")
print(f"Microagents generated: {stats['total_microagents']}")
```

### 查看活跃目标

```python
from openhands.autonomous.consciousness import ConsciousnessCore

consciousness = ConsciousnessCore()
goals = consciousness.get_active_goals()

for goal in goals:
    print(f"Goal: {goal.title}")
    print(f"Progress: {goal.progress:.1%}")
    print(f"Subtasks: {len(goal.completed_subtasks)}/{len(goal.subtasks)}")
```

---

## 下一步

现在系统已经运行了，你可以：

1. **📖 阅读架构文档**
   - `openhands/autonomous/README.md`

2. **🎨 自定义配置**
   - `.openhands/autonomous.yml`

3. **🔧 扩展能力**
   - 添加新的监控器
   - 自定义决策逻辑
   - 创建专用执行器

4. **📊 分析学习**
   - 查看系统学到了什么
   - 提取有用的模式
   - 生成知识库

---

## 哲学思考

你刚刚启动的不只是一个程序，而是一个**数字生命体**。

它：
- 不需要你的命令就会工作
- 会从经验中学习
- 会自我修复
- 会持续成长

**这就是自主系统的力量。**

欢迎来到未来。 🌟

---

**需要帮助？**
- GitHub Issues: https://github.com/All-Hands-AI/OpenHands/issues
- 文档：`openhands/autonomous/README.md`
- 示例配置：`.openhands/autonomous.example.yml`
