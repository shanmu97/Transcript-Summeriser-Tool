from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import FileResponse
from PyPDF2 import PdfReader
from fpdf import FPDF
import tempfile
import os
import re
from fastapi.middleware.cors import CORSMiddleware 
from dotenv import load_dotenv
load_dotenv()
import uvicorn

# Import your GenAI client setup here
# from google import genai

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins="*",  # List of allowed origins (or "*" for all origins)
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods
    allow_headers=["*"],  # Allows all headers
)
GOOGLE_API_KEY = os.environ["GOOGLE_API_KEY"] # Replace with your actual API key
MODEL_ID = "models/gemini-2.0-flash-exp"

def extract_text_from_pdf(file_path):
    text = ""
    with open(file_path, 'rb') as file:
        reader = PdfReader(file)
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text
    return text

def setup_genai_client(api_key):
    # Replace with your actual GenAI client setup
    import google.genai as genai
    return genai.Client(api_key=api_key)

def generate_summary(client, model_id, pdf_text):
    prompt = (
        f"Here is a meeting transcript:\n{pdf_text}\n\n"
        "Please summarize this transcript as if someone at the meeting is telling someone outside the meeting. "
        "Highlight what specific people said and provide the conclusion of the meeting clearly."
        "Generate all the precise Key Takeaways from the meeting with precise subheading for each key takeaway."
        "don't use these kind of lines 'as if someone who attended is telling someone who didn't:'"
        "provide the assigned work for each participant mentioned in the meeting. Use the section header `Assigned Work` to present the tasks assigned to individuals."
        "Don't use bullet points before person name. Bold the person name only in assigned work section and donot make bold in other sections. Add name, works in new lines."
        "Make section titles bold."
    )
    response = client.models.generate_content(
        model=model_id,
        contents=[prompt]
    )
    return response.text

def sanitize_text(text):
    replacements = {
        '\u2019': "'", '\u2018': "'", '\u201c': '"', '\u201d': '"',
        '\u2013': '-', '\u2014': '-', '\u2026': '...'
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    return text

def save_formatted_summary(summary, output_file_path):
    summary = sanitize_text(summary)
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.set_font("Arial", "B", size=18)
    pdf.cell(200, 10, txt="Meeting Summary", ln=True, align='C')
    pdf.ln(10)
    lines = summary.strip().split('\n')
    for line in lines:
        line = line.strip()
        if "John:" in line:
            pdf.set_font("Arial", style="B", size=12)
            pdf.multi_cell(0, 10, line.strip())
        elif line.startswith('####'):
            pdf.set_font("Arial", style="B", size=12)
            pdf.multi_cell(0, 10, line.replace("####", "").strip())
        elif line.startswith('###'):
            pdf.set_font("Arial", style="B", size=18)
            pdf.multi_cell(0, 10, line.replace("###", "").strip())
        elif line.startswith('**') and line.endswith('**'):
            pdf.set_font("Arial", style="B", size=14)
            pdf.multi_cell(0, 10, line.replace("**", "").strip())
        elif line.endswith(':'):
            pdf.set_font("Arial", style="B", size=13)
            pdf.multi_cell(0, 10, line.strip())
        elif line == "":
            pdf.ln(5)
        else:
            pdf.set_font("Arial", style="", size=12)
            pdf.multi_cell(0, 10, line)
    pdf.set_font("Arial", style="B", size=14)
    pdf.ln(10)
    pdf.cell(200, 10, txt="End of Summary", ln=True, align='C')
    pdf.output(output_file_path)

@app.post("/summarize/")
async def summarize_meeting(file: UploadFile = File(...)):
    # Save uploaded PDF to a temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    try:
        # Extract text
        pdf_text = extract_text_from_pdf(tmp_path)
        if not pdf_text:
            raise HTTPException(status_code=400, detail="Could not extract text from PDF.")
        # Generate summary
        client = setup_genai_client(GOOGLE_API_KEY)
        summary = generate_summary(client, MODEL_ID, pdf_text)
        # Save summary to PDF
        output_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        output_pdf.close()
        save_formatted_summary(summary, output_pdf.name)
        # Return the PDF as a download
        return FileResponse(output_pdf.name, filename="meeting_summary.pdf", media_type="application/pdf")
    finally:
        os.unlink(tmp_path)
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))  # Use PORT env variable, default to 10000
    uvicorn.run("main:app", host="0.0.0.0", port=port)