from fastapi import FastAPI, HTTPException, Query, status
from models import EmployeeCreate, Employee, EmployeeUpdate, AverageSalaryByDepartment
from database import db_client
from typing import List, Optional
from datetime import date, datetime
from fastapi.encoders import jsonable_encoder

# Create a FastAPI app instance
app = FastAPI(
    title="Employee Management API",
    description="A FastAPI backend for managing employee data with MongoDB."
)

# Connect to MongoDB on startup
@app.on_event("startup")
async def startup_db_client():
    await db_client.connect()

# Close MongoDB connection on shutdown
@app.on_event("shutdown")
async def shutdown_db_client():
    await db_client.close()

# --- Section 2: Core CRUD APIs ---

@app.post("/employees/", response_model=Employee, status_code=status.HTTP_201_CREATED)
async def create_employee(employee: EmployeeCreate):
    """
    Inserts a new employee record.
    Validation: Ensure employee_id is unique.
    """
    existing_employee = await db_client.collection.find_one({"employee_id": employee.employee_id})
    if existing_employee:
        raise HTTPException(
            status_code=400,
            detail=f"Employee with employee_id '{employee.employee_id}' already exists."
        )

    employee_data = employee.model_dump(by_alias=True)
    
    # Convert joining_date from date to datetime before inserting into MongoDB
    if "joining_date" in employee_data:
        employee_data["joining_date"] = datetime.combine(employee_data["joining_date"], datetime.min.time())
        
    created_employee = await db_client.collection.insert_one(employee_data)
    
    # Get the inserted document to return it with the generated _id
    new_employee = await db_client.collection.find_one({"_id": created_employee.inserted_id})
    
    # Manually convert ObjectId to string before passing to Pydantic model
    new_employee["_id"] = str(new_employee["_id"])
    
    return Employee(**new_employee)

@app.get("/employees/{employee_id}", response_model=Employee)
async def get_employee_by_id(employee_id: str):
    """
    Fetches employee details by employee_id.
    Check: Return 404 if not found.
    """
    employee = await db_client.collection.find_one({"employee_id": employee_id})
    if employee:
        # Manually convert ObjectId to string before passing to Pydantic model
        employee["_id"] = str(employee["_id"])
        return Employee(**employee)
    raise HTTPException(status_code=404, detail="Employee not found")

@app.put("/employees/{employee_id}", response_model=Employee)
async def update_employee(employee_id: str, employee_update: EmployeeUpdate):
    """
    Updates employee details.
    Requirement: Allow partial updates.
    """
    existing_employee = await db_client.collection.find_one({"employee_id": employee_id})
    if not existing_employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    update_data = {k: v for k, v in employee_update.model_dump(exclude_unset=True).items()}
    
    if "joining_date" in update_data and isinstance(update_data["joining_date"], date):
        update_data["joining_date"] = datetime.combine(update_data["joining_date"], datetime.min.time())

    if not update_data:
        # Manually convert ObjectId to string before passing to Pydantic model
        existing_employee["_id"] = str(existing_employee["_id"])
        return Employee(**existing_employee)

    await db_client.collection.update_one(
        {"employee_id": employee_id},
        {"$set": update_data}
    )

    updated_employee = await db_client.collection.find_one({"employee_id": employee_id})
    # Manually convert ObjectId to string before passing to Pydantic model
    updated_employee["_id"] = str(updated_employee["_id"])
    return Employee(**updated_employee)

@app.delete("/employees/{employee_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_employee(employee_id: str):
    delete_result = await db_client.collection.delete_one({"employee_id": employee_id})
    if delete_result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Employee not found")
    return

# --- Section 3: Querying & Aggregation ---

@app.get("/employees/", response_model=List[Employee])
async def list_employees_by_department(department: Optional[str] = Query(None)):
    """
    Returns employees in a specific department, sorted by joining_date (newest first).
    If no department is specified, lists all employees sorted by joining_date.
    """
    query = {}
    if department:
        query["department"] = department
    
    employees = []
    async for employee in db_client.collection.find(query).sort("joining_date", -1):
        # Manually convert ObjectId to string for each employee document
        employee["_id"] = str(employee["_id"])
        employees.append(Employee(**employee))
    return employees

@app.get("/employees/avg-salary", response_model=List[AverageSalaryByDepartment])
async def get_average_salary_by_department():
    """
    Uses MongoDB aggregation to compute the average salary grouped by department.
    """
    pipeline = [
        {"$group": {
            "_id": "$department",
            "avg_salary": {"$avg": "$salary"}
        }},
        {"$project": {
            "department": "$_id",
            "avg_salary": {"$round": ["$avg_salary", 2]},
            "_id": 0
        }},
        {"$sort": {"department": 1}}
    ]
    
    avg_salaries = []
    async for doc in db_client.collection.aggregate(pipeline):
        avg_salaries.append(AverageSalaryByDepartment(**doc))
    
    return avg_salaries

@app.get("/employees/search", response_model=List[Employee])
async def search_employees_by_skill(skill: str = Query(..., description="The skill to search for")):
    """
    Returns employees who have the given skill in their skills array.
    """
    query = {"skills": skill}
    
    employees = []
    async for employee in db_client.collection.find(query):
        # Manually convert ObjectId to string for each employee document
        employee["_id"] = str(employee["_id"])
        employees.append(Employee(**employee))
    
    return employees
