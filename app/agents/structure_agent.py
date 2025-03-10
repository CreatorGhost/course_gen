from typing import Dict, Any, List
from app.agents.base_agent import BaseAgent
from app.utils.logging_utils import setup_logger

# Set up logger
logger = setup_logger("structure_agent")

class StructureAgent(BaseAgent):
    """Agent responsible for organizing content into a logical course structure."""
    
    def __init__(self, model_name: str = "gpt-4o", temperature: float = 0.4):
        """Initialize the structure agent."""
        system_prompt = """
        You are a Structure Agent responsible for organizing educational content into a logical and effective course structure.
        Your task is to take research information and organize it into modules and lessons that follow sound pedagogical principles.
        
        Follow these guidelines:
        1. Organize content from simple to complex concepts
        2. Ensure a logical progression of topics
        3. Create a balanced distribution of content across modules
        4. Design a structure that aligns with the course duration
        5. Include practical applications and exercises where appropriate
        6. Consider the target audience's background and learning needs
        
        IMPORTANT: You must create exactly 5-6 modules, with 2-4 lessons each.
        """
        
        super().__init__(
            name="Structure Agent",
            system_prompt=system_prompt,
            model_name=model_name,
            temperature=temperature
        )
        
        logger.info("Structure Agent initialized")
        
        # Set a custom prompt template for the structure task
        structure_template = """
        {system_prompt}
        
        You have been provided with research information about a course on: {topic}
        
        Additional context:
        - Target audience: {audience}
        - Course duration: {duration}
        
        Research Summary: {research_summary}
        
        Key Concepts:
        {key_concepts}
        
        Based on this information, create a comprehensive course structure with EXACTLY 5-6 modules.
        Each module MUST have 2-4 lessons that build logically upon each other.
        
        Return your course structure in EXACTLY this format:
        
        COURSE TITLE:
        [Your course title]
        
        COURSE DESCRIPTION:
        [Your course description]
        
        MODULE 1: [Module title]
        - Lesson 1.1: [Lesson title]
        - Lesson 1.2: [Lesson title]
        [Add more lessons if needed]
        
        MODULE 2: [Module title]
        - Lesson 2.1: [Lesson title]
        - Lesson 2.2: [Lesson title]
        [Add more lessons if needed]
        
        [Continue for all modules, ensuring you create 5-6 modules total]
        
        RATIONALE:
        [Your rationale]
        """
        
        self.set_prompt_template(
            template=structure_template,
            input_variables=[
                "system_prompt", "topic", "audience", "duration", 
                "research_summary", "key_concepts"
            ]
        )
    
    async def create_structure(
        self, 
        topic: str, 
        research_data: Dict[str, Any],
        audience: str = "", 
        duration: str = ""
    ) -> Dict[str, Any]:
        """
        Create a course structure based on research data.
        
        Args:
            topic: The course topic
            research_data: Research data dictionary
            audience: The target audience for the course
            duration: The duration of the course
            
        Returns:
            Dictionary containing the course structure
        """
        try:
            logger.info(f"Creating structure for topic: {topic}")
            logger.debug(f"Research data keys: {list(research_data.keys())}")
            
            # Extract relevant information from research data
            research_summary = research_data.get("summary", "")
            logger.debug(f"Research summary length: {len(research_summary)}")
            
            # Format key concepts as a string
            key_concepts_list = research_data.get("key_concepts", [])
            logger.debug(f"Number of key concepts: {len(key_concepts_list)}")
            key_concepts = "\n".join([f"- {concept}" for concept in key_concepts_list])
            
            inputs = {
                "system_prompt": self.system_prompt,
                "topic": topic,
                "audience": audience,
                "duration": duration,
                "research_summary": research_summary,
                "key_concepts": key_concepts
            }
            
            logger.debug("Sending structure prompt to LLM")
            result = await self.run(inputs)
            logger.debug(f"Received response from LLM (length: {len(result)})")
            logger.debug("Raw LLM response:")
            logger.debug(result)
            
            # Parse the result into a structured format
            structure_data = self._parse_structure_result(result)
            
            logger.info("Structure creation completed")
            logger.debug(f"Created {len(structure_data['modules'])} modules")
            for module in structure_data['modules']:
                logger.debug(f"Module '{module['title']}' has {len(module['lessons'])} lessons")
            
            return structure_data
            
        except Exception as e:
            logger.error(f"Error creating structure: {str(e)}", exc_info=True)
            raise
    
    def _parse_structure_result(self, result: str) -> Dict[str, Any]:
        """
        Parse the structure result into a structured format.
        
        Args:
            result: The raw structure result
            
        Returns:
            Structured course structure data
        """
        try:
            logger.debug("Starting to parse structure result")
            
            # Initialize the structure data
            structure_data = {
                "course_title": "",
                "course_description": "",
                "modules": [],
                "rationale": ""
            }
            
            # Simple parsing based on section headers
            sections = result.split("\n\n")
            logger.debug(f"Split result into {len(sections)} sections")
            
            current_section = None
            current_module = None
            
            for section in sections:
                section = section.strip()
                logger.debug(f"Processing section starting with: {section[:50]}...")
                
                if "COURSE TITLE:" in section:
                    structure_data["course_title"] = section.replace("COURSE TITLE:", "").strip()
                    logger.debug(f"Found course title: {structure_data['course_title']}")
                elif "COURSE DESCRIPTION:" in section:
                    structure_data["course_description"] = section.replace("COURSE DESCRIPTION:", "").strip()
                    logger.debug("Found course description")
                elif "RATIONALE:" in section:
                    structure_data["rationale"] = section.replace("RATIONALE:", "").strip()
                    logger.debug("Found rationale")
                elif section.startswith("MODULE "):
                    logger.debug(f"Processing module section: {section[:50]}...")
                    # Start a new module
                    lines = section.split("\n")
                    module_title = lines[0].strip()
                    
                    current_module = {
                        "title": module_title,
                        "lessons": []
                    }
                    
                    # Add lessons
                    for i in range(1, len(lines)):
                        lesson_line = lines[i].strip()
                        if lesson_line.startswith("- Lesson ") or lesson_line.startswith("- "):
                            # Extract lesson title (remove the "- Lesson X.Y: " prefix)
                            lesson_parts = lesson_line.split(":", 1)
                            if len(lesson_parts) > 1:
                                lesson_title = lesson_parts[1].strip()
                            else:
                                # If no colon, just remove the dash
                                lesson_title = lesson_line.replace("- ", "", 1).strip()
                            
                            lesson = {
                                "title": lesson_title,
                                "content": ""  # Will be filled by the content agent
                            }
                            
                            current_module["lessons"].append(lesson)
                            logger.debug(f"Added lesson: {lesson_title}")
                    
                    structure_data["modules"].append(current_module)
                    logger.debug(f"Added module '{module_title}' with {len(current_module['lessons'])} lessons")
            
            logger.info(f"Parsing completed. Created {len(structure_data['modules'])} modules")
            return structure_data
            
        except Exception as e:
            logger.error(f"Error parsing structure result: {str(e)}", exc_info=True)
            raise 