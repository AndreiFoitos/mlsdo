# Report 2 for Task 2: Architecture

- Andrei Foitoș (S5233836)
- Andrei-George Iclodean (S6480039)
- Yuwen Zhou (S5521351)

# Executive Summary

This report presents the architecture and deployment pipeline for a machine learning system designed
to classify and process review data. The system implements a microservices architecture using Docker
containers, orchestrated through Docker Compose, with a comprehensive CI/CD pipeline managed by
GitLab CI/CD. The architecture supports asynchronous model inference, centralized model manage-
ment via MLflow, and comprehensive monitoring through Prometheus, Loki, and Grafana.

# System Architecture

To describe our ADD Detection System architecture at multiple levels of abstraction, we adopt the C4
model, which refines the system from its external context to its internal structure. It enables a clear
separation of concerns and supports reasoning about system responsibilities, deployment boundaries
and interactions between components.

We focus only on the first three levels of the C4 model. Level 4 focuses on code-level structures
such as classes and methods, which are highly implementation-specific. Since the objective of this
assignment is to reason about system architecture, deployment, asynchronous processing, and observ-
ability, Levels 1 to 3 already provide sufficient abstraction without introducing unnecessary coupling
to implementation details.

The system follows a microservices architecture pattern, implementing the C4 model for archi-
tectural documentation. The architecture is designed to support scalable machine learning inference
through asynchronous task processing, model versioning and experimentation via MLflow, data per-
sistence across PostgreSQL and MongoDB, a comprehensive observability through metrics, logs, and
dashboards, and containerized deployment for consistency across environments.