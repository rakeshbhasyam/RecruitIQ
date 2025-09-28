from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from typing import Optional
from .settings import settings
from app.models import JobModel, CandidateModel, ScoreModel, AuditModel

class Database:
    client: Optional[AsyncIOMotorClient] = None
    database: Optional[AsyncIOMotorDatabase] = None
    
    # Model instances
    jobs: Optional[JobModel] = None
    candidates: Optional[CandidateModel] = None
    scores: Optional[ScoreModel] = None
    audit_logs: Optional[AuditModel] = None

# Global database instance
db = Database()

async def connect_to_mongo():
    """Create database connection"""
    try:
        db.client = AsyncIOMotorClient(settings.mongodb_url, serverSelectionTimeoutMS=5000)
        db.database = db.client[settings.database_name]
        
        # Test the connection
        await db.client.admin.command('ping')
        
        # Initialize model instances with collections
        db.jobs = JobModel(db.database.jobs)
        db.candidates = CandidateModel(db.database.candidates)
        db.scores = ScoreModel(db.database.scores)
        db.audit_logs = AuditModel(db.database.audit_logs)
        
        # Create indexes for better performance
        await create_indexes()
        print(f"Connected to MongoDB database: {settings.database_name}")
        
    except Exception as e:
        print(f"Failed to connect to MongoDB: {e}")
        print("Using in-memory mock database for demo purposes...")
        # Initialize mock database implementations
        from app.models.mock_database import MockJobModel, MockCandidateModel, MockScoreModel, MockAuditModel
        db.jobs = MockJobModel()
        db.candidates = MockCandidateModel()
        db.scores = MockScoreModel()
        db.audit_logs = MockAuditModel()

async def close_mongo_connection():
    """Close database connection"""
    if db.client:
        db.client.close()
        print("Disconnected from MongoDB")

async def create_indexes():
    """Create database indexes for optimization"""
    try:
        # Job indexes
        await db.database.jobs.create_index("status")
        await db.database.jobs.create_index("created_at")
        
        # Candidate indexes
        await db.database.candidates.create_index("job_id")
        await db.database.candidates.create_index("status")
        await db.database.candidates.create_index("email")
        
        # Score indexes
        await db.database.scores.create_index("candidate_id")
        await db.database.scores.create_index("job_id")
        await db.database.scores.create_index("final_score")
        
        # Audit log indexes
        await db.database.audit_logs.create_index("trace_id")
        await db.database.audit_logs.create_index("agent")
        await db.database.audit_logs.create_index("job_id")
        await db.database.audit_logs.create_index("candidate_id")
        await db.database.audit_logs.create_index("timestamp")
        
        print("Database indexes created successfully")
    except Exception as e:
        print(f"Error creating indexes: {e}")