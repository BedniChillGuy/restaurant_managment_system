"""
Модуль для работы с Redis: кеширование данных и rate limiting
"""
import os
import json
import redis
from typing import Optional, List, Dict, Any, Tuple
from functools import wraps
from fastapi import HTTPException, status
import time


class RedisClient:
    
    def __init__(self):
        self.redis_host = os.getenv("REDIS_HOST", "redis")
        redis_port_env = os.getenv("REDIS_SERVICE_PORT") or os.getenv("REDIS_PORT") or "6379"
        self.redis_port = int(str(redis_port_env).split(":")[-1])
        
        try:
            self.client = redis.Redis(
                host=self.redis_host,
                port=self.redis_port,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            self.client.ping()
        except Exception as e:
            print(f" Не удалось подключиться к Redis: {e}")
            self.client = None
    
    def is_available(self) -> bool:
        if not self.client:
            return False
        try:
            self.client.ping()
            return True
        except:
            return False

    
    def cache_dishes(self, dishes: List[Dict], ttl: int = 300) -> bool:
        if not self.is_available():
            return False
        try:
            dishes_json = json.dumps(dishes, default=str)
            self.client.setex("dishes:all", ttl, dishes_json)
            return True
        except Exception as e:
            print(f"Ошибка кеширования блюд: {e}")
            return False
    
    def get_cached_dishes(self) -> Optional[List[Dict]]:
        if not self.is_available():
            return None
        try:
            cached = self.client.get("dishes:all")
            if cached:
                return json.loads(cached)
        except Exception as e:
            print(f"Ошибка получения блюд из кеша: {e}")
        return None
    
    def invalidate_dishes_cache(self) -> bool:
        if not self.is_available():
            return False
        try:
            self.client.delete("dishes:all")
            return True
        except Exception as e:
            print(f"Ошибка инвалидации кеша блюд: {e}")
            return False

    
    def cache_tables(self, tables: List[Dict], ttl: int = 60) -> bool:
        if not self.is_available():
            return False
        try:
            tables_json = json.dumps(tables, default=str)
            self.client.setex("tables:all", ttl, tables_json)
            return True
        except Exception as e:
            print(f"Ошибка кеширования столов: {e}")
            return False
    
    def get_cached_tables(self) -> Optional[List[Dict]]:
        if not self.is_available():
            return None
        try:
            cached = self.client.get("tables:all")
            if cached:
                return json.loads(cached)
        except Exception as e:
            print(f"Ошибка получения столов из кеша: {e}")
        return None
    
    def cache_available_tables(self, tables: List[Dict], ttl: int = 30) -> bool:

        if not self.is_available():
            return False
        try:
            tables_json = json.dumps(tables, default=str)
            self.client.setex("tables:available", ttl, tables_json)
            return True
        except Exception as e:
            print(f"Ошибка кеширования доступных столов: {e}")
            return False
    
    def get_cached_available_tables(self) -> Optional[List[Dict]]:

        if not self.is_available():
            return None
        try:
            cached = self.client.get("tables:available")
            if cached:
                return json.loads(cached)
        except Exception as e:
            print(f"Ошибка получения доступных столов из кеша: {e}")
        return None
    
    def invalidate_tables_cache(self) -> bool:

        if not self.is_available():
            return False
        try:
            self.client.delete("tables:all", "tables:available")
            return True
        except Exception as e:
            print(f"Ошибка инвалидации кеша столов: {e}")
            return False

    
    def cache_order(self, order_id: int, order_data: Dict, ttl: int = 180) -> bool:
        if not self.is_available():
            return False
        try:
            order_json = json.dumps(order_data, default=str)
            self.client.setex(f"order:{order_id}", ttl, order_json)
            return True
        except Exception as e:
            print(f"Ошибка кеширования заказа {order_id}: {e}")
            return False
    
    def get_cached_order(self, order_id: int) -> Optional[Dict]:
        if not self.is_available():
            return None
        try:
            cached = self.client.get(f"order:{order_id}")
            if cached:
                return json.loads(cached)
        except Exception as e:
            print(f"Ошибка получения заказа {order_id} из кеша: {e}")
        return None
    
    def invalidate_order_cache(self, order_id: int) -> bool:
        if not self.is_available():
            return False
        try:
            self.client.delete(f"order:{order_id}")
            return True
        except Exception as e:
            print(f"Ошибка инвалидации кеша заказа {order_id}: {e}")
            return False
    
    def invalidate_all_orders_cache(self) -> bool:
        if not self.is_available():
            return False
        try:
            keys = self.client.keys("order:*")
            if keys:
                self.client.delete(*keys)
            return True
        except Exception as e:
            print(f"Ошибка инвалидации кеша всех заказов: {e}")
            return False

    def check_rate_limit(self, key: str, max_requests: int = 10, window: int = 60) -> Tuple[bool, int]:
        if not self.is_available():
            return True, max_requests
        
        try:
            current = self.client.incr(key)
            if current == 1:
                self.client.expire(key, window)
            
            remaining = max(0, max_requests - current)
            allowed = current <= max_requests
            
            return allowed, remaining
        except Exception as e:
            print(f"Ошибка проверки rate limit: {e}")
            return True, max_requests

    def increment_dish_views(self, dish_id: int) -> bool:
        if not self.is_available():
            return False
        try:
            self.client.incr(f"stats:dish:{dish_id}:views")
            return True
        except Exception as e:
            print(f"Ошибка увеличения счетчика просмотров блюда {dish_id}: {e}")
            return False
    
    def get_dish_views(self, dish_id: int) -> int:
        if not self.is_available():
            return 0
        try:
            views = self.client.get(f"stats:dish:{dish_id}:views")
            return int(views) if views else 0
        except:
            return 0
    
    def get_popular_dishes(self, limit: int = 10) -> List[Tuple[int, int]]:
        if not self.is_available():
            return []
        try:
            keys = self.client.keys("stats:dish:*:views")
            dishes = []
            for key in keys:
                dish_id = int(key.split(":")[2])
                views = int(self.client.get(key) or 0)
                dishes.append((dish_id, views))

            dishes.sort(key=lambda x: x[1], reverse=True)
            return dishes[:limit]
        except Exception as e:
            print(f"Ошибка получения популярных блюд: {e}")
            return []

    
    def clear_all_cache(self) -> bool:
        if not self.is_available():
            return False
        try:
            # Удаляем только наши ключи, не трогая системные
            patterns = ["dishes:*", "tables:*", "order:*", "stats:*"]
            for pattern in patterns:
                keys = self.client.keys(pattern)
                if keys:
                    self.client.delete(*keys)
            return True
        except Exception as e:
            print(f"Ошибка очистки кеша: {e}")
            return False
    
    def get_cache_info(self) -> Dict[str, Any]:
        if not self.is_available():
            return {"status": "unavailable"}
        
        try:
            info = {
                "status": "available",
                "dishes_cached": self.client.exists("dishes:all"),
                "tables_cached": self.client.exists("tables:all"),
                "available_tables_cached": self.client.exists("tables:available"),
                "cached_orders_count": len(self.client.keys("order:*")),
                "stats_keys_count": len(self.client.keys("stats:*"))
            }
            return info
        except Exception as e:
            return {"status": "error", "error": str(e)}


redis_client = RedisClient()



def rate_limit(max_requests: int = 10, window: int = 60, key_prefix: str = "rate_limit"):

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request = kwargs.get('request') or (args[0] if args and hasattr(args[0], 'client') else None)

            if request and hasattr(request, 'client'):
                client_host = request.client.host if hasattr(request.client, 'host') else "unknown"
                rate_key = f"{key_prefix}:{func.__name__}:{client_host}"
            else:
                rate_key = f"{key_prefix}:{func.__name__}:global"
            
            allowed, remaining = redis_client.check_rate_limit(rate_key, max_requests, window)
            
            if not allowed:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Rate limit exceeded. Try again in {window} seconds."
                )

            response = await func(*args, **kwargs)
            if hasattr(response, 'headers'):
                response.headers["X-RateLimit-Limit"] = str(max_requests)
                response.headers["X-RateLimit-Remaining"] = str(remaining)
                response.headers["X-RateLimit-Reset"] = str(int(time.time()) + window)
            
            return response
        return wrapper
    return decorator

