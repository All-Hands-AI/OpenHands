# GitLab 安装

本指南将引导您完成为GitLab仓库安装和配置OpenHands Cloud的过程。

## 前提条件

- GitLab账户
- 访问OpenHands Cloud

## 安装步骤

1. 登录[OpenHands Cloud](https://app.all-hands.dev)
2. 如果您尚未连接GitLab账户：
   - 点击`连接到GitLab`
   - 查看并接受服务条款
   - 授权OpenHands AI应用程序

## 添加仓库访问权限

您可以授予OpenHands访问特定仓库的权限：

1. 点击`选择GitLab项目`下拉菜单，然后选择`添加更多仓库...`
2. 选择您的组织并选择要授予OpenHands访问权限的特定仓库。
   - OpenHands请求具有以下范围的权限：
     - api：完全API访问
     - read_user：读取用户信息
     - read_repository：读取仓库信息
     - write_repository：写入仓库
   - 用户的仓库访问权限基于：
     - 为仓库授予的权限
     - 用户的GitLab权限（所有者/维护者/开发者）
3. 点击`安装并授权`

## 修改仓库访问权限

您可以随时修改仓库访问权限：
* 使用相同的`选择GitLab项目 > 添加更多仓库`工作流程，或
* 访问设置页面并在`GitLab设置`部分选择`配置GitLab仓库`。

## 使用OpenHands与GitLab

一旦您授予了仓库访问权限，您就可以将OpenHands与您的GitLab仓库一起使用。

有关如何将OpenHands与GitLab问题和合并请求一起使用的详细信息，请参阅[云问题解决器](./cloud-issue-resolver.md)文档。

## 下一步

- [访问云界面](./cloud-ui.md)与网页界面交互
- [使用云问题解决器](./cloud-issue-resolver.md)自动修复代码并获取帮助
- [使用云API](./cloud-api.md)以编程方式与OpenHands交互
