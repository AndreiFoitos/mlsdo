# Report 3 for Task 3

Names:

- Andrei Foitoș (S5233836)
- Andrei-George Iclodean (S6480039)
- Yuwen Zhou (S5521351)

# Work Distribution and Collaboration

| Member | Time Spent (est.) | Topic | Action |
|--------|------------------|-------|--------|
| Andrei Foitos | ~20 hours | Observability & Monitoring | Configured Grafana services, security settings, root URLs, cookies, CSRF protection, embedding, datasources, and Docker Compose deployment |
| Andrei Foitos | ~30 hours | Code Quality & Testing | Refactored backend code for readability, improved consistency, added and refactored unit tests, parameterized tests, improved mocking |
| Andrei Foitos | ~20 hours | CI/CD Improvements | Added linting and testing stages, adjusted pylint thresholds, updated CI structure |
| Andrei Foitos | ~50 hours | Frontend | Initialized frontend, improved UI/UX, updated response formats |
| Andrei Foitos | ~10 hours | Documentation & Reports | Refactored README, added architecture descriptions, model cards, and reports |
| **Andrei Foitos – Total** | **~130 hours** |  |  |
| Andrei-George Iclodean | ~15 hours | Docker & Deployment | Refactored Dockerfiles, docker-compose services and networking |
| Andrei-George Iclodean | ~80 hours | CI/CD Pipeline & Infrastructure | Designed and iterated GitLab CI pipeline, added build/train/update/deploy stages, triggers, rules, SSH automation |
| Andrei-George Iclodean | ~45 hours | Backend & API | Implemented FastAPI endpoints, Celery tasks, inference logic, database handling, task status management |
| Andrei-George Iclodean | ~35–40 hours | Docker & Deployment | Created and refactored Dockerfiles, docker-compose services, networking, health checks |
| Andrei-George Iclodean | ~30 hours | MLOps & Training | Implemented training scripts, retraining triggers, MLflow integration, hyperparameter updates |
| Andrei-George Iclodean | ~20 hours | Data Engineering | CSV loading, PostgreSQL integration, DVC usage, data preprocessing pipelines |
| Andrei-George Iclodean | ~10–15 hours | Documentation & Reports | Refactored README, added architecture descriptions, model cards, and reports |
| **Andrei-George Iclodean – Total** | **~235–245 hours** |  |  |
| Yuwen Zhou | ~50 hours | Data & Preprocessing | Prepared datasets, implemented preprocessing scripts, managed DVC tracking |
| Yuwen Zhou | ~20 hours | CI/CD Support | Fixed CI time limits, modified update_data jobs |
| Yuwen Zhou | ~10 hours | Backend | Backend updates, cleanup, removal of unused files |
| Yuwen Zhou | ~10 hours | Testing | Executed tests on data pipelines, preprocessing scripts, and minor backend components |
| Yuwen Zhou | ~10 hours | Documentation & System Diagrams | Wrote documentation for datasets, preprocessing scripts, and generated system diagrams for project reports |
| **Yuwen Zhou – Total** | **~100 hours** |  |  |

## Agreed-Upon Collaboration Rules and Practices

Although no formal collaboration rules were defined at the start of the project, the team followed shared working practices that emerged during development.

- All work was managed through a shared Git repository with frequent, descriptive commits.
- Tasks were divided based on individual expertise, with clear ownership of components.
- Communication took place informally via messaging and meetings to coordinate changes and decisions.
- Code quality was maintained through refactoring, linting, and automated testing.
- CI/CD pipelines were incrementally developed to support building, testing, training, and deployment.
- Documentation and reports were updated continuously to reflect system changes.

These practices enabled effective collaboration and steady progress throughout the project.

# Use of GenAI

## Prompts

| Tool | Prompt | Integration |
|-----|--------|-------------|
| Claude | Edit the CSS file for the frontend UI layout, focusing on structure and readability rather than final design.” | Used only as an initial reference for frontend styling. The output was manually adapted before integration. No application logic was generated. |
| ChatGPT | “Based on these commits: **"full Git commit history"**, summarize the distribution of work per team member in a structured table.” | Used to support analysis and reporting of development effort. The output was reviewed and incorporated into Report 3. |
| Claude | “Analyze CI pipeline errors related to Docker and GitLab CI configuration.” | Used to assist in understanding error messages and possible causes. All fixes were implemented manually after independent verification. |
| Copilot | Text suggestions while writing commit messages. | Used for phrasing assistance only. All content was reviewed before use. |
| Claude | “Debug Grafana ‘origin not allowed’ errors while setting up a Prometheus dashboard. Suggest troubleshooting steps.” | Used as guidance to understand and fix Grafana origin issues. |

## Usefulness of GenAI

GenAI tools were used in a limited and supportive role during the project. Their primary value was in assisting with non-core tasks such as drafting frontend styling templates, summarizing development activity, improving commit message clarity, and interpreting CI/CD error messages. In these scenarios, GenAI helped reduce development time and supported clearer documentation.

GenAI was not used to generate core application logic, model implementation, or system architecture. In complex or project-specific tasks, the generated outputs were often too generic and required manual adjustment. Therefore, all GenAI suggestions were treated as advisory and were carefully reviewed before integration.

Overall, GenAI served as a supplementary aid rather than a primary development tool, with all critical design and implementation decisions made manually by the team.
