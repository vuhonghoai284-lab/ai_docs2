# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an AI Document Testing System (AI资料自主测试系统) designed to evaluate documentation quality from a user's perspective, identify issues, and generate structured test reports.

## Architecture

### System Design Pattern
- **Frontend/Backend Separation**: React frontend + FastAPI backend
- **Monolithic Service with Modular Design**: Single deployable unit with clear module boundaries
- **External AI Service Integration**: AI models provided via external API gateway by specialized team

### Technology Stack
- **Frontend**: React 18 + TypeScript + Vite + Ant Design + Zustand + TanStack Query
- **Backend**: FastAPI + Python 3.11 + PostgreSQL 15 + Redis 7
- **AI Integration**: External AI API Gateway (通用AI API + 结构化AI API)
- **Deployment**: Docker + Docker Compose

### Key Modules
1. **User Authentication Module** (用户模块): SSO integration for user authentication
2. **Task Management Module** (任务模块): Handles document testing task lifecycle
3. **File Processing Module** (文件模块): Manages document uploads (PDF, Word, Markdown)
4. **AI Analysis Module** (AI分析模块): Integrates with external AI services for document analysis
5. **Report Generation Module** (报告模块): Creates and exports test reports
6. **System Management Module** (系统模块): Health checks and monitoring

## Development Setup

### Prerequisites
- Docker and Docker Compose installed
- AI API credentials (obtained from AI team)
- PostgreSQL 15 and Redis 7 (via Docker)

### Quick Start
```bash
# Set up environment variables
cp .env.example .env
# Edit .env and configure AI_API_KEY and other settings

# Deploy with Docker Compose
docker-compose up -d

# Initialize database
docker-compose exec backend python -m alembic upgrade head
```

### Common Commands
```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# View logs
docker-compose logs -f backend

# Run database migrations
docker-compose exec backend python -m alembic upgrade head

# Access API documentation
# Navigate to: http://localhost:8080/docs
```

## API Integration

### External AI Service Configuration
The system integrates with external AI services via API Gateway. Configure in `.env`:
```
AI_API_GATEWAY_URL=http://ai-model-gateway/api/v1
AI_API_KEY=your-ai-api-key
```

### Service Selection Strategy
- **Structured API**: Used for document analysis and quality checking tasks
- **General API**: Used for general text processing and long content (>8000 chars)

## Task Processing Workflow

### Static Analysis Workflow (静态检测)
1. **File Parsing**: Extract text from PDF/Word/Markdown files
2. **Text Structuring**: Split content into chunks (default 8000 chars) and extract structure
3. **Quality Analysis**: Analyze grammar, logic, completeness via AI models
4. **Result Validation**: Validate JSON output structure and retry if needed
5. **Report Generation**: Generate structured reports with identified issues

### Dynamic Analysis (动态检测)
Planned feature using MCP+Agent for operational validation (not yet implemented in MVP)

## Data Models

### Core Entities
- **Users**: User authentication and profile data
- **Tasks**: Document testing tasks with status tracking
- **Files**: Uploaded document metadata and storage paths
- **Analysis Results**: AI analysis outputs with confidence scores
- **Issues**: Identified documentation problems
- **User Feedback**: User responses to identified issues (accept/reject/comment)
- **Reports**: Generated test reports

## Important Notes

### AI Service Dependencies
- The system relies on external AI API services maintained by a specialized team
- No local AI model deployment required
- Ensure stable network connection to AI gateway
- Monitor API rate limits and quotas

### File Storage
- Files are stored locally in `./data/files/`
- Reports are generated in `./data/reports/`
- Ensure adequate disk space for file storage

### Database Operations
- PostgreSQL stores all persistent data
- Redis handles caching, queues, and session management
- Database migrations managed via Alembic

### Security Considerations
- All API endpoints require JWT authentication
- SSO integration for enterprise authentication
- File uploads limited to 50MB by default
- Supported formats: PDF, DOCX, Markdown only