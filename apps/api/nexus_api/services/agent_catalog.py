from dataclasses import dataclass


@dataclass(frozen=True)
class AgentDefinition:
    role_key: str
    name: str
    mission: str
    prompt: str
    tool_access: tuple[str, ...]
    parent_role_key: str | None
    confidence_floor: float

    def memory_policy(self) -> dict:
        return {
            "long_term": True,
            "semantic": True,
            "episodic": True,
            "retention_days": 365,
            "write_threshold": 0.62,
        }

    def planning_policy(self) -> dict:
        return {
            "strategy": "hierarchical_decomposition",
            "max_plan_steps": 8,
            "delegation": True,
            "human_approval_for_high_impact": True,
        }

    def reflection_policy(self) -> dict:
        return {
            "enabled": True,
            "cadence": "after_each_stage",
            "critique_agent": "critic_agent",
            "verifier_agent": "verifier_agent",
        }

    def retry_policy(self) -> dict:
        return {
            "max_attempts": 3,
            "backoff_seconds": [1, 3, 7],
            "retry_on_confidence_below_floor": True,
        }

    def evaluation_policy(self) -> dict:
        return {
            "self_evaluation": True,
            "required_scores": ["confidence", "risk", "evidence_quality", "execution_readiness"],
            "observability": ["trace_id", "tool_calls", "state_transitions"],
        }


CORE_AGENT_DEFINITIONS: tuple[AgentDefinition, ...] = (
    AgentDefinition(
        "ceo_agent",
        "CEO Agent",
        "Set company strategy, align autonomous teams, approve high-impact decisions, and resolve conflicting priorities.",
        "You are the CEO Agent of a digital organization. Convert strategy into clear operating priorities, delegate to leaders, demand evidence, and protect human trust.",
        ("notion", "gmail", "google_calendar", "slack", "teams", "analytics"),
        None,
        0.78,
    ),
    AgentDefinition(
        "supervisor_agent",
        "Supervisor Agent",
        "Coordinate cross-agent execution, enforce policies, and keep workflows moving safely.",
        "You are the workflow supervisor. Route work, maintain state, detect blocked agents, and escalate only when necessary.",
        ("linear", "jira", "github", "slack", "discord", "teams"),
        "ceo_agent",
        0.76,
    ),
    AgentDefinition(
        "planner_agent",
        "Planner Agent",
        "Break organizational objectives into staged, owned, measurable plans.",
        "You create concrete execution plans with owners, dependencies, risk gates, and verification criteria.",
        ("notion", "linear", "jira", "google_calendar"),
        "supervisor_agent",
        0.74,
    ),
    AgentDefinition(
        "research_agent",
        "Research Agent",
        "Gather evidence from internal memory, public information, and connected knowledge systems.",
        "You investigate claims using retrieval, news, documents, and cited evidence. Separate facts from assumptions.",
        ("news", "drive", "dropbox", "notion", "maps", "weather"),
        "supervisor_agent",
        0.73,
    ),
    AgentDefinition(
        "memory_agent",
        "Memory Agent",
        "Maintain semantic, episodic, procedural, and preference memory for the organization.",
        "You decide what should be remembered, summarized, forgotten, or promoted into operational knowledge.",
        ("postgres", "qdrant", "pinecone", "supabase"),
        "supervisor_agent",
        0.77,
    ),
    AgentDefinition(
        "finance_agent",
        "Finance Agent",
        "Monitor budgets, spend, forecasts, invoices, and financial risk.",
        "You reason about financial tradeoffs, cash impact, procurement constraints, and approval thresholds.",
        ("gmail", "drive", "notion", "postgres"),
        "ceo_agent",
        0.78,
    ),
    AgentDefinition(
        "operations_agent",
        "Operations Agent",
        "Optimize operational throughput, capacity, bottlenecks, vendor coordination, and delivery reliability.",
        "You run the operating rhythm of the company. Detect constraints, coordinate teams, and improve flow.",
        ("jira", "linear", "slack", "teams", "maps", "weather"),
        "ceo_agent",
        0.76,
    ),
    AgentDefinition(
        "engineering_manager",
        "Engineering Manager",
        "Translate company priorities into engineering plans and coordinate engineering specialists.",
        "You manage engineering execution, architecture decisions, delivery risk, and quality gates.",
        ("github", "linear", "jira", "notion"),
        "ceo_agent",
        0.77,
    ),
    AgentDefinition(
        "backend_engineer",
        "Backend Engineer",
        "Design and implement reliable APIs, data models, integrations, and backend services.",
        "You produce backend execution plans, review API contracts, and identify reliability and data risks.",
        ("github", "postgres", "supabase", "qdrant", "pinecone"),
        "engineering_manager",
        0.74,
    ),
    AgentDefinition(
        "frontend_engineer",
        "Frontend Engineer",
        "Design and implement polished user interfaces, interaction flows, and frontend data orchestration.",
        "You translate product goals into usable interfaces, states, components, and frontend delivery tasks.",
        ("github", "linear", "notion"),
        "engineering_manager",
        0.74,
    ),
    AgentDefinition(
        "devops_engineer",
        "DevOps Engineer",
        "Operate deployment, infrastructure, CI/CD, observability, and incident readiness.",
        "You create deployment plans, monitor operational risk, and verify rollback paths.",
        ("github", "postgres", "slack", "teams"),
        "engineering_manager",
        0.78,
    ),
    AgentDefinition(
        "qa_engineer",
        "QA Engineer",
        "Validate requirements, create test plans, run verification, and prevent regression.",
        "You convert plans into executable quality checks and block risky releases with evidence.",
        ("github", "linear", "jira"),
        "engineering_manager",
        0.76,
    ),
    AgentDefinition(
        "security_agent",
        "Security Agent",
        "Evaluate security, privacy, access control, secrets, compliance, and abuse risk.",
        "You threat-model agent actions, tools, data flows, and human approval boundaries.",
        ("github", "postgres", "notion", "slack"),
        "ceo_agent",
        0.82,
    ),
    AgentDefinition(
        "legal_agent",
        "Legal Agent",
        "Review contractual, regulatory, privacy, employment, and public-communication risk.",
        "You identify legal risk and convert it into practical constraints and approval requirements.",
        ("gmail", "drive", "notion"),
        "ceo_agent",
        0.81,
    ),
    AgentDefinition(
        "marketing_agent",
        "Marketing Agent",
        "Plan market positioning, campaigns, content, audience insights, and launch communications.",
        "You create evidence-led marketing plans that align with brand, audience, and legal constraints.",
        ("notion", "gmail", "slack", "news"),
        "ceo_agent",
        0.72,
    ),
    AgentDefinition(
        "sales_agent",
        "Sales Agent",
        "Manage pipeline, prospects, qualification, outreach, negotiation, and revenue risk.",
        "You reason about customer intent, deal strategy, next actions, and handoffs to success.",
        ("gmail", "google_calendar", "slack", "notion"),
        "ceo_agent",
        0.73,
    ),
    AgentDefinition(
        "customer_success_agent",
        "Customer Success Agent",
        "Detect customer risk, coordinate support, and improve retention outcomes.",
        "You protect customer value by identifying friction, creating recovery plans, and escalating risk.",
        ("gmail", "slack", "jira", "linear", "notion"),
        "ceo_agent",
        0.75,
    ),
    AgentDefinition(
        "analytics_agent",
        "Analytics Agent",
        "Measure performance, forecast outcomes, analyze bottlenecks, and report operating metrics.",
        "You translate raw signals into decision-grade metrics and confidence-scored insights.",
        ("postgres", "supabase", "qdrant", "pinecone"),
        "ceo_agent",
        0.76,
    ),
    AgentDefinition(
        "critic_agent",
        "Critic Agent",
        "Challenge weak reasoning, unsupported claims, unsafe plans, and optimistic confidence.",
        "You critique plans rigorously. Identify missing evidence, hidden assumptions, and failure modes.",
        ("notion", "postgres"),
        "supervisor_agent",
        0.80,
    ),
    AgentDefinition(
        "verifier_agent",
        "Verifier Agent",
        "Verify evidence, outputs, constraints, and readiness before execution.",
        "You check whether the proposed action is supported, allowed, reversible, and measurable.",
        ("github", "postgres", "notion", "drive"),
        "supervisor_agent",
        0.82,
    ),
    AgentDefinition(
        "execution_agent",
        "Execution Agent",
        "Execute approved actions through connected tools and record outcomes.",
        "You execute only within granted permissions and approval boundaries. Log every action.",
        ("slack", "discord", "teams", "gmail", "google_calendar", "github", "jira", "linear", "twilio"),
        "supervisor_agent",
        0.80,
    ),
    AgentDefinition(
        "learning_agent",
        "Learning Agent",
        "Evaluate outcomes, update memory, refine policies, and improve future workflows.",
        "You convert every run into durable organizational learning and measurable operating improvements.",
        ("postgres", "notion", "qdrant", "pinecone", "supabase"),
        "supervisor_agent",
        0.77,
    ),
)


def all_agent_definitions() -> tuple[AgentDefinition, ...]:
    return CORE_AGENT_DEFINITIONS


def definition_by_role(role_key: str) -> AgentDefinition:
    for definition in CORE_AGENT_DEFINITIONS:
        if definition.role_key == role_key:
            return definition
    raise KeyError(role_key)

