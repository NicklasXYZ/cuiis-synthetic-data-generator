# Coordinate transformation settings
UTM_ZONE = 35

# Redis settings
REDIS_TTL = 8600
REDIS_HOST = "redis"
REDIS_PORT = 6379
REDIS_DB= "1"
REDIS_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"


REDIS_KV_STORE_PREFIX_GENERATOR = "kvstore"
REDIS_SORTED_SET_PREFIX_GENERATOR = "sortedset"
REDIS_SORTED_SET_GENERATORS = "sortedset-generators"