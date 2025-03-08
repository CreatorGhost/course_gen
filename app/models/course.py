from typing import List, Optional
from pydantic import BaseModel, Field

class CourseRequest(BaseModel):
    """Request model for course generation."""
    brief: str = Field(..., description="A brief description of the course")
    target_audience: Optional[str] = Field(None, description="The target audience for the course")
    course_duration: Optional[str] = Field(None, description="The duration of the course (e.g., '6 weeks')")

class Lesson(BaseModel):
    """Model for a lesson within a module."""
    title: str
    content: str
    resources: List[str] = []

class Module(BaseModel):
    """Model for a course module."""
    title: str
    lessons: List[Lesson]

class CourseResponse(BaseModel):
    """Response model for a generated course."""
    course_title: str
    description: str
    modules: List[Module]
    references: List[str] = [] 