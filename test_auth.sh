#!/bin/bash

# ProteinDance 认证系统测试脚本
# 演示如何正确使用JWT认证和会话管理

API_BASE="http://localhost:5001"
TEST_EMAIL="test_auth@example.com"
TEST_USERNAME="test_auth_user"
TEST_PASSWORD="testpass123"

echo "=================================="
echo "ProteinDance 认证系统测试"
echo "=================================="
echo "API地址: $API_BASE"
echo "测试邮箱: $TEST_EMAIL"
echo "测试时间: $(date)"
echo ""

# 函数：打印步骤
print_step() {
    echo ""
    echo "=========================================="
    echo "步骤: $1"
    echo "=========================================="
}

# 函数：格式化JSON响应
format_json() {
    if command -v jq &> /dev/null; then
        echo "$1" | jq .
    else
        echo "$1"
    fi
}

# 1. 注册用户
print_step "1. 用户注册"
echo "创建测试用户账户..."

register_response=$(curl -s -X POST "$API_BASE/api/auth/register" \
    -H "Content-Type: application/json" \
    -d '{
        "email": "'$TEST_EMAIL'",
        "username": "'$TEST_USERNAME'",
        "password": "'$TEST_PASSWORD'"
    }')

echo "注册响应:"
format_json "$register_response"

# 2. 用户登录
print_step "2. 用户登录"
echo "获取JWT令牌..."

login_response=$(curl -s -X POST "$API_BASE/api/auth/login" \
    -H "Content-Type: application/json" \
    -d '{
        "email": "'$TEST_EMAIL'",
        "password": "'$TEST_PASSWORD'"
    }')

echo "登录响应:"
format_json "$login_response"

# 提取JWT令牌
if command -v jq &> /dev/null; then
    JWT_TOKEN=$(echo "$login_response" | jq -r '.token // empty')
    LOGIN_SUCCESS=$(echo "$login_response" | jq -r '.success // false')
else
    # 简单的文本提取（不够健壮，但在没有jq的情况下可用）
    JWT_TOKEN=$(echo "$login_response" | grep -o '"token":"[^"]*"' | cut -d'"' -f4)
    LOGIN_SUCCESS=$(echo "$login_response" | grep -o '"success":true' | wc -l)
fi

if [ -z "$JWT_TOKEN" ] || [ "$JWT_TOKEN" = "null" ]; then
    echo "❌ 登录失败，无法获取JWT令牌"
    exit 1
fi

echo ""
echo "✅ 登录成功！"
echo "JWT令牌: $JWT_TOKEN"

# 3. 获取用户信息
print_step "3. 获取用户信息"
echo "验证JWT令牌有效性..."

user_info_response=$(curl -s -X GET "$API_BASE/api/auth/me" \
    -H "Authorization: Bearer $JWT_TOKEN")

echo "用户信息响应:"
format_json "$user_info_response"

# 4. 测试无认证访问
print_step "4. 测试无认证访问"
echo "验证未认证用户无法访问受保护的API..."

unauth_response=$(curl -s -X GET "$API_BASE/api/conversations")

echo "无认证访问响应:"
format_json "$unauth_response"

# 5. 创建会话
print_step "5. 创建会话"
echo "测试会话管理功能..."

session_title="药物发现会话 - $(date '+%Y-%m-%d %H:%M:%S')"
create_session_response=$(curl -s -X POST "$API_BASE/api/conversations" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $JWT_TOKEN" \
    -d '{
        "title": "'$session_title'"
    }')

echo "创建会话响应:"
format_json "$create_session_response"

# 提取会话ID
if command -v jq &> /dev/null; then
    SESSION_ID=$(echo "$create_session_response" | jq -r '.session.id // empty')
else
    SESSION_ID=$(echo "$create_session_response" | grep -o '"id":[0-9]*' | cut -d':' -f2)
fi

# 6. 获取会话列表
print_step "6. 获取会话列表"
echo "查看用户所有会话..."

get_sessions_response=$(curl -s -X GET "$API_BASE/api/conversations" \
    -H "Authorization: Bearer $JWT_TOKEN")

echo "会话列表响应:"
format_json "$get_sessions_response"

# 7. 更新会话（如果有会话ID）
if [ -n "$SESSION_ID" ] && [ "$SESSION_ID" != "null" ]; then
    print_step "7. 更新会话"
    echo "修改会话 $SESSION_ID 的标题..."

    update_title="已更新的会话标题 - $(date '+%H:%M:%S')"
    update_session_response=$(curl -s -X PUT "$API_BASE/api/conversations/$SESSION_ID" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $JWT_TOKEN" \
        -d '{
            "title": "'$update_title'"
        }')

    echo "更新会话响应:"
    format_json "$update_session_response"
fi

# 8. 测试受保护的药物发现API
print_step "8. 测试受保护的API"
echo "调用需要认证的药物发现API..."

protected_api_response=$(curl -s -X POST "$API_BASE/api/disease-targets" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $JWT_TOKEN" \
    -d '{
        "disease": "阿尔茨海默病",
        "innovation_level": 5
    }')

echo "受保护API响应:"
format_json "$protected_api_response"

# 总结
print_step "测试总结"
echo "✅ 认证系统测试完成！"
echo ""
echo "关键信息:"
echo "- JWT令牌: $JWT_TOKEN"
echo "- 会话ID: $SESSION_ID"
echo ""
echo "💡 使用此令牌测试其他API:"
echo "curl -H 'Authorization: Bearer $JWT_TOKEN' $API_BASE/api/conversations"
echo ""
echo "📖 认证流程说明:"
echo "1. 用户注册 -> 获取账户（邮件验证已关闭，自动激活）"
echo "2. 用户登录 -> 获取JWT令牌"
echo "3. 使用JWT令牌 -> 访问受保护的API"
echo "4. 会话管理 -> 保存药物发现历史"
echo ""
echo "🔐 安全特性:"
echo "- JWT令牌有效期：24小时"
echo "- 密码哈希存储"
echo "- 用户会话隔离"
echo "- API访问控制"