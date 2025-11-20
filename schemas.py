"""
Database Schemas for Rabbitry Farm Management

Each Pydantic model below represents a MongoDB collection. The collection
name is the lowercase of the class name (e.g., Rabbit -> "rabbit").

These schemas will be returned via the /schema endpoint for tooling and
validation. Use these models when inserting data into the database.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date

# Core entities
class Rabbit(BaseModel):
    tag: str = Field(..., description="Unique ear tag or identifier")
    name: Optional[str] = Field(None, description="Given name")
    sex: str = Field(..., pattern="^(doe|buck)$", description="Sex: doe or buck")
    breed: Optional[str] = Field(None, description="Breed or cross")
    color: Optional[str] = Field(None, description="Color/variety")
    dob: Optional[date] = Field(None, description="Date of birth")
    status: str = Field("active", description="active, sold, retired, deceased")
    sire_tag: Optional[str] = Field(None, description="Father tag if known")
    dam_tag: Optional[str] = Field(None, description="Mother tag if known")
    cage: Optional[str] = Field(None, description="Cage or location label")
    notes: Optional[str] = Field(None, description="Freeform notes")

class Breeding(BaseModel):
    doe_tag: str = Field(..., description="Doe ear tag")
    buck_tag: str = Field(..., description="Buck ear tag")
    date_bred: date = Field(..., description="Breeding date")
    expected_kindling: Optional[date] = Field(None, description="Expected kindling date")
    outcome: Optional[str] = Field(None, description="pending, kindled, missed")
    notes: Optional[str] = Field(None)

class Litter(BaseModel):
    doe_tag: str = Field(...)
    buck_tag: Optional[str] = Field(None)
    breeding_date: Optional[date] = Field(None)
    kindling_date: date = Field(...)
    total_born: int = Field(..., ge=0)
    born_alive: int = Field(..., ge=0)
    fostered_in: int = Field(0, ge=0)
    fostered_out: int = Field(0, ge=0)
    weaned: Optional[int] = Field(None, ge=0)
    notes: Optional[str] = Field(None)

class HealthRecord(BaseModel):
    rabbit_tag: str = Field(...)
    record_date: date = Field(...)
    condition: str = Field(..., description="Symptom or diagnosis")
    treatment: Optional[str] = Field(None)
    medication: Optional[str] = Field(None)
    dose: Optional[str] = Field(None)
    temp_c: Optional[float] = Field(None, ge=30, le=45)
    weight_kg: Optional[float] = Field(None, ge=0)
    vet: Optional[str] = Field(None)
    notes: Optional[str] = Field(None)

class MedicationSchedule(BaseModel):
    rabbit_tag: str = Field(...)
    med_name: str = Field(...)
    dose: str = Field(...)
    route: Optional[str] = Field(None, description="PO, SC, IM, etc.")
    start_date: date = Field(...)
    end_date: Optional[date] = Field(None)
    frequency: Optional[str] = Field(None, description="e.g., BID, daily")
    notes: Optional[str] = Field(None)

class Task(BaseModel):
    title: str = Field(...)
    due_date: Optional[date] = Field(None)
    assigned_to: Optional[str] = Field(None, description="agent: breeding/health/feeding/cleaning")
    rabbit_tag: Optional[str] = Field(None)
    status: str = Field("todo", description="todo, in_progress, done")
    notes: Optional[str] = Field(None)

# Lightweight inputs for agent endpoints
class SymptomCheck(BaseModel):
    rabbit_tag: Optional[str] = None
    symptoms: List[str] = Field(default_factory=list)

class BreedingPlanInput(BaseModel):
    min_doe_age_days: int = Field(154, ge=0)  # ~22 weeks
    min_buck_age_days: int = Field(154, ge=0)
    cooldown_days: int = Field(14, ge=0)

# Example schemas kept for compatibility (can be ignored by app UI)
class User(BaseModel):
    name: str
    email: str
    address: str
    age: Optional[int] = None
    is_active: bool = True

class Product(BaseModel):
    title: str
    description: Optional[str] = None
    price: float
    category: str
    in_stock: bool = True
