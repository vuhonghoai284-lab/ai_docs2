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
- **Backend**: FastAPI + Python 3.11 + SQLite + Redis 7
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
- Python 3.8+
- Node.js 14+
- Docker and Docker Compose installed
- AI API credentials (obtained from AI team)

### Quick Start
```bash
# For Windows users
start.bat

# For Linux/Mac users
chmod +x start.sh
./start.sh
```

### Manual Setup
#### Backend Setup
```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows: venv\Scripts\activate
# Linux/Mac: source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start backend service
python main.py
```

#### Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Start frontend service
npm run dev
```

## Common Commands

### Development Commands
```bash
# Start backend server
cd backend && python main.py

# Start frontend development server
cd frontend && npm run dev

# Run tests
cd backend && python -m pytest tests/

# Install backend dependencies
cd backend && pip install -r requirements.txt

# Install frontend dependencies
cd frontend && npm install
```

### Database Operations
```bash
# The system uses SQLite for development, no separate database setup required
# Database file is located at: ./data/app.db
```

### Testing
```bash
# Run backend tests
cd backend && python -m pytest tests/

# Run specific test file
cd backend && python -m pytest tests/test_api.py
```

## API Integration

### External AI Service Configuration
The system integrates with external AI services via API Gateway. Configure in `backend/config.yaml`:
```
ai_models:
  default_index: 0
  models:
    - label: "GPT-4o Mini (快速)"
      provider: "openai"
      config:
        api_key: "${OPENAI_API_KEY}"
        base_url: "https://api.openai.com/v1"
        model: "gpt-4o-mini"
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
- Files are stored locally in `./data/uploads/`
- Reports are generated in `./data/reports/`
- Ensure adequate disk space for file storage

### Database Operations
- SQLite stores all persistent data
- Redis handles caching, queues, and session management

### Security Considerations
- All API endpoints require authentication
- SSO integration for enterprise authentication
- File uploads limited to 10MB by default
- Supported formats: PDF, DOCX, Markdown, TXT only

### git 操作

- 本项目每次提交请先创建分支，提交本次更新至远端仓库，合入到main分支

### 任务处理

- 所有回答通过中文进行回复
- 任务创建的临时测试脚本统一放到tmp目录中，任务结束时请清理