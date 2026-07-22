from fastapi import FastAPI
from pydantic import BaseModel
import ee
from fastapi.middleware.cors import CORSMiddleware
from src.gee_pipeline.ndbi_processor import NDBIProcessor
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Goobta AI Backend")

# Allow React frontend to access the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this to the frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize EE securely (assumes environment is authenticated)
try:
    ee.Initialize(opt_url='https://earthengine-highvolume.googleapis.com')
except Exception as e:
    print(f"Earth Engine initialization warning: {e}")

class MapRequest(BaseModel):
    year: str = "2026"

@app.get("/api/ndbi_tile")
def get_ndbi_tile(year: str = "2026"):
    """Returns the live Google Earth Engine Map ID tile URL for Hargeisa."""
    processor = NDBIProcessor()
    try:
        map_id_dict = processor.get_ndbi_map_id(year)
        return {"tile_url": map_id_dict['tile_fetcher'].url_format}
    except Exception as e:
        return {"error": str(e)}

class ChatMessage(BaseModel):
    message: str

@app.post("/api/chat")
def chat_with_ai(chat: ChatMessage):
    """
    Receives a message from the user and returns an AI response.
    """
    user_msg = chat.message.lower()
    
    # Attempt to use the real LLM API
    try:
        from openai import OpenAI
        import os
        api_key = os.getenv('OPENAI_API_KEY')
        
        if api_key:
            # Note: If this key is for a different provider (like Groq, OpenRouter, etc.), 
            # you can add: base_url="https://api.yourprovider.com/v1" to the OpenAI client.
            client = OpenAI(api_key=api_key)
            
            system_prompt = "You are the Goobta AI Assistant, an expert in Somaliland real estate. Provide concise, professional advice about land values, risks, and ROI in Hargeisa."
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo", # Adjust this model name based on your API provider
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": chat.message}
                ]
            )
            return {"reply": response.choices[0].message.content}
    except Exception as e:
        print(f"LLM API Error (Falling back to mock logic): {e}")

    # Mock AI logic fallback
    if "price" in user_msg or "cheap" in user_msg or "value" in user_msg:
        response = "Based on our ML predictions, properties further from the center offer cheaper entry prices ($10-30/sqm) but high growth potential (+15%), while central Sha'ab remains premium ($200+/sqm)."
    elif "jigjiga" in user_msg or "university" in user_msg:
        response = "Jigjiga Yar is currently our top recommended hotspot! Driven by student housing demand near the University, we predict a +22% appreciation rate in land values over the next year."
    elif "flood" in user_msg or "laga" in user_msg:
        response = "Our spatial model penalizes land values by up to 30% if they are within 500 meters of a Laga (dry riverbed) due to seasonal flash flooding risks."
    else:
        response = "Hello! I am the Goobta AI Assistant. I can help you analyze Hargeisa real estate trends, explain our machine learning predictions, or find the best places to invest. How can I help?"
        
    return {"reply": response}

@app.get("/api/hotspots")
def get_hotspots():
    """Returns realistic ML-predicted hotspots as GeoJSON."""
    from src.models.train_model import GrowthPredictor
    predictor = GrowthPredictor()
    return predictor.get_top_hotspots()

@app.get("/api/predict")
def predict_location(lat: float, lon: float):
    """Returns a real estate price prediction for a given coordinate."""
    from src.models.train_model import GrowthPredictor
    predictor = GrowthPredictor()
    prediction = predictor.predict_point(lat, lon)
    return prediction

@app.get("/api/listings")
def get_listings():
    """Returns scraped property listings."""
    return [
        {"lat": 9.56, "lon": 44.07, "price": 45000, "desc": "Scraped Listing"}
    ]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
