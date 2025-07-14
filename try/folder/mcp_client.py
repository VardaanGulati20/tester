import requests
import json

# 🧭 MCP Registry Config
REGISTRY_URL = "http://localhost:9000"
ENTRY_TAG = "entry"  # This should match the tag in mcp_server.py's AGENT_CARD

# 🌐 Resolve the MCP Server /ask endpoint
def resolve_entrypoint():
    try:
        res = requests.get(f"{REGISTRY_URL}/resolve", params={"tag": ENTRY_TAG})
        return res.json().get("endpoints", {}).get("ask")
    except Exception as e:
        print(f"❌ Failed to resolve entrypoint from registry: {e}")
        return None

def main():
    SERVER_URL = resolve_entrypoint()
    if not SERVER_URL:
        print("❌ No server found from registry.")
        return

    # 🧾 Ask user a question
    question = input("🗨️  Ask a question: ") or "Give me a lesson plan on software testing"
    intent = "improve_answer"

    try:
        print("\n📡 Sending to MCP Server...")
        response = requests.post(
            SERVER_URL,
            json={"question": question, "intent": intent},
            timeout=300
        )
        data = response.json()

        # ✅ Final Answer
        final_answer = data.get("answer", "[No answer returned]")
        print("\n✅ Final Answer:\n")
        print(final_answer)

        # 🧠 Display Trace
        print("\n🧪 Pipeline Trace:")
        trace = data.get("pipeline_trace", [])
        for i, step in enumerate(trace):
            print(f"\n🔧 Step {i+1} - Tool: {step.get('tool')}")
            for k, v in step.items():
                if k != "tool":
                    print(f"   • {k}: {str(v)[:400]}{'...' if len(str(v)) > 400 else ''}")

    except Exception as e:
        print(f"❌ Request failed: {e}")

if __name__ == "__main__":
    main()
