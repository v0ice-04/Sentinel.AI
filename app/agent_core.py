import json
from datetime import datetime, date, time
import typing_extensions as typing
from google import genai
from google.genai import types
from hindsight_client import Hindsight

from app.config import Settings
from app.models import DeployEvent, IncidentReport, RiskAnalysis, MemoryItem

class RiskOutput(typing.TypedDict):
    risk_score: int
    risk_level: str
    reasoning: str
    recommendation: str

async def analyze_deploy(
    event: DeployEvent,
    hindsight: Hindsight,
    gemini: genai.Client,
    settings: Settings
) -> RiskAnalysis:
    # Step 1: native async recall
    recall_response = await hindsight.arecall(
        bank_id=settings.bank_id,
        query=f"{event.service} deployment {event.change_type}",
        max_tokens=settings.recall_max_tokens,
        budget=settings.recall_budget,
    )
    memories = recall_response.results

    # Step 2: build memory text
    if memories:
        memory_text = "\n".join([
            f"- [{m.type}] {m.text}" for m in memories
        ])
    else:
        memory_text = "No historical data available for this service."

    # Step 3: build prompts
    system_prompt = """You are a DevOps risk analyst with memory of past 
deployment incidents. Use the provided incident history to give 
accurate risk assessments. Always reference specific past incidents 
in your reasoning when available. Be conservative — when in doubt, 
increase the risk score."""

    user_prompt = f"""
Analyze the deployment risk for the following event:

SERVICE: {event.service}
ENVIRONMENT: {event.environment}
CHANGE TYPE: {event.change_type}
TIMESTAMP: {event.timestamp}
DEPLOYED BY: {event.deployed_by or "unknown"}

INCIDENT HISTORY FROM MEMORY:
{memory_text}

Based on this history, assess the deployment risk.
Return risk_score as integer 0-100, risk_level as low/medium/high,
reasoning explaining which past incidents influenced your score,
and a concrete recommendation.
"""

    # Step 4: async Gemini call with JSON schema
    gemini_response = await gemini.aio.models.generate_content(
        model=settings.gemini_model,
        contents=user_prompt,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            response_mime_type="application/json",
            response_schema=RiskOutput,
            temperature=0.2,
            max_output_tokens=settings.gemini_max_output_tokens,
        ),
    )

    # Step 5: parse and return
    parsed = json.loads(gemini_response.text)
    return RiskAnalysis(
        risk_score=parsed["risk_score"],
        risk_level=parsed["risk_level"],
        reasoning=parsed["reasoning"],
        recommendation=parsed["recommendation"],
        memories_used=len(memories),
        analyzed_at=datetime.utcnow(),
    )

async def report_incident(
    incident: IncidentReport,
    hindsight: Hindsight,
    settings: Settings
):
    fact = (
        f"{incident.service} experienced a {incident.severity} severity "
        f"incident on {incident.date}. "
        f"Root cause: {incident.root_cause}. "
        f"Resolution: {incident.resolution}. "
        f"Triggered by: {incident.trigger}."
        + (f" Downtime: {incident.downtime_minutes} minutes."
           if incident.downtime_minutes else "")
    )

    await hindsight.aretain(
        bank_id=settings.bank_id,
        content=fact,
        context="deployment incident",
        timestamp=datetime.combine(incident.date, time.min),
        document_id=f"incident-{incident.service}-{incident.date}",
        metadata={
            "service": incident.service,
            "severity": incident.severity,
            "trigger": incident.trigger,
        }
    )

async def get_service_memories(
    service: str,
    hindsight: Hindsight,
    settings: Settings
) -> list[MemoryItem]:
    recall_response = await hindsight.arecall(
        bank_id=settings.bank_id,
        query=f"{service} deployment incidents",
        max_tokens=4096,
        budget="mid",
    )

    return [
        MemoryItem(
            text=r.text,
            fact_type=r.type,
            context=r.context,
            occurred_start=str(r.occurred_start) if r.occurred_start else None,
            retrieved_at=datetime.utcnow(),
        )
        for r in recall_response.results
    ]
