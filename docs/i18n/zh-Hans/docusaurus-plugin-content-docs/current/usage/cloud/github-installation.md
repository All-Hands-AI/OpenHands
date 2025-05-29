# GitHub 安装

本指南将引导您完成为GitHub仓库安装和配置OpenHands Cloud的过程。

## 前提条件

- GitHub账户
- 访问OpenHands Cloud

## 安装步骤

1. 登录[OpenHands Cloud](https://app.all-hands.dev)
2. 如果您尚未连接GitHub账户：
   - 点击`连接到GitHub`
   - 查看并接受服务条款
   - 授权OpenHands AI应用程序

## 添加仓库访问权限

您可以授予OpenHands访问特定仓库的权限：

1. 点击`选择GitHub项目`下拉菜单，然后选择`添加更多仓库...`
2. 选择您的组织并选择要授予OpenHands访问权限的特定仓库。
   - OpenHands请求短期令牌（8小时过期）并具有以下权限：
     - 操作：读取和写入
     - 管理：只读
     - 提交状态：读取和写入
     - 内容：读取和写入
     - 问题：读取和写入
     - 元数据：只读
     - 拉取请求：读取和写入
     - Webhooks：读取和写入
     - 工作流程：读取和写入
   - 用户的仓库访问权限基于：
     - 为仓库授予的权限
     - 用户的GitHub权限（所有者/协作者）
3. 点击`安装并授权`

## 修改仓库访问权限

您可以随时修改仓库访问权限：
* 使用相同的`选择GitHub项目 > 添加更多仓库`工作流程，或
* 访问设置页面并在`GitHub设置`部分选择`配置GitHub仓库`。

## 使用OpenHands与GitHub

一旦您授予了仓库访问权限，您就可以将OpenHands与您的GitHub仓库一起使用。

有关如何将OpenHands与GitHub问题和拉取请求一起使用的详细信息，请参阅[云问题解决器](./cloud-issue-resolver.md)文档。

## 下一步

- [访问云界面](./cloud-ui.md)与网页界面交互
- [使用云问题解决器](./cloud-issue-resolver.md)自动修复代码并获取帮助
- [使用云API](./cloud-api.md)以编程方式与OpenHands交互
