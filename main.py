import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from database import db, create_document, get_documents
from schemas import (
    Child, Activity, Progress, Badge,
    RecommendationRequest, RecommendationResponse, ReportFilter
)

app = FastAPI(title="Gamified Early Digital Literacy API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- Utilities ----------

def collection(name: str):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not connected")
    return db[name]


def ensure_seed_data():
    # Seed activities if empty
    act_coll = collection("activity")
    if act_coll.count_documents({}) == 0:
        activities: List[dict] = [
            # Keamanan internet
            {"title": "Pilih Kata Sandi Kuat", "topic": "keamanan_internet", "kind": "quiz", "difficulty": "easy", "est_duration": 5, "points": 10, "stars_reward": 1, "asset": "/assets/lock.png"},
            {"title": "Rahasia vs Boleh Dibagi", "topic": "keamanan_internet", "kind": "sorting", "difficulty": "medium", "est_duration": 6, "points": 15, "stars_reward": 2, "asset": "/assets/share.png"},
            {"title": "Tebak Phishing!", "topic": "keamanan_internet", "kind": "quiz", "difficulty": "hard", "est_duration": 7, "points": 20, "stars_reward": 3, "asset": "/assets/phish.png"},
            # Perangkat digital
            {"title": "Kenal Perangkat", "topic": "perangkat_digital", "kind": "memory", "difficulty": "easy", "est_duration": 5, "points": 10, "stars_reward": 1, "asset": "/assets/device.png"},
            {"title": "Pasang Aksesori", "topic": "perangkat_digital", "kind": "puzzle", "difficulty": "medium", "est_duration": 6, "points": 15, "stars_reward": 2, "asset": "/assets/plug.png"},
            {"title": "Perbaiki Jaringan", "topic": "perangkat_digital", "kind": "puzzle", "difficulty": "hard", "est_duration": 8, "points": 20, "stars_reward": 3, "asset": "/assets/wifi.png"},
            # Etika digital
            {"title": "Kata Ajaib Online", "topic": "etika_digital", "kind": "quiz", "difficulty": "easy", "est_duration": 5, "points": 10, "stars_reward": 1, "asset": "/assets/please.png"},
            {"title": "Komentar Baik vs Jahil", "topic": "etika_digital", "kind": "sorting", "difficulty": "medium", "est_duration": 6, "points": 15, "stars_reward": 2, "asset": "/assets/comment.png"},
            {"title": "Jadi Penolong Online", "topic": "etika_digital", "kind": "video", "difficulty": "hard", "est_duration": 7, "points": 20, "stars_reward": 3, "asset": "/assets/help.png"},
            # Berpikir kritis
            {"title": "Cari Perbedaan", "topic": "berpikir_kritis", "kind": "puzzle", "difficulty": "easy", "est_duration": 5, "points": 10, "stars_reward": 1, "asset": "/assets/spot.png"},
            {"title": "Fakta atau Opini?", "topic": "berpikir_kritis", "kind": "quiz", "difficulty": "medium", "est_duration": 6, "points": 15, "stars_reward": 2, "asset": "/assets/fact.png"},
            {"title": "Susun Bukti", "topic": "berpikir_kritis", "kind": "puzzle", "difficulty": "hard", "est_duration": 8, "points": 20, "stars_reward": 3, "asset": "/assets/proof.png"},
        ]
        for a in activities:
            create_document("activity", a)

    # Seed badges if empty
    badge_coll = collection("badge")
    if badge_coll.count_documents({}) == 0:
        badges: List[dict] = [
            {"code": "starter", "label": "Petualang Mungil", "description": "Mulai belajar!", "icon": "🌟"},
            {"code": "streak3", "label": "Rajin 3 Hari", "description": "Belajar 3 hari berturut-turut", "icon": "🔥"},
            {"code": "security", "label": "Penjaga Aman", "description": "Ahli keamanan internet", "icon": "🔒"},
            {"code": "critical", "label": "Detektif Kecil", "description": "Pintar berpikir kritis", "icon": "🕵️"},
        ]
        for b in badges:
            create_document("badge", b)


ensure_seed_data()


# ---------- Basic endpoints ----------

@app.get("/")
def read_root():
    return {"message": "Gamified Early Digital Literacy API running"}


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available" if db is None else "✅ Connected",
        "database_url": "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set",
        "database_name": "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set",
        "connection_status": "Connected" if db is not None else "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["collections"] = db.list_collection_names()[:10]
    except Exception as e:
        response["database"] = f"⚠️ Error: {str(e)[:80]}"
    return response


# ---------- Children ----------

class CreateChild(BaseModel):
    name: str
    age: int
    avatar: Optional[str] = None


@app.post("/children")
def create_child(payload: CreateChild):
    child = Child(name=payload.name, age=payload.age, avatar=payload.avatar)
    child_id = create_document("child", child)
    return {"id": child_id}


@app.get("/children")
def list_children():
    items = get_documents("child")
    # stringify _id
    for it in items:
        it["id"] = str(it.pop("_id"))
    return items


# ---------- Activities ----------

@app.get("/activities")
def list_activities(topic: Optional[str] = None, difficulty: Optional[str] = None, limit: int = 20):
    filt = {}
    if topic:
        filt["topic"] = topic
    if difficulty:
        filt["difficulty"] = difficulty
    items = get_documents("activity", filt, limit)
    for it in items:
        it["id"] = str(it.pop("_id"))
    return items


# ---------- Decision Tree Recommendation ----------

def decide_next_difficulty(last_accuracy: Optional[float], last_duration: Optional[int], last_difficulty: Optional[str]) -> str:
    # Simple interpretable decision tree
    # Root: last_accuracy present?
    if last_accuracy is None:
        return last_difficulty or "easy"
    # Node: performance buckets
    if last_accuracy >= 0.85:
        # fast/slow consideration
        if last_duration is not None and last_duration < 60:
            return "hard" if last_difficulty == "medium" else ("medium" if last_difficulty == "easy" else "hard")
        else:
            return "medium"
    elif 0.6 <= last_accuracy < 0.85:
        return last_difficulty or "medium"
    else:
        return "easy"


def suggest_topics(preferred: Optional[str]) -> List[str]:
    base = ["keamanan_internet", "perangkat_digital", "etika_digital", "berpikir_kritis"]
    if preferred and preferred in base:
        return [preferred] + [t for t in base if t != preferred]
    return base


@app.post("/recommend", response_model=RecommendationResponse)
def recommend(req: RecommendationRequest):
    # Fetch child to tailor XP/level logic (optional here)
    child_doc = collection("child").find_one({"_id": {"$exists": True}, "_id": __import__("bson").ObjectId(req.child_id)}) if req.child_id else None

    next_diff = decide_next_difficulty(req.last_accuracy, req.last_duration_sec, req.last_difficulty)
    topics = suggest_topics(req.preferred_topic)

    # Find up to 6 activities matching topics and difficulty
    acts = list(collection("activity").find({"topic": {"$in": topics}, "difficulty": next_diff}).limit(6))
    acts_out = []
    for a in acts:
        a["id"] = str(a.pop("_id"))
        acts_out.append(a)

    reasoning = (
        "Akurasi tinggi dan waktu cepat → naik tingkat" if (req.last_accuracy and req.last_accuracy >= 0.85 and (req.last_duration_sec or 999) < 60) else
        "Akurasi sedang → pertahankan tingkat saat ini" if (req.last_accuracy and 0.6 <= req.last_accuracy < 0.85) else
        "Akurasi rendah → turunkan tingkat untuk penguatan" if (req.last_accuracy and req.last_accuracy < 0.6) else
        "Tidak ada histori → mulai dari tingkat mudah"
    )

    return RecommendationResponse(
        next_difficulty=next_diff,
        reasoning=reasoning,
        suggested_topics=topics,
        activities=acts_out
    )


# ---------- Progress & Rewards ----------

class SubmitProgress(BaseModel):
    child_id: str
    activity_id: str
    accuracy: float
    duration_sec: int
    mistakes: int = 0


@app.post("/progress")
def submit_progress(p: SubmitProgress):
    # Save progress
    prog = Progress(
        child_id=p.child_id,
        activity_id=p.activity_id,
        accuracy=p.accuracy,
        duration_sec=p.duration_sec,
        mistakes=p.mistakes,
    )
    prog_id = create_document("progress", prog)

    # Update child XP/level and possible badges
    from bson import ObjectId
    ccol = collection("child")
    child = ccol.find_one({"_id": ObjectId(p.child_id)})
    if not child:
        raise HTTPException(status_code=404, detail="Child not found")

    xp_gain = 20 if p.accuracy >= 0.9 else 15 if p.accuracy >= 0.75 else 10
    stars_gain = 3 if p.accuracy >= 0.9 else 2 if p.accuracy >= 0.75 else 1

    new_xp = int(child.get("xp", 0)) + xp_gain
    new_stars = int(child.get("stars", 0)) + stars_gain
    new_level = int(child.get("level", 1))
    # Simple level up every 100 xp
    while new_xp >= 100:
        new_xp -= 100
        new_level += 1

    # Badge starter if first progress
    total_prog = collection("progress").count_documents({"child_id": p.child_id})
    badges = child.get("badges", [])
    if total_prog == 1 and "starter" not in badges:
        badges.append("starter")

    ccol.update_one({"_id": ObjectId(p.child_id)}, {"$set": {"xp": new_xp, "stars": new_stars, "level": new_level, "badges": badges}})

    return {"progress_id": prog_id, "xp": new_xp, "stars": new_stars, "level": new_level, "badges": badges}


# ---------- Reports for Parents/Teachers ----------

@app.post("/report")
def report(filter: ReportFilter):
    limit = filter.limit or 20
    items = get_documents("progress", {"child_id": filter.child_id}, limit)
    for it in items:
        it["id"] = str(it.pop("_id"))
    # Aggregate simple stats
    if len(items) > 0:
        avg_acc = sum(i.get("accuracy", 0) for i in items) / len(items)
        avg_time = sum(i.get("duration_sec", 0) for i in items) / len(items)
    else:
        avg_acc = 0
        avg_time = 0
    return {
        "items": items,
        "summary": {
            "total_sessions": len(items),
            "avg_accuracy": round(avg_acc, 2),
            "avg_duration_sec": round(avg_time),
        }
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)