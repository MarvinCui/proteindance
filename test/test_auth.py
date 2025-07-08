#!/usr/bin/env python3
"""
ProteinDance 认证系统测试脚本
演示如何正确使用JWT认证和会话管理
"""

import requests
import json
import time
from datetime import datetime

# 配置
API_BASE = "http://localhost:5001"
TEST_EMAIL = "test_auth@example.com"
TEST_USERNAME = "test_auth_user"
TEST_PASSWORD = "testpass123"

class AuthTester:
    def __init__(self):
        self.token = None
        self.user_id = None
        self.session = requests.Session()
        
    def print_step(self, step_name, description=""):
        print(f"\n{'='*50}")
        print(f"步骤: {step_name}")
        if description:
            print(f"描述: {description}")
        print(f"{'='*50}")
        
    def print_result(self, response_data, success=True):
        status = "✅ 成功" if success else "❌ 失败"
        print(f"\n结果: {status}")
        print(f"响应数据: {json.dumps(response_data, indent=2, ensure_ascii=False)}")
        
    def register_user(self):
        """注册用户"""
        self.print_step("用户注册", "创建测试用户账户")
        
        url = f"{API_BASE}/api/auth/register"
        data = {
            "email": TEST_EMAIL,
            "username": TEST_USERNAME,
            "password": TEST_PASSWORD
        }
        
        response = self.session.post(url, json=data)
        response_data = response.json()
        
        success = response_data.get("success", False)
        self.print_result(response_data, success)
        
        return success
        
    def login_user(self):
        """用户登录"""
        self.print_step("用户登录", "获取JWT令牌")
        
        url = f"{API_BASE}/api/auth/login"
        data = {
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        }
        
        response = self.session.post(url, json=data)
        response_data = response.json()
        
        success = response_data.get("success", False)
        if success:
            self.token = response_data.get("token")
            self.user_id = response_data.get("user", {}).get("id")
            # 为所有后续请求设置认证头
            self.session.headers.update({
                "Authorization": f"Bearer {self.token}"
            })
            
        self.print_result(response_data, success)
        
        return success
        
    def get_user_info(self):
        """获取用户信息"""
        self.print_step("获取用户信息", "验证JWT令牌有效性")
        
        url = f"{API_BASE}/api/auth/me"
        response = self.session.get(url)
        response_data = response.json()
        
        success = response_data.get("success", False)
        self.print_result(response_data, success)
        
        return success
        
    def create_conversation(self):
        """创建会话"""
        self.print_step("创建会话", "测试会话管理功能")
        
        url = f"{API_BASE}/api/conversations"
        data = {
            "title": f"药物发现会话 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        }
        
        response = self.session.post(url, json=data)
        response_data = response.json()
        
        success = response_data.get("success", False)
        session_id = None
        if success:
            session_id = response_data.get("session", {}).get("id")
            
        self.print_result(response_data, success)
        
        return success, session_id
        
    def get_conversations(self):
        """获取会话列表"""
        self.print_step("获取会话列表", "查看用户所有会话")
        
        url = f"{API_BASE}/api/conversations"
        response = self.session.get(url)
        response_data = response.json()
        
        success = response_data.get("success", False)
        self.print_result(response_data, success)
        
        return success
        
    def update_conversation(self, session_id):
        """更新会话"""
        self.print_step("更新会话", f"修改会话 {session_id} 的标题")
        
        url = f"{API_BASE}/api/conversations/{session_id}"
        data = {
            "title": f"已更新的会话标题 - {datetime.now().strftime('%H:%M:%S')}"
        }
        
        response = self.session.put(url, json=data)
        response_data = response.json()
        
        success = response_data.get("success", False)
        self.print_result(response_data, success)
        
        return success
        
    def test_protected_api(self):
        """测试需要认证的API"""
        self.print_step("测试受保护的API", "调用需要认证的药物发现API")
        
        url = f"{API_BASE}/api/disease-targets"
        data = {
            "disease": "阿尔茨海默病",
            "innovation_level": 5
        }
        
        response = self.session.post(url, json=data)
        
        # 检查响应状态
        if response.status_code == 200:
            response_data = response.json()
            success = response_data.get("success", False)
            self.print_result(response_data, success)
            return success
        else:
            print(f"❌ HTTP错误: {response.status_code}")
            try:
                error_data = response.json()
                print(f"错误详情: {json.dumps(error_data, indent=2, ensure_ascii=False)}")
            except:
                print(f"响应文本: {response.text}")
            return False
            
    def test_without_auth(self):
        """测试无认证访问受保护的API"""
        self.print_step("测试无认证访问", "验证未认证用户无法访问受保护的API")
        
        # 临时移除认证头
        temp_headers = self.session.headers.copy()
        if "Authorization" in self.session.headers:
            del self.session.headers["Authorization"]
        
        url = f"{API_BASE}/api/conversations"
        response = self.session.get(url)
        
        # 恢复认证头
        self.session.headers.update(temp_headers)
        
        if response.status_code == 401:
            print("✅ 正确阻止了未认证访问")
            try:
                error_data = response.json()
                print(f"错误响应: {json.dumps(error_data, indent=2, ensure_ascii=False)}")
            except:
                print(f"响应状态: {response.status_code}")
            return True
        else:
            print("❌ 未正确阻止未认证访问")
            return False
            
    def run_full_test(self):
        """运行完整的认证测试"""
        print("开始 ProteinDance 认证系统测试")
        print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"API地址: {API_BASE}")
        print(f"测试邮箱: {TEST_EMAIL}")
        
        # 测试步骤
        success_count = 0
        total_tests = 8
        
        # 1. 注册用户（可能已存在）
        if self.register_user():
            success_count += 1
        elif "已被注册" in str(self.session.get(f"{API_BASE}/api/auth/register").text):
            print("用户已存在，跳过注册")
            success_count += 1
            
        # 2. 用户登录
        if self.login_user():
            success_count += 1
            
            # 3. 获取用户信息
            if self.get_user_info():
                success_count += 1
                
            # 4. 测试无认证访问
            if self.test_without_auth():
                success_count += 1
                
            # 5. 创建会话
            success, session_id = self.create_conversation()
            if success:
                success_count += 1
                
                # 6. 更新会话
                if session_id and self.update_conversation(session_id):
                    success_count += 1
                    
            # 7. 获取会话列表
            if self.get_conversations():
                success_count += 1
                
            # 8. 测试受保护的API
            if self.test_protected_api():
                success_count += 1
        
        # 测试总结
        print(f"\n{'='*50}")
        print("测试总结")
        print(f"{'='*50}")
        print(f"总测试数: {total_tests}")
        print(f"成功测试: {success_count}")
        print(f"失败测试: {total_tests - success_count}")
        print(f"成功率: {success_count/total_tests*100:.1f}%")
        
        if success_count == total_tests:
            print("🎉 所有测试通过！认证系统运行正常。")
        else:
            print("⚠️  部分测试失败，请检查系统配置。")
            
        # 显示获取的令牌信息
        if self.token:
            print(f"\n✅ 有效的JWT令牌已获取:")
            print(f"Bearer {self.token}")
            print(f"\n💡 使用此令牌测试API:")
            print(f"curl -H 'Authorization: Bearer {self.token}' {API_BASE}/api/conversations")
            

if __name__ == "__main__":
    tester = AuthTester()
    tester.run_full_test()