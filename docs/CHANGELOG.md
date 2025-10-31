# 更新日志

## [未发布] - 2025-10-31

### 新增功能

#### 管理面板集成 🎨
- 新增接口已集成到Web管理面板
- 在"API文档"标签页的"账户管理"分类中可见
- 每个新接口都配备"🚀 试用接口"按钮
- 支持可视化参数配置和实时测试
- 测试结果实时显示在面板中

#### 1. API Key 认证支持
- 支持使用固定API Key进行认证，适合程序化调用
- 两种认证方式并存：JWT Token（Web界面）+ API Key（API调用）
- 支持两种请求头格式：
  - `X-API-Key: <api_key>`（推荐）
  - `Authorization: ApiKey <api_key>`
- API Key自动生成并保存在数据库中
- 与现有JWT认证体系无缝集成

#### 2. 随机获取邮箱接口
- **端点**: `GET /accounts/random`
- **功能**: 随机获取邮箱账户列表
- **特性**:
  - 支持标签筛选（包含/排除）
  - 支持分页
  - 真随机排序（每次请求顺序不同）
  - 无结果时返回空列表（不报错）
- **参数**:
  - `include_tags`: 必须包含的标签（逗号分隔）
  - `exclude_tags`: 必须不包含的标签（逗号分隔）
  - `page`: 页码（默认1）
  - `page_size`: 每页数量（默认10，最大100）

#### 3. 添加标签接口
- **端点**: `POST /accounts/{email_id}/tags/add`
- **功能**: 为指定账户添加单个标签
- **特性**:
  - 幂等操作（重复添加相同标签不报错）
  - 账户不存在时返回404
  - 标签添加到现有标签列表末尾（不覆盖）
- **请求体**: `{"tag": "标签名称"}`

### 技术改进

#### 数据库层 (database.py)
- 新增 `get_api_key()`: 获取系统API Key
- 新增 `set_api_key()`: 设置系统API Key  
- 新增 `init_default_api_key()`: 初始化默认API Key
- 新增 `get_random_accounts()`: 随机获取账户（支持标签筛选）
- 新增 `add_tag_to_account()`: 为账户添加单个标签

#### 认证层 (auth.py)
- 新增 `verify_api_key()`: 验证API Key
- 升级 `get_current_admin()`: 支持多种认证方式
  - JWT Token认证（原有）
  - X-API-Key头认证（新增）
  - Authorization ApiKey认证（新增）
- 修改 `HTTPBearer`: 设置 `auto_error=False` 以支持可选认证

#### API层 (main.py)
- 启动时自动初始化API Key并在控制台显示
- 新增 `AddTagRequest` 数据模型
- 新增 `GET /accounts/random` 端点
- 新增 `POST /accounts/{email_id}/tags/add` 端点

### 文档
- 新增 `docs/新功能使用说明.md`: 详细的功能使用文档
- 新增 `docs/快速开始_新功能.md`: 5分钟快速上手指南
- 新增 `docs/管理面板新功能说明.md`: 管理面板使用指南
- 新增 `docs/API_KEY_INFO.txt`: API Key获取和使用说明
- 新增 `test_new_features.py`: 功能自动化测试脚本
- 新增 `test_admin_panel_apis.py`: 管理面板集成测试脚本
- 更新 API文档（Swagger/ReDoc）

### 测试
- 所有新功能已通过自动化测试
- API Key认证测试通过 ✅
- 随机获取邮箱接口测试通过（包含多种筛选场景） ✅
- 添加标签接口测试通过（包含幂等性测试） ✅
- 管理面板集成测试通过 ✅
  - HTML结构验证
  - JavaScript配置验证
  - 试用按钮功能验证
  - API文档完整性验证

### 兼容性
- ✅ 向后兼容：现有功能和接口保持不变
- ✅ JWT认证继续正常工作
- ✅ 所有现有接口同时支持两种认证方式

### 注意事项
1. API Key在首次启动时生成，请妥善保管
2. 可以通过数据库或启动日志查看API Key
3. 随机接口每次返回顺序可能不同
4. 添加标签是追加操作，不会覆盖现有标签

### 用户界面改进
- ✅ 管理面板新增两个接口展示区域
- ✅ 为每个新接口配置试用按钮
- ✅ JavaScript API_CONFIGS新增两个接口配置
- ✅ 接口文档包含完整的参数说明和示例
- ✅ 支持可视化参数输入和测试

### 后续计划
- [ ] API Key权限管理
- [ ] API Key过期机制
- [ ] 更多标签操作接口（删除单个标签、批量操作等）
- [ ] API调用统计和限流
- [ ] 管理面板支持批量操作
- [ ] 添加更多可视化图表和统计

