#!/bin/bash

# Launch the portfolio management stack
# Usage: ./run_all.sh [--public]
# If --public is supplied and ngrok is installed, the web dashboard will be
# exposed publicly via ngrok.

set -e

PUBLIC=0
if [ "$1" = "--public" ]; then
    PUBLIC=1
fi

# Start Kafka and Zookeeper
./kafka-3.1.0-src/bin/zookeeper-server-start.sh -daemon ./kafka-3.1.0-src/config/zookeeper.properties
sleep 5
./kafka-3.1.0-src/bin/kafka-server-start.sh -daemon ./kafka-3.1.0-src/config/server.properties

# Start Redis
redis-server --daemonize yes

# Start Cassandra
cassandra -R

# Start Spark streaming job
spark-2.4.5-bin-hadoop2.6/bin/spark-submit \
  --packages org.apache.spark:spark-streaming-kafka-0-8_2.11:2.4.5 \
  Portfolio-Management-System/Spark/spark-stream.py stock-analyzer average-stock-price &

# Start Redis publisher which bridges Kafka to Redis
python3 Portfolio-Management-System/Redis/redis-publisher.py stock-analyzer localhost:9092 average-stock-price &

# Start Cassandra consumer to persist data
python3 Portfolio-Management-System/Cassandra/data-storage.py stock-analyzer localhost:9092 stock stock localhost &

# Start Flask producer
python3 Portfolio-Management-System/Kafka/flask-kafka.py &

# Start Node.js dashboard
(
  cd Portfolio-Management-System/Node.JS
  npm install
  node index.js --port=3000 --redis_host=localhost --redis_port=6379 --subscribe_topic=average-stock-price &
)

if [ "$PUBLIC" = "1" ]; then
  if ! command -v ngrok >/dev/null; then
    echo "ngrok not found. Install from https://ngrok.com/"
    exit 1
  fi
  echo "Starting ngrok to expose the dashboard..."
  ngrok http 3000
else
  echo "Stack started locally. Access the dashboard at http://localhost:3000"
fi
