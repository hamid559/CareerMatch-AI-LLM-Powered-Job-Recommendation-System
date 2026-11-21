from pydantic import BaseModel, Field

class ProfileIn(BaseModel):
    name: str = "Candidate"
    resume_text: str = Field(min_length=30, max_length=50000)

class JobIn(BaseModel):
    title: str
    company: str
    location: str = "India"
    work_mode: str = "Not specified"
    experience: str = "Entry level"
    description: str = Field(min_length=30)
    skills: list[str] = []

class JobOut(BaseModel):
    id: int
    title: str
    company: str
    location: str
    work_mode: str
    experience: str
    description: str
    skills: list[str]
    class Config:
        from_attributes = True
