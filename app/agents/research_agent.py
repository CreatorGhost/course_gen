from typing import Dict, Any, List, Optional
from app.agents.base_agent import BaseAgent
from app.utils.web_research import get_web_research_tool
from app.utils.logging_utils import setup_logger

# Set up logger
logger = setup_logger("research_agent")

class ResearchAgent(BaseAgent):
    """Agent responsible for researching content from the web."""
    
    def __init__(self, model_name: str = "gpt-3.5-turbo", temperature: float = 0.5):
        """Initialize the research agent."""
        system_prompt = """
        You are a Research Agent responsible for gathering accurate and relevant information from the web.
        Your task is to research topics thoroughly and provide comprehensive information that will be used to create educational content.
        
        Follow these guidelines:
        1. Focus on gathering information from reputable sources
        2. Ensure the information is up-to-date and accurate
        3. Collect a diverse range of perspectives and resources
        4. Organize the information in a clear and coherent manner
        5. Cite all sources properly
        6. Prioritize depth of understanding over breadth when researching specific topics
        """
        
        # Get the web research tool
        web_research_tool = get_web_research_tool()
        
        super().__init__(
            name="Research Agent",
            system_prompt=system_prompt,
            model_name=model_name,
            temperature=temperature,
            tools=[web_research_tool]
        )
        
        # Set a custom prompt template for the research task
        research_template = """
        {system_prompt}
        
        Your task is to research the following topic: {topic}
        
        Additional context:
        - Target audience: {audience}
        - Course duration: {duration}
        
        Based on this information and using the web research tools available to you, gather comprehensive information on this topic.
        
        Return your findings in the following format:
        
        RESEARCH SUMMARY:
        [A brief summary of what you found]
        
        KEY CONCEPTS:
        [List of key concepts with brief explanations]
        
        RESOURCES:
        [List of useful resources with URLs]
        
        INSIGHTS:
        [Any additional insights or observations]
        """
        
        self.set_prompt_template(
            template=research_template,
            input_variables=["system_prompt", "topic", "audience", "duration"]
        )
        
        logger.info("Research Agent initialized")
    
    async def research_topic(self, topic: str, audience: str = "", duration: str = "") -> Dict[str, Any]:
        """
        Research a specific topic.
        
        Args:
            topic: The topic to research
            audience: The target audience for the content
            duration: The duration of the course
            
        Returns:
            Dictionary containing research results
        """
        try:
            logger.info(f"Starting research for topic: {topic}")
            logger.debug(f"Audience: {audience}")
            logger.debug(f"Duration: {duration}")
            
            inputs = {
                "system_prompt": self.system_prompt,
                "topic": topic,
                "audience": audience,
                "duration": duration
            }
            
            logger.debug("Sending research prompt to LLM")
            result = await self.run(inputs)
            logger.debug("Received response from LLM")
            
            # Parse the result into a structured format
            research_data = self._parse_research_result(result)
            
            logger.info("Successfully parsed research data")
            logger.debug(f"Research data sections: {list(research_data.keys())}")
            return research_data
            
        except Exception as e:
            logger.error(f"Error during research: {str(e)}", exc_info=True)
            return {
                "error": f"Research failed: {str(e)}"
            }
    
    def _parse_research_result(self, result: str) -> Dict[str, Any]:
        """
        Parse the research result into a structured format.
        
        Args:
            result: The raw research result
            
        Returns:
            Structured research data
        """
        # Initialize the research data
        research_data = {
            "summary": "",
            "key_concepts": [],
            "resources": [],
            "insights": ""
        }
        
        # Simple parsing based on section headers
        sections = result.split("\n\n")
        current_section = None
        
        for section in sections:
            if "RESEARCH SUMMARY:" in section:
                current_section = "summary"
                research_data["summary"] = section.replace("RESEARCH SUMMARY:", "").strip()
            elif "KEY CONCEPTS:" in section:
                current_section = "key_concepts"
                concepts_text = section.replace("KEY CONCEPTS:", "").strip()
                # Split by line and remove empty lines
                research_data["key_concepts"] = [line.strip() for line in concepts_text.split("\n") if line.strip()]
            elif "RESOURCES:" in section:
                current_section = "resources"
                resources_text = section.replace("RESOURCES:", "").strip()
                # Split by line and remove empty lines
                research_data["resources"] = [line.strip() for line in resources_text.split("\n") if line.strip()]
            elif "INSIGHTS:" in section:
                current_section = "insights"
                research_data["insights"] = section.replace("INSIGHTS:", "").strip()
            elif current_section:
                # Append to the current section
                if current_section == "summary":
                    research_data["summary"] += "\n" + section
                elif current_section == "key_concepts":
                    research_data["key_concepts"].extend([line.strip() for line in section.split("\n") if line.strip()])
                elif current_section == "resources":
                    research_data["resources"].extend([line.strip() for line in section.split("\n") if line.strip()])
                elif current_section == "insights":
                    research_data["insights"] += "\n" + section
        
        return research_data 