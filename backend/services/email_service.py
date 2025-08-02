"""
邮件服务模块
支持 Resend、SendGrid 和 SMTP 三种方式发送邮件
"""
import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
import requests

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        # Resend配置（优先使用）
        self.resend_api_key = os.getenv('RESEND_API_KEY')
        self.resend_from_email = os.getenv('RESEND_FROM_EMAIL', 'ProteinDance <noreply@proteindance.com>')
        
        # SendGrid配置（备用）
        self.sendgrid_api_key = os.getenv('SENDGRID_API_KEY')
        self.sendgrid_from_email = os.getenv('SENDGRID_FROM_EMAIL', 'noreply@proteindance.com')
        
        # SMTP配置（最后备用）
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_username = os.getenv('SMTP_USERNAME')
        self.smtp_password = os.getenv('SMTP_PASSWORD')
        self.smtp_from_email = os.getenv('SMTP_FROM_EMAIL', self.smtp_username)
        
        # 前端URL配置
        self.frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:5173')
    
    def send_email_via_resend(self, to_email: str, subject: str, html_content: str) -> bool:
        """使用Resend发送邮件"""
        if not self.resend_api_key:
            logger.error("Resend API key not configured")
            return False
        
        try:
            url = "https://api.resend.com/emails"
            
            data = {
                "from": self.resend_from_email,
                "to": [to_email],
                "subject": subject,
                "html": html_content
            }
            
            headers = {
                "Authorization": f"Bearer {self.resend_api_key}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(url, json=data, headers=headers)
            
            if response.status_code == 200:
                logger.info(f"Resend邮件发送成功: {to_email}")
                return True
            else:
                logger.error(f"Resend发送失败: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Resend邮件发送异常: {e}")
            return False
    
    def send_email_via_sendgrid(self, to_email: str, subject: str, html_content: str) -> bool:
        """使用SendGrid发送邮件"""
        if not self.sendgrid_api_key:
            logger.error("SendGrid API key not configured")
            return False
        
        try:
            url = "https://api.sendgrid.com/v3/mail/send"
            
            data = {
                "personalizations": [
                    {
                        "to": [{"email": to_email}],
                        "subject": subject
                    }
                ],
                "from": {"email": self.sendgrid_from_email, "name": "ProteinDance"},
                "content": [
                    {
                        "type": "text/html",
                        "value": html_content
                    }
                ]
            }
            
            headers = {
                "Authorization": f"Bearer {self.sendgrid_api_key}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(url, json=data, headers=headers)
            
            if response.status_code == 202:
                logger.info(f"邮件发送成功: {to_email}")
                return True
            else:
                logger.error(f"SendGrid发送失败: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"SendGrid邮件发送异常: {e}")
            return False
    
    def send_email_via_smtp(self, to_email: str, subject: str, html_content: str) -> bool:
        """使用SMTP发送邮件"""
        if not self.smtp_username or not self.smtp_password:
            logger.error("SMTP credentials not configured")
            return False
        
        try:
            # 创建邮件对象
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"ProteinDance <{self.smtp_from_email}>"
            msg['To'] = to_email
            
            # 添加HTML内容
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            # 连接SMTP服务器
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.smtp_username, self.smtp_password)
            
            # 发送邮件
            text = msg.as_string()
            server.sendmail(self.smtp_from_email, to_email, text)
            server.quit()
            
            logger.info(f"SMTP邮件发送成功: {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"SMTP邮件发送异常: {e}")
            return False
    
    def send_email(self, to_email: str, subject: str, html_content: str) -> bool:
        """发送邮件（优先使用Resend，失败则尝试SendGrid，最后使用SMTP）"""
        # 首先尝试Resend
        if self.resend_api_key:
            if self.send_email_via_resend(to_email, subject, html_content):
                return True
            logger.warning("Resend发送失败，尝试SendGrid")
        
        # 备用SendGrid
        if self.sendgrid_api_key:
            if self.send_email_via_sendgrid(to_email, subject, html_content):
                return True
            logger.warning("SendGrid发送失败，尝试SMTP")
        
        # 最后备用SMTP
        return self.send_email_via_smtp(to_email, subject, html_content)
    
    def send_verification_email(self, to_email: str, username: str, token: str) -> bool:
        """发送邮箱验证邮件"""
        verify_url = f"{self.frontend_url}/verify-email?token={token}"
        
        subject = "ProteinDance - 验证您的邮箱"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
                    line-height: 1.6;
                    margin: 0;
                    padding: 0;
                    background-color: #f5f5f5;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    background-color: white;
                    padding: 40px;
                    border-radius: 8px;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                    margin-top: 40px;
                }}
                .logo {{
                    text-align: center;
                    margin-bottom: 30px;
                }}
                .logo h1 {{
                    color: #4f46e5;
                    font-size: 28px;
                    margin: 0;
                }}
                .button {{
                    display: inline-block;
                    padding: 12px 24px;
                    background-color: #4f46e5;
                    color: white;
                    text-decoration: none;
                    border-radius: 6px;
                    font-weight: 600;
                    margin: 20px 0;
                }}
                .footer {{
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 1px solid #e5e7eb;
                    color: #6b7280;
                    font-size: 14px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="logo">
                    <h1>🧬 ProteinDance</h1>
                </div>
                
                <h2>欢迎使用 ProteinDance!</h2>
                
                <p>你好 <strong>{username}</strong>,</p>
                
                <p>感谢您注册 ProteinDance 药物发现平台！为了确保账户安全，请点击下面的按钮验证您的邮箱地址：</p>
                
                <div style="text-align: center;">
                    <a href="{verify_url}" class="button">验证邮箱</a>
                </div>
                
                <p>如果按钮无法点击，您也可以复制以下链接到浏览器地址栏：</p>
                <p style="word-break: break-all; color: #4f46e5;">{verify_url}</p>
                
                <p><strong>注意：</strong>此验证链接将在24小时后过期。</p>
                
                <div class="footer">
                    <p>如果您没有注册 ProteinDance 账户，请忽略此邮件。</p>
                    <p>© 2025 ProteinDance. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(to_email, subject, html_content)
    
    def send_password_reset_email(self, to_email: str, username: str, token: str) -> bool:
        """发送密码重置邮件"""
        reset_url = f"{self.frontend_url}/reset-password?token={token}"
        
        subject = "ProteinDance - 重置您的密码"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
                    line-height: 1.6;
                    margin: 0;
                    padding: 0;
                    background-color: #f5f5f5;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    background-color: white;
                    padding: 40px;
                    border-radius: 8px;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                    margin-top: 40px;
                }}
                .logo {{
                    text-align: center;
                    margin-bottom: 30px;
                }}
                .logo h1 {{
                    color: #4f46e5;
                    font-size: 28px;
                    margin: 0;
                }}
                .button {{
                    display: inline-block;
                    padding: 12px 24px;
                    background-color: #dc2626;
                    color: white;
                    text-decoration: none;
                    border-radius: 6px;
                    font-weight: 600;
                    margin: 20px 0;
                }}
                .footer {{
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 1px solid #e5e7eb;
                    color: #6b7280;
                    font-size: 14px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="logo">
                    <h1>🧬 ProteinDance</h1>
                </div>
                
                <h2>密码重置请求</h2>
                
                <p>你好 <strong>{username}</strong>,</p>
                
                <p>我们收到了您的密码重置请求。点击下面的按钮来设置新密码：</p>
                
                <div style="text-align: center;">
                    <a href="{reset_url}" class="button">重置密码</a>
                </div>
                
                <p>如果按钮无法点击，您也可以复制以下链接到浏览器地址栏：</p>
                <p style="word-break: break-all; color: #dc2626;">{reset_url}</p>
                
                <p><strong>安全提醒：</strong></p>
                <ul>
                    <li>此重置链接将在24小时后过期</li>
                    <li>如果您没有请求重置密码，请忽略此邮件</li>
                    <li>为了账户安全，请设置强密码</li>
                </ul>
                
                <div class="footer">
                    <p>如果您有任何问题，请联系我们的支持团队。</p>
                    <p>© 2025 ProteinDance. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(to_email, subject, html_content)