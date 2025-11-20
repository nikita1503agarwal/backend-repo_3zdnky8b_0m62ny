import os
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional, Type

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from database import create_document, get_documents, db
import schemas as app_schemas

app = FastAPI(title="Rabbitry Farm Management API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- Utility ----------

def collection_name(model_cls: Type[BaseModel]) -> str:
    return model_cls.__name__.lower()


def to_dict_list(docs: List[Dict[str, Any]]):
    out = []
    for d in docs:
        d = dict(d)
        if "_id" in d:
            d["_id"] = str(d["_id"])  # stringify ObjectId
        out.append(d)
    return out


def parse_date_safe(value: Optional[str]) -> Optional[date]:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except Exception:
        return None


# ---------- Health Check ----------

@app.get("/")
def read_root():
    return {"message": "Rabbitry backend is running"}


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set",
        "database_name": "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set",
        "connection_status": "Not Connected",
        "collections": [],
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["connection_status"] = "Connected"
            try:
                response["collections"] = db.list_collection_names()
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️ Connected but Error: {str(e)[:80]}"
        else:
            response["database"] = "⚠️ Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:80]}"
    return response


# ---------- Schema Endpoint ----------

@app.get("/schema")
def get_schema():
    """Expose Pydantic model schemas for tooling/validation"""
    result: Dict[str, Any] = {}
    for name in dir(app_schemas):
        attr = getattr(app_schemas, name)
        if isinstance(attr, type) and issubclass(attr, BaseModel) and attr is not BaseModel:
            try:
                result[name] = attr.model_json_schema()
            except Exception:
                # Fallback if schema generation fails
                result[name] = {"title": name}
    return result


# ---------- Core CRUD Endpoints ----------

# Rabbits
@app.post("/rabbits")
def create_rabbit(payload: app_schemas.Rabbit):
    rid = create_document(collection_name(app_schemas.Rabbit), payload)
    return {"id": rid}


@app.get("/rabbits")
def list_rabbits(tag: Optional[str] = None, sex: Optional[str] = None, status: Optional[str] = None, limit: Optional[int] = Query(None, ge=1, le=200)):
    filt: Dict[str, Any] = {}
    if tag:
        filt["tag"] = tag
    if sex:
        filt["sex"] = sex
    if status:
        filt["status"] = status
    docs = get_documents(collection_name(app_schemas.Rabbit), filt, limit)
    return to_dict_list(docs)


# Health Records
@app.post("/health")
def create_health_record(payload: app_schemas.HealthRecord):
    hid = create_document(collection_name(app_schemas.HealthRecord), payload)
    return {"id": hid}


@app.get("/health")
def list_health_records(rabbit_tag: Optional[str] = None, limit: Optional[int] = Query(None, ge=1, le=200)):
    filt: Dict[str, Any] = {}
    if rabbit_tag:
        filt["rabbit_tag"] = rabbit_tag
    docs = get_documents(collection_name(app_schemas.HealthRecord), filt, limit)
    return to_dict_list(docs)


# Breeding events
@app.post("/breedings")
def create_breeding(payload: app_schemas.Breeding):
    bid = create_document(collection_name(app_schemas.Breeding), payload)
    return {"id": bid}


@app.get("/breedings")
def list_breedings(doe_tag: Optional[str] = None, buck_tag: Optional[str] = None, outcome: Optional[str] = None, limit: Optional[int] = Query(None, ge=1, le=200)):
    filt: Dict[str, Any] = {}
    if doe_tag:
        filt["doe_tag"] = doe_tag
    if buck_tag:
        filt["buck_tag"] = buck_tag
    if outcome:
        filt["outcome"] = outcome
    docs = get_documents(collection_name(app_schemas.Breeding), filt, limit)
    return to_dict_list(docs)


# Litters
@app.post("/litters")
def create_litter(payload: app_schemas.Litter):
    lid = create_document(collection_name(app_schemas.Litter), payload)
    return {"id": lid}


@app.get("/litters")
def list_litters(doe_tag: Optional[str] = None, kindling_date: Optional[str] = None, limit: Optional[int] = Query(None, ge=1, le=200)):
    filt: Dict[str, Any] = {}
    if doe_tag:
        filt["doe_tag"] = doe_tag
    kd = parse_date_safe(kindling_date)
    if kd:
        filt["kindling_date"] = kd
    docs = get_documents(collection_name(app_schemas.Litter), filt, limit)
    return to_dict_list(docs)


# Medication schedules
@app.post("/medication")
def create_medication(payload: app_schemas.MedicationSchedule):
    mid = create_document(collection_name(app_schemas.MedicationSchedule), payload)
    return {"id": mid}


@app.get("/medication")
def list_medication(rabbit_tag: Optional[str] = None, active_only: bool = False, today: Optional[str] = None, limit: Optional[int] = Query(None, ge=1, le=200)):
    filt: Dict[str, Any] = {}
    if rabbit_tag:
        filt["rabbit_tag"] = rabbit_tag
    docs = get_documents(collection_name(app_schemas.MedicationSchedule), filt, limit)
    records = to_dict_list(docs)
    if active_only:
        today_date = parse_date_safe(today) or date.today()
        active = []
        for r in records:
            sd = date.fromisoformat(str(r.get("start_date"))) if r.get("start_date") else None
            ed = None
            if r.get("end_date"):
                try:
                    ed = date.fromisoformat(str(r.get("end_date")))
                except Exception:
                    ed = None
            if sd and sd <= today_date and (ed is None or today_date <= ed):
                active.append(r)
        return active
    return records


# Tasks
@app.post("/tasks")
def create_task(payload: app_schemas.Task):
    tid = create_document(collection_name(app_schemas.Task), payload)
    return {"id": tid}


@app.get("/tasks")
def list_tasks(status: Optional[str] = None, assigned_to: Optional[str] = None, limit: Optional[int] = Query(None, ge=1, le=200)):
    filt: Dict[str, Any] = {}
    if status:
        filt["status"] = status
    if assigned_to:
        filt["assigned_to"] = assigned_to
    docs = get_documents(collection_name(app_schemas.Task), filt, limit)
    return to_dict_list(docs)


# ---------- Agents ----------

# Breeding Planner Agent
@app.post("/agents/breeding/plan")
def breeding_plan(params: app_schemas.BreedingPlanInput):
    rabbits = to_dict_list(get_documents(collection_name(app_schemas.Rabbit)))

    def age_in_days(r: Dict[str, Any]) -> Optional[int]:
        dob = r.get("dob")
        if not dob:
            return None
        try:
            # DOB may already be a date or string
            if isinstance(dob, date):
                d = dob
            else:
                d = date.fromisoformat(str(dob))
            return (date.today() - d).days
        except Exception:
            return None

    does = [r for r in rabbits if r.get("sex") == "doe" and r.get("status", "active") == "active"]
    bucks = [r for r in rabbits if r.get("sex") == "buck" and r.get("status", "active") == "active"]

    # Index recent breedings to respect cooldown by doe
    breedings = to_dict_list(get_documents(collection_name(app_schemas.Breeding)))
    last_bred: Dict[str, date] = {}
    for b in breedings:
        doe = b.get("doe_tag")
        dt = b.get("date_bred")
        if doe and dt:
            try:
                d = dt if isinstance(dt, date) else date.fromisoformat(str(dt))
                if doe not in last_bred or d > last_bred[doe]:
                    last_bred[doe] = d
            except Exception:
                pass

    suggested_pairs: List[Dict[str, Any]] = []
    for doe in does:
        doe_age = age_in_days(doe)
        if doe_age is not None and doe_age < params.min_doe_age_days:
            continue
        # cooldown
        lb = last_bred.get(doe.get("tag"))
        if lb and (date.today() - lb).days < params.cooldown_days:
            continue
        # find compatible buck
        for buck in bucks:
            buck_age = age_in_days(buck)
            if buck_age is not None and buck_age < params.min_buck_age_days:
                continue
            # avoid pairing immediate relatives and same tag
            if buck.get("tag") == doe.get("tag"):
                continue
            if buck.get("tag") in {doe.get("sire_tag"), doe.get("dam_tag")}:
                continue
            if doe.get("tag") in {buck.get("sire_tag"), buck.get("dam_tag")}:
                continue
            exp_kindling = date.today() + timedelta(days=31)
            suggested_pairs.append({
                "doe_tag": doe.get("tag"),
                "buck_tag": buck.get("tag"),
                "reason": "Meets age and cooldown; not closely related",
                "expected_kindling": exp_kindling.isoformat(),
            })
            break  # one buck per doe in plan

    # Generate suggested tasks
    tasks = [
        {
            "title": f"Breed {p['doe_tag']} to {p['buck_tag']}",
            "due_date": date.today().isoformat(),
            "assigned_to": "breeding",
            "rabbit_tag": p["doe_tag"],
            "status": "todo",
            "notes": f"Expected kindling {p['expected_kindling']}",
        }
        for p in suggested_pairs
    ]

    return {"suggested_pairs": suggested_pairs, "tasks": tasks, "summary": {
        "eligible_does": len(does),
        "eligible_bucks": len(bucks),
        "suggested_count": len(suggested_pairs),
    }}


# Health/Doctor Agent - simple symptom checker
@app.post("/agents/health/check")
def symptom_check(payload: app_schemas.SymptomCheck):
    symptoms = {s.strip().lower() for s in payload.symptoms if s.strip()}

    rules = [
        {
            "match_any": {"diarrhea", "runny stool"},
            "condition": "Enteritis/Diarrhea",
            "severity": "medium",
            "actions": [
                "Isolate affected rabbit and ensure hydration",
                "Remove fresh greens; offer hay and water",
                "Consult vet for antidiarrheals if severe or persistent",
            ],
            "tips": ["Monitor stool consistency and appetite daily"],
        },
        {
            "match_any": {"head tilt", "nystagmus", "loss of balance"},
            "condition": "Possible E. cuniculi or inner ear infection",
            "severity": "high",
            "actions": [
                "Seek veterinary evaluation promptly",
                "Minimize stress and provide safe padded area",
            ],
            "tips": ["Record onset time and any trauma history"],
        },
        {
            "match_any": {"sneezing", "nasal discharge", "runny nose"},
            "condition": "Upper respiratory signs",
            "severity": "medium",
            "actions": [
                "Check environment (dust, ammonia, drafts)",
                "Consult vet; avoid penicillins orally in rabbits",
            ],
            "tips": ["Track temperature and breathing effort"],
        },
        {
            "match_any": {"not eating", "anorexia", "no feces", "bloat"},
            "condition": "GI stasis",
            "severity": "high",
            "actions": [
                "Urgent vet care if severe; encourage hydration",
                "Provide safe warmth and gentle tummy massage if trained",
            ],
            "tips": ["Log fecal output and weight every 12h"],
        },
        {
            "match_any": {"mites", "itching", "flaky skin", "crusty ears"},
            "condition": "Parasites (fur/ear mites)",
            "severity": "low",
            "actions": [
                "Topical ivermectin or selamectin per vet guidance",
                "Clean environment; treat in-contact rabbits",
            ],
            "tips": ["Recheck in 7-14 days"],
        },
    ]

    findings: List[Dict[str, Any]] = []
    for rule in rules:
        if symptoms & rule["match_any"]:
            findings.append({
                "condition": rule["condition"],
                "severity": rule["severity"],
                "immediate_actions": rule["actions"],
                "monitoring_tips": rule["tips"],
            })

    overall_severity = "low"
    if any(f["severity"] == "high" for f in findings):
        overall_severity = "high"
    elif any(f["severity"] == "medium" for f in findings):
        overall_severity = "medium"

    # Optional: attach recent health history
    history: List[Dict[str, Any]] = []
    if payload.rabbit_tag:
        hist_docs = get_documents(collection_name(app_schemas.HealthRecord), {"rabbit_tag": payload.rabbit_tag}, limit=10)
        history = to_dict_list(hist_docs)

    return {
        "rabbit_tag": payload.rabbit_tag,
        "reported_symptoms": list(symptoms),
        "probable_conditions": findings,
        "overall_severity": overall_severity,
        "history": history,
        "disclaimer": "This is guidance only and not a diagnosis. Consult a veterinarian.",
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
