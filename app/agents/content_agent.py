from typing import Dict, Any, List
from app.agents.base_agent import BaseAgent

class ContentAgent(BaseAgent):
    """Agent responsible for generating detailed content for each module and lesson."""
    
    def __init__(self, model_name: str = "gpt-4o", temperature: float = 0.5):
        """Initialize the content agent."""
        system_prompt = """
        You are a Content Agent responsible for creating detailed educational content for courses.
        Your task is to generate comprehensive, accurate, and engaging content for course lessons.
        
        Follow these guidelines:
        1. Create clear and concise explanations of concepts
        2. Use examples to illustrate complex ideas
        3. Include relevant case studies and real-world applications
        4. Write in an engaging and conversational style
        5. Ensure content is accurate and up-to-date
        6. Tailor the content to the target audience's background and learning needs
        7. Include relevant activities or exercises where appropriate
        """
        
        super().__init__(
            name="Content Agent",
            system_prompt=system_prompt,
            model_name=model_name,
            temperature=temperature
        )
        
        # Set a custom prompt template for the content creation task
        content_template = """
        {system_prompt}
        
        You are creating content for a course titled: {course_title}
        
        Course Description: {course_description}
        
        You need to create content for:
        Module: {module_title}
        Lesson: {lesson_title}
        
        Additional context:
        - Target audience: {audience}
        - Course duration: {duration}
        
        Research information:
        {research_info}
        
        Based on this information, create comprehensive and engaging content for this lesson.
        The content should be educational, accurate, and tailored to the target audience.
        
        Return your content in the following format:
        
        CONTENT:
        [Your lesson content here, including explanations, examples, and any exercises]
        
        RESOURCES:
        [List 2-4 relevant resources for further learning]
        """
        
        self.set_prompt_template(
            template=content_template,
            input_variables=[
                "system_prompt", "course_title", "course_description", 
                "module_title", "lesson_title", "audience", "duration",
                "research_info"
            ]
        )
    
    async def generate_lesson_content(
        self,
        course_title: str,
        course_description: str,
        module_title: str,
        lesson_title: str,
        research_data: Dict[str, Any],
        audience: str = "",
        duration: str = ""
    ) -> Dict[str, Any]:
        """
        Generate content for a specific lesson.
        
        Args:
            course_title: The title of the course
            course_description: The course description
            module_title: The title of the module
            lesson_title: The title of the lesson
            research_data: Research data dictionary
            audience: The target audience for the course
            duration: The duration of the course
            
        Returns:
            Dictionary containing the lesson content and resources
        """
        # Prepare research information
        research_info = f"""
        Summary:
        {research_data.get('summary', '')}
        
        Key Concepts:
        {self._format_list(research_data.get('key_concepts', []))}
        
        Insights:
        {research_data.get('insights', '')}
        """
        
        inputs = {
            "system_prompt": self.system_prompt,
            "course_title": course_title,
            "course_description": course_description,
            "module_title": module_title,
            "lesson_title": lesson_title,
            "audience": audience,
            "duration": duration,
            "research_info": research_info
        }
        
        result = await self.run(inputs)
        
        # Parse the result into a structured format
        content_data = self._parse_content_result(result)
        
        return content_data
    
    def _format_list(self, items: List[str]) -> str:
        """Format a list of items as a string with bullet points."""
        return "\n".join([f"- {item}" for item in items])
    
    def _parse_content_result(self, result: str) -> Dict[str, Any]:
        """
        Parse the content result into a structured format.
        
        Args:
            result: The raw content result
            
        Returns:
            Structured lesson content data
        """
        # Initialize the content data
        content_data = {
            "content": "",
            "resources": []
        }
        
        # Simple parsing based on section headers
        if "CONTENT:" in result and "RESOURCES:" in result:
            # Split by RESOURCES: to separate content and resources
            parts = result.split("RESOURCES:")
            
            if len(parts) >= 2:
                # Get content (remove the CONTENT: prefix)
                content_data["content"] = parts[0].replace("CONTENT:", "").strip()
                
                # Get resources
                resources_text = parts[1].strip()
                # Split by line and remove empty lines
                resources = [line.strip() for line in resources_text.split("\n") if line.strip()]
                content_data["resources"] = resources
        else:
            # Fallback if the format is not as expected
            content_data["content"] = result
        
        return content_data 