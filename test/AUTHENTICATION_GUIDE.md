# ProteinDance 认证系统使用指南

## 项目认证架构概述

ProteinDance 项目采用基于JWT（JSON Web Token）的认证系统，提供完整的用户管理和会话保存功能。

### 核心组件

1. **后端认证服务** (`backend/services/auth_service.py`)
   - JWT令牌生成和验证
   - 用户注册、登录、密码重置
   - 用户状态管理

2. **前端认证服务** (`autoui/src/services/authService.ts`)
   - 令牌存储和管理
   - API请求认证头注入
   - 用户状态同步

3. **会话管理** (`backend/services/conversation_service.py`)
   - 用户会话创建、更新、删除
   - 会话历史保存
   - 用户数据隔离

4. **数据库层** (`backend/database/db_manager.py`)
   - 用户信息存储
   - 会话数据持久化
   - 认证令牌管理

## 认证流程

### 1. 用户注册
```bash
curl -X POST http://localhost:5001/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "username": "username",
    "password": "password123"
  }'
```

**响应示例:**
```json
{
  "success": true,
  "message": "注册成功！用户已自动激活（邮件验证已关闭）",
  "user": {
    "id": 6,
    "email": "user@example.com",
    "username": "username",
    "status": "active",
    "email_verified": true
  },
  "auto_activated": true,
  "email_verification_enabled": false
}
```

### 2. 用户登录
```bash
curl -X POST http://localhost:5001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "password123"
  }'
```

**响应示例:**
```json
{
  "success": true,
  "message": "登录成功",
  "user": {
    "id": 6,
    "email": "user@example.com",
    "username": "username",
    "status": "active",
    "email_verified": true
  },
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "requires_verification": false
}
```

### 3. 使用JWT令牌访问受保护的API
```bash
curl -X GET http://localhost:5001/api/auth/me \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

## 环境配置

### 1. 环境变量设置
在 `.env` 文件中配置：
```env
# JWT 配置
JWT_SECRET=your-super-secret-jwt-key-change-in-production
JWT_EXPIRE_HOURS=24

# 邮件验证配置（当前已关闭）
EMAIL_VERIFICATION_ENABLED=false

# 前端URL
FRONTEND_URL=http://localhost:3000
```

### 2. 数据库初始化
系统使用SQLite数据库，会自动创建以下表：
- `users` - 用户信息
- `verification_tokens` - 验证令牌
- `conversation_sessions` - 对话会话
- `conversation_messages` - 对话消息

## API端点详解

### 认证相关端点

#### POST /api/auth/register
- **功能**: 用户注册
- **认证**: 不需要
- **请求体**: `{email, username, password}`
- **响应**: 用户信息和注册状态

#### POST /api/auth/login
- **功能**: 用户登录
- **认证**: 不需要
- **请求体**: `{email, password}`
- **响应**: 用户信息和JWT令牌

#### GET /api/auth/me
- **功能**: 获取当前用户信息
- **认证**: 需要JWT令牌
- **响应**: 用户详细信息

#### POST /api/auth/request-password-reset
- **功能**: 请求密码重置
- **认证**: 不需要
- **请求体**: `{email}`

#### POST /api/auth/reset-password
- **功能**: 重置密码
- **认证**: 不需要
- **请求体**: `{token, new_password}`

### 会话管理端点

#### POST /api/conversations
- **功能**: 创建新会话
- **认证**: 需要JWT令牌
- **请求体**: `{title}`
- **响应**: 会话信息

#### GET /api/conversations
- **功能**: 获取用户会话列表
- **认证**: 需要JWT令牌
- **查询参数**: `limit` (默认50)
- **响应**: 会话列表

#### GET /api/conversations/{session_id}
- **功能**: 获取会话详情
- **认证**: 需要JWT令牌
- **响应**: 会话详情和消息

#### PUT /api/conversations/{session_id}
- **功能**: 更新会话
- **认证**: 需要JWT令牌
- **请求体**: `{title?, is_active?}`

#### DELETE /api/conversations/{session_id}
- **功能**: 删除会话
- **认证**: 需要JWT令牌
- **响应**: 删除确认

#### GET /api/conversations/search
- **功能**: 搜索会话
- **认证**: 需要JWT令牌
- **查询参数**: `q` (搜索关键词), `limit` (默认20)

## 前端集成

### 1. 认证服务使用
```typescript
import authService from '../services/authService'

// 登录
const loginResult = await authService.login({
  email: 'user@example.com',
  password: 'password123'
})

// 检查登录状态
const isAuthenticated = authService.isAuthenticated()

// 获取当前用户
const currentUser = authService.getCurrentUser()

// 获取JWT令牌
const token = authService.getToken()
```

### 2. API请求认证
```typescript
// 自动添加认证头
const headers = authService.getApiHeaders()

// 或手动添加
fetch('/api/conversations', {
  headers: {
    'Authorization': `Bearer ${authService.getToken()}`,
    'Content-Type': 'application/json'
  }
})
```

## 测试认证功能

### 1. 使用提供的测试脚本
```bash
# 运行完整认证测试
./test_auth.sh
```

### 2. 手动测试流程
```bash
# 1. 注册用户
curl -X POST http://localhost:5001/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "username": "testuser", "password": "testpass123"}'

# 2. 登录获取令牌
TOKEN=$(curl -s -X POST http://localhost:5001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "testpass123"}' \
  | jq -r '.token')

# 3. 使用令牌访问API
curl -H "Authorization: Bearer $TOKEN" http://localhost:5001/api/conversations
```

## 会话保存功能

### 1. 创建会话
```bash
curl -X POST http://localhost:5001/api/conversations \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"title": "我的药物发现会话"}'
```

### 2. 保存会话消息
会话消息会在用户进行药物发现流程时自动保存，包括：
- 用户输入的疾病名称
- AI分析结果
- 选择的靶点
- 预测的口袋
- 筛选的化合物
- 对接结果

### 3. 会话管理
用户可以：
- 重命名会话
- 删除会话
- 搜索历史会话
- 查看会话详情

## 安全特性

### 1. JWT令牌安全
- 使用强随机密钥签名
- 24小时过期时间
- 包含用户ID和基本信息
- 防止令牌篡改

### 2. 密码安全
- 使用PBKDF2算法哈希存储
- 不存储明文密码
- 支持密码重置功能

### 3. 用户隔离
- 每个用户只能访问自己的会话
- API端点权限控制
- 数据库级别的用户隔离

### 4. 错误处理
- 统一的错误响应格式
- 请求ID跟踪
- 详细的日志记录

## 常见问题

### Q1: 如何获取有效的JWT令牌？
**A**: 通过用户登录API (`/api/auth/login`) 获取令牌，响应中的 `token` 字段即为JWT令牌。

### Q2: 令牌过期怎么办？
**A**: 令牌过期后需要重新登录获取新令牌。当前令牌有效期为24小时。

### Q3: 如何测试API是否需要认证？
**A**: 不带 `Authorization` 头访问受保护的API，应该返回401错误。

### Q4: 会话数据如何与用户关联？
**A**: 所有会话数据都通过JWT令牌中的用户ID与用户关联，确保数据隔离。

### Q5: 邮件验证是否开启？
**A**: 当前邮件验证功能已关闭，用户注册后自动激活，可以直接登录。

## 开发建议

1. **前端开发**: 
   - 使用 `authService` 统一管理认证状态
   - 在API请求中自动添加认证头
   - 处理令牌过期和登录状态同步

2. **后端开发**:
   - 为需要认证的API使用 `require_auth` 依赖
   - 为可选认证的API使用 `get_current_user` 依赖
   - 正确处理认证错误

3. **测试**:
   - 使用提供的测试脚本验证认证功能
   - 测试令牌过期和无效令牌场景
   - 验证用户数据隔离

4. **部署**:
   - 在生产环境中更改JWT密钥
   - 配置HTTPS确保令牌传输安全
   - 设置合适的CORS策略

## 有效的测试令牌示例

**当前可用的测试令牌**:
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjo2LCJlbWFpbCI6InRlc3RfYXV0aEBleGFtcGxlLmNvbSIsInVzZXJuYW1lIjoidGVzdF9hdXRoX3VzZXIiLCJleHAiOjE3NTE5OTIyNDMsImlhdCI6MTc1MTkwNTg0M30.bsMvrZwkz05uaY5LinHuyzkBc-JML24KJJGqDHVH488
```

**使用示例**:
```bash
curl -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjo2LCJlbWFpbCI6InRlc3RfYXV0aEBleGFtcGxlLmNvbSIsInVzZXJuYW1lIjoidGVzdF9hdXRoX3VzZXIiLCJleHAiOjE3NTE5OTIyNDMsImlhdCI6MTc1MTkwNTg0M30.bsMvrZwkz05uaY5LinHuyzkBc-JML24KJJGqDHVH488" \
  http://localhost:5001/api/conversations
```

**令牌信息**:
- 用户ID: 6
- 邮箱: test_auth@example.com
- 用户名: test_auth_user
- 过期时间: 24小时有效期

---

通过以上指南，您应该能够完全理解并正确使用ProteinDance项目的认证系统。如有问题，请参考测试脚本或查看相关源代码。