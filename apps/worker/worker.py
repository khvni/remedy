import os
import sys
from pathlib import Path

from rq import Worker, Queue
from redis import Redis

# Ensure worker can resolve project modules when launched as a script
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

listen = ['remedy']
redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
conn = Redis.from_url(redis_url)

if __name__ == '__main__':
    queues = [Queue(name, connection=conn) for name in listen]
    worker = Worker(queues)
    worker.work()
