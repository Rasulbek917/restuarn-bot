"""
Ishga tushirish: python run.py
(yoki: uvicorn app.main:app --host 0.0.0.0 --port 4000)
"""
import uvicorn

from app.config import settings

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.PORT, reload=False)
