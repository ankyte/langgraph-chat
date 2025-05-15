from predictive_chat import suggest_followups

if __name__ == "__main__":
    query = "Ask a fund-related question"
    suggestions = suggest_followups(query)
    print(suggestions)
    
    for s in suggestions:
        print("-", s.strip("-• "))