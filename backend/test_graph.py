import asyncio
import os
import sys
from dotenv import load_dotenv

# Add the current directory to sys.path so we can import app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.agents.graph import research_graph
from app.agents.state import ResearchState

# Load environment variables from .env
load_dotenv()

async def main():
    # Quick sanity check for API keys
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    tavily_key = os.getenv("TAVILY_API_KEY")
    
    print("=" * 60)
    print("      AI Research Assistant - Agent Graph Test      ")
    print("=" * 60)
    print(f"Anthropic API Key Loaded: {'Yes (sk-ant...)' if anthropic_key else 'No X'}")
    print(f"Tavily API Key Loaded:    {'Yes (tvly...)' if tavily_key else 'No X'}")
    print("-" * 60)

    if not anthropic_key or not tavily_key:
        print("[WARNING] Missing API keys! Make sure to create a backend/.env file")
        print("with ANTHROPIC_API_KEY and TAVILY_API_KEY before running the full pipeline.")
        print("-" * 60)

    # Initialize a dummy research state
    test_topic = "Self-Attention Mechanism in Transformers"
    initial_state: ResearchState = {
        "report_id": "test-report-uuid-12345",
        "user_id": "test-user-uuid-67890",
        "topic": test_topic,
        "queries": [],
        "subtopics": [],
        "research_direction": "",
        "raw_sources": [],
        "validated_sources": [],
        "findings": [],
        "report_markdown": "",
        "current_agent": "",
        "completed_agents": [],
        "error": None,
    }

    print(f"Starting test run for topic: '{test_topic}'...")
    print("Executing research graph nodes sequentially (this can take 30-60s)...")
    print("-" * 60)

    try:
        # We run the research graph and stream the execution state deltas
        async for event in research_graph.astream(initial_state):
            node_name = list(event.keys())[0]
            state_delta = event[node_name]
            
            print(f"🟢 [Node Complete] -> {node_name.upper()}")
            
            if state_delta.get("error"):
                print(f"   ❌ Error: {state_delta['error']}")
                return
            
            # Print node-specific outputs for clarity
            if node_name == "planner":
                print(f"   • Direction: {state_delta.get('research_direction')}")
                print(f"   • Generated Queries: {len(state_delta.get('queries', []))} items")
                print(f"   • Subtopics: {state_delta.get('subtopics')}")
            elif node_name == "search":
                print(f"   • Raw Sources Found: {len(state_delta.get('raw_sources', []))} items")
            elif node_name == "validator":
                print(f"   • Validated Sources: {len(state_delta.get('validated_sources', []))} items")
            elif node_name == "extractor":
                print(f"   • Key Findings Extracted: {len(state_delta.get('findings', []))} items")
            elif node_name == "synthesizer":
                print(f"   • Report generated successfully!")
            
            print("-" * 60)

        # Retrieve the final completed state
        print("Gathering final compiled state...")
        final_state = await research_graph.ainvoke(initial_state)
        report_preview = final_state.get("report_markdown", "")
        
        print("\n" + "=" * 60)
        print("🎉 Graph execution finished successfully!")
        print("=" * 60)
        
        if report_preview:
            preview_lines = report_preview.strip().split("\n")[:15]
            print("📝 Report Preview (First 15 lines):")
            print("-" * 60)
            print("\n".join(preview_lines))
            print("...")
            print("-" * 60)
        else:
            print("❌ No report markdown was generated.")
            
    except Exception as e:
        print(f"\n❌ Execution Failed with exception: {e}")
        print("Check if you have internet access and valid API keys.")

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
