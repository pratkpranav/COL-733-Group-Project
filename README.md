# Portfolio Management System

This repository contains a prototype stock portfolio management platform built with multiple services:

- **Kafka** for event streaming
- **Spark** for stream processing
- **Cassandra** for storage
- **Redis** for pub/sub
- **Node.js** for the web interface

The `run_all.sh` script starts the entire stack using the local binaries included in the repo. It assumes Java and Python dependencies are already installed.

## Usage

```bash
./run_all.sh
```

If you would like to expose the dashboard to the internet, install [ngrok](https://ngrok.com/) and run:

```bash
./run_all.sh --public
```

This launches ngrok so the Node.js dashboard becomes accessible via a public URL printed by ngrok.

Once all services are running you can point your browser to `http://localhost:3000` to access the web interface.

Deploying this stack publicly requires a host with sufficient resources. One possible approach is to create a virtual machine on a cloud provider (e.g. AWS EC2) and run the same script there. Make sure to update any firewall rules to expose the necessary ports.

