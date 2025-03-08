from fastapi import APIRouter, HTTPException, BackgroundTasks
from app.models.course import CourseRequest, CourseResponse
from app.agents.orchestrator import generate_course

router = APIRouter(
    prefix="/api/courses",
    tags=["courses"],
    responses={404: {"description": "Not found"}},
)

@router.post("/generate", response_model=CourseResponse)
async def create_course(course_request: CourseRequest):
    """
    Generate a course based on the provided brief description.
    
    This endpoint triggers the multi-agent system to research and generate
    a complete course structure with modules and content.
    """
    try:
        # Call the multi-agent orchestrator to generate the course
        course = await generate_course(
            brief=course_request.brief,
            target_audience=course_request.target_audience,
            course_duration=course_request.course_duration
        )
        return course
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate course: {str(e)}")

@router.get("/example", response_model=CourseResponse)
async def get_example_course():
    """
    Get an example course response.
    
    This endpoint returns a predefined example of a generated course.
    """
    # Example course for testing/demonstration
    return CourseResponse(
        course_title="Introduction to Microfinance: Fundamentals and Applications",
        description="A comprehensive introduction to microfinance principles, designed for beginners with no prior financial knowledge.",
        modules=[
            {
                "title": "Module 1: Understanding Microfinance Basics",
                "lessons": [
                    {
                        "title": "What is Microfinance?",
                        "content": "Microfinance is the provision of financial services to low-income individuals or groups who might otherwise not have access to conventional banking services...",
                        "resources": ["Resource 1", "Resource 2"]
                    },
                    {
                        "title": "Key Concepts and Terminology",
                        "content": "This lesson covers the essential terms and concepts in microfinance...",
                        "resources": ["Resource 3"]
                    }
                ]
            },
            {
                "title": "Module 2: The History and Evolution of Microfinance",
                "lessons": [
                    {
                        "title": "Origins of Microfinance",
                        "content": "The modern microfinance movement is often credited to Muhammad Yunus, who started the Grameen Bank in Bangladesh...",
                        "resources": []
                    }
                ]
            }
        ],
        references=[
            "Source 1: Journal of Microfinance Studies",
            "Source 2: World Bank Microfinance Reports"
        ]
    ) 