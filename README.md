# Distributed LLM Podcast Generator

[![Status](https://img.shields.io/badge/status-experimental-yellow.svg)](https://github.com/CornelliusHadriana/DistributedLLMPodcastGenerator)
[![License](https://img.shields.io/badge/license-See%20LICENSE-blue.svg)](LICENSE)

A service-style pipeline that converts newsletters and articles into podcast-ready scripts and audio using LLM summarization, script generation templates, and text-to-speech. The system is built as a lightweight FastAPI control plane with background workers (RQ) for long-running LLM and audio tasks.

Table of contents
- What the project does
- Why this project is useful
- Quickstart (installation & run)
  - Prerequisites
  - Configuration
  - Install
  - Run the API
  - Start workers
  - Example requests
- Project layout
- Development & tests
- Where to get help
- Maintainers & contributing

## What the project does
Distributed LLM Podcast Generator accepts written newsletter or article content, enqueues an asynchronous processing pipeline, and produces:
- A podcast-style script generated from LLM-based summarization and prompting.
- A rendered audio file (TTS) with optional SSML and post-processing.
- Status tracking for pipeline stages so clients can poll progress and fetch outputs.

Primary components:
- FastAPI control plane for ingesting content, returning job IDs, and exposing status/result endpoints.
- RQ-backed worker processes for chunking, summarization, script generation, TTS, and publishing.
- MongoDB for persistence (articles, episodes, pipeline status) and Redis for queues.

## Why this project is useful
- Non-blocking API: clients submit content and immediately receive a job id; heavy work runs in workers.
- Modular pipeline: summarization, script generation, and TTS are separated and swappable.
- Production-like patterns: queue-backed workers and status tracking mirror real-world architectures—good base for experimentation or productionization.
- Extensible prompts and datasets for fine-tuning and experimentation (processing/ and fine_tuning/).

## Quickstart

### Prerequisites
- Python 3.9+ (use pyenv or similar)
- MongoDB (or a Mongo-compatible service)
- Redis (for RQ queues)
- Google Cloud credentials if using Google TTS, or other TTS provider credentials depending on your configuration
- LLM API credentials (if using OpenAI/Hugging Face/etc.) as required by your model configuration

### Configuration
1. Copy and edit environment example (if present):
   - cp .env.example .env
   - Set relevant variables in `.env`:
     - MONGODB_URI (or DB connection used by repo)
     - REDIS_URL (or redis connection string)
     - GOOGLE_APPLICATION_CREDENTIALS (if using Google Cloud TTS)
     - GMAIL OAuth file path (if using email ingestion)
     - OPENAI_API_KEY (or other LLM keys) — set according to your processing config
2. Place sensitive credential files under `credentials/` (example: `credentials/gmail_oauth.json`) and do NOT commit them.

Check the `config/` directory for the project's configuration modules and update as needed.

### Install
Clone and install dependencies:

```bash
git clone https://github.com/CornelliusHadriana/DistributedLLMPodcastGenerator.git
cd DistributedLLMPodcastGenerator

python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
