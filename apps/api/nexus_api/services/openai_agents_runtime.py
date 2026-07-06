from dataclasses import dataclass

from nexus_api.config import get_settings
from nexus_api.models import Agent


@dataclass(frozen=True)
class OpenAIAgentResult:
    available: bool
    output: str
    confidence: float


async def run_openai_agent(agent: Agent, objective: str) -> OpenAIAgentResult:
    settings = get_settings()
    if not settings.openai_api_key:
        return OpenAIAgentResult(
            available=False,
            output="OpenAI Agents SDK is installed but no OpenAI API key is configured.",
            confidence=0.0,
        )
    from agents import Agent as SDKAgent
    from agents import Runner

    sdk_agent = SDKAgent(
        name=agent.name,
        instructions=f"{agent.system_prompt}\n\nMission: {agent.mission}",
    )
    result = await Runner.run(sdk_agent, objective)
    return OpenAIAgentResult(
        available=True,
        output=str(result.final_output),
        confidence=agent.confidence_floor,
    )

