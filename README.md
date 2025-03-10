# Course Generation System

A multi-agent system architecture that generates complete educational courses from brief descriptions. The system researches relevant content, organizes it into modules, and produces a structured course with comprehensive content.

## Architecture

The system uses a multi-agent architecture with specialized agents:

1. **Research Agent**: Gathers information from web sources on the course topic
2. **Structure Agent**: Organizes content into a logical course structure with modules and lessons
3. **Content Agent**: Generates detailed content for each lesson
4. **Quality Agent**: Reviews and refines the course content

These agents are orchestrated using LangGraph, a framework for building complex agent workflows.

## Requirements

- Python 3.8+
- OpenAI API key
- Tavily API key (for web research)

## Installation

1. Clone the repository:

```bash
git clone https://github.com/CreatorGhost/course_gen
cd course_gen
```

2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the root directory with your API keys:

```
OPENAI_API_KEY=your_openai_api_key
TAVILY_API_KEY=your_tavily_api_key
PORT=8000
```

## Running the Application

Start the FastAPI server:

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`.

## API Endpoints

### Generate a Course

```
POST /api/courses/generate
```

Request body:

```json
{
  "brief": "A microfinance course for beginners who need to learn from basics",
  "target_audience": "College students with no financial background",
  "course_duration": "6 weeks"
}
```

Response:

```json
{
  "course_title": "Introduction to Microfinance: Fundamentals and Applications",
  "description": "A comprehensive introduction to microfinance principles, designed for beginners with no prior financial knowledge.",
  "modules": [
    {
      "title": "Module 1: Understanding Microfinance Basics",
      "lessons": [
        {
          "title": "What is Microfinance?",
          "content": "Microfinance is the provision of financial services to low-income individuals...",
          "resources": [...]
        },
        ...
      ]
    },
    ...
  ],
  "references": [...]
}
```

### Get Example Course

```
GET /api/courses/example
```

Returns a sample course response for testing and demonstration purposes.

## System Components

### Agents

- `ResearchAgent`: Conducts web research on the course topic
- `StructureAgent`: Creates a logical course structure
- `ContentAgent`: Generates detailed content for lessons
- `QualityAgent`: Reviews and refines the content

### Workflow

1. The Research Agent gathers information about the course topic
2. The Structure Agent organizes the information into modules and lessons
3. The Content Agent generates detailed content for each lesson
4. The workflow finalizes the course by compiling all generated data

## Development

The system is built with:

- FastAPI for the API endpoints
- LangGraph for agent orchestration
- LangChain for agent tools and utilities
- OpenAI GPT models for content generation
- Tavily for web research

## Notes

- For production use, you would need to implement more robust error handling and logging
- Consider implementing caching to reduce API calls and improve performance
- The system currently uses GPT-4o, but can be configured to use other models
