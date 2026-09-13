from app.core.database import SessionLocal
from app.models.user import User
from app.services.rag_service import ask_question

db = SessionLocal()

# Replace with your actual user_id (check /auth/me response for your id)
USER_ID = 7

answer = ask_question(db, USER_ID, "What was my total cholesterol level?")
print("Answer:")
print(answer)

db.close()