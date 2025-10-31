# 🔑 验证码检测和复制功能说明

## 📋 功能概述

系统现已支持自动检测邮件中的验证码，并提供一键复制功能。当系统在邮件主题或正文中检测到验证码时，会自动在邮件列表和详情页面中显示验证码提示和复制按钮。

**版本**: v2.2.0  
**开发日期**: 2025-10-31  
**状态**: ✅ 已完成

---

## ✨ 功能特性

### 1. 智能验证码检测

- **多格式支持**：
  - 4-8位纯数字验证码（如：123456）
  - 字母数字组合（如：ABC123、AB1234）
  - 带分隔符的验证码（如：123-456）
  - HTML标签中的验证码（`<b>`, `<strong>`, `<span>`）

- **多语言关键词识别**：
  - 中文：验证码、动态码、安全码、激活码等
  - 英文：verification code, OTP, security code等
  - 其他语言：西班牙语、法语、荷兰语

- **智能评分系统**：
  - 根据上下文关键词评分
  - 优先选择最可能的验证码
  - 排除常见的非验证码单词

### 2. 前端展示

#### 邮件列表视图

- **验证码图标**：在包含验证码的邮件主题旁显示🔑图标
- **复制按钮**：操作栏中显示"🔑 复制验证码"按钮
- **悬停提示**：鼠标悬停显示验证码内容

#### 邮件详情视图

- **高亮显示区域**：
  - 绿色背景突出显示
  - 左侧边框强调
  - 验证码以大号字体展示

- **复制按钮**：
  - "📋 复制验证码"按钮
  - 点击即可复制到剪切板
  - 显示成功提示通知

### 3. 复制功能

- **现代剪切板API**：优先使用 `navigator.clipboard.writeText()`
- **降级方案**：不支持现代API时使用传统 `document.execCommand('copy')`
- **友好提示**：复制成功后显示通知消息
- **错误处理**：复制失败时给出明确提示

---

## 🏗️ 技术实现

### 后端模块

#### 1. `verification_code_detector.py`

```python
class VerificationCodeDetector:
    """验证码检测器"""
    
    def detect(self, subject: str = "", body: str = "") -> Optional[Dict[str, str]]:
        """
        检测邮件中的验证码
        
        Returns:
            {"code": "验证码", "location": "subject/body", "context": "上下文"}
        """
```

**核心功能**：
- 关键词匹配
- 正则表达式提取
- 验证码有效性验证
- 上下文分析
- 候选评分排序

#### 2. 数据模型更新

```python
class EmailItem(BaseModel):
    # ... 其他字段
    verification_code: Optional[str] = None  # 新增字段

class EmailDetailsResponse(BaseModel):
    # ... 其他字段
    verification_code: Optional[str] = None  # 新增字段
```

#### 3. 邮件服务集成

```python
# 在获取邮件列表时检测
code_info = detect_verification_code(subject=subject, body="")

# 在获取邮件详情时检测
code_info = detect_verification_code(subject=subject, body=body_content)
```

### 前端实现

#### 1. 邮件列表渲染

```javascript
// 检测验证码并显示按钮
const verificationCodeBtn = email.verification_code ? 
    `<button onclick="copyVerificationCode('${email.verification_code}')">
        🔑 复制验证码
    </button>` : '';

// 显示验证码图标
${email.verification_code ? '<span style="color: #10b981;">🔑</span>' : ''}
```

#### 2. 邮件详情展示

```javascript
// 高亮显示验证码区域
const verificationCodeHtml = data.verification_code ? `
    <div style="background: #dcfce7; border-left: 4px solid #10b981;">
        <strong>🔑 检测到验证码:</strong>
        <code>${data.verification_code}</code>
        <button onclick="copyVerificationCode('${data.verification_code}')">
            📋 复制验证码
        </button>
    </div>
` : '';
```

#### 3. 复制功能实现

```javascript
async function copyVerificationCode(code) {
    try {
        if (navigator.clipboard && navigator.clipboard.writeText) {
            // 现代API
            await navigator.clipboard.writeText(code);
            showNotification(`验证码已复制: ${code}`, 'success');
        } else {
            // 降级方案
            const textArea = document.createElement('textarea');
            textArea.value = code;
            document.body.appendChild(textArea);
            textArea.select();
            document.execCommand('copy');
            document.body.removeChild(textArea);
            showNotification(`验证码已复制: ${code}`, 'success');
        }
    } catch (err) {
        showNotification('复制失败: ' + err.message, 'error');
    }
}
```

---

## 📱 使用指南

### 场景1：从邮件列表复制验证码

1. 打开邮箱账户的邮件列表
2. 查找带有🔑图标的邮件（表示包含验证码）
3. 点击操作栏中的"🔑 复制验证码"按钮
4. 系统显示"验证码已复制"提示
5. 在需要的地方粘贴（Ctrl+V 或 Cmd+V）

### 场景2：从邮件详情复制验证码

1. 点击邮件查看详情
2. 如果邮件包含验证码，顶部会显示绿色高亮区域
3. 区域中显示检测到的验证码
4. 点击"📋 复制验证码"按钮
5. 系统显示"验证码已复制"提示
6. 在需要的地方粘贴

### 场景3：手动复制（备用方案）

如果自动检测未能识别验证码：
1. 打开邮件详情
2. 手动选中验证码文本
3. 使用浏览器的复制功能（Ctrl+C）

---

## 🔍 支持的验证码格式

### 纯数字验证码

```
123456 (6位)
1234 (4位)
12345678 (8位)
```

### 字母数字组合

```
ABC123
AB1234
A1B2C3
XYZ789
```

### 带分隔符

```
123-456
123 456
12-34-56
```

### HTML中的验证码

```html
您的验证码是：<b>123456</b>
Your OTP: <strong>ABC123</strong>
验证码：<span>789456</span>
```

### 特殊格式

```
code: 123456
Code: ABC123
验证码：123456
OTP: 9876
```

---

## 🎯 检测规则

### 关键词要求

邮件必须包含以下任一关键词才会进行检测：

**中文**：验证码、验证码、动态码、动态码、确认码、安全码、校验码、激活码

**英文**：verification code, verify code, confirmation code, security code, OTP, one-time password, PIN code, activation code

### 验证码要求

- 长度：4-8个字符
- 排除：常见单词（http, mail, dear, hello等）
- 优先：纯数字、大写字母数字组合
- 位置：靠近关键词的优先级更高

---

## 🧪 测试用例

### 测试用例 1：纯数字验证码

**输入**：
- 主题：`Your verification code`
- 正文：`Your verification code is: 123456. Please use it within 10 minutes.`

**预期**：✅ 检测到验证码 `123456`

### 测试用例 2：字母数字组合

**输入**：
- 主题：`验证码通知`
- 正文：`您的验证码是：<strong>ABC123</strong>，请在5分钟内使用。`

**预期**：✅ 检测到验证码 `ABC123`

### 测试用例 3：OTP格式

**输入**：
- 主题：`Security Code`
- 正文：`Your OTP is 9876. Do not share with anyone.`

**预期**：✅ 检测到验证码 `9876`

### 测试用例 4：激活码

**输入**：
- 主题：`账户激活`
- 正文：`激活码：<b>XYZ789</b>`

**预期**：✅ 检测到验证码 `XYZ789`

---

## 📊 性能优化

### 检测性能

- **邮件列表**：只检测主题，避免获取正文
- **邮件详情**：检测主题和正文，获取最准确结果
- **正则预编译**：初始化时编译所有正则表达式
- **缓存机制**：检测结果与邮件一同缓存

### 前端性能

- **按需渲染**：只在有验证码时显示按钮
- **异步复制**：使用async/await避免阻塞
- **错误恢复**：提供降级方案确保功能可用

---

## 🔧 配置说明

### 自定义关键词

编辑 `verification_code_detector.py`：

```python
KEYWORDS = [
    '验证码',
    'verification code',
    # 添加你的关键词
    '自定义关键词',
]
```

### 自定义正则模式

编辑 `verification_code_detector.py`：

```python
PATTERNS = [
    r'(?:code|Code)[:\s]+([A-Z0-9]{4,8})',
    # 添加你的模式
    r'your-pattern-here',
]
```

### 调整验证规则

```python
def _is_valid_code(self, code: str) -> bool:
    # 修改长度要求
    if len(code) < 4 or len(code) > 8:
        return False
    
    # 添加自定义排除规则
    if code.lower() in your_exclude_list:
        return False
    
    return True
```

---

## ⚠️ 注意事项

### 隐私安全

- ✅ 验证码仅在前端临时展示
- ✅ 不会永久存储到数据库
- ✅ 复制后不会发送到服务器
- ✅ 仅本地浏览器处理

### 兼容性

- ✅ Chrome 63+
- ✅ Firefox 53+
- ✅ Safari 13.1+
- ✅ Edge 79+
- ✅ 提供降级方案支持旧浏览器

### 限制说明

- ⚠️ 验证码必须有明确的关键词标识
- ⚠️ 过于复杂的格式可能无法识别
- ⚠️ 图片中的验证码无法识别
- ⚠️ 不支持语音验证码

---

## 🐛 故障排查

### 问题1：验证码未被检测到

**原因**：
- 邮件中没有验证码关键词
- 验证码格式不符合规则
- 验证码被误判为普通单词

**解决**：
- 检查邮件是否包含关键词
- 查看验证码格式是否在支持范围内
- 在 `_is_valid_code` 中调整排除列表

### 问题2：复制功能不工作

**原因**：
- 浏览器不支持剪切板API
- 页面未在HTTPS下（现代API要求）
- 浏览器权限被阻止

**解决**：
- 使用HTTPS协议访问
- 允许浏览器剪切板权限
- 系统会自动使用降级方案

### 问题3：检测到错误的验证码

**原因**：
- 邮件中有多个数字序列
- 评分系统选择了错误的候选

**解决**：
- 调整 `_select_best_candidate` 中的评分规则
- 增加关键词权重
- 优化正则表达式优先级

---

## 📈 未来改进

### 短期计划

- [ ] 支持更多验证码格式
- [ ] 添加验证码有效期提示
- [ ] 支持多个验证码同时展示
- [ ] 添加验证码历史记录

### 长期计划

- [ ] OCR识别图片中的验证码
- [ ] AI模型提高检测准确率
- [ ] 支持自动填充验证码
- [ ] 集成浏览器扩展

---

## 🤝 贡献指南

如果你想改进验证码检测功能：

1. Fork项目
2. 修改 `verification_code_detector.py`
3. 添加测试用例
4. 提交Pull Request

---

## 📝 更新日志

### v2.2.0 (2025-10-31)

- ✨ 新增验证码自动检测功能
- ✨ 新增一键复制验证码功能
- ✨ 邮件列表显示验证码图标
- ✨ 邮件详情高亮显示验证码
- ✨ 支持多种验证码格式
- ✨ 支持中英文关键词
- ✨ 智能评分系统

---

## 📞 支持

- **问题反馈**：GitHub Issues
- **功能建议**：欢迎提交Pull Request
- **技术支持**：查看项目文档

---

**文档版本**: 1.0  
**最后更新**: 2025-10-31  
**维护者**: Outlook Manager Team


