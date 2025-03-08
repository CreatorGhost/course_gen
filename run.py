import uvicorn
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

if __name__ == "__main__":
    # Get port from environment variables or use default
    port = int(os.getenv("PORT", 8000))
    
    # Run the FastAPI application
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True) 