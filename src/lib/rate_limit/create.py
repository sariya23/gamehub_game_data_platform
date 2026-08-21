from src.lib.rate_limit.rate_limit import RateLimitConfig, RateLimiter


def create_rate_limiter(config: RateLimitConfig) -> RateLimiter:
    return RateLimiter(config)