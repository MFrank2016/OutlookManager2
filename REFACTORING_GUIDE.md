# 代码拆分指南

## 已完成的拆分

### JavaScript 模块 (static/js/)
已创建以下模块文件：
- ✅ `api.js` - API请求相关函数和配置
- ✅ `utils.js` - 工具函数（日期格式化、验证码检测、复制功能等）
- ✅ `ui.js` - UI工具函数（通知、模态框、页面管理等）
- ✅ `accounts.js` - 账户管理相关函数

### CSS 模块 (static/css/)
已创建以下样式文件：
- ✅ `base.css` - 基础样式和工具类
- ✅ `components.css` - 组件样式（按钮、表单、卡片、模态框、通知等）

## 待完成的拆分

### 1. 继续拆分 JavaScript

需要从原 `app.js` (3384行) 中继续提取以下模块：

#### `emails.js` - 邮件管理模块
提取内容：
- 邮件相关全局变量 (allEmails, filteredEmails, emailCurrentPage等)
- loadEmails()
- renderEmails()
- createEmailTableRow()
- showEmailDetail()
- renderEmailContent()
- searchAndLoadEmails()
- clearSearchFilters()
- 邮件分页函数 (emailNextPage, emailPrevPage等)
- 自动刷新相关函数 (startAutoRefresh, stopAutoRefresh)

#### `admin.js` - 管理面板模块
提取内容：
- switchAdminTab()
- loadTablesList()
- loadTableData()
- renderTableData()
- openAddRecordModal()
- editTableRow()
- deleteTableRow()
- loadSystemConfigs()
- editConfig()

#### `apitest.js` - API测试模块
提取内容：
- openApiTest()
- closeApiTestModal()
- executeApiTest()
- resetApiTestForm()

#### `batch.js` - 批量操作模块
提取内容：
- batchAddAccounts()
- validateBatchFormat()
- loadSampleData()
- testAccountConnection()

#### `tags.js` - 标签管理模块
提取内容：
- editAccountTags()
- renderCurrentTags()
- addTag()
- removeTag()
- saveAccountTags()

#### `context-menu.js` - 右键菜单模块
提取内容：
- showAccountContextMenu()
- hideContextMenu()
- openInNewTab()
- copyAccountLink()
- contextEditTags()
- contextDeleteAccount()

#### `main.js` - 主入口文件
保留内容：
- 初始化代码
- 事件监听器绑定
- 键盘快捷键
- 页面可见性监听

### 2. 继续拆分 CSS

需要从原 `style.css` (2324行) 中继续提取以下模块：

#### `layout.css` - 布局样式
提取内容：
```css
.app-container
.sidebar, .sidebar-header, .sidebar-nav
.nav-item
.main-content, .main-header, .main-body
```

#### `accounts.css` - 账户相关样式
提取内容：
```css
.account-list, .account-item
.account-avatar, .account-info, .account-details
.account-status-row, .account-status
.account-actions
.account-tags, .account-tag
.account-refresh-info
```

#### `emails.css` - 邮件相关样式
提取内容：
```css
.email-table
.email-item, .email-avatar, .email-sender
.email-subject, .email-date
.email-content-tabs, .content-tab
.email-detail-meta
```

#### `admin.css` - 管理面板样式
提取内容：
```css
.admin-panel
.tables-list, .table-item, .table-icon
.configs-list, .config-item, .config-icon
.data-table, .table-responsive
.api-test-modal, .api-test-content
```

#### `search-filter.css` - 搜索和过滤样式
提取内容：
```css
.search-container, .search-input, .search-icon
.filter-container, .filter-group
.filter-label, .filter-select
```

#### `responsive.css` - 响应式样式
提取内容：
```css
@media (max-width: 768px) { ... }
@media (max-width: 480px) { ... }
```

## 如何更新 HTML 文件

### 更新 index.html

将原来的单文件引用：
```html
<link rel="stylesheet" href="static/css/style.css">
<script src="static/js/app.js"></script>
```

替换为模块化引用：

```html
<!-- CSS 模块（按顺序加载） -->
<link rel="stylesheet" href="static/css/base.css">
<link rel="stylesheet" href="static/css/layout.css">
<link rel="stylesheet" href="static/css/components.css">
<link rel="stylesheet" href="static/css/accounts.css">
<link rel="stylesheet" href="static/css/emails.css">
<link rel="stylesheet" href="static/css/admin.css">
<link rel="stylesheet" href="static/css/search-filter.css">
<link rel="stylesheet" href="static/css/responsive.css">

<!-- JavaScript 模块（按依赖顺序加载） -->
<script src="static/js/api.js"></script>
<script src="static/js/utils.js"></script>
<script src="script/js/ui.js"></script>
<script src="static/js/accounts.js"></script>
<script src="static/js/emails.js"></script>
<script src="static/js/batch.js"></script>
<script src="static/js/tags.js"></script>
<script src="static/js/admin.js"></script>
<script src="static/js/apitest.js"></script>
<script src="static/js/context-menu.js"></script>
<script src="static/js/main.js"></script>
```

## 拆分步骤

### 步骤 1: 创建剩余的 JavaScript 模块

```bash
# 为每个模块创建对应的文件
touch static/js/emails.js
touch static/js/admin.js
touch static/js/apitest.js
touch static/js/batch.js
touch static/js/tags.js
touch static/js/context-menu.js
touch static/js/main.js
```

### 步骤 2: 创建剩余的 CSS 模块

```bash
# 为每个模块创建对应的文件
touch static/css/layout.css
touch static/css/accounts.css
touch static/css/emails.css
touch static/css/admin.css
touch static/css/search-filter.css
touch static/css/responsive.css
```

### 步骤 3: 从原文件中复制对应内容

1. 打开原 `app.js`，按照上述模块划分复制相应函数到新文件
2. 打开原 `style.css`，按照上述模块划分复制相应样式到新文件
3. 确保全局变量和函数依赖关系正确

### 步骤 4: 更新 HTML 文件

修改 `static/index.html` 和其他相关 HTML 文件，更新脚本和样式引用

### 步骤 5: 测试

1. 清除浏览器缓存
2. 重新加载页面
3. 测试各个功能模块是否正常工作
4. 检查浏览器控制台是否有错误

### 步骤 6: 删除原文件（可选）

确认所有功能正常后，可以删除或归档原始的 `app.js` 和 `style.css`

```bash
# 备份原文件
mv static/js/app.js static/js/app.js.bak
mv static/css/style.css static/css/style.css.bak
```

## 模块依赖关系

```
api.js (无依赖)
  ↓
utils.js (无依赖)
  ↓
ui.js (依赖: api, utils)
  ↓
accounts.js (依赖: api, utils, ui)
emails.js (依赖: api, utils, ui)
batch.js (依赖: api, ui)
tags.js (依赖: api, ui)
admin.js (依赖: api, utils, ui)
apitest.js (依赖: api, ui)
context-menu.js (依赖: accounts, ui)
  ↓
main.js (依赖: 所有上述模块)
```

## 注意事项

1. **全局变量**: 在 JavaScript 模块中声明的变量默认是全局的（使用 `var`/`let`/`const` 在顶层）
2. **函数可见性**: 所有函数都是全局可见的，可以被其他模块调用
3. **加载顺序**: 必须按依赖关系顺序加载脚本
4. **CSS 优先级**: 后加载的 CSS 会覆盖先加载的同名选择器
5. **响应式样式**: responsive.css 应该最后加载，以确保媒体查询正确应用

## 进一步优化建议

完成基本拆分后，可以考虑：

1. **使用 ES6 模块**: 将脚本改为使用 `import/export`
2. **使用构建工具**: 使用 Webpack 或 Vite 进行打包
3. **CSS 预处理器**: 使用 SASS/LESS 进行更好的样式管理
4. **代码压缩**: 使用工具压缩 CSS 和 JavaScript
5. **懒加载**: 按需加载非关键模块

## 快速命令

一键创建所有剩余文件：
```bash
# JavaScript 模块
touch static/js/{emails,admin,apitest,batch,tags,context-menu,main}.js

# CSS 模块
touch static/css/{layout,accounts,emails,admin,search-filter,responsive}.css
```

