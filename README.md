# ADD Detection System

## Overview

This system addresses the challenge of identifying Architectural Design Decisions (ADDs) in software development issues. ADDs represent critical knowledge about why a system is designed a certain way, but this information is often scattered across issue tracking systems and rarely explicitly documented.

Our ML-powered solution automatically classifies issues to determine if they contain architectural decisions, helping teams:
- **Document architectural knowledge** automatically
- **Search and retrieve** relevant architectural decisions
- **Understand design rationale** from historical issues
- **Maintain architectural context** as teams evolve

### Problem Context

Traditional software architecture focuses on component structures and interactions, but modern architectural knowledge includes the *decisions* that led to those structures. Research shows that:
- ADDs are predominantly tacit knowledge
- Dedicated documentation tools have low adoption
- Issue tracking systems contain implicit architectural knowledge
- Manual extraction is time-consuming and incomplete

### Solution Approach

Our system uses a fine-tuned DistilBERT model trained on 6,200+ manually annotated issues to classify three types of ADDs:
- **Existence Decisions**: Component creation/deletion and interactions
- **Executive Decisions**: Development process and tooling choices
- **Property Decisions**: System-wide quality attributes

---

## Features

### Core Functionality
- **Single Issue Prediction**: Real-time ADD classification with confidence scores
- **Batch Processing**: Parallel classification of multiple issues
- **Keyword Search**: Full-text search across issue database
- **Asynchronous Processing**: Non-blocking API with task queuing
- **Web Interface**: Responsive React-based frontend

### Production Features
- **MLflow Integration**: Model versioning and experiment tracking
- **Performance Monitoring**: Prometheus + Grafana dashboards
- **Centralized Logging**: Loki-based log aggregation
- **Security**: Environment-based secrets management
- **CI/CD Pipeline**: Automated testing, linting, and deployment
- **Docker Compose**: One-command deployment
- **Data Versioning**: DVC for reproducible datasets

### Bonus Features
- **Human-in-the-Loop**: User contribution system for labeled data
- **Automated Retraining**: GitLab pipeline triggers on new data
- **Model Cards**: Comprehensive model documentation
- **Data Validation**: Pandera-based quality checks

---

## System Architecture

### High-Level Architecture
```
┌─────────────────┐
│   Web Browser   │
└────────┬────────┘
         │
┌────────▼────────┐
│  Nginx (80)     │  ← Frontend
│  React SPA      │
└────────┬────────┘
         │
┌────────▼────────┐
│  FastAPI (8080) │  ← Backend API
│  + Prometheus   │
└────┬───────┬────┘
     │       │
     │   ┌───▼────────┐
     │   │ Celery     │  ← Async Workers
     │   │ Workers    │
     │   └───┬────────┘
     │       │
┌────▼───────▼────┐
│  Redis (6379)   │  ← Task Queue + Cache
└─────────────────┘

┌─────────────────┐
│ PostgreSQL      │  ← Application DB
│ (5432)          │
└─────────────────┘

┌─────────────────┐
│ MLflow (5000)   │  ← Model Registry
│ + MinIO (9000)  │
│ + PostgreSQL    │
└─────────────────┘

┌─────────────────┐
│ Grafana (3000)  │  ← Monitoring
│ + Prometheus    │
│ + Loki          │
└─────────────────┘

┌─────────────────┐
│ MongoDB (27017) │  ← Source Data
└─────────────────┘
```

### Component Interactions

1. **Frontend → API**: HTTP/REST requests
2. **API → Celery**: Task submissions via Redis
3. **Celery → MLflow**: Model loading from registry
4. **API → PostgreSQL**: Data persistence and search
5. **All Services → Prometheus**: Metrics collection
6. **All Services → Loki**: Log aggregation
7. **Grafana**: Visualization of metrics and logs

---

## Technology Stack

### Backend
- **API Framework**: FastAPI 0.110+
- **Async Processing**: Celery 5.6.2 + Redis 4.5.5
- **ML Framework**: PyTorch 2.2.0 + Transformers
- **Model Registry**: MLflow + MinIO (S3-compatible)
- **Database**: PostgreSQL 15
- **Data Validation**: Pandera

### Frontend
- **Framework**: React 18.2
- **HTTP Client**: Axios 1.6
- **Build Tool**: React Scripts 5.0
- **Web Server**: Nginx (Alpine)

### DevOps & Infrastructure
- **Containerization**: Docker + Docker Compose
- **CI/CD**: GitLab CI/CD
- **Monitoring**: Prometheus + Grafana 10.4
- **Logging**: Loki
- **Data Versioning**: DVC (Google Drive remote)
- **Code Quality**: PyLint

### ML/Data
- **Base Model**: DistilBERT (distilbert-base-uncased)
- **Metrics**: TorchMetrics (Accuracy, F1, Precision, Recall)
- **Class Balancing**: Weighted loss functions
- **Data Source**: MongoDB (Jira repositories)

---

## Getting Started

### Prerequisites

- **Docker** 20.10+ and **Docker Compose** 3.8+
- **Git** 2.30+
- **DVC** 2.0+ (for data management)
- **Python** 3.11+ (for local development)
- **Node.js** 20+ (for frontend development)

### Quick Start (Production)

1. **Clone the Repository**
```bash
   git clone <repository-url>
   cd <repository-name>
```

2. **Configure Environment Variables**
```bash
   cat > .env << EOF
   GITLAB_TRIGGER_TOKEN=<your-token>
   GITLAB_PROJECT_ID=<your-project-id>
   GITLAB_REF=main
   MLFLOW_MODEL_NAME=add_detection_model
   EOF
```

3. **Pull Data from DVC**
```bash
   dvc pull
```

4. **Start All Services**
```bash
   docker compose up -d
```

5. **Initialize Database**
```bash
   docker compose exec app-api python backend/api/init_db.py
```

6. **Load Training Data**
```bash
   docker compose exec app-api python data/preprocessing/ppl-load_data.py
```

7. **Access the System**
   - Frontend: https://mlops.digital-lab.dev/?warpgate-target=Group%206%20HTTP%20Frontend
   - API Docs: http://localhost:8080/docs
   - MLflow: https://mlops.digital-lab.dev/?warpgate-target=Group%206%20MLFlow%20Console
   - Grafana: https://mlops.digital-lab.dev/grafana/login (admin/admin)
   - Backend: https://mlops.digital-lab.dev/?warpgate-target=Group%206%20HTTP%20Backend

### Development Setup

1. **Install Python Dependencies**
```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
```

2. **Install Frontend Dependencies**
```bash
   cd frontend
   npm install
   npm start
```

3. **Run Local Services**
```bash
   # Start infrastructure only
   docker compose up -d postgres-ml redis mongo mlflow
   
   # Run API locally
   uvicorn backend.api.app:app --reload --port 8080
   
   # Run Celery worker locally
   celery -A backend.inference.tasks worker --loglevel=info
```

---


## Data Management

### Data Sources

The system uses two primary datasets from [Zenodo](https://zenodo.org/records/8372644):

1. **JiraRepos** (2.8M issues): Raw Jira data from multiple projects
2. **MiningDesignDecisions** (6.2K annotated): Manually labeled issues

### DVC Workflow

**Setup DVC Remote**
```bash
# Configure Google Drive remote
dvc remote add -d myremotename gdrive://0AGs8R3WqQ9mRUk9PVA
dvc remote modify myremotename gdrive_client_id <your-client-id>
dvc remote modify myremotename gdrive_client_secret <your-secret>
```

**Track Data**
```bash
# Add data to DVC
dvc add data/issue_with_labels.csv

# Push to remote
dvc push
```

**Reproduce Pipeline**
```bash
# Run data preprocessing
dvc repro
```

### Data Pipeline

The `dvc.yaml` defines a reproducible pipeline:
```yaml
stages:
  preprocess:
    cmd: python data/preprocessing/ppl-load_data.py
    deps:
      - data/preprocessing/ppl-load_data.py
      - data/issue_with_labels.csv
    params:
      - preprocessing.params
    outs:
      - data/processed/

  train:
    cmd: python data/training/ppl-train.py
    deps:
      - data/training/ppl-train.py
      - data/processed/
    params:
      - training.learning_rate
      - training.batch_size
      - training.epochs
    metrics:
      - metrics/train_metrics.json
```

### Data Preprocessing

**Extraction from MongoDB**:
```python
# data/preprocessing/preprocessing.py
python data/preprocessing/preprocessing.py
```

**Loading to PostgreSQL**:
```python
# Load processed data into database
python data/preprocessing/ppl-load_data.py
```

**Validation with Pandera**:
```python
# Validate data quality
python data/preprocessing/pandera_check.py
```

### Database Schema

**Processed Issues** (Training Data):
```sql
CREATE TABLE processed_issues (
    issue_key VARCHAR(50) PRIMARY KEY,
    summary TEXT,
    description TEXT,
    label_existence BOOLEAN,
    label_executive BOOLEAN,
    label_property BOOLEAN,
    project VARCHAR(50)
);
```

**Issues** (Runtime Predictions):
```sql
CREATE TABLE issues (
    id SERIAL PRIMARY KEY,
    task_id TEXT UNIQUE,
    summary TEXT NOT NULL,
    description TEXT NOT NULL,
    label VARCHAR(20),
    prediction VARCHAR(20),
    confidence FLOAT,
    status TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Labeled Issues** (User Contributions):
```sql
CREATE TABLE labeled_issues (
    id SERIAL PRIMARY KEY,
    summary TEXT NOT NULL,
    description TEXT NOT NULL,
    label VARCHAR(20) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    source VARCHAR(50) DEFAULT 'user_submission',
    notes TEXT
);
```

---

## Model Development

### Architecture

**Base Model**: DistilBERT (distilbert-base-uncased)
- 66M parameters
- 6-layer transformer encoder
- 512 token context window
- Binary classification head (ADD vs non-ADD)

### Training Process

**Configuration**:
- Learning Rate: 2e-5
- Batch Size: 4
- Epochs: 4
- Max Sequence Length: 256
- Optimizer: AdamW with weight decay (0.01)
- Class Weighting: Balanced using sklearn

**Data Split**:
- Training: 70%
- Validation: 15%
- Test: 15%

**Run Training**:
```bash
# Standard training
python data/training/ppl-train.py

# CI mode (faster, for testing)
export CI_MODE=true
python data/training/ppl-train.py
```

### MLflow Integration

**Tracking Metrics**:
- Accuracy, F1 Score, Precision, Recall
- Training loss and validation loss
- Per-class performance metrics
- Model hyperparameters

**Model Registry**:
```python
# Register model
mlflow.pytorch.log_model(
    model,
    artifact_path='trained-model',
    registered_model_name='add_detection_model'
)

# Load for inference
model = mlflow.pytorch.load_model("models:/add_detection_model/1")
```

**Access MLflow UI**:
```bash
# http://localhost:5000
docker compose up -d mlflow
```

### Performance Metrics

Example metrics from validation set:
- **Accuracy**: 0.85+
- **F1 Score**: 0.82+
- **Precision**: 0.84+
- **Recall**: 0.80+

### Model Card

See [Model Card](reports/report-1/model-card.md) for detailed documentation including:
- Intended use cases
- Training data characteristics
- Performance metrics
- Limitations and biases
- Ethical considerations

---

## API Documentation

### Base URL
```
http://localhost:8080
```

### Authentication
Currently no authentication required (development mode).

### Endpoints

#### Health Check
```http
GET /
```

**Response**:
```json
{
  "status": "healthy",
  "message": "ADD Detection API is running",
  "version": "1.0.0"
}
```

#### Single Prediction
```http
POST /api/predictions
Content-Type: application/json

{
  "summary": "Migrate to microservices architecture",
  "description": "We need to break down the monolith into smaller services for better scalability..."
}
```

**Response** (202 Accepted):
```json
{
  "task_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "PENDING"
}
```

#### Check Prediction Status
```http
GET /api/predictions/{task_id}
```

**Response** (Success):
```json
{
  "task_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "SUCCESS",
  "result": {
    "label": "ADD",
    "probability": 0.94,
    "is_add": true,
    "types": {
      "existence": true,
      "executive": false,
      "property": false
    }
  }
}
```

#### Batch Prediction
```http
POST /api/predictions/batch
Content-Type: application/json

{
  "issues": [
    {
      "summary": "Fix login button color",
      "description": "Change button from green to blue"
    },
    {
      "summary": "Choose database technology",
      "description": "Decide between PostgreSQL and MongoDB..."
    }
  ]
}
```

**Response** (202 Accepted):
```json
{
  "task_ids": [
    "task-id-1",
    "task-id-2"
  ],
  "status": "PENDING"
}
```

#### Search Issues
```http
GET /api/issues/search?keyword=authentication&limit=50&offset=0
```

**Response**:
```json
{
  "results": [
    {
      "id": 1,
      "summary": "Implement OAuth2 authentication",
      "description": "Replace basic auth with OAuth2...",
      "label": "ADD",
      "created_at": "2026-01-20T10:30:00"
    }
  ],
  "total": 142,
  "limit": 50,
  "offset": 0,
  "keyword": "authentication"
}
```

#### Submit Labeled Data (Bonus)
```http
POST /api/issues/labeled
Content-Type: application/json

{
  "summary": "Refactor authentication module",
  "description": "Move from basic auth to JWT tokens...",
  "label": "ADD"
}
```

**Response** (201 Created):
```json
{
  "id": 15,
  "message": "Labeled issue submitted successfully",
  "summary": "Refactor authentication module",
  "label": "ADD",
  "created_at": "2026-01-25T14:22:00"
}
```

#### Statistics
```http
GET /api/stats
```

**Response**:
```json
{
  "total_issues": 3456,
  "total_labeled": 127,
  "api_version": "1.0.0"
}
```

### Interactive API Documentation

Access Swagger UI at: http://localhost:8080/docs
Access ReDoc at: http://localhost:8080/redoc

---

## Frontend Interface

### Features

1. **Single Prediction Tab**
   - Form for summary and description input
   - Real-time status updates
   - Confidence score visualization
   - Decision type breakdown

2. **Batch Processing Tab**
   - Dynamic form with add/remove issue functionality
   - Parallel processing of multiple issues
   - Progress tracking
   - Individual result cards

3. **Search Database Tab**
   - Keyword-based search
   - Pagination support
   - Highlighted search terms
   - Quick example searches

4. **Contribute Data Tab**
   - Submit labeled examples
   - Contribute to model improvement
   - Automatic retraining trigger (every N submissions)

### Development
```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm start

# Build for production
npm run build

# Run tests
npm test
```

### Configuration

Frontend communicates with API via proxy configuration:
```nginx
# frontend/nginx.conf
location /api/ {
    proxy_pass http://app-api:8080/api/;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
}
```

---

## CI/CD Pipeline

### Pipeline Stages
```yaml
stages:
  - build        # Build Docker images
  - setup        # Infrastructure setup
  - update       # Data updates
  - lint         # Code quality checks
  - test         # Automated testing
  - training     # Model retraining
  - deploy       # Service deployment
```

### Key Jobs

**1. Build App Image**
```yaml
build_app:
  stage: build
  script:
    - docker build -t $CI_REGISTRY_IMAGE:app-latest .
    - docker push $CI_REGISTRY_IMAGE:app-latest
  rules:
    - changes:
        - backend/api/**
        - backend/inference/**
```

**2. Setup Infrastructure**
```yaml
setup_infra:
  stage: setup
  script:
    - docker compose down
    - docker compose up -d
```

**3. Lint Code**
```yaml
lint_code:
  stage: lint
  script:
    - pylint backend/api backend/inference --fail-under=8.0
  rules:
    - if: '$CI_COMMIT_BRANCH=="develop"'
```

**4. Run Tests**
```yaml
run_tests:
  stage: test
  script:
    - pytest tests --maxfail=1 --disable-warnings
```

**5. Train Model**
```yaml
train_model:
  stage: training
  script:
    - python data/training/ppl-train.py
  rules:
    - if: '$CI_PIPELINE_SOURCE == "trigger"'
```

**6. Deploy API**
```yaml
deploy_api:
  stage: deploy
  script:
    - docker compose up -d --no-deps --build app-api
  rules:
    - changes:
        - backend/api/**
```

### Triggering Retraining

The system can automatically trigger model retraining when new labeled data is submitted:
```python
# backend/api/app.py
def trigger_gitlab_training_pipeline():
    url = f"https://gitlab.com/api/v4/projects/{project_id}/trigger/pipeline"
    payload = {
        "token": trigger_token,
        "ref": "main",
        "variables[RETRAIN_REASON]": "new_labeled_data"
    }
    requests.post(url, data=payload)
```

### Required Environment Variables

Set in GitLab CI/CD Settings → Variables:
- `CI_REGISTRY_USER`: GitLab registry username
- `CI_REGISTRY_PASSWORD`: GitLab registry password
- `GITLAB_TRIGGER_TOKEN`: Pipeline trigger token
- `GITLAB_PROJECT_ID`: GitLab project ID
- `MLFLOW_MODEL_NAME`: Model name in registry

---

## Monitoring & Logging

### Prometheus Metrics

**Exposed Metrics**:
- HTTP request duration
- Request count by endpoint
- Response status codes
- Active connections
- Model inference time

**Configuration**:
```yaml
# prometheus/prometheus.yml
scrape_configs:
  - job_name: 'app-api'
    static_configs:
      - targets: ['app-api:8080']
  
  - job_name: 'celery-worker'
    static_configs:
      - targets: ['celery-worker:8080']
```

### Grafana Dashboards

Access at: http://localhost:3000 (admin/admin)

**Pre-configured Datasources**:
- Prometheus (metrics)
- Loki (logs)

**Key Dashboards**:
1. **API Performance**
   - Request rate
   - Error rate
   - Latency percentiles
   - Endpoint breakdown

2. **Model Performance**
   - Inference time
   - Prediction distribution
   - Confidence scores
   - Task queue depth

3. **System Health**
   - CPU/Memory usage
   - Database connections
   - Redis queue size
   - Container status

### Loki Logs

**Log Aggregation**:
```yaml
# docker-compose.yml
logging:
  driver: "json-file"
  options:
    tag: "{{.Name}}"
```

**Query Examples**:
```logql
# All API errors
{container_name="app-api"} |= "ERROR"

# Celery task failures
{container_name="celery-worker"} |= "FAILURE"

# Specific endpoint logs
{container_name="app-api"} |= "/api/predictions"
```

### Application Logging
```python
# backend/inference/tasks.py
import logging

logger = logging.getLogger(__name__)
logger.info(f"Task success: task_id={task_id} duration={dur:.3f}s")
logger.error(f"Task failure: task_id={task_id} error={err_msg}")
```

---

### CI Integration

Tests run automatically on every push:
```yaml
# .gitlab-ci.yml
run_tests:
  stage: test
  script:
    - pytest tests --maxfail=1 --disable-warnings
```

---

## Security

### Secrets Management

**Environment Variables**:
```bash
# .env (not committed)
GITLAB_TRIGGER_TOKEN=<secret>
GITLAB_PROJECT_ID=<id>
MLFLOW_MODEL_NAME=add_detection_model
```

**Docker Compose**:
```yaml
environment:
  - POSTGRES_URL=${POSTGRES_URL}
  - REDIS_URL=${REDIS_URL}
  - MLFLOW_TRACKING_URI=${MLFLOW_TRACKING_URI}
```

**GitLab CI/CD Variables**:
- Set in: Settings → CI/CD → Variables
- Marked as "Masked" and "Protected"
- Never logged in pipeline output

### Database Security

**PostgreSQL**:
- Password-protected access
- Non-default passwords in production
- Network isolation via Docker networks

**MinIO (S3 Storage)**:
- Service account with limited permissions
- Bucket-specific access policies
- Separate credentials for MLflow

### API Security

**Current Implementation** (Development):
- No authentication (development only)
- CORS enabled for localhost

**Production Recommendations**:
- Add JWT/OAuth2 authentication
- Rate limiting with Redis
- HTTPS only
- API key management
- Input validation and sanitization

### Network Security

**Docker Networks**:
```yaml
networks:
  assignment:
    driver: bridge
```

All services isolated in private network, only exposed ports accessible.

---
