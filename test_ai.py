from ai import ask_ai

while True:
    user_input = input("You: ")

    if user_input.lower() == "exit":
        break

    reply = ask_ai(user_input)

    print("\nAI:", reply)
    print("-" * 50)