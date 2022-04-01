# - read from any kafka
# - do computation
# - write back to kafka

import atexit
import logging
import json
import sys
import time

from kafka import KafkaProducer
from kafka.errors import KafkaError, KafkaTimeoutError
from pyspark import SparkContext
from pyspark.streaming import StreamingContext
from pyspark.streaming.kafka import KafkaUtils


topic = None
target_topic = None
brokers = None
kafka_producer = None


def shutdown_hook(producer):
    try:
        print('Flushing pending messages to kafka, timeout is set to 10s')
        producer.flush(10)
        print('Finish flushing pending messages to kafka')
    except KafkaError as kafka_error:
        print('Failed to flush pending messages to kafka, caused by: %s', kafka_error.message)
    finally:
        try:
            print('Closing kafka connection')
            producer.close(10)
        except Exception as e:
            print('Failed to close kafka connection, caused by: %s', e.message)


def process_stream(stream):

    def send_to_kafka(rdd):
        print('In send to Kafka Function!!')
        results = rdd.collect()
        # print('Size of Buffer:', results)
        for r in results:
            # print(r)
            data = json.dumps(
                {
                    'symbol': r[0],
                    'timestamp': time.time(),
                    'close': r[1][1][0],
                    'average': r[1][2][0]/r[1][2][1],
                    'open' : r[1][0][0],
                    'high' : r[1][3][0],
                    'low' : r[1][4][0],
                    'volume' : r[1][5],
                    'price' : r[1][6],
                    'name' : r[1][7]
                }
            )
            print("Results: ",data)
            try:
                # print('Sending average price %s to kafka' % data)
                bprice = json.dumps(data).encode('utf-8')
                kafka_producer.send(target_topic, value=bprice)
            except KafkaError as error:
                print('Failed to send average stock price to kafka, caused by: %s', error.message)

    def pairs(data):
        # record = json.loads(data[1].decode('utf-8'))[0]
        print("Data: ",data[1])
        record = json.loads(data[1])
        # a, b, c, d, e = record.get('StockSymbol'), (float(record.get('Open')),1), (float(record.get('Close')),1), (float(record.get('High')),1), (float(record.get('Low')),1), round(float(record.get('Price')), 2), record.get('Name')
        return record.get('StockSymbol'), [(float(record.get('Open')), 1), (float(record.get('Close')), 1), (float(record.get('Close')), 1), (float(record.get('High')), 1), (float(record.get('Low')), 1), int(record.get('Volume')), round(float(record.get('Price')), 1), record.get('Name')]
    
    stream.map(pairs).reduceByKey(lambda l1, l2: (l1[0], l1[1], (l1[2][0]+l2[2][0], l1[2][1]+l2[2][1]), l1[3], l1[4], l1[5], l1[6], l1[7])).foreachRDD(send_to_kafka)
    # stream.map(pair).reduceByKey(lambda a, b: (a[0] + b[0], a[1] + b[1])).map(lambda k: (k[0], k[1][0]/k[1][1])).foreachRDD(send_to_kafka)
    # stream.map(pairs).foreachRDD(send_to_kafka)


if __name__ == '__main__':
    if len(sys.argv) != 4:
        print("Usage: stream-process.py [topic] [target-topic] [broker-list]")
        exit(1)

    # - create SparkContext and StreamingContext
    sc = SparkContext("local[2]", "StockAveragePrice")
    sc.setLogLevel('ERROR')
    ssc = StreamingContext(sc, 5)

    topic, target_topic, brokers = sys.argv[1:]

    # - instantiate a kafka stream for processing
    directKafkaStream = KafkaUtils.createDirectStream(ssc, [topic], {'metadata.broker.list': brokers})
    process_stream(directKafkaStream)

    # - instantiate a simple kafka producer
    kafka_producer = KafkaProducer(
        bootstrap_servers=brokers
    )

    # - setup proper shutdown hook
    atexit.register(shutdown_hook, kafka_producer)

    ssc.start()
    ssc.awaitTermination()