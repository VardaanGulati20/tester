import requests
from logger import sanitize_text, save_to_pdf

def ask_question(question):
    try:
        response = requests.post(
            "http://localhost:8000/invoke",
            json={"input": question}
        )
        result = response.json()
    except Exception as e:
        print(f"❌ Failed to reach MCP server: {e}")
        return

    if "error" in result:
        print(f"❌ MCP Server Error: {result['error']}")
        return

    
    initial_answer = result.get("initial_answer", "")
    critic_feedback_1 = result.get("critic_feedback_1", "")
    final_answer = result.get("final_answer", "")
    critic_feedback_2 = result.get("critic_feedback_2", "")
    score_1 = result.get("score_1", 0)
    score_2 = result.get("score_2", 0)

    print("\n--- MCP Educational Assistant Output ---")
    print(f"\n📌 Question:\n{question}")
    print(f"\n📖 Initial Answer:\n{initial_answer}")
    print(f"\n🧠 Critic Feedback (Initial Answer):\n{critic_feedback_1} (Score: {score_1})")
    print(f"\n✅ Final Improved Answer:\n{final_answer}")
    print(f"\n🧠 Critic Feedback (Final Answer):\n{critic_feedback_2} (Score: {score_2})")

    
    sections = {
        "Question": sanitize_text(question),
        "Initial Answer": sanitize_text(initial_answer),
        "Critic Feedback (Initial Answer)": sanitize_text(f"{critic_feedback_1} (Score: {score_1})"),
        "Final Improved Answer": sanitize_text(final_answer),
        "Critic Feedback (Final Answer)": sanitize_text(f"{critic_feedback_2} (Score: {score_2})"),
    }

    save_to_pdf(sections, filename="mcp_output.pdf")

if __name__ == "__main__":
    user_question = input("Enter your educational question: ")
    ask_question(user_question)
