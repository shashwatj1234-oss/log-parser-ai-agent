import React, { useState } from "react";

function App() {
  const [file, setFile] = useState(null);
  const [prompt, setPrompt] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file || !prompt) return alert("Please select a file and enter a prompt");

    const formData = new FormData();
    formData.append("file", file);
    formData.append("prompt", prompt);

    setLoading(true);
    setResult(null);

    try {
      const res = await fetch("http://localhost:8000/analyze", {
        method: "POST",
        body: formData,
      });
      const data = await res.json();
      setResult(data);
    } catch (err) {
      console.error(err);
      alert("Error calling API");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: "2rem", fontFamily: "Arial, sans-serif" }}>
      <h2>Log Analyzer</h2>
      <form onSubmit={handleSubmit} style={{ marginBottom: "1rem" }}>
        <input type="file" accept=".ndjson,.json" onChange={handleFileChange} />
        <br /><br />
        <input
          type="text"
          placeholder="Enter your prompt"
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          style={{ width: "300px" }}
        />
        <br /><br />
        <button type="submit" disabled={loading}>
          {loading ? "Analyzing..." : "Analyze Logs"}
        </button>
      </form>

      {result && (
        <div>
          <h3>Analysis Result</h3>
          <pre style={{ background: "#f4f4f4", padding: "1rem" }}>
            {JSON.stringify(result, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}

export default App;
