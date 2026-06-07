from fastapi import Request
from hindsight_client import Hindsight
from groq import AsyncGroq

def get_hindsight(request: Request) -> Hindsight:
    return request.app.state.hindsight

def get_groq(request: Request) -> AsyncGroq:
    return request.app.state.groq
