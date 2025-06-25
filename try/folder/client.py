
import requests
import json
from logger import save_to_pdf, sanitize_text  

MCP_SERVER_URL = "https://f157-2405-201-6806-f03e-6844-38b1-1f36-2b6b.ngrok-free.app/invoke"

def main():
    print(" MCP Client (Educational Assistant)")
    question = input("Enter your question: ").strip()
    context = {}

    payload = {
        "input": question,
        "context": context
    }

    print("\n⏳ Sending request to MCP Tool Server...")
    try:
        response = requests.post(
            MCP_SERVER_URL,
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload)
        )

        if response.status_code == 200:
            result = response.json()
            output = result.get("output", "")

            # Clean output to prevent PDF encoding issues
            clean_output = sanitize_text(output)

            print("\n✅ Final Agent Answer:\n")
            if "Final Agent Answer" in clean_output:
                full_answer_block = clean_output.split("Final Agent Answer:")[-1].split("Full Scraped Content")[0].strip()
                print(full_answer_block)
            else:
                print(clean_output)

            with open("mcp_output.txt", "w", encoding="utf-8") as f:
                f.write(output)
                print("📝 Full output saved to 'mcp_output.txt'.")

            save_to_pdf(output, filename="mcp_output.pdf", question=question)

        else:
            print(f"❌ Server returned status code {response.status_code}")
            print(response.text)

    except Exception as e:
        print(f"❌ Error communicating with MCP server: {e}")

if __name__ == "__main__":
    main()
