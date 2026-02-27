import os
from typing import TypedDict, List, Dict, Any, Literal
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

# Import your Strategist tools from the previous script
from strategist_agent import execute_strategist_pipeline, ManuscriptProfile


# ==========================================
# 1. DEFINE THE GLOBAL STATE
# ==========================================
# This TypedDict is the "memory" of the application.
# It gets passed around to every agent as they do their work.
class SlushpilotState(TypedDict):
    manuscript: Dict[str, Any]
    publishers: List[Dict[str, Any]]
    emails_drafted: bool
    drafted_emails: List[str]
    next_action: str


# ==========================================
# 2. THE SUPERVISOR ROUTER NODE
# ==========================================
# We use Pydantic to force the Supervisor to only output valid route names
class SupervisorDecision(BaseModel):
    next_node: Literal["Strategist", "PitchWriter", "FINISH"] = Field(
        description="The next agent to route to based on the current state of the project."
    )


def supervisor_agent(state: SlushpilotState):
    """The brain of the operation. Reviews state and decides the next step."""
    print("\n[👑 SUPERVISOR] Reviewing global state...")

    # We use a blazingly fast, cheap model for basic routing logic
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are the Supervisor AI for 'Slushpilot', an application that helps authors pitch their books.
        Your job is to look at the current state of the project and route to the correct agent.

        RULES:
        1. If 'publishers' is empty, route to 'Strategist' to find matching publishers.
        2. If 'publishers' has data, but 'emails_drafted' is False, route to 'PitchWriter' to draft the query letters.
        3. If 'emails_drafted' is True, route to 'FINISH' to end the pipeline."""),
        ("user", "CURRENT STATE: {state}")
    ])

    chain = prompt | llm.with_structured_output(SupervisorDecision)
    decision = chain.invoke({"state": state})

    print(f"[👑 SUPERVISOR] Decision made. Routing to: {decision.next_node}")

    # Update the state with the routing decision
    return {"next_action": decision.next_node}


# ==========================================
# 3. THE WORKER NODES
# ==========================================
def strategist_node(state: SlushpilotState):
    """Wrapper that calls your actual Strategist script."""
    print("\n[⚙️ WORKER] Strategist Agent activated...")

    # Reconstruct the Pydantic model for your existing script
    manuscript_profile = ManuscriptProfile(**state["manuscript"])

    # Run the heavy vector search and reasoning
    top_publishers = execute_strategist_pipeline(manuscript_profile)

    # Convert Pydantic objects back to dicts to store in the Global State
    pub_dicts = [pub.model_dump() for pub in top_publishers]

    return {"publishers": pub_dicts}


def pitch_writer_node(state: SlushpilotState):
    """A mock node for the Pitch Writer we will build next."""
    print("\n[⚙️ WORKER] Pitch Writer Agent activated...")

    pubs = state.get("publishers", [])
    print(f"           Drafting emails for {len(pubs)} publishers using their custom hooks...")

    # MOCK BEHAVIOR: We will replace this with actual LLM email generation later
    mock_emails = [f"Drafted email for {p['publisher_id']}" for p in pubs]

    return {
        "emails_drafted": True,
        "drafted_emails": mock_emails
    }


# ==========================================
# 4. CONDITIONAL ROUTING FUNCTION
# ==========================================
def route_from_supervisor(state: SlushpilotState):
    """Tells LangGraph which edge to follow based on the Supervisor's decision."""
    decision = state.get("next_action")
    if decision == "Strategist":
        return "strategist_node"
    elif decision == "PitchWriter":
        return "pitch_writer_node"
    else:
        return END


# ==========================================
# 5. BUILD THE LANGGRAPH
# ==========================================
def build_graph():
    workflow = StateGraph(SlushpilotState)

    # Add our nodes (the agents)
    workflow.add_node("supervisor", supervisor_agent)
    workflow.add_node("strategist_node", strategist_node)
    workflow.add_node("pitch_writer_node", pitch_writer_node)

    # Add Edges (The flow of data)
    # 1. The graph ALWAYS starts by asking the Supervisor what to do
    workflow.add_edge(START, "supervisor")

    # 2. The Supervisor dynamically routes to the workers or finishes
    workflow.add_conditional_edges(
        "supervisor",
        route_from_supervisor,
        {
            "strategist_node": "strategist_node",
            "pitch_writer_node": "pitch_writer_node",
            END: END
        }
    )

    # 3. When workers finish, they MUST hand control back to the Supervisor
    workflow.add_edge("strategist_node", "supervisor")
    workflow.add_edge("pitch_writer_node", "supervisor")

    # Compile the graph
    return workflow.compile()


# ==========================================
# 6. EXECUTION
# ==========================================
if __name__ == "__main__":
    app = build_graph()

    # Initialize the starting state with the author's input
    initial_state = {
        "manuscript": {
            "genre": "Sci-Fi Thriller",
            "word_count": 85000,
            "blurb": "In a future where memories can be extracted and sold...",
            "comparative_titles": ["Dark Matter by Blake Crouch"],
            "target_audience": "Adults who enjoy dystopian espionage."
        },
        "publishers": [],  # Empty! Supervisor will see this.
        "emails_drafted": False,  # False! Supervisor will see this.
        "drafted_emails": [],
        "next_action": ""
    }

    print("🚀 Starting Slushpilot Pipeline...")
    # Invoke the graph
    final_state = app.invoke(initial_state)

    print("\n🎉 PIPELINE COMPLETE!")
    print(f"Total Publishers Found: {len(final_state['publishers'])}")
    print(f"Total Emails Drafted: {len(final_state['drafted_emails'])}")