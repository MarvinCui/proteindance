"""
对话管理服务
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from ..database.db_manager import DatabaseManager
from ..models.user import ConversationSession, ConversationMessage, SessionCreate, SessionUpdate

logger = logging.getLogger(__name__)

class ConversationService:
    def __init__(self):
        self.db = DatabaseManager()
    
    def create_session(self, user_id: int, title: str = None) -> Dict[str, Any]:
        """创建新的对话会话"""
        try:
            # 如果没有提供标题，生成默认标题
            if not title:
                now = datetime.now()
                title = f"对话 {now.strftime('%Y-%m-%d %H:%M')}"
            
            session = self.db.create_session(user_id, title)
            if not session:
                return {
                    "success": False,
                    "error": "会话创建失败",
                    "error_code": "CREATE_FAILED"
                }
            
            return {
                "success": True,
                "session": {
                    "id": session.id,
                    "title": session.title,
                    "created_at": session.created_at,
                    "updated_at": session.updated_at,
                    "is_active": session.is_active
                }
            }
            
        except Exception as e:
            logger.error(f"创建会话失败: {e}")
            return {
                "success": False,
                "error": "创建过程中发生错误",
                "error_code": "CREATE_ERROR"
            }
    
    def get_user_sessions(self, user_id: int, limit: int = 50) -> Dict[str, Any]:
        """获取用户的对话会话列表"""
        try:
            sessions = self.db.get_user_sessions(user_id, limit)
            
            session_list = []
            for session in sessions:
                # 获取会话的最后一条消息
                messages = self.db.get_session_messages(session.id, limit=1)
                last_message = messages[0] if messages else None
                
                session_data = {
                    "id": session.id,
                    "title": session.title,
                    "created_at": session.created_at,
                    "updated_at": session.updated_at,
                    "is_active": session.is_active,
                    "last_message": {
                        "content": last_message.content[:100] + "..." if last_message and len(last_message.content) > 100 else last_message.content if last_message else None,
                        "created_at": last_message.created_at if last_message else None,
                        "message_type": last_message.message_type if last_message else None
                    } if last_message else None
                }
                session_list.append(session_data)
            
            return {
                "success": True,
                "sessions": session_list
            }
            
        except Exception as e:
            logger.error(f"获取用户会话失败: {e}")
            return {
                "success": False,
                "error": "获取会话列表失败",
                "error_code": "FETCH_ERROR"
            }
    
    def get_session_detail(self, session_id: int, user_id: int) -> Dict[str, Any]:
        """获取会话详情和消息列表"""
        try:
            session = self.db.get_session_by_id(session_id)
            if not session:
                return {
                    "success": False,
                    "error": "会话不存在",
                    "error_code": "SESSION_NOT_FOUND"
                }
            
            # 验证会话所有权
            if session.user_id != user_id:
                return {
                    "success": False,
                    "error": "无权访问此会话",
                    "error_code": "ACCESS_DENIED"
                }
            
            # 获取会话消息
            messages = self.db.get_session_messages(session_id)
            
            message_list = []
            for msg in messages:
                message_data = {
                    "id": msg.id,
                    "message_type": msg.message_type,
                    "content": msg.content,
                    "disease_name": msg.disease_name,
                    "innovation_level": msg.innovation_level,
                    "step": msg.step,
                    "result_data": msg.result_data,
                    "created_at": msg.created_at
                }
                message_list.append(message_data)
            
            return {
                "success": True,
                "session": {
                    "id": session.id,
                    "title": session.title,
                    "created_at": session.created_at,
                    "updated_at": session.updated_at,
                    "is_active": session.is_active
                },
                "messages": message_list
            }
            
        except Exception as e:
            logger.error(f"获取会话详情失败: {e}")
            return {
                "success": False,
                "error": "获取会话详情失败",
                "error_code": "DETAIL_ERROR"
            }
    
    def update_session(self, session_id: int, user_id: int, updates: SessionUpdate) -> Dict[str, Any]:
        """更新会话信息"""
        try:
            session = self.db.get_session_by_id(session_id)
            if not session:
                return {
                    "success": False,
                    "error": "会话不存在",
                    "error_code": "SESSION_NOT_FOUND"
                }
            
            # 验证会话所有权
            if session.user_id != user_id:
                return {
                    "success": False,
                    "error": "无权修改此会话",
                    "error_code": "ACCESS_DENIED"
                }
            
            success = self.db.update_session(
                session_id,
                title=updates.title,
                is_active=updates.is_active
            )
            
            if not success:
                return {
                    "success": False,
                    "error": "会话更新失败",
                    "error_code": "UPDATE_FAILED"
                }
            
            # 获取更新后的会话信息
            updated_session = self.db.get_session_by_id(session_id)
            
            return {
                "success": True,
                "session": {
                    "id": updated_session.id,
                    "title": updated_session.title,
                    "created_at": updated_session.created_at,
                    "updated_at": updated_session.updated_at,
                    "is_active": updated_session.is_active
                }
            }
            
        except Exception as e:
            logger.error(f"更新会话失败: {e}")
            return {
                "success": False,
                "error": "更新过程中发生错误",
                "error_code": "UPDATE_ERROR"
            }
    
    def delete_session(self, session_id: int, user_id: int) -> Dict[str, Any]:
        """删除会话（软删除）"""
        try:
            session = self.db.get_session_by_id(session_id)
            if not session:
                return {
                    "success": False,
                    "error": "会话不存在",
                    "error_code": "SESSION_NOT_FOUND"
                }
            
            # 验证会话所有权
            if session.user_id != user_id:
                return {
                    "success": False,
                    "error": "无权删除此会话",
                    "error_code": "ACCESS_DENIED"
                }
            
            # 软删除：设置为非活动状态
            success = self.db.update_session(session_id, is_active=False)
            
            if not success:
                return {
                    "success": False,
                    "error": "会话删除失败",
                    "error_code": "DELETE_FAILED"
                }
            
            return {
                "success": True,
                "message": "会话已删除"
            }
            
        except Exception as e:
            logger.error(f"删除会话失败: {e}")
            return {
                "success": False,
                "error": "删除过程中发生错误",
                "error_code": "DELETE_ERROR"
            }
    
    def add_message(self, session_id: int, user_id: int, message_type: str,
                   content: str, disease_name: str = None,
                   innovation_level: int = None, step: int = None,
                   result_data: dict = None) -> Dict[str, Any]:
        """添加对话消息"""
        try:
            session = self.db.get_session_by_id(session_id)
            if not session:
                return {
                    "success": False,
                    "error": "会话不存在",
                    "error_code": "SESSION_NOT_FOUND"
                }
            
            # 验证会话所有权
            if session.user_id != user_id:
                return {
                    "success": False,
                    "error": "无权操作此会话",
                    "error_code": "ACCESS_DENIED"
                }
            
            message = self.db.add_message(
                session_id=session_id,
                user_id=user_id,
                message_type=message_type,
                content=content,
                disease_name=disease_name,
                innovation_level=innovation_level,
                step=step,
                result_data=result_data
            )
            
            if not message:
                return {
                    "success": False,
                    "error": "消息添加失败",
                    "error_code": "ADD_FAILED"
                }
            
            return {
                "success": True,
                "message": {
                    "id": message.id,
                    "message_type": message.message_type,
                    "content": message.content,
                    "disease_name": message.disease_name,
                    "innovation_level": message.innovation_level,
                    "step": message.step,
                    "result_data": message.result_data,
                    "created_at": message.created_at
                }
            }
            
        except Exception as e:
            logger.error(f"添加消息失败: {e}")
            return {
                "success": False,
                "error": "添加消息过程中发生错误",
                "error_code": "ADD_ERROR"
            }
    
    def save_drug_discovery_session(self, user_id: int, disease_name: str,
                                  innovation_level: int, workflow_data: dict,
                                  logs: List[dict]) -> Dict[str, Any]:
        """保存药物发现会话"""
        try:
            # 创建会话
            title = f"{disease_name} - 药物发现"
            session_result = self.create_session(user_id, title)
            
            if not session_result["success"]:
                return session_result
            
            session_id = session_result["session"]["id"]
            
            # 添加用户输入消息
            self.add_message(
                session_id=session_id,
                user_id=user_id,
                message_type="user",
                content=f"开始药物发现流程: {disease_name}",
                disease_name=disease_name,
                innovation_level=innovation_level,
                step=0,
                result_data={
                    "disease": disease_name,
                    "innovation_level": innovation_level
                }
            )
            
            # 添加系统响应消息
            system_content = f"正在为疾病 '{disease_name}' 进行药物发现分析（创新度: {innovation_level}）"
            
            self.add_message(
                session_id=session_id,
                user_id=user_id,
                message_type="system",
                content=system_content,
                disease_name=disease_name,
                innovation_level=innovation_level,
                step=0,
                result_data={
                    "workflow_data": workflow_data,
                    "logs": logs,
                    "timestamp": datetime.now().isoformat()
                }
            )
            
            return {
                "success": True,
                "session_id": session_id,
                "message": "药物发现会话已保存"
            }
            
        except Exception as e:
            logger.error(f"保存药物发现会话失败: {e}")
            return {
                "success": False,
                "error": "保存会话过程中发生错误",
                "error_code": "SAVE_ERROR"
            }
    
    def search_sessions(self, user_id: int, query: str, limit: int = 20) -> Dict[str, Any]:
        """搜索用户的对话会话"""
        try:
            # 这里使用简单的SQL LIKE搜索，实际项目中可以考虑使用全文搜索
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT DISTINCT s.* FROM conversation_sessions s
                    LEFT JOIN conversation_messages m ON s.id = m.session_id
                    WHERE s.user_id = ? AND s.is_active = TRUE
                    AND (s.title LIKE ? OR m.content LIKE ? OR m.disease_name LIKE ?)
                    ORDER BY s.updated_at DESC
                    LIMIT ?
                ''', (user_id, f'%{query}%', f'%{query}%', f'%{query}%', limit))
                
                rows = cursor.fetchall()
                
                sessions = []
                for row in rows:
                    session_data = {
                        "id": row["id"],
                        "title": row["title"],
                        "created_at": row["created_at"],
                        "updated_at": row["updated_at"],
                        "is_active": row["is_active"]
                    }
                    sessions.append(session_data)
                
                return {
                    "success": True,
                    "sessions": sessions,
                    "query": query
                }
                
        except Exception as e:
            logger.error(f"搜索会话失败: {e}")
            return {
                "success": False,
                "error": "搜索过程中发生错误",
                "error_code": "SEARCH_ERROR"
            }
    
    def save_workflow_data(self, session_id: int, user_id: int, workflow_data: dict) -> Dict[str, Any]:
        """保存工作流数据到会话"""
        try:
            session = self.db.get_session_by_id(session_id)
            if not session:
                return {
                    "success": False,
                    "error": "会话不存在",
                    "error_code": "SESSION_NOT_FOUND"
                }
            
            # 验证会话所有权
            if session.user_id != user_id:
                return {
                    "success": False,
                    "error": "无权操作此会话",
                    "error_code": "ACCESS_DENIED"
                }
            
            # 添加工作流数据消息
            message = self.add_message(
                session_id=session_id,
                user_id=user_id,
                message_type="workflow",
                content="工作流数据已保存",
                result_data=workflow_data
            )
            
            if not message["success"]:
                return message
            
            return {
                "success": True,
                "message": "工作流数据已保存",
                "workflow_data": workflow_data
            }
            
        except Exception as e:
            logger.error(f"保存工作流数据失败: {e}")
            return {
                "success": False,
                "error": "保存工作流数据过程中发生错误",
                "error_code": "SAVE_WORKFLOW_ERROR"
            }