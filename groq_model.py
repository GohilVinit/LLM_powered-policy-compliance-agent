
import os
import openai
from dotenv import load_dotenv

load_dotenv()

openai.api_key = os.getenv("GROQ_API_KEY")
openai.api_base = "https://api.groq.com/openai/v1"  # Groq base URL

def run_completion(prompt):
    response = openai.ChatCompletion.create(
        model="llama3-70b-8192",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.05,
        max_tokens=1200,
        top_p=0.9,
        frequency_penalty=0.0,
        presence_penalty=0.0,
        stop=None
    )
    raw_response = response['choices'][0]['message']['content']
    return raw_response