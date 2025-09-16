from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, GetCoreSchemaHandler
from pydantic_core import core_schema
from bson import ObjectId


# Custom ObjectId field for MongoDB
class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_core_schema__(cls, source, handler: GetCoreSchemaHandler):
        return core_schema.json_or_python_schema(
            json_schema=core_schema.str_schema(),
            python_schema=core_schema.no_info_after_validator_function(
                cls.validate,
                core_schema.str_schema()
            ),
            serialization=core_schema.to_string_ser_schema(),
        )

    @classmethod
    def __get_pydantic_json_schema__(cls, schema, handler: GetCoreSchemaHandler):
        # Generate schema dict via handler
        json_schema = handler(schema)
        json_schema.update(
            type="string",
            examples=["64f8b7b7e1f4b3b2c2c2c2c2"]  # Example ObjectId string
        )
        return json_schema


# Employee document structure
class Employee(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    employee_id: str = Field(..., example="E123")
    name: str = Field(..., example="John Doe")
    department: str = Field(..., example="Engineering")
    salary: float = Field(..., example=75000)
    joining_date: datetime
    skills: List[str] = Field(..., example=["Python", "MongoDB"])

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


# Model for creating a new employee
class EmployeeCreate(BaseModel):
    employee_id: str = Field(..., example="E123")
    name: str = Field(..., example="John Doe")
    department: str = Field(..., example="Engineering")
    salary: float = Field(..., example=75000)
    joining_date: datetime
    skills: List[str] = Field(..., example=["Python", "MongoDB"])


# Model for updating an employee (partial updates allowed)
class EmployeeUpdate(BaseModel):
    name: Optional[str] = Field(None, example="Jane Smith")
    department: Optional[str] = Field(None, example="HR")
    salary: Optional[float] = Field(None, example=60000)
    joining_date: Optional[datetime] = None
    skills: Optional[List[str]] = Field(None, example=["Communication", "Recruitment"])


# Response model for average salary
class AverageSalaryByDepartment(BaseModel):
    department: str
    avg_salary: float
