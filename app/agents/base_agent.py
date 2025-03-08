import os
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableSequence
from langchain_openai import ChatOpenAI
from app.utils.logging_utils import setup_logger

# Set up logger
logger = setup_logger("base_agent")

# Load environment variables
load_dotenv()

# Initialize OpenAI API key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    logger.error("OpenAI API key not found in environment variables")
    raise ValueError("OpenAI API key not found")

class BaseAgent:
    """Base class for all agents in the system."""
    
    def __init__(
        self,
        name: str,
        system_prompt: str,
        model_name: str = "gpt-3.5-turbo",
        temperature: float = 0.7,
        tools: Optional[List[Any]] = None
    ):
        """
        Initialize the base agent.
        
        Args:
            name: Name of the agent
            system_prompt: System prompt for the agent
            model_name: LLM model name to use
            temperature: Temperature for the LLM
            tools: List of tools available to the agent
        """
        self.name = name
        self.system_prompt = system_prompt
        self.model_name = model_name
        self.temperature = temperature
        self.tools = tools or []
        
        logger.info(f"Initializing {name} with model {model_name}")
        
        try:
            # Initialize the LLM
            self.llm = ChatOpenAI(
                model=model_name,
                temperature=temperature,
                openai_api_key=OPENAI_API_KEY
            )
            logger.debug(f"LLM initialized with temperature {temperature}")
            
            # Initialize with default prompt template
            self.prompt_template = PromptTemplate(
                input_variables=["input", "context"],
                template=f"{system_prompt}\n\nInput: {{input}}\nContext: {{context}}"
            )
            logger.debug("Default prompt template initialized")
            
            # Create a runnable sequence
            self.chain = self.prompt_template | self.llm
            logger.info(f"{name} initialization completed")
            
        except Exception as e:
            logger.error(f"Error initializing {name}: {str(e)}", exc_info=True)
            raise
    
    def set_prompt_template(self, template: str, input_variables: List[str]):
        """
        Set a custom prompt template.
        
        Args:
            template: The prompt template string
            input_variables: List of input variable names
        """
        try:
            logger.debug(f"Setting custom prompt template for {self.name}")
            logger.debug(f"Input variables: {input_variables}")
            
            self.prompt_template = PromptTemplate(
                input_variables=input_variables,
                template=template
            )
            self.chain = self.prompt_template | self.llm
            logger.info("Custom prompt template set successfully")
            
        except Exception as e:
            logger.error(f"Error setting prompt template: {str(e)}", exc_info=True)
            raise
    
    async def run(self, inputs: Dict[str, Any], context: str = "") -> str:
        """
        Run the agent with the given inputs.
        
        Args:
            inputs: Dictionary of inputs to the agent
            context: Additional context for the agent
            
        Returns:
            The agent's response
        """
        try:
            logger.info(f"Running {self.name}")
            logger.debug(f"Input keys: {list(inputs.keys())}")
            
            # Add context to inputs
            inputs["context"] = context
            
            # Run the chain
            logger.debug("Invoking LLM chain")
            result = await self.chain.ainvoke(inputs)
            logger.debug(f"Received response from LLM: {type(result)}")
            
            # Extract the content from the response
            if hasattr(result, 'content'):
                logger.debug("Extracting content from response")
                content = result.content
            else:
                logger.debug("Converting response to string")
                content = str(result)
            
            logger.debug(f"Response length: {len(content)}")
            logger.info(f"{self.name} completed successfully")
            return content
            
        except Exception as e:
            logger.error(f"Error running {self.name}: {str(e)}", exc_info=True)
            raise 