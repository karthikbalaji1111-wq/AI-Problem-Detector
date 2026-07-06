from datetime import UTC, datetime, timedelta
from typing import TypedDict

from langgraph.graph import END, START, StateGraph
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from nexus_api.models import (
    Agent,
    AgentMessage,
    AgentRun,
    Approval,
    Notification,
    Organization,
    RunStatus,
    Task,
    TaskStatus,
)
from nexus_api.services.memory import recall, remember


class WorkforceState(TypedDict):
    objective: str
    organization_id: str
    run_id: str
    trace_id: str
    plan: list[dict]
    evidence: list[dict]
    delegation: list[dict]
    critique: list[dict]
    verification: dict
    execution: list[dict]
    confidence: float
    risk_score: float
    approval_required: bool


class AgentRuntime:
    def __init__(self, db: Session) -> None:
        self.db = db

    def run(self, *, run: AgentRun) -> AgentRun:
        run.status = RunStatus.RUNNING.value
        self.db.commit()
        graph = self._build_graph()
        initial: WorkforceState = {
            "objective": run.objective,
            "organization_id": run.organization_id,
            "run_id": run.id,
            "trace_id": run.trace_id,
            "plan": [],
            "evidence": [],
            "delegation": [],
            "critique": [],
            "verification": {},
            "execution": [],
            "confidence": 0.0,
            "risk_score": 0.0,
            "approval_required": False,
        }
        final_state = graph.invoke(initial)
        run.state = dict(final_state)
        run.confidence = final_state["confidence"]
        run.risk_score = final_state["risk_score"]
        if final_state["approval_required"]:
            run.status = RunStatus.WAITING_APPROVAL.value
        else:
            run.status = RunStatus.SUCCEEDED.value
            run.completed_at = datetime.now(UTC)
        self.db.commit()
        self.db.refresh(run)
        return run

    def resume_after_approval(self, *, run: AgentRun) -> AgentRun:
        state = dict(run.state)
        if not state:
            raise ValueError("Run has no persisted state")
        state["approval_required"] = False
        state = self._execute(state)
        state = self._learn(state)
        run.state = state
        run.status = RunStatus.SUCCEEDED.value
        run.confidence = state["confidence"]
        run.risk_score = state["risk_score"]
        run.completed_at = datetime.now(UTC)
        self.db.commit()
        self.db.refresh(run)
        return run

    def _build_graph(self):
        graph = StateGraph(WorkforceState)
        graph.add_node("plan", self._plan)
        graph.add_node("research", self._research)
        graph.add_node("delegate", self._delegate)
        graph.add_node("critique", self._critique)
        graph.add_node("verify", self._verify)
        graph.add_node("execute", self._execute)
        graph.add_node("learn", self._learn)
        graph.add_edge(START, "plan")
        graph.add_edge("plan", "research")
        graph.add_edge("research", "delegate")
        graph.add_edge("delegate", "critique")
        graph.add_edge("critique", "verify")
        graph.add_conditional_edges(
            "verify",
            lambda state: "approval" if state["approval_required"] else "execute",
            {"approval": END, "execute": "execute"},
        )
        graph.add_edge("execute", "learn")
        graph.add_edge("learn", END)
        return graph.compile()

    def _agents(self, organization_id: str) -> dict[str, Agent]:
        agents = self.db.scalars(select(Agent).where(Agent.organization_id == organization_id)).all()
        return {agent.role_key: agent for agent in agents}

    def _next_sequence(self, run_id: str) -> int:
        current = self.db.scalar(
            select(func.max(AgentMessage.sequence)).where(AgentMessage.run_id == run_id)
        )
        return int(current or 0) + 1

    def _message(
        self,
        state: WorkforceState,
        role_key: str,
        message_type: str,
        content: str,
        confidence: float,
        meta: dict,
    ) -> None:
        agents = self._agents(state["organization_id"])
        agent = agents.get(role_key)
        message = AgentMessage(
            run_id=state["run_id"],
            organization_id=state["organization_id"],
            agent_id=agent.id if agent else None,
            sequence=self._next_sequence(state["run_id"]),
            message_type=message_type,
            content=content,
            confidence=confidence,
            meta=meta,
        )
        self.db.add(message)
        self.db.commit()

    def _plan(self, state: WorkforceState) -> WorkforceState:
        agents = self._agents(state["organization_id"])
        steps = [
            {
                "owner": "research_agent",
                "title": "Collect evidence",
                "description": f"Gather internal memory and external context for: {state['objective']}",
            },
            {
                "owner": "operations_agent",
                "title": "Design execution path",
                "description": "Identify dependencies, owners, bottlenecks, and approval gates.",
            },
            {
                "owner": "critic_agent",
                "title": "Critique plan",
                "description": "Find unsupported claims, unsafe actions, and missing constraints.",
            },
            {
                "owner": "verifier_agent",
                "title": "Verify readiness",
                "description": "Score confidence, risk, reversibility, and evidence quality.",
            },
        ]
        for step in steps:
            owner = agents.get(step["owner"])
            task = Task(
                organization_id=state["organization_id"],
                owner_agent_id=owner.id if owner else None,
                title=step["title"],
                description=step["description"],
                status=TaskStatus.PLANNING.value,
                priority=1 if step["owner"] == "verifier_agent" else 2,
                due_at=datetime.now(UTC) + timedelta(days=2),
                meta={"run_id": state["run_id"], "trace_id": state["trace_id"]},
            )
            self.db.add(task)
        self.db.commit()
        state["plan"] = steps
        state["confidence"] = 0.68
        self._message(
            state,
            "planner_agent",
            "plan",
            f"Created a four-stage workforce plan for '{state['objective']}' with research, operations, critique, and verification gates.",
            0.68,
            {"plan": steps, "streaming": True, "observability": {"trace_id": state["trace_id"]}},
        )
        return state

    def _research(self, state: WorkforceState) -> WorkforceState:
        memories = recall(self.db, organization_id=state["organization_id"], query=state["objective"], limit=5)
        evidence = [
            {
                "source": "organizational_memory",
                "content": memory.content,
                "importance": memory.importance,
            }
            for memory in memories
        ]
        if not evidence:
            evidence = [
                {
                    "source": "first_run_context",
                    "content": "No prior memory was found. The workforce is operating from the current objective, domain, and agent policies.",
                    "importance": 0.5,
                }
            ]
        state["evidence"] = evidence
        state["confidence"] = 0.71
        self._message(
            state,
            "research_agent",
            "evidence",
            f"Retrieved {len(evidence)} evidence records and separated current assumptions from durable memory.",
            0.71,
            {"evidence": evidence},
        )
        return state

    def _delegate(self, state: WorkforceState) -> WorkforceState:
        domain = self.db.get(Organization, state["organization_id"]).domain
        default_delegates = ["operations_agent", "finance_agent", "security_agent", "analytics_agent"]
        if domain in {"software", "freestyle"}:
            default_delegates.extend(["engineering_manager", "backend_engineer", "frontend_engineer"])
        if domain in {"manufacturing", "agriculture"}:
            default_delegates.extend(["operations_agent", "customer_success_agent"])
        if domain in {"government", "healthcare", "ngo", "education", "disaster_management"}:
            default_delegates.extend(["legal_agent", "customer_success_agent"])
        delegation = [
            {
                "agent": role_key,
                "assignment": f"Analyze '{state['objective']}' from the {role_key.replace('_', ' ')} perspective.",
                "expected_output": "risks, actions, dependencies, and confidence score",
            }
            for role_key in dict.fromkeys(default_delegates)
        ]
        state["delegation"] = delegation
        state["confidence"] = 0.74
        self._message(
            state,
            "supervisor_agent",
            "delegation",
            f"Delegated work to {len(delegation)} agents and established collaboration state.",
            0.74,
            {"delegation": delegation},
        )
        return state

    def _critique(self, state: WorkforceState) -> WorkforceState:
        risks = [
            {
                "risk": "Insufficient external evidence",
                "severity": 0.42,
                "mitigation": "Require verifier confirmation before execution.",
            },
            {
                "risk": "Cross-team dependency drift",
                "severity": 0.36,
                "mitigation": "Supervisor keeps Kanban ownership and due dates current.",
            },
        ]
        if any("send" in str(step).lower() for step in state["plan"]):
            risks.append(
                {
                    "risk": "External communication impact",
                    "severity": 0.72,
                    "mitigation": "Route to human approval before dispatch.",
                }
            )
        state["critique"] = risks
        state["risk_score"] = round(max(item["severity"] for item in risks), 2)
        state["confidence"] = 0.76
        self._message(
            state,
            "critic_agent",
            "critique",
            "Critiqued the plan and identified the highest risk as "
            f"{max(risks, key=lambda item: item['severity'])['risk']}.",
            0.76,
            {"risks": risks},
        )
        return state

    def _verify(self, state: WorkforceState) -> WorkforceState:
        organization = self.db.get(Organization, state["organization_id"])
        evidence_quality = min(1.0, 0.55 + len(state["evidence"]) * 0.08)
        execution_readiness = 0.72 if len(state["delegation"]) >= 4 else 0.58
        confidence = round((evidence_quality + execution_readiness + state["confidence"]) / 3, 2)
        risk_score = round(max(state["risk_score"], 1 - confidence + 0.15), 2)
        approval_required = risk_score >= organization.risk_tolerance
        verification = {
            "evidence_quality": round(evidence_quality, 2),
            "execution_readiness": execution_readiness,
            "confidence": confidence,
            "risk_score": risk_score,
            "approval_required": approval_required,
            "policy": "human approval required when risk exceeds organization tolerance",
        }
        state["verification"] = verification
        state["confidence"] = confidence
        state["risk_score"] = risk_score
        state["approval_required"] = approval_required
        self._message(
            state,
            "verifier_agent",
            "verification",
            f"Verified workflow confidence at {confidence:.0%} and risk at {risk_score:.0%}. Approval required: {approval_required}.",
            confidence,
            verification,
        )
        if approval_required:
            agents = self._agents(state["organization_id"])
            approval = Approval(
                organization_id=state["organization_id"],
                run_id=state["run_id"],
                requested_by_agent_id=agents["verifier_agent"].id,
                title=f"Approve workforce execution: {state['objective'][:100]}",
                rationale="Risk exceeds the organization's configured tolerance. A human operator must approve before external execution.",
                risk_score=risk_score,
            )
            self.db.add(approval)
            notification = Notification(
                organization_id=state["organization_id"],
                title="Approval required",
                body=f"NEXUS needs approval to execute: {state['objective']}",
                severity="warning",
            )
            self.db.add(notification)
            self.db.commit()
        return state

    def _execute(self, state: WorkforceState) -> WorkforceState:
        execution = [
            {
                "action": "create_internal_operating_record",
                "status": "completed",
                "result": "Tasks, timeline, memory, and notification records persisted.",
            },
            {
                "action": "notify_workspace",
                "status": "completed",
                "result": "Internal notification generated for organization operators.",
            },
        ]
        notification = Notification(
            organization_id=state["organization_id"],
            title="Workforce run completed",
            body=f"Agents completed the run: {state['objective']}",
            severity="success",
        )
        self.db.add(notification)
        self.db.commit()
        state["execution"] = execution
        self._message(
            state,
            "execution_agent",
            "execution",
            "Executed approved internal actions and persisted operating records.",
            state["confidence"],
            {"execution": execution},
        )
        return state

    def _learn(self, state: WorkforceState) -> WorkforceState:
        content = (
            f"Objective: {state['objective']}. Confidence: {state['confidence']}. "
            f"Risk: {state['risk_score']}. Delegated agents: "
            f"{', '.join(item['agent'] for item in state['delegation'])}."
        )
        agents = self._agents(state["organization_id"])
        remember(
            self.db,
            organization_id=state["organization_id"],
            agent_id=agents["learning_agent"].id,
            memory_type="episodic",
            content=content,
            importance=0.78,
            meta={"run_id": state["run_id"], "trace_id": state["trace_id"]},
        )
        self._message(
            state,
            "learning_agent",
            "learning",
            "Stored the completed run as episodic memory for future planning and evaluation.",
            0.78,
            {"memory_type": "episodic"},
        )
        return state
