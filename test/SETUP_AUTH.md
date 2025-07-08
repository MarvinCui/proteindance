# ProteinDance 用户认证系统设置指南

## 功能特性

✅ **完整的用户管理系统**
- 用户注册/登录
- 邮箱验证
- 密码重置
- JWT认证

✅ **对话历史管理**
- ChatGPT风格的对话界面
- 保存药物发现会话
- 搜索历史对话
- 会话管理（重命名、删除）

✅ **邮件服务支持**
- SendGrid API（推荐）
- SMTP邮箱备用方案

## 快速开始

### 1. 安装后端依赖

```bash
# 安装认证相关依赖
pip install -r requirements-auth.txt

# 或者单独安装
pip install pyjwt==2.8.0 sendgrid==6.11.0 pydantic[email]==2.5.0
```

### 2. 配置环境变量

复制 `.env.example` 为 `.env` 并配置：

```bash
cp .env.example .env
```

**必需配置：**
```env
# JWT密钥（生产环境必须更改）
JWT_SECRET=your-super-secret-jwt-key-change-in-production

# 前端URL
FRONTEND_URL=http://localhost:3000
```

**邮件服务配置（选择一种）：**

#### 方案1: SendGrid（推荐）
```env
SENDGRID_API_KEY=your-sendgrid-api-key
SENDGRID_FROM_EMAIL=noreply@yourdomain.com
```

#### 方案2: Gmail SMTP
```env
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=your-email@gmail.com
```

### 3. 获取API密钥

#### SendGrid（推荐）
1. 注册 [SendGrid](https://sendgrid.com/)
2. 创建API密钥：Settings → API Keys → Create API Key
3. 选择"Full Access"或配置邮件发送权限
4. 复制API密钥到 `.env` 文件

#### Gmail SMTP（备用）
1. 启用Gmail两步验证
2. 生成应用专用密码：Google账户 → 安全性 → 应用专用密码
3. 使用应用专用密码而非Gmail密码

### 4. 启动应用

```bash
# 启动后端
uvicorn backend.app:app --host 0.0.0.0 --port 5001 --reload

# 启动前端（新终端）
cd autoui
npm install  # 如果还没安装依赖
npm run dev
```

### 5. 测试功能

1. 访问 `http://localhost:3000`
2. 点击左侧边栏的"注册"按钮
3. 填写注册信息
4. 查收验证邮件
5. 验证邮箱后登录

## 界面说明

### 左侧边栏功能
- **新建对话**：开始新的药物发现会话
- **对话历史**：查看所有历史对话
- **搜索功能**：搜索对话内容
- **用户信息**：显示当前登录用户
- **登录/注册**：未登录时显示认证按钮

### 对话管理
- 自动保存药物发现流程
- 支持会话重命名
- 软删除机制（可恢复）
- 时间显示（刚刚、X分钟前等）

## API端点

### 认证相关
- `POST /api/auth/register` - 用户注册
- `POST /api/auth/login` - 用户登录
- `POST /api/auth/verify-email` - 验证邮箱
- `POST /api/auth/request-password-reset` - 请求密码重置
- `POST /api/auth/reset-password` - 重置密码
- `GET /api/auth/me` - 获取当前用户信息

### 对话管理
- `POST /api/conversations` - 创建对话
- `GET /api/conversations` - 获取对话列表
- `GET /api/conversations/{id}` - 获取对话详情
- `PUT /api/conversations/{id}` - 更新对话
- `DELETE /api/conversations/{id}` - 删除对话
- `GET /api/conversations/search` - 搜索对话

## 数据库说明

系统使用SQLite数据库，自动创建以下表：
- `users` - 用户信息
- `verification_tokens` - 验证令牌
- `conversation_sessions` - 对话会话
- `conversation_messages` - 对话消息

数据库文件：`proteindance.db`

## 安全特性

- JWT令牌认证
- 密码哈希存储（PBKDF2）
- 邮箱验证机制
- 令牌过期管理
- CORS配置
- SQL注入防护

## 故障排除

### 邮件发送失败
1. 检查API密钥配置
2. 确认发送邮箱地址
3. 查看后端日志
4. 尝试备用SMTP配置

### 数据库问题
```bash
# 删除数据库重新初始化
rm proteindance.db
# 重启后端，数据库会自动重建
```

### 前端连接问题
1. 确认后端运行在5001端口
2. 检查CORS配置
3. 确认API_BASE地址正确

## 自定义配置

### 修改JWT过期时间
```env
JWT_EXPIRE_HOURS=24  # 默认24小时
```

### 自定义邮件模板
编辑 `backend/services/email_service.py` 中的HTML模板

### 调整数据库位置
```env
DB_PATH=custom/path/to/database.db
```

## 生产部署注意事项

1. **更改JWT密钥**：使用强随机密钥
2. **配置HTTPS**：确保邮件链接安全
3. **设置CORS**：限制允许的域名
4. **备份数据库**：定期备份SQLite文件
5. **监控日志**：配置日志收集

## 支持

如有问题，请检查：
1. `.env` 文件配置
2. 后端日志输出
3. 浏览器控制台
4. 网络连接状态