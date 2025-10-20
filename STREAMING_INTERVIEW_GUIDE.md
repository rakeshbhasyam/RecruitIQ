# Streaming Interview System - Implementation Guide

## Overview

The RecruitIQ system has been enhanced with a **streaming interview process** that enables real-time, adaptive questioning. This replaces the previous batch-based interview system with a dynamic, context-aware approach.

## Key Features

### 🎯 **Adaptive Questioning**
- Questions are generated dynamically based on previous answers
- Each question builds upon the candidate's responses
- Context is maintained throughout the interview session
- Progressive difficulty adjustment based on candidate performance

### 🔄 **Real-time Flow**
- One question at a time (no more batch processing)
- Immediate evaluation of each answer
- Context-aware follow-up questions
- Session state management

### 📊 **Enhanced Evaluation**
- Individual answer scoring
- Real-time feedback generation
- Overall assessment with detailed insights
- Session-based scoring system

## Architecture Changes

### New Database Schema

#### Interview Sessions Collection
```python
{
    "_id": "session_id",
    "candidate_id": "candidate_123",
    "job_id": "job_456",
    "max_questions": 5,
    "interview_type": "technical",
    "status": "active",  # active, completed
    "current_question_index": 0,
    "questions_and_answers": [
        {
            "question": "What is your experience with Python?",
            "answer": "I have 5 years of experience...",
            "score": 0.85,
            "explanation": "Strong technical knowledge demonstrated",
            "timestamp": "2024-01-15T10:30:00Z"
        }
    ],
    "context": {
        "previous_topics": ["Python", "Web Development"],
        "difficulty_level": "intermediate"
    },
    "is_completed": false,
    "overall_score": null,
    "overall_assessment": null,
    "created_at": "2024-01-15T10:00:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
}
```

### New API Endpoints

#### 1. Start Interview Session
```http
POST /interviews/start
Content-Type: application/json

{
    "candidate_id": "candidate_123",
    "job_id": "job_456",
    "max_questions": 5,
    "interview_type": "technical"
}
```

**Response:**
```json
{
    "session_id": "session_123",
    "first_question": "Tell me about your experience with Python...",
    "question_index": 0,
    "is_complete": false,
    "context": {}
}
```

#### 2. Get Next Question
```http
POST /interviews/next_question
Content-Type: application/json

{
    "session_id": "session_123",
    "answer": "I have 5 years of experience with Python..."
}
```

**Response:**
```json
{
    "session_id": "session_123",
    "question": "Great! Can you walk me through how you would implement a REST API?",
    "question_index": 1,
    "is_complete": false,
    "context": {
        "previous_topics": ["Python", "Web Development"]
    }
}
```

#### 3. Get Session Details
```http
GET /interviews/session/{session_id}
```

#### 4. Get Candidate Sessions
```http
GET /interviews/candidate/{candidate_id}/sessions
```

## Implementation Details

### Interview Agent Enhancements

#### New Methods Added:

1. **`start_interview_session()`**
   - Creates a new interview session
   - Generates the first question
   - Initializes session context

2. **`get_next_question()`**
   - Processes the previous answer
   - Generates the next adaptive question
   - Updates session context
   - Handles interview completion

3. **`_generate_next_question()`**
   - Creates adaptive prompts based on previous Q&A
   - Uses context to generate relevant follow-ups
   - Implements progressive difficulty

4. **`_process_answer()`**
   - Evaluates individual answers
   - Updates session with Q&A pairs
   - Maintains conversation context

### Adaptive Prompting System

#### Question Generation Prompt
```python
def _create_adaptive_question_prompt(self, candidate, job, previous_qa):
    """Generate next question based on previous answers"""
    context_text = ""
    if previous_qa:
        context_text = "\n\nPrevious Questions and Answers:\n"
        for i, qa in enumerate(previous_qa, 1):
            context_text += f"{i}. Q: {qa['question']}\n   A: {qa['answer']}\n"
    
    return f"""You are an expert technical interviewer conducting an adaptive interview. 
    Generate the next question based on the candidate's previous answers.
    
    Job Details: {job_details}
    Candidate Profile: {candidate_profile}
    {context_text}
    
    Generate ONE follow-up question that:
    1. Builds on the candidate's previous answers
    2. Tests deeper technical knowledge
    3. Explores areas not yet covered
    4. Is appropriate for their experience level
    5. Relates to the job requirements
    """
```

#### Answer Evaluation Prompt
```python
def _create_single_answer_evaluation_prompt(self, question, answer, job, previous_qa):
    """Evaluate individual answers with context"""
    return f"""You are an expert technical interviewer evaluating a candidate's answer.
    
    Job Context: {job_context}
    {previous_qa_context}
    
    Current Question and Answer:
    Q: {question}
    A: {answer}
    
    Evaluate this answer and provide:
    1. A score from 0.0 to 1.0
    2. A brief explanation
    3. Key strengths demonstrated
    4. Areas for improvement
    """
```

## Usage Examples

### Python Client Example

```python
import requests
import json

# Start interview session
start_response = requests.post("http://localhost:8000/interviews/start", json={
    "candidate_id": "candidate_123",
    "job_id": "job_456",
    "max_questions": 5,
    "interview_type": "technical"
})

session_data = start_response.json()
session_id = session_data["session_id"]
current_question = session_data["first_question"]

print(f"Question 1: {current_question}")

# Candidate provides answer
candidate_answer = "I have 5 years of experience with Python..."

# Get next question
next_response = requests.post("http://localhost:8000/interviews/next_question", json={
    "session_id": session_id,
    "answer": candidate_answer
})

next_data = next_response.json()

if next_data["is_complete"]:
    print("Interview Complete!")
    print(f"Overall Score: {next_data['overall_score']}")
    print(f"Assessment: {next_data['overall_assessment']}")
else:
    print(f"Question 2: {next_data['question']}")
    # Continue with next answer...
```

### JavaScript/Frontend Example

```javascript
class StreamingInterview {
    constructor(candidateId, jobId) {
        this.candidateId = candidateId;
        this.jobId = jobId;
        this.sessionId = null;
        this.currentQuestionIndex = 0;
    }
    
    async startInterview() {
        const response = await fetch('/interviews/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                candidate_id: this.candidateId,
                job_id: this.jobId,
                max_questions: 5,
                interview_type: 'technical'
            })
        });
        
        const data = await response.json();
        this.sessionId = data.session_id;
        return data.first_question;
    }
    
    async submitAnswer(answer) {
        const response = await fetch('/interviews/next_question', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_id: this.sessionId,
                answer: answer
            })
        });
        
        return await response.json();
    }
}

// Usage
const interview = new StreamingInterview('candidate_123', 'job_456');
const firstQuestion = await interview.startInterview();
console.log(`Question: ${firstQuestion}`);

// After candidate answers
const nextData = await interview.submitAnswer("My experience with Python...");
if (nextData.is_complete) {
    console.log("Interview completed!");
} else {
    console.log(`Next question: ${nextData.question}`);
}
```

## Migration from Legacy System

### Backward Compatibility

The legacy batch interview system is still supported through the `/interviews/generate` and `/interviews/submit` endpoints. However, new implementations should use the streaming endpoints:

- **Legacy**: `/interviews/generate` → **New**: `/interviews/start`
- **Legacy**: `/interviews/submit` → **New**: `/interviews/next_question`

### Data Migration

Existing interview data can be migrated to the new session-based format:

```python
# Convert legacy interview data to session format
def migrate_legacy_interview(legacy_data):
    session_data = {
        "candidate_id": legacy_data["candidate_id"],
        "job_id": legacy_data["job_id"],
        "max_questions": len(legacy_data["questions"]),
        "interview_type": "technical",
        "status": "completed",
        "questions_and_answers": [
            {
                "question": qa["question"],
                "answer": qa["answer"],
                "score": legacy_data.get("scores", [0.5] * len(legacy_data["questions"]))[i],
                "explanation": "Migrated from legacy system"
            }
            for i, qa in enumerate(legacy_data["questions_and_answers"])
        ],
        "is_completed": True,
        "overall_score": legacy_data.get("overall_score", 0.5),
        "overall_assessment": legacy_data.get("assessment", "Migrated interview")
    }
    return session_data
```

## Benefits of Streaming Interviews

### 1. **Improved Candidate Experience**
- More natural conversation flow
- Adaptive difficulty based on responses
- Real-time feedback and context

### 2. **Better Assessment Quality**
- Deeper technical exploration
- Context-aware questioning
- More accurate evaluation

### 3. **Enhanced Analytics**
- Session-based tracking
- Individual answer analysis
- Progressive performance metrics

### 4. **Scalability**
- Real-time processing
- Reduced memory usage
- Better resource management

## Testing

Run the test script to see the streaming interview in action:

```bash
python test_streaming_interview.py
```

This demonstrates:
- Session creation
- Adaptive questioning
- Context management
- Interview completion

## Future Enhancements

### Planned Features:
1. **Multi-modal Support**: Voice and video integration
2. **Real-time Collaboration**: Multiple interviewers
3. **Advanced Analytics**: Performance insights and trends
4. **Custom Question Banks**: Role-specific question sets
5. **Integration APIs**: Third-party assessment tools

## Conclusion

The streaming interview system represents a significant advancement in automated interview technology, providing a more natural, adaptive, and effective assessment experience for both candidates and recruiters.
