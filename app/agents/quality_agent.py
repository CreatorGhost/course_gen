from typing import Dict, Any, List
from app.agents.base_agent import BaseAgent
from app.models.course import CourseResponse, Module, Lesson

class QualityAgent(BaseAgent):
    """Agent responsible for reviewing and refining course content."""
    
    def __init__(self, model_name: str = "gpt-3.5-turbo", temperature: float = 0.3):
        """Initialize the quality agent."""
        system_prompt = """
        You are a Quality Agent responsible for reviewing and refining educational course content.
        Your task is to ensure that course content is accurate, comprehensive, and well-structured.
        
        Follow these guidelines:
        1. Check for factual accuracy and correctness
        2. Ensure content is comprehensive and covers all necessary aspects
        3. Verify that the content is appropriate for the target audience
        4. Check for logical flow and coherence within and between lessons
        5. Look for gaps in content or explanations
        6. Ensure consistency in style and terminology
        7. Verify that resources are relevant and useful
        """
        
        super().__init__(
            name="Quality Agent",
            system_prompt=system_prompt,
            model_name=model_name,
            temperature=temperature
        )
        
        # Set a custom prompt template for the quality review task
        quality_template = """
        {system_prompt}
        
        You are reviewing a course titled: {course_title}
        
        Course Description: {course_description}
        
        Target audience: {audience}
        Course duration: {duration}
        
        Please review the following module and its lessons:
        
        Module: {module_title}
        
        {lessons_content}
        
        Based on this information, review the content and provide improvements.
        Focus on accuracy, comprehensiveness, appropriateness for the audience, and overall quality.
        
        Return your review and improvements in the following format:
        
        MODULE REVIEW:
        [Your overall assessment of the module]
        
        IMPROVEMENTS:
        [Specific improvements for the module as a whole]
        
        LESSON REVIEWS:
        [For each lesson, provide specific feedback and improvements]
        
        REVISED CONTENT:
        [Provide revised content for any lessons that need significant improvement]
        """
        
        self.set_prompt_template(
            template=quality_template,
            input_variables=[
                "system_prompt", "course_title", "course_description", 
                "module_title", "lessons_content", "audience", "duration"
            ]
        )
    
    async def review_module(
        self,
        course_title: str,
        course_description: str,
        module: Dict[str, Any],
        audience: str = "",
        duration: str = ""
    ) -> Dict[str, Any]:
        """
        Review and refine a module and its lessons.
        
        Args:
            course_title: The title of the course
            course_description: The course description
            module: The module dictionary with lessons
            audience: The target audience for the course
            duration: The duration of the course
            
        Returns:
            Dictionary containing the reviewed and improved module
        """
        # Format lessons content for review
        lessons_content = ""
        for i, lesson in enumerate(module.get("lessons", [])):
            lessons_content += f"""
            Lesson {i+1}: {lesson.get('title', '')}
            
            Content:
            {lesson.get('content', '')}
            
            Resources:
            {self._format_list(lesson.get('resources', []))}
            
            ---
            """
        
        inputs = {
            "system_prompt": self.system_prompt,
            "course_title": course_title,
            "course_description": course_description,
            "module_title": module.get("title", ""),
            "lessons_content": lessons_content,
            "audience": audience,
            "duration": duration
        }
        
        result = await self.run(inputs)
        
        # Parse the result and update the module
        improved_module = self._parse_review_result(result, module)
        
        return improved_module
    
    def _format_list(self, items: List[str]) -> str:
        """Format a list of items as a string with bullet points."""
        return "\n".join([f"- {item}" for item in items])
    
    def _parse_review_result(self, result: str, original_module: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse the review result and update the module.
        
        Args:
            result: The raw review result
            original_module: The original module dictionary
            
        Returns:
            Updated module dictionary
        """
        # Create a copy of the original module to update
        module = dict(original_module)
        
        # Check if there's a REVISED CONTENT section
        if "REVISED CONTENT:" in result:
            # Split the result to get the revised content section
            parts = result.split("REVISED CONTENT:")
            if len(parts) >= 2:
                revised_content = parts[1].strip()
                
                # This is a simplified implementation
                # In a real system, you would need more sophisticated parsing
                # to correctly match revised content to specific lessons
                
                # For now, we'll just add the improvement notes to each lesson
                module_review = ""
                improvements = ""
                
                if "MODULE REVIEW:" in result:
                    module_review_parts = result.split("MODULE REVIEW:")[1].split("IMPROVEMENTS:")[0].strip()
                    module_review = module_review_parts
                
                if "IMPROVEMENTS:" in result:
                    improvements_parts = result.split("IMPROVEMENTS:")[1].split("LESSON REVIEWS:")[0].strip()
                    improvements = improvements_parts
                
                # Add review notes to the module
                module["quality_review"] = {
                    "module_review": module_review,
                    "improvements": improvements
                }
                
                # For this simplified implementation, we'll just add the revised content
                # as a note in the module for reference
                module["quality_review"]["revised_content_notes"] = revised_content
        
        return module
    
    async def review_course(self, course: CourseResponse, audience: str = "", duration: str = "") -> CourseResponse:
        """
        Review and refine an entire course.
        
        Args:
            course: The course response object
            audience: The target audience for the course
            duration: The duration of the course
            
        Returns:
            Updated course response
        """
        improved_modules = []
        
        for module in course.modules:
            # Convert module to dict for processing
            module_dict = {
                "title": module.title,
                "lessons": [{"title": lesson.title, "content": lesson.content, "resources": lesson.resources} 
                            for lesson in module.lessons]
            }
            
            # Review and improve the module
            improved_module_dict = await self.review_module(
                course_title=course.course_title,
                course_description=course.description,
                module=module_dict,
                audience=audience,
                duration=duration
            )
            
            # Convert back to Module object
            improved_lessons = [
                Lesson(title=lesson.get("title"), content=lesson.get("content"), resources=lesson.get("resources", []))
                for lesson in improved_module_dict.get("lessons", [])
            ]
            
            improved_module = Module(title=improved_module_dict.get("title"), lessons=improved_lessons)
            improved_modules.append(improved_module)
        
        # Create updated course
        improved_course = CourseResponse(
            course_title=course.course_title,
            description=course.description,
            modules=improved_modules,
            references=course.references
        )
        
        return improved_course 