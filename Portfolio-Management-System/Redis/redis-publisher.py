# - read from kafka topic
# - publish to redis pub

from kafka import KafkaConsumer

import sys
# import argparse
import atexit
# import logging
import redis

# - default kafka topic to write to
topic_name = 'stock-analyzer'

# - default kafka broker location
kafka_broker = '127.0.0.1:9092'



def shutdown_hook(kafka_consumer):
    print('Shutdown kafka consumer')
    kafka_consumer.close()

if __name__ == '__main__':
    topic_name = sys.argv[1]
    kafka_broker = sys.argv[2]
    redis_channel = sys.argv[3]
    redis_host = sys.argv[4]
    redis_port = sys.argv[5]

    # - instantiate a simple kafka consumer
    kafka_consumer = KafkaConsumer(
        topic_name,
        bootstrap_servers=kafka_broker
    )

    # - instantiate a redis client
    redis_client = redis.StrictRedis(host=redis_host, port=redis_port)

    # - setup proper shutdown hook
    atexit.register(shutdown_hook, kafka_consumer)

    for msg in kafka_consumer:
        print('Received new data from kafka %s' % str(msg))
        redis_client.publish(redis_channel, msg.value)
        print("Published:", redis_channel, msg.value)

