import traceback
from app.core import SessionLocal
from app.models.user_model import User
from app.auth.service import hash_password

db = SessionLocal()
try:
    u = User(
        email='test3@example.com',
        password=hash_password('pass123'),
        username='test',
        is_active=True,
        created_at='2026-06-02',
        updated_at='2026-06-02'
    )
    db.add(u)
    db.commit()
    print('done', u.id)
except Exception:
    traceback.print_exc()
finally:
    db.close()
