#!/usr/bin/env bash
set -e

SERVICES=("api-gateway" "posts" "users")
PYTHON_CMD="python3"

LOG_DIR="logs"
mkdir -p "$LOG_DIR"

echo ""
echo "log directory: $LOG_DIR"
echo ""

if ! command -v $PYTHON_CMD &> /dev/null; then
    echo "python3 not found"
    exit 1
fi


setup_service() {
    SERVICE=$1
    echo -e "\n configuring microservice: $SERVICE"

    if [ ! -d "$SERVICE" ]; then
        echo "directory $SERVICE not found — skipping"
        return
    fi

    cd $SERVICE

    if [ ! -d ".venv" ]; then
        echo "creating .venv for $SERVICE..."
        $PYTHON_CMD -m venv .venv
    else
        echo ".venv already exists — using existing environment"
    fi

    
    source .venv/bin/activate
    pip install --upgrade pip setuptools wheel

    pip install -e ../shared
    pip install -e .
    pip install watchfiles
    pip freeze > requirements.lock

    deactivate
    cd ..
}

for SERVICE in "${SERVICES[@]}"; do
    setup_service $SERVICE
done


run_service() {
    SERVICE=$1
    CMD=$2

    echo ""
    echo "starting $SERVICE"

    cd $SERVICE
    source .venv/bin/activate

    LOG_PATH="../${LOG_DIR}/${SERVICE}.log"

    echo "logging to: ${LOG_PATH}"

    
    nohup sh -c "$CMD" > "$LOG_PATH" 2>&1 &

    deactivate
    cd ..
}

echo ""
echo " remember to start RabbitMQ and databases manually in saperate terminal:"
echo ""
echo "  docker compose up -d rabbitmq mongo_posts postgres_users"
echo ""


run_service "api-gateway" "uvicorn api_gateway.app.main:app --host 0.0.0.0 --port 8000 --reload"
run_service "posts" "watchfiles python -m posts.app.main"
run_service "users" "watchfiles python -m users.app.main"
