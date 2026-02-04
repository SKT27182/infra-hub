Centralized Resource Management Platform for a Single VM
Overview

This project aims to build a centralized, service-oriented resource management platform for a single Oracle VM (16 GB RAM) that hosts multiple independent application projects.

Instead of running duplicate Docker containers for common infrastructure services inside each project, this platform will deploy shared core services once and expose them to all projects running on the VM. Each service will be managed centrally with full administrative control, observability, and interactive access.

The goal is to reduce memory usage, simplify service management, and standardize infrastructure usage across projects.

Problem Statement

Currently, multiple projects on the same VM run their own Docker containers for common services such as:

PostgreSQL

Redis

MinIO

MongoDB

Vector databases

Admin dashboards

This leads to:

Duplicate services consuming unnecessary RAM and disk

Complex port management

Harder debugging and monitoring

Fragmented admin access across projects

Operational overhead when restarting or upgrading services

Proposed Solution

Create a centralized infrastructure layer that runs shared services in Docker containers, exposed via fixed ports or internal networks, and used by all application projects on the VM.

Each service will be:

Deployed once

Fully admin-accessible

Independently restartable, stoppable, or removable

Observable and manageable from a single control plane

Initial Services Scope

The first phase will include the following services, each running in isolated Docker containers and exposed on dedicated ports:

Core Data & Storage Services

PostgreSQL

Redis

MongoDB

Qdrant (vector database)

MinIO (object storage)

Management & Admin Tools

pgAdmin (PostgreSQL management)

RedisInsight (Redis management)

MongoDB admin interface

Key Capabilities
1. Centralized Service Deployment

All shared services run in one place

Consistent versions across all projects

Controlled startup, shutdown, and restarts

2. Administrative Control Plane

A unified admin interface that allows:

Viewing running services

Starting, stopping, pausing, and restarting containers

Monitoring resource usage (CPU, RAM, disk)

Managing ports and service health

3. Deep Service Management

Each service should expose native administrative capabilities, for example:

PostgreSQL

View all databases

View tables inside a database

Inspect table schemas and data

Manage users and permissions

Redis

Inspect keys and namespaces

View memory usage

Execute Redis commands interactively

MongoDB

View databases and collections

Inspect documents

Manage indexes and users

MinIO

Manage buckets and objects

View storage usage

Access MinIO console

Qdrant

Manage collections

Inspect vectors and payloads

Monitor index and storage stats

4. Interactive Consoles

Each service should provide console-level access, such as:

SQL console for PostgreSQL

Redis CLI access

Mongo shell access

MinIO web console

Qdrant API explorer

This allows real-time interaction, debugging, and data inspection without entering containers manually.

Architecture Philosophy

Service-first architecture: services exist independently of applications

Single source of truth for infrastructure

Loose coupling: applications consume services via network endpoints

Docker-native: containers as the base abstraction

VM-optimized: designed specifically for a single powerful machine

Benefits

Lower overall memory and CPU usage

No duplicated infrastructure services

Faster project setup (reuse existing services)

Easier upgrades and maintenance

Centralized observability and control

Cleaner port and network management

Improved developer productivity

Security & Access Control (Future Scope)

To ensure safe multi-project usage, the platform should eventually support:

Service-level authentication and credentials

Role-based access control (admin vs read-only)

Network isolation between services and projects

Secrets management (passwords, tokens, keys)

Observability & Monitoring (Future Scope)

Planned enhancements include:

Service health checks

Logs aggregation

Resource usage dashboards

Alerts for failures or high resource usage

Extensibility

The platform should be designed to easily add new shared services, such as:

Message brokers (Kafka, RabbitMQ)

Search engines (OpenSearch, Elasticsearch)

Cache layers

Monitoring tools

CI/CD utilities

Final Goal

The ultimate goal is to transform a single VM into a mini internal cloud platform, offering shared, managed infrastructure services that multiple projects can reliably and efficiently consume—without the complexity of full Kubernetes or external cloud services.