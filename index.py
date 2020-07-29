import json
import redis
__redis_service = None
def initializer_for_dx():
    print("==========================================")
    global __redis_service
    __redis_service = redis.Redis(host="127.0.0.1", port=6379, decode_responses=True)

def handler_for_dx(event, context):
    evt = json.loads(event)
    host=(evt['host'])
    v=evt['value']
    k=evt['key']
    __redis_service.set(k, v)
    return 'end'
