#!/bin/bash

# Script to run RQ workers for all services
# Usage: ./run_workers.sh [service_name]
# If no service_name is provided, all workers will be started

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

start_worker() {
    local queue_name=$1
    local service_name=$2
    
    echo -e "${BLUE}Starting RQ worker for ${service_name} (queue: ${queue_name})...${NC}"
    
    cd "$PROJECT_ROOT"
    rq worker "$queue_name" --path . &
    
    echo -e "${GREEN}Started ${service_name} worker (PID: $!)${NC}"
}

if [ -z "$1" ]; then
    # Start all workers
    echo "Starting all RQ workers..."
    echo "NOTE: Queue names are outdated and need to be updated for the new architecture"
    start_worker "ingestion" "Ingestion"
    start_worker "llm" "LLM Worker"
    
    echo ""
    echo "All workers started. Use 'pkill -f rq worker' to stop all workers."
    echo ""
    echo "TODO: Update workers for new architecture:"
    echo "  - ingest_article (Normalizer)"
    echo "  - summarize_chunks (Summarization)"
    echo "  - assemble_summary (Assembly)"
    echo "  - text_to_speech (TTS)"
    echo "  - publish_episode (Publisher)"
else
    # Start specific worker
    case "$1" in
        ingestion)
            start_worker "ingestion" "Ingestion"
            ;;
        llm)
            start_worker "llm" "LLM Worker"
            ;;
        *)
            echo "Unknown service: $1"
            echo "Available services: ingestion, llm"
            echo ""
            echo "NOTE: These queue names are outdated. The new architecture requires:"
            echo "  - ingest_article"
            echo "  - summarize_chunks"
            echo "  - assemble_summary"
            echo "  - text_to_speech"
            echo "  - publish_episode"
            exit 1
            ;;
    esac
fi

wait
