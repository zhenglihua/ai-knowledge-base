"""
性能优化工具
- 缓存管理
- 数据库连接池优化
- 请求限流
"""
import time
import functools
from typing import Optional, Any
from datetime import datetime, timedelta

# 简单的内存缓存
class Cache:
    def __init__(self):
        self._cache = {}
        self._expire = {}
    
    def get(self, key: str) -> Optional[Any]:
        if key in self._cache:
            if time.time() < self._expire.get(key, 0):
                return self._cache[key]
            else:
                self.delete(key)
        return None
    
    def set(self, key: str, value: Any, expire_seconds: int = 300):
        self._cache[key] = value
        self._expire[key] = time.time() + expire_seconds
    
    def delete(self, key: str):
        self._cache.pop(key, None)
        self._expire.pop(key, None)
    
    def clear(self):
        self._cache.clear()
        self._expire.clear()

# 全局缓存实例
cache = Cache()

def cached(expire_seconds: int = 300):
    """缓存装饰器"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 生成缓存键
            key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # 尝试从缓存获取
            result = cache.get(key)
            if result is not None:
                return result
            
            # 执行函数
            result = func(*args, **kwargs)
            
            # 存入缓存
            cache.set(key, result, expire_seconds)
            
            return result
        return wrapper
    return decorator

def clear_cache_pattern(pattern: str):
    """清除匹配模式的缓存"""
    keys_to_delete = [k for k in cache._cache.keys() if pattern in k]
    for key in keys_to_delete:
        cache.delete(key)

# 性能监控
class PerformanceMonitor:
    def __init__(self):
        self.metrics = {
            'requests': 0,
            'errors': 0,
            'total_latency': 0,
            'start_time': time.time()
        }
    
    def record_request(self, latency_ms: float, error: bool = False):
        self.metrics['requests'] += 1
        self.metrics['total_latency'] += latency_ms
        if error:
            self.metrics['errors'] += 1
    
    def get_stats(self):
        uptime = time.time() - self.metrics['start_time']
        requests = self.metrics['requests']
        return {
            'uptime_seconds': int(uptime),
            'total_requests': requests,
            'errors': self.metrics['errors'],
            'avg_latency_ms': round(self.metrics['total_latency'] / requests, 2) if requests > 0 else 0,
            'requests_per_minute': round(requests / (uptime / 60), 2) if uptime > 0 else 0
        }

monitor = PerformanceMonitor()

def measure_latency(func):
    """测量函数执行时间"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        try:
            result = func(*args, **kwargs)
            latency = (time.time() - start) * 1000
            monitor.record_request(latency)
            return result
        except Exception as e:
            latency = (time.time() - start) * 1000
            monitor.record_request(latency, error=True)
            raise e
    return wrapper

# 数据库查询优化
def optimize_query(query, limit: int = 100):
    """优化数据库查询"""
    # 添加限制
    if limit > 1000:
        limit = 1000
    return query.limit(limit)