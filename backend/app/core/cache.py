from cachetools import TTLCache

# 24h caches for external lookups; keys are plain strings/tuples.
attractions_cache: TTLCache = TTLCache(maxsize=512, ttl=86400)
distance_cache: TTLCache = TTLCache(maxsize=4096, ttl=86400)
pricing_cache: TTLCache = TTLCache(maxsize=512, ttl=3600)
