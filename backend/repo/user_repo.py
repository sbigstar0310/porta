import aiosqlite
from models import User


class UserRepo:
    def __init__(self):
        pass

    async def get_user_info(self, user_id: int = 1) -> User | None:
        """DB에서 사용자 정보 조회"""
        try:
            async with aiosqlite.connect("porta.db") as db:
                cursor = await db.execute(
                    """
                    SELECT id, email,timezone, language, created_at, updated_at, last_login
                    FROM users WHERE id = ?
                    """,
                    (user_id,),
                )
                row = await cursor.fetchone()

                if row:
                    return User(
                        id=row[0],
                        email=row[1],
                        timezone=row[2],
                        language=row[3],
                        created_at=row[4],
                        updated_at=row[5],
                        last_login=row[6],
                    )
                return None
        except Exception as e:
            print(f"Error fetching user info: {e}")
            return None
