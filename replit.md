# Overview

This is an AI-powered recruitment system that uses a multi-agent workflow to automate the candidate evaluation process. The system allows recruiters to post job descriptions and automatically scores candidates based on resume analysis and AI-generated interviews. It follows an agentic architecture where specialized AI agents handle different stages of the recruitment pipeline: resume ingestion, parsing, job matching, interview generation, and final scoring.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Backend Framework
**FastAPI with Python**: The core API is built using FastAPI, providing async request handling and automatic API documentation. The application uses lifespan context managers for proper database connection management during startup and shutdown.

## Database Layer
**MongoDB with Motor**: Uses MongoDB as the primary database with Motor (async MongoDB driver) for non-blocking database operations. The system includes a fallback mock database implementation for development when MongoDB is unavailable. Collections include jobs, candidates, scores, and audit logs for comprehensive tracking.

## Multi-Agent Architecture
**Specialized AI Agents**: The system implements a chain of specialized agents using Google's Gemini AI model:
- **ResumeIngestionAgent**: Extracts text from PDF/DOCX files
- **ResumeParserAgent**: Structures resume data using AI parsing
- **ResumeMatcherAgent**: Scores candidates against job requirements
- **InterviewAgent**: Generates and evaluates interview questions
- **FinalScoringAgent**: Calculates composite scores using weighted criteria

## Data Models
**Pydantic Schemas**: Strong typing and validation using Pydantic models for all data structures including jobs, candidates, scores, and audit logs. Each model includes both create and response variants with proper field validation.

## Workflow Orchestration
**WorkflowService**: Coordinates the multi-agent pipeline ensuring proper sequencing and error handling. Uses trace IDs for end-to-end request tracking and comprehensive audit logging.

## API Structure
**RESTful Endpoints**: Organized into logical controllers (jobs, candidates, interviews, scoring) with proper HTTP status codes and error handling. Includes health checks and comprehensive API documentation.

## File Processing
**Multi-format Support**: Handles PDF and Word document resume uploads with temporary file management and automatic cleanup on errors.

## Audit and Tracing
**Comprehensive Logging**: Every agent action is logged with trace IDs, enabling full request lifecycle tracking and debugging capabilities.

# External Dependencies

## AI Services
- **Google Gemini AI**: Primary AI model (gemini-2.5-flash) for all natural language processing tasks including resume parsing, job matching, and interview generation
- **Google GenAI SDK**: Latest SDK for interacting with Gemini models

## Database
- **MongoDB**: Primary data storage for all application data
- **Motor**: Async MongoDB driver for Python

## File Processing
- **PyPDF2**: PDF text extraction from resume files
- **python-docx**: Word document processing for resume analysis

## Web Framework
- **FastAPI**: Main web framework with async support
- **Pydantic**: Data validation and serialization
- **CORS Middleware**: Cross-origin request handling for frontend integration

## Development Tools
- **aiofiles**: Async file operations
- **python-multipart**: File upload handling
- **uvicorn**: ASGI server for running the FastAPI application