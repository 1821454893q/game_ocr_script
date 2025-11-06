import time
from functools import wraps

# 计时装饰器
def calculate_time(description=""):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            end_time = time.time()
            elapsed_time = (end_time - start_time) * 1000  # 毫秒
            func_name = description if description else func.__name__
            print(f"⏱️  {func_name} 耗时: {elapsed_time:.2f}ms")
            return result
        return wrapper
    return decorator