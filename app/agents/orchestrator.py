import asyncio
from typing import Dict, Any, List, Optional, Tuple, cast
from langchain_core.tools import BaseTool
from langgraph.graph import StateGraph, END
from langgraph.prebuilt.tool_node import ToolNode
from pydantic import BaseModel, Field

from app.agents.research_agent import ResearchAgent
from app.agents.structure_agent import StructureAgent
from app.agents.content_agent import ContentAgent
from app.agents.quality_agent import QualityAgent
from app.models.course import CourseResponse, Module, Lesson
from app.utils.logging_utils import setup_logger, log_state

# Set up logger
logger = setup_logger("orchestrator")

# Define the state for the graph
class AgentState(BaseModel):
    """State object for the multi-agent graph."""
    brief: str = Field(..., description="The brief description of the course")
    target_audience: Optional[str] = Field(None, description="Target audience for the course")
    course_duration: Optional[str] = Field(None, description="Duration of the course")
    research_data: Optional[Dict[str, Any]] = Field(None, description="Research data collected")
    course_structure: Optional[Dict[str, Any]] = Field(None, description="Structure of the course")
    content_data: Optional[Dict[str, List[Dict[str, Any]]]] = Field(None, description="Content for each module and lesson")
    final_course: Optional[Dict[str, Any]] = Field(None, description="Final course data")
    error: Optional[str] = Field(None, description="Error message if any")

# Initialize agents
logger.info("Initializing agents...")
research_agent = ResearchAgent()
structure_agent = StructureAgent()
content_agent = ContentAgent()
quality_agent = QualityAgent()
logger.info("All agents initialized successfully")

# Define agent functions
async def research_course_topic(state: AgentState) -> AgentState:
    """Research the course topic."""
    try:
        logger.info(f"Starting research for course topic: {state.brief}")
        log_state(logger, state.dict(), "Initial")
        
        research_data = await research_agent.research_topic(
            topic=state.brief,
            audience=state.target_audience or "",
            duration=state.course_duration or ""
        )
        
        logger.info("Research completed successfully")
        logger.debug(f"Research data keys: {list(research_data.keys() if research_data else [])}")
        
        new_state = AgentState(
            brief=state.brief,
            target_audience=state.target_audience,
            course_duration=state.course_duration,
            research_data=research_data
        )
        log_state(logger, new_state.dict(), "Final")
        return new_state
    except Exception as e:
        logger.error(f"Research error: {str(e)}", exc_info=True)
        return AgentState(
            brief=state.brief,
            target_audience=state.target_audience,
            course_duration=state.course_duration,
            error=f"Research error: {str(e)}"
        )

async def create_course_structure(state: AgentState) -> AgentState:
    """Create the course structure."""
    try:
        logger.info("Starting course structure creation")
        log_state(logger, state.dict(), "Initial")
        
        if not state.research_data:
            logger.error("No research data available")
            return AgentState(
                brief=state.brief,
                target_audience=state.target_audience,
                course_duration=state.course_duration,
                error="No research data available for creating course structure"
            )
        
        course_structure = await structure_agent.create_structure(
            topic=state.brief,
            research_data=state.research_data,
            audience=state.target_audience or "",
            duration=state.course_duration or ""
        )
        
        logger.info("Course structure created successfully")
        logger.debug(f"Structure keys: {list(course_structure.keys() if course_structure else [])}")
        
        new_state = AgentState(
            brief=state.brief,
            target_audience=state.target_audience,
            course_duration=state.course_duration,
            research_data=state.research_data,
            course_structure=course_structure
        )
        log_state(logger, new_state.dict(), "Final")
        return new_state
    except Exception as e:
        logger.error(f"Structure creation error: {str(e)}", exc_info=True)
        return AgentState(
            brief=state.brief,
            target_audience=state.target_audience,
            course_duration=state.course_duration,
            research_data=state.research_data,
            error=f"Structure creation error: {str(e)}"
        )

async def generate_course_content(state: AgentState) -> AgentState:
    """Generate content for the course."""
    try:
        logger.info("Starting course content generation")
        log_state(logger, state.dict(), "Initial")
        
        if not state.course_structure:
            logger.error("No course structure available")
            return AgentState(
                brief=state.brief,
                target_audience=state.target_audience,
                course_duration=state.course_duration,
                research_data=state.research_data,
                error="No course structure available for generating content"
            )
        
        # Extract course information
        course_title = state.course_structure.get("course_title", "")
        course_description = state.course_structure.get("course_description", "")
        modules = state.course_structure.get("modules", [])
        
        logger.info(f"Generating content for {len(modules)} modules")
        content_data = {}
        
        # Generate content for each module and lesson
        for module in modules:
            module_title = module.get("title", "")
            logger.info(f"Processing module: {module_title}")
            content_data[module_title] = []
            
            for lesson in module.get("lessons", []):
                lesson_title = lesson.get("title", "")
                logger.info(f"Generating content for lesson: {lesson_title}")
                
                try:
                    lesson_content = await content_agent.generate_lesson_content(
                        course_title=course_title,
                        course_description=course_description,
                        module_title=module_title,
                        lesson_title=lesson_title,
                        research_data=state.research_data,
                        audience=state.target_audience or "",
                        duration=state.course_duration or ""
                    )
                    
                    logger.debug(f"Lesson content generated successfully for {lesson_title}")
                    content_data[module_title].append({
                        "title": lesson_title,
                        "content": lesson_content.get("content", ""),
                        "resources": lesson_content.get("resources", [])
                    })
                except Exception as e:
                    logger.error(f"Error generating content for lesson '{lesson_title}': {str(e)}", exc_info=True)
                    content_data[module_title].append({
                        "title": lesson_title,
                        "content": f"Error generating content: {str(e)}",
                        "resources": []
                    })
        
        logger.info("Content generation completed")
        new_state = AgentState(
            brief=state.brief,
            target_audience=state.target_audience,
            course_duration=state.course_duration,
            research_data=state.research_data,
            course_structure=state.course_structure,
            content_data=content_data
        )
        log_state(logger, new_state.dict(), "Final")
        return new_state
    except Exception as e:
        logger.error(f"Content generation error: {str(e)}", exc_info=True)
        return AgentState(
            brief=state.brief,
            target_audience=state.target_audience,
            course_duration=state.course_duration,
            research_data=state.research_data,
            course_structure=state.course_structure,
            error=f"Content generation error: {str(e)}"
        )

async def finalize_course(state: AgentState) -> AgentState:
    """Finalize the course by compiling all data."""
    try:
        logger.info("Starting course finalization")
        log_state(logger, state.dict(), "Initial")
        
        if not state.course_structure:
            logger.error("Missing course structure")
            return AgentState(
                brief=state.brief,
                target_audience=state.target_audience,
                course_duration=state.course_duration,
                research_data=state.research_data,
                error="Missing course structure for finalizing the course"
            )
            
        if not state.content_data:
            logger.error("Missing content data")
            return AgentState(
                brief=state.brief,
                target_audience=state.target_audience,
                course_duration=state.course_duration,
                research_data=state.research_data,
                course_structure=state.course_structure,
                error="Missing content data for finalizing the course"
            )
        
        # Extract course information
        course_title = state.course_structure.get("course_title", "")
        course_description = state.course_structure.get("course_description", "")
        modules_structure = state.course_structure.get("modules", [])
        
        logger.info(f"Processing {len(modules_structure)} modules for final compilation")
        modules = []
        
        for module_structure in modules_structure:
            module_title = module_structure.get("title", "")
            logger.info(f"Finalizing module: {module_title}")
            
            lesson_content_list = state.content_data.get(module_title, [])
            logger.debug(f"Found {len(lesson_content_list)} lessons for module {module_title}")
            
            lessons = []
            for lesson_data in lesson_content_list:
                lesson = {
                    "title": lesson_data.get("title", ""),
                    "content": lesson_data.get("content", ""),
                    "resources": lesson_data.get("resources", [])
                }
                lessons.append(lesson)
                logger.debug(f"Added lesson: {lesson['title']}")
            
            module = {
                "title": module_title,
                "lessons": lessons
            }
            modules.append(module)
        
        # Gather references
        references = []
        if state.research_data and "resources" in state.research_data:
            references = state.research_data.get("resources", [])
            logger.debug(f"Added {len(references)} references")
        
        final_course = {
            "course_title": course_title,
            "description": course_description,
            "modules": modules,
            "references": references
        }
        
        logger.info("Course finalization completed successfully")
        new_state = AgentState(
            brief=state.brief,
            target_audience=state.target_audience,
            course_duration=state.course_duration,
            research_data=state.research_data,
            course_structure=state.course_structure,
            content_data=state.content_data,
            final_course=final_course
        )
        log_state(logger, new_state.dict(), "Final")
        return new_state
    except Exception as e:
        logger.error(f"Course finalization error: {str(e)}", exc_info=True)
        return AgentState(
            brief=state.brief,
            target_audience=state.target_audience,
            course_duration=state.course_duration,
            research_data=state.research_data,
            course_structure=state.course_structure,
            content_data=state.content_data,
            error=f"Course finalization error: {str(e)}"
        )

def should_end(state: AgentState) -> str:
    """Determine if the workflow should end."""
    if state.error:
        logger.error(f"Workflow ended with error: {state.error}")
        return "end"
    
    if state.final_course:
        logger.info("Workflow completed successfully")
        return "end"
    
    logger.debug("Workflow continuing")
    return "continue"

# Build the graph
def build_course_generation_graph() -> StateGraph:
    """Build the course generation graph."""
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("research", research_course_topic)
    workflow.add_node("structure", create_course_structure)
    workflow.add_node("content", generate_course_content)
    workflow.add_node("finalize", finalize_course)
    
    # Add edges
    workflow.add_edge("research", "structure")
    workflow.add_edge("structure", "content")
    workflow.add_edge("content", "finalize")
    
    # Set conditional edges
    workflow.add_conditional_edges(
        "finalize",
        should_end,
        {
            "end": END,
            "continue": "finalize"
        }
    )
    
    workflow.set_entry_point("research")
    
    return workflow

# Main function to generate a course
async def generate_course(
    brief: str,
    target_audience: Optional[str] = None,
    course_duration: Optional[str] = None
) -> CourseResponse:
    """
    Generate a complete educational course based on a brief description.
    
    Args:
        brief: Brief description of the course
        target_audience: Target audience for the course
        course_duration: Duration of the course
        
    Returns:
        A CourseResponse object containing the generated course
    """
    logger.info(f"Generating course for: {brief}")
    
    try:
        # Initialize the state
        initial_state = AgentState(
            brief=brief,
            target_audience=target_audience,
            course_duration=course_duration
        )
        
        # Build the graph
        workflow = build_course_generation_graph()
        
        # Compile the graph
        app = workflow.compile()
        
        # Run the graph
        result = await app.ainvoke(initial_state)
        
        # Convert result dict to AgentState
        result_dict = dict(result)
        logger.debug(f"Result keys: {list(result_dict.keys())}")
        
        if result_dict.get("error"):
            logger.error(f"Course generation failed: {result_dict['error']}")
            raise Exception(f"Course generation failed: {result_dict['error']}")
        
        final_course_data = result_dict.get("final_course")
        if not final_course_data:
            logger.error("Course generation failed: No final course data available")
            raise Exception("Course generation failed: No final course data available")
        
        # Convert the final course data to a CourseResponse object
        logger.debug("Converting final course data to CourseResponse")
        logger.debug(f"Final course data keys: {list(final_course_data.keys())}")
        
        # Convert modules
        modules = []
        for module_data in final_course_data.get("modules", []):
            # Convert lessons
            lessons = []
            for lesson_data in module_data.get("lessons", []):
                lesson = Lesson(
                    title=lesson_data.get("title", ""),
                    content=lesson_data.get("content", ""),
                    resources=lesson_data.get("resources", [])
                )
                lessons.append(lesson)
                logger.debug(f"Created lesson: {lesson.title}")
            
            # Create module
            module = Module(
                title=module_data.get("title", ""),
                lessons=lessons
            )
            modules.append(module)
            logger.debug(f"Created module: {module.title} with {len(module.lessons)} lessons")
        
        # Create course response
        course_response = CourseResponse(
            course_title=final_course_data.get("course_title", ""),
            description=final_course_data.get("description", ""),
            modules=modules,
            references=final_course_data.get("references", [])
        )
        
        logger.info("Successfully created CourseResponse object")
        logger.debug(f"Course has {len(course_response.modules)} modules")
        return course_response
        
    except Exception as e:
        logger.error(f"Error in generate_course: {str(e)}", exc_info=True)
        raise 