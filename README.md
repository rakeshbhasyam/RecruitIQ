# RecruitIQ - AI-Powered Recruitment System

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.117+-green.svg)](https://fastapi.tiangolo.com)
[![MongoDB](https://img.shields.io/badge/MongoDB-7.0+-green.svg)](https://mongodb.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.6+-orange.svg)](https://langchain-ai.github.io/langgraph/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 🚀 Overview

RecruitIQ is an intelligent recruitment system that leverages AI agents to automate and enhance the candidate evaluation process. Built with FastAPI, MongoDB, and LangGraph, it provides a comprehensive solution for resume parsing, candidate matching, interview generation, and scoring.

## ✨ Key Features

- **🤖 AI-Powered Resume Parsing**: Automatically extracts skills, experience, and education from resumes
- **🎯 Intelligent Candidate Matching**: Uses semantic similarity and rule-based scoring to match candidates with job requirements
- **💬 Dynamic Interview Generation**: Creates personalized interview questions based on job descriptions and candidate profiles
- **📊 Comprehensive Scoring System**: Combines resume matching and interview performance for final candidate evaluation
- **🔍 Full Audit Trail**: Complete logging of all agent activities for compliance and debugging
- **⚡ Agent-Based Architecture**: Modular design with specialized agents for each recruitment task

## 🏗️ Architecture

The system uses a multi-agent architecture orchestrated by LangGraph:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Resume         │    │  Resume         │    │  Resume         │
│  Ingestion      │───▶│  Parser         │───▶│  Matcher        │
│  Agent          │    │  Agent          │    │  Agent          │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                       │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Final          │◀───│  Interview      │◀───│  Scoring        │
│  Scoring        │    │  Agent          │    │  Agent          │
│  Agent          │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🛠️ Technology Stack

- **Backend**: FastAPI, Python 3.11+
- **Database**: MongoDB 7.0+
- **AI/ML**: Google Gemini API, LangChain, LangGraph

## 📋 Prerequisites

- Python 3.11 or higher
- Google Gemini API key
- MongoDB (local or cloud instance)

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/recruitiq.git
cd recruitiq
```

### 2. Environment Setup

Create a `.env` file in the root directory:

```env
# Google Gemini API Key
GEMINI_API_KEY=your_gemini_api_key_here

# Database Configuration
DATABASE_URL=mongodb://localhost:27017/recruitiq
DATABASE_NAME=recruitiq

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=true
```

### 3. Setup and Run

```bash
# Create virtual environment
python -m venv myvenv
source myvenv/bin/activate  # On Windows: myvenv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start MongoDB (if running locally)
# Make sure MongoDB is running on localhost:27017

# Start the application
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## 📚 API Documentation

Once the application is running, you can access:

- **Interactive API Docs**: http://localhost:8000/docs
- **ReDoc Documentation**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

### Key Endpoints

- `POST /jobs/` - Create a new job posting
- `POST /candidates/` - Upload candidate resume
- `GET /candidates/{candidate_id}/process` - Process candidate through the pipeline
- `POST /interviews/generate` - Generate interview questions
- `POST /interviews/evaluate` - Evaluate interview responses
- `GET /scoring/{candidate_id}` - Get candidate scoring results
- `GET /audit/{trace_id}` - Get audit logs for a specific trace

## 🔧 Configuration

### Agent Configuration

The system uses several specialized agents:

- **Resume Ingestion Agent**: Handles file uploads and text extraction
- **Resume Parser Agent**: Extracts structured data from resumes
- **Resume Matcher Agent**: Matches candidates with job requirements
- **Interview Agent**: Generates and evaluates interview questions
- **Final Scoring Agent**: Combines all scores for final evaluation

### Database Schema

The system uses MongoDB with the following collections:

- `jobs` - Job postings and requirements
- `candidates` - Candidate information and parsed resumes
- `scores` - Scoring results and breakdowns
- `audit_logs` - Complete audit trail of agent activities

## 🧪 Testing

```bash
# Run tests (when test suite is implemented)
pytest

# Run with coverage
pytest --cov=app
```

## 📊 Monitoring and Logging

The system provides comprehensive logging and monitoring:

- **Audit Logs**: Every agent action is logged with trace IDs
- **Error Tracking**: Detailed error logging with context
- **Performance Metrics**: Response times and success rates
- **Health Checks**: System health monitoring endpoints


## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🗺️ Roadmap

- [ ] **MVP 2**: Human-in-the-loop workflows
- [ ] **Video Interview Support**: Integration with video conferencing APIs
- [ ] **Advanced Analytics**: Dashboard with recruitment metrics
- [ ] **Multi-language Support**: Resume parsing in multiple languages
- [ ] **Integration APIs**: Connect with popular ATS systems
- [ ] **Mobile App**: React Native mobile application

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) for the excellent web framework
- [LangChain](https://langchain.com/) for AI agent orchestration
- [Google Gemini](https://ai.google.dev/) for powerful AI capabilities
- [MongoDB](https://mongodb.com/) for flexible data storage

---

**Made with ❤️ by the RecruitIQ Team**

