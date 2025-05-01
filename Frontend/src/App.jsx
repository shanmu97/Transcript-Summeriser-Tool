import React, { useState } from "react";
import "./App.css";

function App() {
  const [file, setFile] = useState(null);
  const [summaryText, setSummaryText] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [isDarkMode, setIsDarkMode] = useState(false);

  // Handle file selection
  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
    setError("");
  };


  // Optional: Handle text input change (if you want to use your Input component for other inputs)
  const handleInputChange = (value) => {
    setSummaryText(value);
  };

  // Upload PDF and get summarized PDF
  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!file) {
      setError("Please upload a PDF file.");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await fetch("https://transcript-summeriser-tool.onrender.com/summarize/", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Error: ${response.statusText}`);
      }

      // Get blob from response (PDF file)
      const blob = await response.blob();

      // Create a URL for the blob and download it
      const url = window.URL.createObjectURL(new Blob([blob]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", "meeting_summary.pdf");
      document.body.appendChild(link);
      link.click();
      link.parentNode.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError(err.message || "Something went wrong!");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-full mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6 text-center">Transcriptify</h1>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label
            htmlFor="pdfFile"
            className="block mb-2 font-semibold text-center"
          >
            Upload PDF File
          </label>
          <input
            type="file"
            required
            id="pdfFile"
            accept="application/pdf"
            onChange={handleFileChange}
            className="block w-1/7 text-sm text-gray-900 border border-gray-300 rounded-md cursor-pointer focus:outline-none focus:ring-2 focus:ring-blue-500 mx-auto"
          />
        </div>

        {/* Example usage of your Input component */}
        {/* <Input
          type="text"
          placeholder="Optional input"
          onChange={handleInputChange}
          id="optionalInput"
          name="optionalInput"
        /> */}

        <button
          type="submit"
          disabled={loading}
          className="w-3xl bg-gray-600 text-white py-2 rounded-md hover:bg-black disabled:opacity-50 block mx-auto"
        >
          {loading ? "Generating Summary..." : "Generate Summary"}
        </button>
      </form>

      {error && <p className="mt-4 text-red-600 font-semibold">{error}</p>}
    </div>
  );
}

export default App;
