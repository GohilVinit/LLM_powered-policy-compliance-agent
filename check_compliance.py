

# import json
# import logging
# from groq_model import run_completion
# from embed_policy import embed_policy_text
# from pymilvus import Collection, connections, utility, CollectionSchema, FieldSchema, DataType
# import numpy as np

# # Configure logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# def create_collection(collection_name, json_file_path):
#     """Create a Milvus collection and populate it with data from the JSON file if it doesn't exist."""
#     if utility.has_collection(collection_name):
#         logger.info(f"Collection '{collection_name}' already exists.")
#         return Collection(name=collection_name)

#     logger.info(f"Creating collection '{collection_name}'...")
#     # Define schema (match store_milvus.py)
#     fields = [
#         FieldSchema(name="topic_name", dtype=DataType.VARCHAR, max_length=512, is_primary=True),
#         FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=768),
#         FieldSchema(name="full_paragraph", dtype=DataType.VARCHAR, max_length=5000)
#     ]
#     schema = CollectionSchema(fields=fields, description=f"{collection_name} policy schema")
#     collection = Collection(name=collection_name, schema=schema)

#     # Create index (match store_milvus.py)
#     index_params = {
#         "metric_type": "L2",
#         "index_type": "IVF_FLAT",
#         "params": {"nlist": 128}
#     }
#     collection.create_index(field_name="embedding", index_params=index_params)

#     # Load data from JSON file
#     with open(json_file_path, "r", encoding="utf-8") as f:
#         policy_data = json.load(f)

#     if not isinstance(policy_data, list):
#         logger.error(f"Invalid JSON format in {json_file_path}. Expected a list.")
#         return collection

#     embeddings = []
#     topic_names = []
#     full_paragraphs = []

#     for item in policy_data:
#         full_paragraph = item.get("full_paragraph", "")
#         topic_name = item.get("topic_name", "Unknown Topic")
#         if full_paragraph:
#             embedding = embed_policy_text([full_paragraph])[0]
#             embeddings.append(embedding)
#             topic_names.append(topic_name)
#             full_paragraphs.append(full_paragraph)

#     # Insert data into Milvus
#     collection.insert([topic_names, full_paragraphs, embeddings])
#     collection.load()
#     logger.info(f"Populated collection '{collection_name}' with {len(embeddings)} entries.")
#     return collection

# def search_milvus(collection_name, query_embedding, top_k=1):
#     """Search Milvus for most relevant paragraph based on embedding."""
#     if collection_name == "bank_policy":
#         json_file_path = "../ui/data/Bank_Policy.json"
#     elif collection_name == "vendor_policy":
#         json_file_path = "../ui/data/Vendor_Policy.json"
#     else:
#         raise ValueError(f"Unknown collection name: {collection_name}")

#     collection = create_collection(collection_name, json_file_path)

#     search_params = {"metric_type": "L2", "params": {"nprobe": 10}}

#     results = collection.search(
#         data=[query_embedding],
#         anns_field="embedding",
#         param=search_params,
#         limit=top_k,
#         output_fields=["topic_name", "full_paragraph"]
#     )
#     hits = results[0]
#     if hits:
#         return hits[0].entity.get("full_paragraph")
#     return ""

# def clean_questions(question_list):
#     """Clean malformed question arrays into a list of individual questions."""
#     cleaned_questions = []
#     for q in question_list:
#         if isinstance(q, str):
#             # Handle JSON-encoded strings like "[question1, question2]"
#             if q.strip().startswith("[") and q.strip().endswith("]"):
#                 try:
#                     parsed = json.loads(q)
#                     if isinstance(parsed, list):
#                         for pq in parsed:
#                             cleaned = pq.strip().strip('"').strip(',').strip()
#                             if cleaned:
#                                 cleaned_questions.append(cleaned)
#                     else:
#                         cleaned = q.strip('[').strip(']').strip('"').strip(',').strip()
#                         if cleaned:
#                             cleaned_questions.append(cleaned)
#                 except json.JSONDecodeError:
#                     cleaned = q.strip('[').strip(']').strip('"').strip(',').strip()
#                     if cleaned:
#                         cleaned_questions.append(cleaned)
#             else:
#                 # Handle individual questions with trailing commas or quotes
#                 cleaned = q.strip('[').strip(']').strip('"').strip(',').strip()
#                 if cleaned:
#                     cleaned_questions.append(cleaned)
#         else:
#             logger.warning(f"Unexpected question format: {q}")
#             cleaned_questions.append(str(q))
#     return cleaned_questions

# def check_compliance_with_milvus():
#     # Load question set
#     with open("../ui/data/Bank_Policy_questions.json") as f:
#         questions = json.load(f)

#     # Connect to Milvus
#     connections.connect(alias="default", host="localhost", port="19530")

#     results = {}

#     for topic, question_list in questions.items():
#         results[topic] = []

#         # Clean the question list to get individual questions
#         cleaned_questions = clean_questions(question_list)
#         logger.info(f"Cleaned questions for topic '{topic}': {cleaned_questions}")

#         for question in cleaned_questions:
#             # Generate embedding for the question
#             embedding = embed_policy_text([question])[0]

#             # Retrieve most relevant policy paragraphs from both bank & vendor collections
#             try:
#                 bank_paragraph = search_milvus("bank_policy", embedding)
#                 vendor_paragraph = search_milvus("vendor_policy", embedding)
#             except Exception as e:
#                 logger.error(f"Error searching Milvus for question '{question}': {e}")
#                 results[topic].append({
#                     "question": question,
#                     "error": f"Failed to retrieve policy paragraphs: {str(e)}"
#                 })
#                 continue

#             # Build LLM prompt
#             prompt = f"""
# You are a Compliance Auditor.

# Bank Policy: {bank_paragraph}

# Vendor Policy: {vendor_paragraph}

# Question: {question}

# Evaluate whether the vendor is compliant with the bank’s policy. Return a JSON:
# {{
#   "question": "{question}",
#   "answer_from_bank": "...",
#   "answer_from_vendor": "...",
#   "compliance_status": "Compliant/Non-Compliant/Partially Compliant",
#   "reference_bank": "...",
#   "reference_vendor": "..."
# }}
#             """

#             # Run completion (now returns a parsed JSON dict)
#             try:
#                 parsed = run_completion(prompt)
#                 results[topic].append(parsed)
#             except Exception as e:
#                 print(f"⚠️ Failed to get valid response for: {question}, error: {e}")
#                 results[topic].append({
#                     "question": question,
#                     "error": f"Failed to get valid response from LLM: {str(e)}"
#                 })

#     with open("../ui/data/compliance_results_milvus.json", "w") as f:
#         json.dump(results, f, indent=2)

# if __name__ == "__main__":
#     check_compliance_with_milvus()




import json
import logging
from groq_model import run_completion
from embed_policy import embed_policy_text
from pymilvus import Collection, connections, utility, CollectionSchema, FieldSchema, DataType
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_collection(collection_name, json_file_path):
    """Create a Milvus collection and populate it with data from the JSON file if it doesn't exist."""
    if utility.has_collection(collection_name):
        logger.info(f"Collection '{collection_name}' already exists.")
        return Collection(name=collection_name)

    logger.info(f"Creating collection '{collection_name}'...")
    # Define schema (match store_milvus.py)
    fields = [
        FieldSchema(name="topic_name", dtype=DataType.VARCHAR, max_length=512, is_primary=True),
        FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=768),
        FieldSchema(name="full_paragraph", dtype=DataType.VARCHAR, max_length=5000)
    ]
    schema = CollectionSchema(fields=fields, description=f"{collection_name} policy schema")
    collection = Collection(name=collection_name, schema=schema)

    # Create index (match store_milvus.py)
    index_params = {
        "metric_type": "L2",
        "index_type": "IVF_FLAT",
        "params": {"nlist": 128}
    }
    collection.create_index(field_name="embedding", index_params=index_params)

    # Load data from JSON file
    with open(json_file_path, "r", encoding="utf-8") as f:
        policy_data = json.load(f)

    if not isinstance(policy_data, list):
        logger.error(f"Invalid JSON format in {json_file_path}. Expected a list.")
        return collection

    embeddings = []
    topic_names = []
    full_paragraphs = []

    for item in policy_data:
        full_paragraph = item.get("full_paragraph", "")
        topic_name = item.get("topic_name", "Unknown Topic")
        if full_paragraph:
            embedding = embed_policy_text([full_paragraph])[0]
            embeddings.append(embedding)
            topic_names.append(topic_name)
            full_paragraphs.append(full_paragraph)

    # Insert data into Milvus
    collection.insert([topic_names, full_paragraphs, embeddings])
    collection.load()
    logger.info(f"Populated collection '{collection_name}' with {len(embeddings)} entries.")
    return collection

def search_milvus(collection_name, query_embedding, top_k=1):
    """Search Milvus for most relevant paragraph based on embedding."""
    if collection_name == "bank_policy":
        json_file_path = "../ui/data/Bank_Policy.json"
    elif collection_name == "vendor_policy":
        json_file_path = "../ui/data/Vendor_Policy.json"
    else:
        raise ValueError(f"Unknown collection name: {collection_name}")

    collection = create_collection(collection_name, json_file_path)

    search_params = {"metric_type": "L2", "params": {"nprobe": 10}}

    results = collection.search(
        data=[query_embedding],
        anns_field="embedding",
        param=search_params,
        limit=top_k,
        output_fields=["topic_name", "full_paragraph"]
    )
    hits = results[0]
    if hits:
        return hits[0].entity.get("full_paragraph")
    return ""

def clean_questions(question_list):
    """Clean malformed question arrays into a list of individual questions."""
    cleaned_questions = []
    for q in question_list:
        if isinstance(q, str):
            # Handle JSON-encoded strings like "[question1, question2]"
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
                # Handle individual questions with trailing commas or quotes
                cleaned = q.strip('[').strip(']').strip('"').strip(',').strip()
                if cleaned:
                    cleaned_questions.append(cleaned)
        else:
            logger.warning(f"Unexpected question format: {q}")
            cleaned_questions.append(str(q))
    return cleaned_questions

def extract_json_from_llm_response(response):
    """Extract and parse JSON from LLM response text."""
    try:
        # Check if the response is already a dict (properly formatted JSON)
        if isinstance(response, dict):
            return response
        
        # Try to parse the entire response as JSON
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass
        
        # Look for JSON within the response text using common patterns
        json_start = response.find("{")
        json_end = response.rfind("}")
        
        if json_start != -1 and json_end != -1:
            json_str = response[json_start:json_end+1]
            return json.loads(json_str)
            
        # If all attempts fail, raise an exception
        raise ValueError("Could not extract JSON from LLM response")
    except Exception as e:
        logger.error(f"Error extracting JSON from LLM response: {e}")
        logger.debug(f"Problematic response: {response}")
        return {
            "error": f"Failed to parse LLM response: {str(e)}",
            "raw_response": response
        }

def check_compliance_with_milvus():
    # Load question set
    with open("../ui/data/Bank_Policy_questions.json") as f:
        questions = json.load(f)

    # Connect to Milvus
    connections.connect(alias="default", host="localhost", port="19530")

    results = {}

    for topic, question_list in questions.items():
        results[topic] = []

        # Clean the question list to get individual questions
        cleaned_questions = clean_questions(question_list)
        logger.info(f"Cleaned questions for topic '{topic}': {cleaned_questions}")

        for question in cleaned_questions:
            # Generate embedding for the question
            embedding = embed_policy_text([question])[0]

            # Retrieve most relevant policy paragraphs from both bank & vendor collections
            try:
                bank_paragraph = search_milvus("bank_policy", embedding)
                vendor_paragraph = search_milvus("vendor_policy", embedding)
            except Exception as e:
                logger.error(f"Error searching Milvus for question '{question}': {e}")
                results[topic].append({
                    "question": question,
                    "error": f"Failed to retrieve policy paragraphs: {str(e)}"
                })
                continue

            # Build LLM prompt
            prompt = f"""
You are a Compliance Auditor.

Bank Policy: {bank_paragraph}

Vendor Policy: {vendor_paragraph}

Question: {question}

Evaluate whether the vendor is compliant with the bank's policy. Return a JSON:
{{
  "question": "{question}",
  "answer_from_bank": "...",
  "answer_from_vendor": "...",
  "compliance_status": "Compliant/Non-Compliant/Partially Compliant",
  "reference_bank": "...",
  "reference_vendor": "..."
}}
            """

            # Run completion and ensure we have proper JSON
            try:
                response = run_completion(prompt)
                # Extract JSON from the response
                parsed_json = extract_json_from_llm_response(response)
                # Add the parsed JSON to results
                results[topic].append(parsed_json)
            except Exception as e:
                print(f"⚠️ Failed to get valid response for: {question}, error: {e}")
                results[topic].append({
                    "question": question,
                    "error": f"Failed to get valid response from LLM: {str(e)}"
                })

    with open("../ui/data/compliance_results_milvus.json", "w") as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    check_compliance_with_milvus()