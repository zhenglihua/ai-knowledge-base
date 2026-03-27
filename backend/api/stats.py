"""
数据统计API - 文档统计、问答统计、用户活跃度
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, desc
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import json

from models.database import get_db, Document, ChatMessage, Conversation, UserActivity, DailyStats

router = APIRouter(prefix="/api/stats", tags=["stats"])

@router.get("/dashboard")
def get_dashboard_stats(db: Session = Depends(get_db)):
    """获取仪表盘统计数据"""
    today = datetime.now().date()
    today_str = today.isoformat()
    
    # 文档统计
    total_docs = db.query(Document).count()
    active_docs = db.query(Document).filter(Document.status == 'active').count()
    
    # 今日上传
    today_uploads = db.query(Document).filter(
        func.date(Document.created_at) == today
    ).count()
    
    # 分类统计
    category_stats = db.query(
        Document.category,
        func.count(Document.id).label('count')
    ).group_by(Document.category).all()
    
    # 问答统计
    total_chats = db.query(ChatMessage).filter(ChatMessage.role == 'user').count()
    today_chats = db.query(ChatMessage).filter(
        ChatMessage.role == 'user',
        func.date(ChatMessage.created_at) == today
    ).count()
    
    # 平均响应时间
    avg_latency = db.query(func.avg(ChatMessage.latency_ms)).filter(
        ChatMessage.role == 'assistant'
    ).scalar() or 0
    
    # 活跃对话数
    active_conversations = db.query(Conversation).filter(
        Conversation.updated_at >= datetime.now() - timedelta(days=7)
    ).count()
    
    return {
        "documents": {
            "total": total_docs,
            "active": active_docs,
            "today_uploads": today_uploads,
            "categories": [
                {"name": c.category, "count": c.count}
                for c in category_stats
            ]
        },
        "chats": {
            "total": total_chats,
            "today": today_chats,
            "avg_latency_ms": round(avg_latency, 2),
            "active_conversations": active_conversations
        },
        "updated_at": datetime.now().isoformat()
    }

@router.get("/documents")
def get_document_stats(
    days: int = Query(default=30, le=365),
    db: Session = Depends(get_db)
):
    """获取文档统计详情"""
    start_date = datetime.now() - timedelta(days=days)
    
    # 按日统计上传量
    daily_uploads = db.query(
        func.date(Document.created_at).label('date'),
        func.count(Document.id).label('count')
    ).filter(
        Document.created_at >= start_date
    ).group_by(
        func.date(Document.created_at)
    ).order_by('date').all()
    
    # 文件类型统计
    file_type_stats = db.query(
        Document.file_type,
        func.count(Document.id).label('count'),
        func.sum(Document.file_size).label('total_size')
    ).group_by(Document.file_type).all()
    
    # 最近上传
    recent_docs = db.query(Document).order_by(
        desc(Document.created_at)
    ).limit(10).all()
    
    # 热门分类
    top_categories = db.query(
        Document.category,
        func.count(Document.id).label('count')
    ).group_by(Document.category).order_by(
        desc('count')
    ).limit(10).all()
    
    return {
        "summary": {
            "total": db.query(Document).count(),
            "period_days": days,
            "period_uploads": sum(d.count for d in daily_uploads)
        },
        "daily_uploads": [
            {"date": str(d.date), "count": d.count}
            for d in daily_uploads
        ],
        "file_types": [
            {
                "type": f.file_type,
                "count": f.count,
                "total_size_mb": round((f.total_size or 0) / 1024 / 1024, 2)
            }
            for f in file_type_stats
        ],
        "top_categories": [
            {"name": c.category, "count": c.count}
            for c in top_categories
        ],
        "recent_documents": [
            {
                "id": d.id,
                "title": d.title,
                "category": d.category,
                "created_at": d.created_at.isoformat()
            }
            for d in recent_docs
        ]
    }

@router.get("/chats")
def get_chat_stats(
    days: int = Query(default=30, le=365),
    db: Session = Depends(get_db)
):
    """获取问答统计详情"""
    start_date = datetime.now() - timedelta(days=days)
    
    # 按日统计问答量
    daily_chats = db.query(
        func.date(ChatMessage.created_at).label('date'),
        func.count(ChatMessage.id).label('count')
    ).filter(
        ChatMessage.role == 'user',
        ChatMessage.created_at >= start_date
    ).group_by(
        func.date(ChatMessage.created_at)
    ).order_by('date').all()
    
    # 按小时统计（今日）
    today = datetime.now().date()
    hourly_chats = db.query(
        func.strftime('%H', ChatMessage.created_at).label('hour'),
        func.count(ChatMessage.id).label('count')
    ).filter(
        ChatMessage.role == 'user',
        func.date(ChatMessage.created_at) == today
    ).group_by('hour').order_by('hour').all()
    
    # 延迟分布
    latency_ranges = db.query(
        func.case(
            (ChatMessage.latency_ms < 1000, '<1s'),
            (ChatMessage.latency_ms < 3000, '1-3s'),
            (ChatMessage.latency_ms < 5000, '3-5s'),
            else_='>5s'
        ).label('range'),
        func.count(ChatMessage.id).label('count')
    ).filter(
        ChatMessage.role == 'assistant'
    ).group_by('range').all()
    
    # 热门问题（基于对话标题）
    popular_topics = db.query(
        Conversation.title,
        func.count(ChatMessage.id).label('message_count')
    ).join(ChatMessage, Conversation.id == ChatMessage.conversation_id).group_by(
        Conversation.id
    ).order_by(desc('message_count')).limit(10).all()
    
    return {
        "summary": {
            "total_questions": db.query(ChatMessage).filter(ChatMessage.role == 'user').count(),
            "total_answers": db.query(ChatMessage).filter(ChatMessage.role == 'assistant').count(),
            "period_days": days,
            "period_questions": sum(d.count for d in daily_chats)
        },
        "daily_chats": [
            {"date": str(d.date), "count": d.count}
            for d in daily_chats
        ],
        "hourly_distribution": [
            {"hour": h.hour, "count": h.count}
            for h in hourly_chats
        ],
        "latency_distribution": [
            {"range": l.range, "count": l.count}
            for l in latency_ranges
        ],
        "avg_latency_ms": round(
            db.query(func.avg(ChatMessage.latency_ms)).filter(
                ChatMessage.role == 'assistant'
            ).scalar() or 0, 2
        ),
        "popular_topics": [
            {"title": t.title, "message_count": t.message_count}
            for t in popular_topics
        ]
    }

@router.get("/users")
def get_user_activity(
    days: int = Query(default=30, le=365),
    db: Session = Depends(get_db)
):
    """获取用户活跃度统计"""
    start_date = datetime.now() - timedelta(days=days)
    
    # 活跃用户列表
    active_users = db.query(
        Conversation.user_id,
        func.count(Conversation.id).label('conversation_count'),
        func.count(ChatMessage.id).label('message_count')
    ).join(ChatMessage, Conversation.id == ChatMessage.conversation_id).filter(
        Conversation.created_at >= start_date
    ).group_by(Conversation.user_id).order_by(
        desc('message_count')
    ).limit(20).all()
    
    # 活动类型分布
    activity_types = db.query(
        UserActivity.activity_type,
        func.count(UserActivity.id).label('count')
    ).filter(
        UserActivity.created_at >= start_date
    ).group_by(UserActivity.activity_type).all()
    
    # 按日活跃用户
    daily_active = db.query(
        func.date(UserActivity.created_at).label('date'),
        func.count(func.distinct(UserActivity.user_id)).label('unique_users'),
        func.count(UserActivity.id).label('total_activities')
    ).filter(
        UserActivity.created_at >= start_date
    ).group_by('date').order_by('date').all()
    
    return {
        "summary": {
            "period_days": days,
            "unique_users": len(active_users),
            "total_activities": sum(a.count for a in activity_types)
        },
        "top_users": [
            {
                "user_id": u.user_id,
                "conversations": u.conversation_count,
                "messages": u.message_count
            }
            for u in active_users
        ],
        "activity_distribution": [
            {"type": a.activity_type, "count": a.count}
            for a in activity_types
        ],
        "daily_activity": [
            {
                "date": str(d.date),
                "unique_users": d.unique_users,
                "total_activities": d.total_activities
            }
            for d in daily_active
        ]
    }

@router.get("/search-trends")
def get_search_trends(
    days: int = Query(default=7, le=30),
    db: Session = Depends(get_db)
):
    """获取搜索趋势（基于问答内容的关键词提取）"""
    start_date = datetime.now() - timedelta(days=days)
    
    # 获取最近的查询
    recent_queries = db.query(ChatMessage).filter(
        ChatMessage.role == 'user',
        ChatMessage.created_at >= start_date
    ).order_by(desc(ChatMessage.created_at)).limit(100).all()
    
    # 简单的关键词统计
    keyword_counts = {}
    for q in recent_queries:
        words = q.content.split()
        for word in words:
            if len(word) >= 2:  # 过滤短词
                keyword_counts[word] = keyword_counts.get(word, 0) + 1
    
    # 排序取前20
    top_keywords = sorted(
        keyword_counts.items(),
        key=lambda x: x[1],
        reverse=True
    )[:20]
    
    return {
        "period_days": days,
        "total_queries": len(recent_queries),
        "top_keywords": [
            {"keyword": k, "count": c}
            for k, c in top_keywords
        ],
        "recent_queries": [
            {
                "query": q.content[:50] + "..." if len(q.content) > 50 else q.content,
                "created_at": q.created_at.isoformat()
            }
            for q in recent_queries[:20]
        ]
    }

# 每日统计更新任务（可由定时任务调用）
@router.post("/daily-update")
def update_daily_stats(db: Session = Depends(get_db)):
    """更新每日统计数据"""
    today = datetime.now().date().isoformat()
    
    # 检查是否已存在
    stats = db.query(DailyStats).filter(DailyStats.date == today).first()
    if not stats:
        stats = DailyStats(date=today)
        db.add(stats)
    
    # 统计今日数据
    stats.chat_count = db.query(ChatMessage).filter(
        ChatMessage.role == 'user',
        func.date(ChatMessage.created_at) == datetime.now().date()
    ).count()
    
    stats.upload_count = db.query(Document).filter(
        func.date(Document.created_at) == datetime.now().date()
    ).count()
    
    stats.unique_users = db.query(func.distinct(Conversation.user_id)).filter(
        func.date(Conversation.updated_at) == datetime.now().date()
    ).count()
    
    db.commit()
    
    return {"message": "每日统计已更新", "date": today}