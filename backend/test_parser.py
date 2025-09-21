from utils import ParserUtil, LogFilter

if __name__ == "__main__":
    logs = ParserUtil.parse_ndjson("sample.ndjson")
    print("Total records:", len(logs))
    if logs:
        print("First normalized record: ", logs[1],  "\n")

    prompt = "cart service crashing db timeout"
    filtered = LogFilter.filter_logs(logs, prompt, limit=150)

    # peek
    for r in filtered[:3]:
        print(r["_score"], r.get("containerName"), "->", r.get("log", "")[:80])
