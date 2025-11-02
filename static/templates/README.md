# 模板系统文档

## 📁 目录结构

```
templates/
├── README.md              # 本文件
├── base.html              # 基础框架模板
├── index.html             # 主入口模板
├── components/            # 可复用组件
│   ├── sidebar.html       # 侧边栏导航
│   ├── context_menu.html  # 右键菜单
│   └── api_docs_content.html # API文档内容
├── pages/                 # 独立页面模块
│   ├── accounts.html      # 账户列表页面
│   ├── add_account.html   # 添加单个账户
│   ├── batch_add.html     # 批量添加账户
│   ├── admin_panel.html   # 系统管理面板
│   ├── api_docs.html      # API接口文档
│   └── emails.html        # 邮件列表页面
└── modals/                # 模态框组件
    ├── email_detail.html  # 邮件详情弹窗
    ├── tags.html          # 标签管理弹窗
    ├── record.html        # 记录编辑弹窗
    ├── config_edit.html   # 配置编辑弹窗
    └── api_test.html      # API测试弹窗
```

## 🎨 模板说明

### base.html - 基础框架
**职责**: 提供整体HTML结构、CSS和JS引用

**包含**:
- HTML头部定义
- 所有CSS样式表引用
- 侧边栏容器
- 主内容区域容器
- 通知容器
- 所有JavaScript文件引用

**使用**:
```html
{% extends "base.html" %}

{% block content %}
  <!-- 你的内容 -->
{% endblock %}
```

### index.html - 主入口
**职责**: 组合所有页面和模态框

**结构**:
```html
{% extends "base.html" %}

{% block content %}
  {% include 'pages/accounts.html' %}
  {% include 'pages/add_account.html' %}
  <!-- ... 更多页面 ... -->
{% endblock %}
```

## 🧩 组件详解

### components/sidebar.html
**导航菜单组件**

功能:
- 系统Logo和标题
- 菜单项（邮箱账户、添加账户、批量添加、管理面板、API管理、邮件列表）
- 折叠/展开按钮
- 工具提示支持

依赖JavaScript:
- `toggleSidebar()` - 切换侧边栏状态
- `showPage()` - 显示指定页面

### components/context_menu.html
**右键菜单组件**

功能:
- 在新标签页打开
- 复制账户链接
- 管理账户标签
- 删除账户

依赖JavaScript:
- `openInNewTab()`
- `copyAccountLink()`
- `contextEditTags()`
- `contextDeleteAccount()`

### components/api_docs_content.html
**API文档内容**

功能:
- API基础信息展示
- 认证方式说明
- 版本信息
- Swagger链接

## 📄 页面模块

### pages/accounts.html
**邮箱账户管理页面**

功能:
- 账户列表展示（表格形式）
- 搜索功能（按邮箱、标签）
- 状态筛选（刷新状态）
- 时间范围筛选
- 分页控制
- 批量操作（刷新Token）

依赖JavaScript函数:
- `loadAccountsSmart()` - 加载账户列表
- `searchAccounts()` - 搜索账户
- `clearSearch()` - 清除搜索条件
- `changePage()` - 切换页面
- `showBatchRefreshDialog()` - 显示批量刷新对话框

### pages/add_account.html
**添加单个账户页面**

功能:
- 邮箱地址输入
- Refresh Token输入（大文本框）
- Client ID输入
- 标签管理（可选）
- 连接测试
- 表单验证

依赖JavaScript函数:
- `addAccount()` - 添加账户
- `clearAddAccountForm()` - 清空表单
- `testAccountConnection()` - 测试连接

### pages/batch_add.html
**批量添加账户页面**

功能:
- 批量输入（格式：邮箱----密码----token----clientId）
- 格式验证
- 进度条显示
- 结果反馈
- 示例数据加载

格式示例:
```
email@outlook.com----password----refresh_token----client_id
```

依赖JavaScript函数:
- `batchAddAccounts()` - 执行批量添加
- `validateBatchFormat()` - 验证格式
- `loadSampleData()` - 加载示例

### pages/admin_panel.html
**系统管理面板**

功能:
- 数据表管理（查看、编辑、删除记录）
- 系统配置管理
- 缓存统计和管理

标签页:
1. **数据表管理**: 管理accounts、admins、system_config表
2. **系统配置**: 配置IMAP、连接池等参数
3. **缓存统计**: 查看缓存使用情况、执行LRU清理

依赖JavaScript函数:
- `switchAdminTab()` - 切换标签
- `loadTablesList()` - 加载表列表
- `loadCacheStatistics()` - 加载缓存统计

### pages/api_docs.html
**API接口文档页面**

功能:
- API接口列表
- 请求参数说明
- 响应示例
- 在线测试功能

依赖:
- `components/api_docs_content.html` - API文档内容
- `modals/api_test.html` - API测试弹窗

### pages/emails.html
**邮件列表页面**

功能:
- 邮件列表展示（表格）
- 发件人/主题搜索
- 文件夹筛选（全部、收件箱、垃圾邮件）
- 排序（日期正序/倒序）
- 分页浏览
- 邮件统计（总数、未读、今日）

依赖JavaScript函数:
- `loadEmails()` - 加载邮件列表
- `searchAndLoadEmails()` - 搜索邮件
- `refreshEmails()` - 刷新邮件
- `emailPrevPage()` / `emailNextPage()` - 翻页

## 🔔 模态框模块

### modals/email_detail.html
**邮件详情弹窗**

显示:
- 邮件主题
- 发件人/收件人
- 发送时间
- 邮件正文（HTML/纯文本）

JavaScript接口:
- `closeEmailModal()` - 关闭弹窗

### modals/tags.html
**标签管理弹窗**

功能:
- 显示当前标签
- 添加新标签
- 删除标签
- 保存更改

JavaScript接口:
- `closeTagsModal()` - 关闭弹窗
- `addTag()` - 添加标签
- `saveAccountTags()` - 保存标签

### modals/record.html
**记录编辑弹窗**

功能:
- 动态生成表单字段
- 编辑数据表记录
- 保存更改

JavaScript接口:
- `closeRecordModal()` - 关闭弹窗
- `saveTableRecord()` - 保存记录

### modals/config_edit.html
**配置编辑弹窗**

功能:
- 编辑系统配置项
- 配置键（只读）
- 配置值（可编辑）
- 描述说明

JavaScript接口:
- `closeConfigEditModal()` - 关闭弹窗
- `saveConfigEdit()` - 保存配置

### modals/api_test.html
**API测试弹窗**

功能:
- 显示请求信息（方法、端点）
- 路径参数输入
- 查询参数输入
- 请求体输入（JSON）
- 显示响应结果

JavaScript接口:
- `closeApiTestModal()` - 关闭弹窗
- `executeApiTest()` - 执行测试
- `resetApiTestForm()` - 重置表单

## 🔧 开发指南

### 修改现有组件

1. **定位文件**: 根据功能找到对应的HTML文件
2. **编辑内容**: 修改HTML结构或内容
3. **保存文件**: 无需重启服务（开发模式）
4. **刷新浏览器**: 查看效果

### 添加新组件

1. **创建文件**:
```bash
# 在适当目录创建
touch static/templates/components/new_component.html
```

2. **编写组件**:
```html
<!-- 新组件 - 功能说明 -->
<div class="new-component">
  <h3>新组件标题</h3>
  <p>组件内容...</p>
</div>
```

3. **引入组件**:
```html
<!-- 在需要使用的地方 -->
{% include 'components/new_component.html' %}
```

4. **测试验证**:
```bash
python3 test_templates.py
```

### 添加新页面

1. **创建页面文件**:
```bash
touch static/templates/pages/new_page.html
```

2. **编写页面内容**:
```html
<!-- 新页面 -->
<div id="newPage" class="page hidden">
  <div class="card">
    <h3>页面标题</h3>
    <p>页面内容...</p>
  </div>
</div>
```

3. **在index.html中引入**:
```html
{% include 'pages/new_page.html' %}
```

4. **添加导航项** (可选，在sidebar.html中):
```html
<button
  class="nav-item"
  onclick="showPage('newPage', this)"
  data-tooltip="新页面"
>
  <span class="icon">🆕</span>
  <span class="nav-text">新页面</span>
</button>
```

### 添加新模态框

1. **创建模态框文件**:
```bash
touch static/templates/modals/new_modal.html
```

2. **编写模态框内容**:
```html
<!-- 新模态框 -->
<div id="newModal" class="modal hidden">
  <div class="modal-content">
    <div class="modal-header">
      <h3>模态框标题</h3>
      <button class="modal-close" onclick="closeNewModal()">
        &times;
      </button>
    </div>
    <div class="modal-body">
      <!-- 内容 -->
    </div>
    <div class="modal-footer">
      <button class="btn btn-secondary" onclick="closeNewModal()">
        取消
      </button>
      <button class="btn btn-primary" onclick="saveNewModal()">
        确定
      </button>
    </div>
  </div>
</div>
```

3. **在base.html中引入**:
```html
{% include 'modals/new_modal.html' %}
```

## 🎯 最佳实践

### 1. 命名规范
- 文件名: `kebab-case.html`
- ID: `camelCase`
- Class: `kebab-case`

### 2. 代码组织
- 每个文件专注一个功能
- 保持文件小而精（<300行）
- 添加清晰的注释

### 3. 依赖管理
- 在文件顶部注释说明依赖
- 标注需要的JavaScript函数
- 说明使用的CSS类

### 4. 注释规范
```html
<!-- 组件名称 - 功能说明 -->
<div class="component">
  <!-- 子模块说明 -->
  <div class="sub-module">
    <!-- 内容 -->
  </div>
</div>
```

## 🧪 测试

### 运行测试脚本
```bash
python3 test_templates.py
```

### 预期输出
```
🎉 所有模板测试通过!
```

### 手动测试
1. 启动服务: `python3 main.py`
2. 访问: http://localhost:8001/
3. 检查每个页面和功能

## 📚 相关文档

- [HTML_MODULARIZATION.md](../../HTML_MODULARIZATION.md) - 完整重构报告
- [QUICK_START_TEMPLATES.md](../../QUICK_START_TEMPLATES.md) - 快速上手指南
- [MODULARIZATION_SUMMARY.md](../../MODULARIZATION_SUMMARY.md) - 重构总结

## 🆘 故障排除

### 模板不显示
1. 检查文件路径是否正确
2. 确认文件名拼写无误
3. 查看浏览器控制台错误

### 样式不生效
1. 检查CSS类名是否正确
2. 确认CSS文件已加载
3. 清除浏览器缓存

### JavaScript错误
1. 检查依赖的JS函数是否存在
2. 查看控制台错误信息
3. 确认JS文件加载顺序

## 💡 提示

- 使用VS Code等现代编辑器获得更好的开发体验
- 安装Jinja2语法高亮插件
- 使用浏览器开发者工具调试
- 保持模板简洁，复杂逻辑放在JavaScript中

---

**维护者**: OutlookManager Team  
**最后更新**: 2025-11-01  
**版本**: 1.0.0

