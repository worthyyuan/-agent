import asyncio
import sys

from app.agents.experts import review_security

sys.stdout.reconfigure(encoding="utf-8", errors="replace")


async def main():
    code = (
        "1|import sqlite3\n"
        "2|user_id = request.args.get('id')\n"
        "3|query = \"SELECT * FROM users WHERE id = \" + user_id\n"
        "4|cursor.execute(query)\n"
    )
    findings = await review_security(code)
    print("=== review_security 返回的 findings ===")
    for f in findings:
        print(f.model_dump())


asyncio.run(main())
