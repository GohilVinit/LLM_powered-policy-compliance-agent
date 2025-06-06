import os
import openai
import docx
import json
from dotenv import load_dotenv
import groq_model

def clean_response(response):
    cleaned = response.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned.replace("```json", "").replace("```", "").strip()
    elif cleaned.startswith("```"):
        cleaned = cleaned.replace("```", "").strip()
    return cleaned

def load_docx_text(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Document not found: {path}")
    doc = docx.Document(path)
    text = "\n".join([para.text for para in doc.paragraphs if para.text.strip()])
    if not text:
        raise ValueError(f"Document is empty: {path}")
    return text

def extract_structured_sections(doc_path, source_name=""):
    text = load_docx_text(doc_path)
    prompt = f"""You are a Policy Extractor AI. Your task is to extract information from the provided policy text and return it in a structured JSON format. The JSON must be valid, with no markdown, code blocks, or extra text. The structure should be a list of sections, where each section follows this format:

[
  {{
    "topic_name": "Concise section title",
    "full_paragraph": "The complete text of this section from the document.",
    "keywords": ["keyword1", "keyword2", "keyword3"]
  }},
  ...
]

Policy text:
{text}

Return only the JSON list, nothing else. Ensure the JSON is properly formatted and valid."""
    
    response = groq_model.run_completion(prompt)
    try:
        cleaned_response = clean_response(response)
        return json.loads(cleaned_response)
    except json.JSONDecodeError as e:
        print(f"⚠️ JSON parsing failed for {source_name or doc_path}: {e}")
        print(f"Raw response: {response}")
        with open(f"llm_output_{source_name or 'unknown'}.txt", "w", encoding="utf-8") as f:
            f.write(response)
        raise

def process_and_save(doc_path, json_filename, source_name):
    data = extract_structured_sections(doc_path, source_name)
    if data:
        with open(json_filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print(f"💾 Saved structured data to {json_filename}")
    else:
        print(f"⚠️ Skipped saving JSON for {source_name} due to parsing error.")