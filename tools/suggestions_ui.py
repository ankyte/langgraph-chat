from predictive_chat import suggest_followups

if __name__ == "__main__":
    query = input("Ask a fund-related question: ")
    suggestions = suggest_followups(query)

    print("\nSuggested follow-up questions:")
    for s in suggestions:
        print("-", s.strip("-• "))