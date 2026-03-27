from sqlalchemy import create_engine, Column, String, Text, DateTime, Integer, ForeignKey, Float, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

Base = declarative_base()
engine = create_engine('sqlite:///knowledge_base.db', echo=False, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)

# 导入认证模型以确保表创建
try:
    from models.auth_models import User, Role, Permission, RefreshToken, AuditLog, DocumentAccessLog, Department
except ImportError:
    pass  # 认证模型可能尚未创建

class Document(Base):
    __tablename__ = 'documents'
    
    id = Column(String, primary_key=True)
    filename = Column(String, nullable=False)
    title = Column(String)
    content = Column(Text)
    category = Column(String, default='未分类')
    tags = Column(String)
    file_path = Column(String)
    file_size = Column(Integer)
    file_type = Column(String)
    status = Column(String, default='active')  # active, processing, error
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

class Conversation(Base):
    """对话会话表"""
    __tablename__ = 'conversations'
    
    id = Column(String, primary_key=True)
    title = Column(String, default='新对话')
    user_id = Column(String, default='anonymous')  # 支持多用户
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 关联消息
    messages = relationship("ChatMessage", back_populates="conversation", cascade="all, delete-orphan")

class ChatMessage(Base):
    """聊天消息表"""
    __tablename__ = 'chat_messages'
    
    id = Column(String, primary_key=True)
    conversation_id = Column(String, ForeignKey('conversations.id'), nullable=False)
    role = Column(String, nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    sources = Column(Text)  # JSON格式存储引用来源
    tokens_used = Column(Integer, default=0)
    latency_ms = Column(Integer, default=0)  # 响应延迟毫秒
    created_at = Column(DateTime, default=datetime.now)
    
    conversation = relationship("Conversation", back_populates="messages")

class UserActivity(Base):
    """用户活动统计表"""
    __tablename__ = 'user_activities'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, default='anonymous')
    activity_type = Column(String, nullable=False)  # chat, upload, search, login
    details = Column(Text)  # JSON格式存储详情
    created_at = Column(DateTime, default=datetime.now)

class DailyStats(Base):
    """每日统计数据表"""
    __tablename__ = 'daily_stats'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(String, unique=True, nullable=False)  # YYYY-MM-DD
    chat_count = Column(Integer, default=0)
    upload_count = Column(Integer, default=0)
    search_count = Column(Integer, default=0)
    unique_users = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    avg_latency_ms = Column(Integer, default=0)


class Category(Base):
    """文档分类表"""
    __tablename__ = 'categories'
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(Text)
    color = Column(String, default='blue')  # UI显示颜色
    icon = Column(String, default='📄')  # UI图标
    sort_order = Column(Integer, default=0)  # 排序
    is_preset = Column(Integer, default=0)  # 是否预设分类
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 关联文档 - 使用viewonly避免外键问题
    documents = relationship("Document", 
                           primaryjoin="remote(Category.name) == foreign(Document.category)",
                           viewonly=True)


class Tag(Base):
    """标签表"""
    __tablename__ = 'tags'
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    tag_type = Column(String, default='custom')  # equipment, process, parameter, material, custom
    description = Column(Text)
    color = Column(String, default='default')
    usage_count = Column(Integer, default=0)  # 使用次数
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class DocumentTag(Base):
    """文档-标签关联表"""
    __tablename__ = 'document_tags'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(String, ForeignKey('documents.id'), nullable=False)
    tag_id = Column(String, ForeignKey('tags.id'), nullable=False)
    confidence = Column(Float, default=1.0)  # 标签置信度（AI提取的标签可能低于1）
    created_at = Column(DateTime, default=datetime.now)
    
    # 复合唯一约束
    __table_args__ = (
        UniqueConstraint('document_id', 'tag_id', name='unique_document_tag'),
    )


# 更新Document模型，添加与Category的关系
Document.category_obj = relationship("Category", 
                                    primaryjoin="remote(Category.name) == foreign(Document.category)",
                                    viewonly=True)


def init_db():
    Base.metadata.create_all(engine)
    
    # 初始化预设分类
    _init_preset_categories()


def _init_preset_categories():
    """初始化预设分类"""
    db = SessionLocal()
    try:
        preset_categories = [
            {"id": "process", "name": "工艺文档", "color": "blue", "icon": "⚙️", "description": "工艺制程相关文档"},
            {"id": "equipment", "name": "设备文档", "color": "green", "icon": "🔧", "description": "设备维护、操作手册"},
            {"id": "cim", "name": "CIM系统", "color": "purple", "icon": "💻", "description": "计算机集成制造系统"},
            {"id": "quality", "name": "质量管控", "color": "orange", "icon": "📊", "description": "质量检测与管控"},
            {"id": "production", "name": "生产管理", "color": "cyan", "icon": "🏭", "description": "生产计划与调度"},
            {"id": "safety", "name": "安全环保", "color": "red", "icon": "🛡️", "description": "安全与环保规范"},
            {"id": "other", "name": "其他文档", "color": "default", "icon": "📄", "description": "其他类型文档"},
        ]
        
        for cat in preset_categories:
            existing = db.query(Category).filter(Category.id == cat["id"]).first()
            if not existing:
                category = Category(
                    id=cat["id"],
                    name=cat["name"],
                    description=cat.get("description"),
                    color=cat.get("color", "blue"),
                    icon=cat.get("icon", "📄"),
                    is_preset=1,
                    sort_order=list(preset_categories).index(cat)
                )
                db.add(category)
        
        db.commit()
    except Exception as e:
        print(f"初始化预设分类失败: {e}")
        db.rollback()
    finally:
        db.close()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_db_session():
    """获取数据库会话（用于非依赖注入场景）"""
    return SessionLocal()