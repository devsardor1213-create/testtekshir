from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional
import sqlite3
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_FILE = "database.sqlite"

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL,
        name TEXT NOT NULL,
        surname TEXT,
        subject TEXT,
        group_id INTEGER,
        teacher_id INTEGER
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS groups (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        subject TEXT NOT NULL,
        teacher_id INTEGER NOT NULL
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS tests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        subject TEXT NOT NULL,
        level TEXT NOT NULL,
        group_id INTEGER NOT NULL,
        teacher_id INTEGER NOT NULL,
        question_count INTEGER NOT NULL,
        questions TEXT DEFAULT '[]',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    try:
        c.execute("ALTER TABLE tests ADD COLUMN questions TEXT DEFAULT '[]'")
    except sqlite3.OperationalError:
        pass
    
    c.execute('''CREATE TABLE IF NOT EXISTS results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        test_id INTEGER NOT NULL,
        student_id INTEGER NOT NULL,
        score INTEGER NOT NULL,
        percentage INTEGER NOT NULL,
        date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Check if admin exists
    c.execute("SELECT id FROM users WHERE username = 'admin'")
    if not c.fetchone():
        c.execute("INSERT INTO users (username, password, role, name) VALUES ('admin', '123', 'admin', 'Admin')")
    
    conn.commit()
    conn.close()

init_db()

class LoginModel(BaseModel):
    username: str
    password: str

class UserModel(BaseModel):
    id: Optional[int] = None
    username: str
    password: str
    role: str
    name: str
    surname: Optional[str] = ""
    subject: Optional[str] = ""
    groupId: Optional[int] = None
    teacherId: Optional[int] = None

class GroupModel(BaseModel):
    id: Optional[int] = None
    name: str
    subject: str
    teacherId: int

class TestModel(BaseModel):
    id: Optional[int] = None
    title: str
    subject: str
    level: str
    groupId: int
    teacherId: int
    questionCount: int
    questions: Optional[str] = "[]"
    createdAt: Optional[str] = None

class ResultModel(BaseModel):
    id: Optional[int] = None
    testId: int
    studentId: int
    score: int
    percentage: int
    date: Optional[str] = None

def row_to_user(row):
    return {
        "id": row["id"],
        "username": row["username"],
        "password": row["password"],
        "role": row["role"],
        "name": row["name"],
        "surname": row["surname"],
        "subject": row["subject"],
        "groupId": row["group_id"],
        "teacherId": row["teacher_id"]
    }

def row_to_group(row):
    return {
        "id": row["id"],
        "name": row["name"],
        "subject": row["subject"],
        "teacherId": row["teacher_id"]
    }

def row_to_test(row):
    return {
        "id": row["id"],
        "title": row["title"],
        "subject": row["subject"],
        "level": row["level"],
        "groupId": row["group_id"],
        "teacherId": row["teacher_id"],
        "questionCount": row["question_count"],
        "questions": row["questions"],
        "createdAt": row["created_at"]
    }

def row_to_result(row):
    return {
        "id": row["id"],
        "testId": row["test_id"],
        "studentId": row["student_id"],
        "score": row["score"],
        "percentage": row["percentage"],
        "date": row["date"]
    }

@app.post("/login")
def login(creds: LoginModel):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username = ? AND password = ?", (creds.username, creds.password))
    user = c.fetchone()
    conn.close()
    if user:
        return {"success": True, "user": row_to_user(user)}
    return {"success": False, "message": "Invalid credentials"}

@app.get("/users")
def get_users():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM users")
    users = [row_to_user(r) for r in c.fetchall()]
    conn.close()
    return users

@app.post("/users")
def add_user(user: UserModel):
    conn = get_db()
    c = conn.cursor()
    try:
        c.execute("""INSERT INTO users (username, password, role, name, surname, subject, group_id, teacher_id) 
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?)""", 
                  (user.username, user.password, user.role, user.name, user.surname, user.subject, user.groupId, user.teacherId))
        conn.commit()
        new_id = c.lastrowid
        conn.close()
        return {"success": True, "id": new_id}
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=400, detail="Bunday login (username) band! Iltimos, boshqa login kiriting.")

@app.put("/users/{user_id}")
def edit_user(user_id: int, user: UserModel):
    conn = get_db()
    c = conn.cursor()
    try:
        c.execute("""UPDATE users SET username=?, password=?, role=?, name=?, surname=?, subject=?, group_id=?, teacher_id=? 
                     WHERE id=?""", 
                  (user.username, user.password, user.role, user.name, user.surname, user.subject, user.groupId, user.teacherId, user_id))
        conn.commit()
        conn.close()
        return {"success": True}
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=400, detail="Bunday login (username) band! Iltimos, boshqa login kiriting.")

@app.delete("/users/{user_id}")
def delete_user(user_id: int):
    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM users WHERE id=?", (user_id,))
    conn.commit()
    conn.close()
    return {"success": True}

@app.get("/groups")
def get_groups():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM groups")
    groups = [row_to_group(r) for r in c.fetchall()]
    conn.close()
    return groups

@app.post("/groups")
def add_group(group: GroupModel):
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT INTO groups (name, subject, teacher_id) VALUES (?, ?, ?)", 
              (group.name, group.subject, group.teacherId))
    conn.commit()
    new_id = c.lastrowid
    conn.close()
    return {"success": True, "id": new_id}

@app.delete("/groups/{group_id}")
def delete_group(group_id: int):
    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM groups WHERE id=?", (group_id,))
    conn.commit()
    conn.close()
    return {"success": True}

@app.put("/groups/{group_id}")
def edit_group(group_id: int, group: GroupModel):
    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE groups SET name=?, subject=? WHERE id=?", (group.name, group.subject, group_id))
    conn.commit()
    conn.close()
    return {"success": True}

@app.get("/tests")
def get_tests():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM tests")
    tests = [row_to_test(r) for r in c.fetchall()]
    conn.close()
    return tests

@app.post("/tests")
def add_test(test: TestModel):
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT INTO tests (title, subject, level, group_id, teacher_id, question_count, questions) VALUES (?, ?, ?, ?, ?, ?, ?)", 
              (test.title, test.subject, test.level, test.groupId, test.teacherId, test.questionCount, test.questions))
    conn.commit()
    new_id = c.lastrowid
    conn.close()
    return {"success": True, "id": new_id}

@app.delete("/tests/{test_id}")
def delete_test(test_id: int):
    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM tests WHERE id=?", (test_id,))
    conn.commit()
    conn.close()
    return {"success": True}

@app.get("/results")
def get_results():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM results")
    results = [row_to_result(r) for r in c.fetchall()]
    conn.close()
    return results

@app.post("/results")
def add_result(res: ResultModel):
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT INTO results (test_id, student_id, score, percentage) VALUES (?, ?, ?, ?)", 
              (res.testId, res.studentId, res.score, res.percentage))
    conn.commit()
    new_id = c.lastrowid
    conn.close()
    return {"success": True, "id": new_id}



import os
app.mount("/", StaticFiles(directory=os.path.dirname(os.path.abspath(__file__)), html=True), name="static")
