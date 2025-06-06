
# import sys
# import os
# import json
# import logging
# from fastapi import FastAPI, File, UploadFile, HTTPException
# from fastapi.responses import JSONResponse
# from fastapi.middleware.cors import CORSMiddleware
# from extract_sections import extract_structured_sections
# from check_compliance import check_compliance_with_milvus
# from store_milvus import store_in_milvus
# from generate_questions import generate_questions_from_policy
# from pydantic import BaseModel

# # Configure logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# app = FastAPI()

# # Enable CORS for frontend communication
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],  # Update with your frontend URL in production
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # Ensure data directory exists
# os.makedirs("../ui/data", exist_ok=True)

# latest_bank_json = None
# latest_vendor_json = None

# # Helper function to check if file exists and load JSON
# @app.get("/list-json-files/")
# async def list_json_files():
#     """
#     Return a list of all JSON files in the 'data' folder.
#     """
#     try:
#         # Get all .json files from the data folder
#         json_files = [f for f in os.listdir("../ui/data") if f.endswith(".json")]
#         print(f"Found JSON files: {json_files}")  # Debugging line
#         if not json_files:
#             return {"json_files": []}  # Return empty array if no files are found

#         return {"json_files": json_files}

#     except Exception as e:
#         logger.error(f"Error fetching JSON files: {str(e)}")
#         raise HTTPException(status_code=500, detail=f"Error fetching JSON files: {str(e)}")


# @app.post("/upload-policy/")
# async def upload_policy(file: UploadFile = File(...), is_bank: bool = False):
#     """
#     Upload a policy document (.docx), process it into JSON, and store it in Milvus.
#     """
#     logger.debug(f"Received file: {file.filename}, is_bank: {is_bank}")
    
#     try:
#         # Validate file type
#         if not file.filename.endswith(".docx"):
#             raise HTTPException(status_code=400, detail="Only .docx files are supported")

#         # Save uploaded file to 'data' directory
#         file_path = os.path.join("../ui/data", file.filename)
#         with open(file_path, "wb") as f:
#             f.write(await file.read())
#         logger.info(f"Uploaded file saved: {file_path}")

#         # Generate JSON filename based on the original file name (without suffix)
#         base_filename = os.path.splitext(file.filename)[0]  # Remove .docx extension
#         json_filename = f"{base_filename}.json"
        
#         # Extract structured sections
#         data = extract_structured_sections(file_path, base_filename)
#         logger.info(f"Extracted structured sections from {file.filename}")

#         # Save extracted data as JSON file
#         json_path = os.path.join("../ui/data", json_filename)
#         with open(json_path, "w", encoding="utf-8") as f:
#             json.dump(data, f, indent=2)
#         logger.info(f"JSON file created: {json_path}")

#         # Store in Milvus
#         collection_name = base_filename.replace(" ", "_").lower()
#         store_in_milvus(json_path, collection_name)
#         logger.info(f"Data stored in Milvus collection: {collection_name}")

#         # Update latest policy JSON (depending on whether it's bank or vendor)
#         global latest_bank_json, latest_vendor_json
#         if is_bank:
#             latest_bank_json = json_filename
#         else:
#             latest_vendor_json = json_filename

#         return {
#             "message": f"File '{file.filename}' successfully uploaded, processed, and stored in Milvus collection '{collection_name}'",
#             "json_file": json_filename,
#             "milvus_collection": collection_name
#         }

#     except Exception as e:
#         logger.error(f"Error processing file '{file.filename}': {e}", exc_info=True)
#         raise HTTPException(status_code=500, detail=f"Error processing file '{file.filename}': {str(e)}")


# class GenerateQuestionsRequest(BaseModel):
#     json_file: str

# def load_json_from_file(file_path: str):
#     """
#     Load and return a JSON file from the specified path.
#     """
#     with open(file_path, "r", encoding="utf-8") as f:
#         return json.load(f)

# @app.post("/generate-questions/")
# async def generate_questions(request: GenerateQuestionsRequest):
#     """
#     Generate compliance questions from the selected bank policy JSON.
#     """
#     try:
#         json_filename = request.json_file
#         if not json_filename:
#             raise HTTPException(status_code=400, detail="No JSON file provided")

#         # Define paths for the input JSON and the generated questions JSON
#         json_path = os.path.join("../ui/data", json_filename)
#         base_name = os.path.splitext(json_filename)[0]
#         questions_filename = f"{base_name}_questions.json"
#         questions_path = os.path.join("../ui/data", questions_filename)
#         default_output_path = os.path.join("../ui/data", "bank_questions.json")

#         # Try to generate questions
#         try:
#             generate_questions_from_policy(json_path, output_path=default_output_path)
#             logger.info(f"Questions generated and saved to '{default_output_path}'")

#             # After generation, move/rename the 'bank_questions.json' to the specific output file
#             if os.path.exists(default_output_path):
#                 os.rename(default_output_path, questions_path)
#                 logger.info(f"Renamed 'bank_questions.json' to '{questions_filename}'")
#             else:
#                 logger.error(f"Default output file not found: {default_output_path}")
#                 raise HTTPException(status_code=500, detail="Failed to find generated questions file.")

#         except Exception as e:
#             logger.error(f"Error generating questions: {e}")
#             # Create an empty questions file in case of generation error
#             with open(questions_path, "w", encoding="utf-8") as f:
#                 json.dump({}, f, indent=2)
#             logger.info(f"Created empty questions file due to generation error.")

#         # Load and return the generated questions from the file
#         questions = load_json_from_file(questions_path)
#         return {
#             "message": f"Questions generated from '{json_filename}'",
#             "questions_file": questions_filename,
#             "questions": questions
#         }

#     except Exception as e:
#         logger.error(f"Unexpected error in generate_questions: {e}")
#         raise HTTPException(status_code=500, detail=str(e))
    
# @app.get("/compliance-results/")
# async def get_compliance_results():
#     """
#     Get the compliance results from the file generated by the compliance check.
#     """
#     check_compliance_with_milvus()
#     try:
#         # Read the results from the compliance check JSON file
#         with open("compliance_results_milvus.json", "r") as f:
#             results = json.load(f)

#         return JSONResponse(content=results)

#     except FileNotFoundError:
#         raise HTTPException(status_code=404, detail="Compliance results not found.")
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

# @app.get("/get-file-content/")
# async def get_file_content(filename: str):
#     """
#     Fetch and return the content of the specified JSON file, cleaning malformed question arrays if necessary.
#     """
#     try:
#         if not filename.endswith(".json"):
#             raise HTTPException(status_code=400, detail="Only JSON files are supported")

#         file_path = os.path.join("../ui/data", filename)
#         if not os.path.exists(file_path):
#             raise HTTPException(status_code=404, detail=f"File '{filename}' not found")

#         with open(file_path, "r", encoding="utf-8") as f:
#             content = json.load(f)

#         logger.info(f"Loaded file '{filename}' with type: {type(content).__name__}")

#         # Clean malformed question arrays in questions JSON
#         if isinstance(content, dict) and filename.endswith("_questions.json"):
#             logger.info(f"Cleaning questions JSON for '{filename}'")
#             for topic, questions in content.items():
#                 if isinstance(questions, list) and questions:
#                     cleaned_questions = []
#                     for q in questions:
#                         if isinstance(q, str):
#                             # Check if the string is a JSON array of questions
#                             if q.strip().startswith("[") and q.strip().endswith("]"):
#                                 try:
#                                     # Parse the JSON-like string as a list
#                                     parsed = json.loads(q)
#                                     if isinstance(parsed, list):
#                                         # Add each parsed question, cleaning artifacts
#                                         for pq in parsed:
#                                             cleaned = pq.strip().strip('"').strip(',').strip()
#                                             if cleaned:
#                                                 cleaned_questions.append(cleaned)
#                                     else:
#                                         # Not a list, treat as single question
#                                         cleaned = q.strip('[').strip(']').strip('"').strip(',').strip()
#                                         if cleaned:
#                                             cleaned_questions.append(cleaned)
#                                 except json.JSONDecodeError:
#                                     # Fallback: treat as single question, clean artifacts
#                                     cleaned = q.strip('[').strip(']').strip('"').strip(',').strip()
#                                     if cleaned:
#                                         cleaned_questions.append(cleaned)
#                             else:
#                                 # Single question, clean artifacts
#                                 cleaned = q.strip('[').strip(']').strip('"').strip(',').strip()
#                                 if cleaned:
#                                     cleaned_questions.append(cleaned)
#                         else:
#                             logger.warning(f"Unexpected question format for topic '{topic}': {q}")
#                             cleaned_questions.append(str(q))
#                     content[topic] = cleaned_questions
#                     logger.info(f"Cleaned questions for topic '{topic}': {cleaned_questions}")
#                 else:
#                     logger.warning(f"Invalid questions format for topic '{topic}': {questions}")
#                     content[topic] = []

#         logger.info(f"Returning cleaned content for '{filename}': {json.dumps(content, indent=2)}")
#         return content

#     except Exception as e:
#         logger.error(f"Error fetching file '{filename}': {str(e)}", exc_info=True)
#         raise HTTPException(status_code=500, detail=f"Error fetching file '{filename}': {str(e)}")


import sys
import os
import json
import logging
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from extract_sections import extract_structured_sections
from check_compliance import check_compliance_with_milvus
from store_milvus import store_in_milvus
from generate_questions import generate_questions_from_policy
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Enable CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure data directory exists
os.makedirs("../ui/data", exist_ok=True)

latest_bank_json = None
latest_vendor_json = None

@app.get("/list-json-files/")
async def list_json_files():
    """
    Return a list of all JSON files in the 'data' folder.
    """
    try:
        json_files = [f for f in os.listdir("../ui/data") if f.endswith(".json")]
        print(f"Found JSON files: {json_files}")
        if not json_files:
            return {"json_files": []}

        return {"json_files": json_files}

    except Exception as e:
        logger.error(f"Error fetching JSON files: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching JSON files: {str(e)}")

@app.post("/upload-policy/")
async def upload_policy(file: UploadFile = File(...), is_bank: bool = False):
    """
    Upload a policy document (.docx), process it into JSON, and store it in Milvus.
    """
    logger.debug(f"Received file: {file.filename}, is_bank: {is_bank}")
    
    try:
        if not file.filename.endswith(".docx"):
            raise HTTPException(status_code=400, detail="Only .docx files are supported")

        file_path = os.path.join("../ui/data", file.filename)
        with open(file_path, "wb") as f:
            f.write(await file.read())
        logger.info(f"Uploaded file saved: {file_path}")

        base_filename = os.path.splitext(file.filename)[0]
        json_filename = f"{base_filename}.json"
        
        data = extract_structured_sections(file_path, base_filename)
        logger.info(f"Extracted structured sections from {file.filename}")

        json_path = os.path.join("../ui/data", json_filename)
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        logger.info(f"JSON file created: {json_path}")

        collection_name = base_filename.replace(" ", "_").lower()
        store_in_milvus(json_path, collection_name)
        logger.info(f"Data stored in Milvus collection: {collection_name}")

        global latest_bank_json, latest_vendor_json
        if is_bank:
            latest_bank_json = json_filename
        else:
            latest_vendor_json = json_filename

        return {
            "message": f"File '{file.filename}' successfully uploaded, processed, and stored in Milvus collection '{collection_name}'",
            "json_file": json_filename,
            "milvus_collection": collection_name
        }

    except Exception as e:
        logger.error(f"Error processing file '{file.filename}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing file '{file.filename}': {str(e)}")

class GenerateQuestionsRequest(BaseModel):
    json_file: str

def load_json_from_file(file_path: str):
    """
    Load and return a JSON file from the specified path.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

@app.post("/generate-questions/")
async def generate_questions(request: GenerateQuestionsRequest):
    """
    Generate compliance questions from the selected bank policy JSON.
    """
    try:
        json_filename = request.json_file
        if not json_filename:
            raise HTTPException(status_code=400, detail="No JSON file provided")

        json_path = os.path.join("../ui/data", json_filename)
        base_name = os.path.splitext(json_filename)[0]
        questions_filename = f"{base_name}_questions.json"
        questions_path = os.path.join("../ui/data", questions_filename)
        default_output_path = os.path.join("../ui/data", "bank_questions.json")

        try:
            generate_questions_from_policy(json_path, output_path=default_output_path)
            logger.info(f"Questions generated and saved to '{default_output_path}'")

            if os.path.exists(default_output_path):
                os.rename(default_output_path, questions_path)
                logger.info(f"Renamed 'bank_questions.json' to '{questions_filename}'")
            else:
                logger.error(f"Default output file not found: {default_output_path}")
                raise HTTPException(status_code=500, detail="Failed to find generated questions file.")

        except Exception as e:
            logger.error(f"Error generating questions: {e}")
            with open(questions_path, "w", encoding="utf-8") as f:
                json.dump({}, f, indent=2)
            logger.info(f"Created empty questions file due to generation error.")

        questions = load_json_from_file(questions_path)
        return {
            "message": f"Questions generated from '{json_filename}'",
            "questions_file": questions_filename,
            "questions": questions
        }

    except Exception as e:
        logger.error(f"Unexpected error in generate_questions: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/compliance-results/")
async def get_compliance_results():
    """
    Get the compliance results from the file generated by the compliance check.
    """
    check_compliance_with_milvus()
    try:
        # Read the results from the compliance check JSON file
        with open("../compliance_results_milvus.json", "r") as f:
            results = json.load(f)

        return JSONResponse(content=results)

    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Compliance results not found.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/get-file-content/")
async def get_file_content(filename: str):
    """
    Fetch and return the content of the specified JSON file, cleaning malformed question arrays if necessary.
    """
    try:
        if not filename.endswith(".json"):
            raise HTTPException(status_code=400, detail="Only JSON files are supported")

        file_path = os.path.join("../ui/data", filename)
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail=f"File '{filename}' not found")

        with open(file_path, "r", encoding="utf-8") as f:
            content = json.load(f)

        logger.info(f"Loaded file '{filename}' with type: {type(content).__name__}")

        if isinstance(content, dict) and filename.endswith("_questions.json"):
            logger.info(f"Cleaning questions JSON for '{filename}'")
            for topic, questions in content.items():
                if isinstance(questions, list) and questions:
                    cleaned_questions = []
                    for q in questions:
                        if isinstance(q, str):
                            if q.strip().startswith("[") and q.strip().endswith("]"):
                                try:
                                    parsed = json.loads(q)
                                    if isinstance(parsed, list):
                                        for pq in parsed:
                                            cleaned = pq.strip().strip('"').strip(',').strip()
                                            if cleaned:
                                                cleaned_questions.append(cleaned)
                                    else:
                                        cleaned = q.strip('[').strip(']').strip('"').strip(',').strip()
                                        if cleaned:
                                            cleaned_questions.append(cleaned)
                                except json.JSONDecodeError:
                                    cleaned = q.strip('[').strip(']').strip('"').strip(',').strip()
                                    if cleaned:
                                        cleaned_questions.append(cleaned)
                            else:
                                cleaned = q.strip('[').strip(']').strip('"').strip(',').strip()
                                if cleaned:
                                    cleaned_questions.append(cleaned)
                        else:
                            logger.warning(f"Unexpected question format for topic '{topic}': {q}")
                            cleaned_questions.append(str(q))
                    content[topic] = cleaned_questions
                    logger.info(f"Cleaned questions for topic '{topic}': {cleaned_questions}")
                else:
                    logger.warning(f"Invalid questions format for topic '{topic}': {questions}")
                    content[topic] = []

        logger.info(f"Returning cleaned content for '{filename}': {json.dumps(content, indent=2)}")
        return content

    except Exception as e:
        logger.error(f"Error fetching file '{filename}': {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching file '{filename}': {str(e)}")