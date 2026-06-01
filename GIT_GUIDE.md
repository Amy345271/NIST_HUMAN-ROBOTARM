# Git 使用入门指南

这份文档面向刚开始使用 Git 的同学，尽量用最常见、最实用的方式来说明。

## 1. Git 是什么

Git 是一个版本管理工具，用来记录文件改动，方便你：

- 查看历史记录
- 撤销错误修改
- 和 GitHub 协作
- 管理多个分支

你可以把它理解成“项目的时间机器”。

## 2. 最常用的概念

### 仓库（repository）
项目代码所在的 Git 管理空间。

### 工作区（working tree）
你正在编辑的文件。

### 暂存区（staging area）
准备提交的文件集合。

### 提交（commit）
把一批改动保存成一个版本。

### 分支（branch）
同一个项目的不同开发线路。

### 远程仓库（remote）
GitHub 上的仓库地址，例如 `origin`。

## 3. 初始化仓库

如果一个文件夹还不是 Git 仓库：

```bash
git init
```

查看当前状态：

```bash
git status
```

## 4. 最基本的提交流程

这是最常见的工作流程：

```bash
git status
git add .
git commit -m "你的提交说明"
git push
```

含义如下：

- `git add .`：把改动加入暂存区
- `git commit -m`：生成一次提交
- `git push`：把提交推送到远程仓库

## 5. 常用命令

### 查看状态

```bash
git status
```

### 查看提交历史

```bash
git log --oneline
```

### 查看差异

```bash
git diff
```

查看已暂存的差异：

```bash
git diff --cached
```

### 添加文件

```bash
git add 文件名
```

添加所有改动：

```bash
git add .
```

### 提交修改

```bash
git commit -m "修复说明"
```

### 推送到远程

```bash
git push
```

### 拉取远程更新

```bash
git pull
```

## 6. 分支操作

查看分支：

```bash
git branch
```

创建并切换到新分支：

```bash
git checkout -b feature/test
```

切换分支：

```bash
git checkout main
```

合并分支：

```bash
git merge feature/test
```

## 7. 回退与撤销

### 撤销工作区修改

```bash
git restore 文件名
```

### 撤销暂存区文件

```bash
git restore --staged 文件名
```

### 回退到上一次提交

```bash
git reset --soft HEAD~1
```

### 丢弃最近一次提交并回到修改前

```bash
git reset --hard HEAD~1
```

注意：`--hard` 会丢失未保存的改动，谨慎使用。

## 8. 远程仓库常用命令

查看远程地址：

```bash
git remote -v
```

添加远程仓库：

```bash
git remote add origin https://github.com/你的账号/你的仓库.git
```

第一次推送并建立跟踪关系：

```bash
git push -u origin main
```

### 推送失败：无法连接 GitHub

如果看到类似下面的报错：

```bash
fatal: unable to access 'https://github.com/...': Failed to connect to github.com port 443
```

通常不是命令写错，而是网络连不上 GitHub。可以按这个顺序排查：

1. 先确认当前网络能正常访问 github.com
2. 如果在校园网、公司网或代理环境里，检查代理或 VPN 是否可用
3. 再用 `git remote -v` 看远程地址是否写对
4. 网络恢复后重新执行 `git push`

如果一直连不上，也可以改用 SSH 方式连接远程仓库。

## 9. 常见工作场景

### 场景 1：改完代码后保存

```bash
git add .
git commit -m "完成某个功能"
git push
```

### 场景 2：先同步别人的更新

```bash
git pull
```

### 场景 3：误改了文件，想恢复

```bash
git restore 文件名
```

### 场景 4：新功能先单独开发

```bash
git checkout -b feature/new-task
```

## 10. 提交信息怎么写

建议短、清晰、动词开头，例如：

- `add`：新增功能
- `fix`：修复问题
- `update`：更新内容
- `refactor`：重构代码
- `docs`：修改文档

例子：

```bash
git commit -m "docs: add git usage guide"
```

## 11. 在本项目里的建议流程

在这个仓库里，你通常会这样做：

1. 修改 `scripts/` 或文档
2. 用 `git status` 看改动
3. 用 `git add .` 暂存
4. 用 `git commit -m` 提交
5. 用 `git push` 推送到 GitHub

如果是大改动，建议一次只做一类事情，比如：

- 只改转换脚本
- 只改文档
- 只改同步模板

这样更容易回退和排查问题。

## 12. 学习建议

- 先熟悉 `status / add / commit / push`
- 再学习 `branch / merge`
- 最后学习 `reset / revert`
- 每次提交都写清楚说明

如果你愿意，我还可以继续给你补一份“Git 常见报错与解决办法”。
