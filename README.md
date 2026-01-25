# ADD Detection System

**Machine Learning Systems Deployment and Optimizations**  

---

## 📋 Table of Contents

- Overview  
- Features  
- System Architecture  
- Technology Stack  
- Getting Started  
- Project Structure  
- Data Management  
- Model Development  
- API Documentation  
- Frontend Interface  
- CI/CD Pipeline  
- Monitoring & Logging  
- Testing  
- Security  
- Contributing  
- License  

---

## Overview

This system addresses the challenge of identifying **Architectural Design Decisions (ADDs)** in software development issues. ADDs represent critical knowledge about *why* a system is designed a certain way, but this information is often scattered across issue tracking systems and rarely explicitly documented.

Our ML-powered solution automatically classifies issues to determine if they contain architectural decisions, helping teams to:

- Document architectural knowledge automatically  
- Search and retrieve relevant architectural decisions  
- Understand design rationale from historical issues  
- Maintain architectural context as teams evolve  

---

## Problem Context

Traditional software architecture focuses on component structures and interactions, but modern architectural knowledge includes the *decisions* that led to those structures. Research shows that:

- ADDs are predominantly **tacit knowledge**  
- Dedicated documentation tools have **low adoption**  
- Issue tracking systems contain **implicit architectural knowledge**  
- Manual extraction is **time-consuming and incomplete**  

---

## Solution Approach

Our system uses a **fine-tuned DistilBERT model** trained on **6,200+ manually annotated issues** to classify three types of Architectural Design Decisions:

### 1. Existence Decisions
- Component creation and deletion  
- Definition of component interactions  

### 2. Executive Decisions
- Development process choices  
- Tooling and infrastructure decisions  

### 3. Property Decisions
- System-wide quality attributes  
- Performance, scalability, security, and maintainability concerns  

---
## Features

### Core Functionality

- **Single Issue Prediction**  
  Real-time ADD classification with confidence scores

- **Batch Processing**  
  Parallel classification of multiple issues

- **Keyword Search**  
  Full-text search across the issue database

- **Asynchronous Processing**  
  Non-blocking API with task queuing

- **Web Interface**  
  Responsive React-based frontend

---

### Production Features

- **MLflow Integration**  
  Model versioning and experiment tracking

- **Performance Monitoring**  
  Prometheus + Grafana dashboards

- **Centralized Logging**  
  Loki-based log aggregation

- **Security**  
  Environment-based secrets management

- **CI/CD Pipeline**  
  Automated testing, linting, and deployment

- **Docker Compose**  
  One-command deployment

- **Data Versioning**  
  DVC for reproducible datasets

---

### Bonus Features

- **Human-in-the-Loop**  
  User contribution system for labeled data

- **Automated Retraining**  
  GitLab pipeline triggers on new data

- **Model Cards**  
  Comprehensive model documentation

- **Data Validation**  
  Pandera-based quality checks

  ## System Architecture

### High-Level Architecture

add high level diagram here


### Component Interactions

- **Frontend → API**: HTTP/REST requests  
- **API → Celery**: Task submissions via Redis  
- **Celery → MLflow**: Model loading from registry  
- **API → PostgreSQL**: Data persistence and search  
- **All Services → Prometheus**: Metrics collection  
- **All Services → Loki**: Log aggregation  
- **Grafana**: Visualization of metrics and logs  

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

### ML / Data

- **Base Model**: DistilBERT (`distilbert-base-uncased`)  
- **Metrics**: TorchMetrics (Accuracy, F1, Precision, Recall)  
- **Class Balancing**: Weighted loss functions  
- **Data Source**: MongoDB (Jira repositories)  

---

## Getting Started

### Prerequisites

- Docker 20.10+ and Docker Compose 3.8+  
- Git 2.30+  
- DVC 2.0+ (for data management)  
- Python 3.11+ (for local development)  
- Node.js 20+ (for frontend development)  

---

### Quick Start (Production)

#### Clone the Repository

```bash
git clone <repository-url>
cd <repository-name>
```
#### Configure Environment Variables

```
cat > .env << EOF
GITLAB_TRIGGER_TOKEN=<your-token>
GITLAB_PROJECT_ID=<your-project-id>
GITLAB_REF=main
MLFLOW_MODEL_NAME=add_detection_model
EOF
```
Pull Data from DVC
```
dvc pull
```

#### Start All Services

```
docker compose up -d
```

#### Initialize Database
```
docker compose exec app-api python backend/api/init_db.py
```

#### Load Training Data

```
docker compose exec app-api python data/preprocessing/ppl-load_data.py
```





