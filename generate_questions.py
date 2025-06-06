# import json
# import os
# from groq_model import run_completion
# import logging
# import re

# # Configure logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# def generate_questions_from_policy(json_path):
#     """
#     Generate a flexible number of concise compliance questions per topic from a policy JSON file using Groq.
#     Questions cover all key policy details, are unique, and adjust to paragraph complexity.
    
#     Args:
#         json_path (str): Path to the policy JSON file.
        
#     Writes:
#         bank_questions.json in the 'data' directory: Generated questions per topic.
#     """
#     try:
#         logger.info(f"Loading JSON file: {json_path}")
#         with open(json_path, "r", encoding="utf-8") as f:
#             data = json.load(f)

#         output = {}
#         all_questions = set()  # Track questions to prevent duplicates

#         for section in data:
#             topic = section["topic_name"]
#             paragraph = section["full_paragraph"]

#             prompt = f"""You are a compliance auditor assistant. Based on the following policy section, generate a concise set of questions to check vendor compliance. The questions should:
#             - Comprehensively cover all key details in the section (e.g., retention periods, encryption, backups).
#             - Be clear, answerable based on the policy, and avoid redundancy or overly granular details.
#             - Be unique and specific to the section, differing from questions for other sections.
#             - Adjust in number based on the complexity and length of the section (e.g., more questions for detailed paragraphs, fewer for simple ones).
#             Return the response as a valid JSON array of strings, e.g., ["question1", "question2"]. Ensure:
#             - The output is enclosed in square brackets with double-quoted strings.
#             - The output is parseable as JSON with no additional text, trailing commas, or malformed formatting.

#             Section: {paragraph}
#             """

#             try:
#                 logger.info(f"Generating questions for topic: {topic}")
#                 response = run_completion(prompt)
#                 logger.debug(f"Raw response for {topic}: {response}")

#                 # Attempt to parse as JSON
#                 try:
#                     questions = json.loads(response)
#                     if not isinstance(questions, list) or not all(isinstance(q, str) for q in questions):
#                         logger.warning(f"Invalid response format for {topic}: {questions}")
#                         questions = [f"Does the vendor comply with the {topic} requirements?"]
#                 except json.JSONDecodeError:
#                     logger.warning(f"JSON parsing failed for {topic}, attempting to extract questions")
#                     # Extract questions from non-JSON response
#                     lines = response.split('\n')
#                     questions = [line.strip() for line in lines if line.strip() and (line.strip()[0].isdigit() or line.strip().startswith('-') or '?' in line)]
#                     questions = [re.sub(r'^\d+\.?\s*|-+\s*', '', q).strip() for q in questions if q]
#                     # Deduplicate
#                     questions = list(dict.fromkeys(questions))
#                     if not questions:
#                         questions = [f"Does the vendor comply with the {topic} requirements?"]
#                     logger.info(f"Extracted questions for {topic}: {questions}")

#                 # Ensure uniqueness and filter questions
#                 final_questions = []
#                 for q in questions:
#                     if q not in all_questions:
#                         final_questions.append(q)
#                         all_questions.add(q)
#                 if not final_questions:
#                     default = f"Does the vendor comply with the {topic} requirements?"
#                     if default not in all_questions:
#                         final_questions.append(default)
#                         all_questions.add(default)

#                 output[topic] = final_questions
#                 logger.info(f"Generated {len(final_questions)} questions for {topic}: {final_questions}")

#             except Exception as e:
#                 logger.error(f"Failed to generate questions for {topic}: {e}")
#                 default = f"Does the vendor comply with the {topic} requirements?"
#                 if default not in all_questions:
#                     output[topic] = [default]
#                     all_questions.add(default)
#                 else:
#                     output[topic] = []

#         output_path = os.path.join("data", "bank_questions.json")
#         logger.info(f"Writing questions to {output_path}")
#         with open(output_path, "w", encoding="utf-8") as f:
#             json.dump(output, f, indent=2)

#     except Exception as e:
#         logger.error(f"Error processing {json_path}: {e}", exc_info=True)
#         raise


import json
import os
import re
import logging
from groq_model import run_completion

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

def extract_questions_fallback(response: str, topic: str) -> list:
    """
    Attempts to extract questions from a non-JSON response.
    """
    logger.warning(f"Attempting fallback parsing for topic: {topic}")
    lines = response.split('\n')
    questions = [line.strip() for line in lines if '?' in line or line.strip().startswith(('-', '*', '1.'))]
    cleaned = [re.sub(r'^\d+\.?\s*|-+\s*|\*\s*', '', q).strip() for q in questions]
    return list(dict.fromkeys(q for q in cleaned if q))  # Remove duplicates and empties

def generate_questions_for_section(topic: str, paragraph: str, all_questions: set) -> list:
    prompt = f"""You are a compliance auditor assistant. Based on the following policy section, generate a concise set of questions to check vendor compliance. The questions should:
- Comprehensively cover all key details (e.g., retention periods, encryption, backups).
- Be clear, unique, answerable from the policy, and non-redundant.
- Adjust quantity based on complexity (more for long/detailed paragraphs, fewer for short/simple ones).
Return a JSON array like: ["question1", "question2"] — valid, parseable, with no extra text.

Section: {paragraph}
"""

    try:
        logger.info(f"Generating questions for topic: {topic}")
        response = run_completion(prompt)
        logger.debug(f"Raw response: {response}")

        try:
            questions = json.loads(response)
            if not isinstance(questions, list) or not all(isinstance(q, str) for q in questions):
                raise ValueError("Invalid format")
        except Exception:
            questions = extract_questions_fallback(response, topic)

        # Deduplicate against all existing questions
        final_questions = [q for q in questions if q not in all_questions]
        if not final_questions:
            fallback = f"Does the vendor comply with the {topic} requirements?"
            if fallback not in all_questions:
                final_questions = [fallback]
        all_questions.update(final_questions)
        return final_questions

    except Exception as e:
        logger.error(f"Error generating questions for '{topic}': {e}")
        fallback = f"Does the vendor comply with the {topic} requirements?"
        if fallback not in all_questions:
            all_questions.add(fallback)
            return [fallback]
        return []

def generate_questions_from_policy(json_path: str, output_path: str = "data/bank_questions.json"):
    """
    Reads a policy JSON file and generates concise compliance questions per section.
    """
    try:
        logger.info(f"Loading policy JSON: {json_path}")
        with open(json_path, "r", encoding="utf-8") as f:
            policy_data = json.load(f)

        result = {}
        all_questions = set()

        for section in policy_data:
            topic = section.get("topic_name")
            paragraph = section.get("full_paragraph")
            if not topic or not paragraph:
                logger.warning(f"Skipping incomplete section: {section}")
                continue

            questions = generate_questions_for_section(topic, paragraph, all_questions)
            result[topic] = questions
            logger.info(f"{len(questions)} questions generated for '{topic}'.")

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)
        logger.info(f"Questions saved to: {output_path}")

    except Exception as e:
        logger.error(f"Failed to process {json_path}: {e}", exc_info=True)
        raise
