from fastapi import Request
from hindsight_client import Hindsight
from google import genai

def get_hindsight(request: Request) -> Hindsight:
    return request.app.state.hindsight

def get_gemini(request: Request) -> genai.Client:
    return request.app.state.gemini
