import asyncio
from app.database import engine, Base
# You MUST import all your models here so SQLAlchemy knows they exist
# before it tries to create tables for them.
from app.models.user import User 
from app.models.prompt import prompts
from app.models.image import image
from app.models.social import Like , Collection , CollectionPrompt , Comment
# ... import other models as you build them

async def reset_database():
    print("⚠️  Warning: This will DROP ALL TABLES in the database!")
    confirm = input("Are you sure you want to proceed? (y/N): ")
    
    if confirm.lower() != 'y':
        print("Aborting database reset.")
        return

    print("Dropping all tables...")
    # We use engine.begin() for DDL operations (Data Definition Language)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        print("All tables dropped successfully.")

        print("Recreating tables from current models...")
        await conn.run_sync(Base.metadata.create_all)
        print("Database reset complete! 🚀")

if __name__ == "__main__":
    # Running the async function
    asyncio.run(reset_database())