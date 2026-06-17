import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv("backend/.env")
db_url = os.getenv("DATABASE_URL")

if not db_url:
    print("DATABASE_URL not found in .env")
    exit(1)

# SQLAlchemy psycopg URL fix if needed
if db_url.startswith("postgresql://"):
    db_url = db_url.replace("postgresql://", "postgresql+psycopg://", 1)

engine = create_engine(db_url)

with engine.connect() as conn:
    print("Migrating database...")
    try:
        conn.execute(text("ALTER TABLE threats ADD COLUMN target_department VARCHAR(100);"))
        conn.execute(text("ALTER TABLE threats ADD COLUMN target_role VARCHAR(100);"))
        conn.commit()
        print("✅ Columns added successfully.")
    except Exception as e:
        print(f"⚠️ Error or columns already exist: {e}")
