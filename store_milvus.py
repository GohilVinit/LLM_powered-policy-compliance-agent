from pymilvus import connections, Collection, CollectionSchema, FieldSchema, DataType, utility
import json
import numpy as np
from embed_policy import embed_policy_text
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def connect_to_milvus():
    try:
        connections.connect(alias="default", host="localhost", port="19530")
        logger.info("✅ Connected to Milvus")
    except Exception as e:
        logger.error(f"Failed to connect to Milvus: {e}")
        raise Exception(f"Failed to connect to Milvus: {e}")

def create_schema(name, dim):
    fields = [
        FieldSchema(name="topic_name", dtype=DataType.VARCHAR, max_length=512, is_primary=True),
        FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=dim),
        FieldSchema(name="full_paragraph", dtype=DataType.VARCHAR, max_length=5000)
    ]
    return CollectionSchema(fields, description=f"{name} policy schema")

def validate_data(data):
    for d in data:
        if not isinstance(d, dict) or "topic_name" not in d or "full_paragraph" not in d:
            raise ValueError("Invalid JSON structure: Missing required fields")
        if len(d["topic_name"]) > 512:
            raise ValueError(f"topic_name too long: {d['topic_name']}")
        if len(d["full_paragraph"]) > 5000:
            raise ValueError(f"full_paragraph too long: {d['full_paragraph']}")
    topic_names = [d["topic_name"] for d in data]
    if len(topic_names) != len(set(topic_names)):
        raise ValueError("Duplicate topic_name found in JSON data")

def store_in_milvus(json_file, collection_name):
    logger.debug(f"Processing JSON file: {json_file} for collection: {collection_name}")
    connect_to_milvus()

    if utility.has_collection(collection_name):
        utility.drop_collection(collection_name)
        logger.info(f"🗑️ Dropped existing collection: {collection_name}")

    try:
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        validate_data(data)
        logger.debug(f"Loaded and validated {len(data)} entries from {json_file}")
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON file {json_file}: {e}")
        raise ValueError(f"Failed to parse JSON file {json_file}: {e}")
    except FileNotFoundError:
        logger.error(f"JSON file not found: {json_file}")
        raise FileNotFoundError(f"JSON file not found: {json_file}")

    try:
        texts = [d["full_paragraph"] for d in data]
        logger.debug(f"Generating embeddings for {len(texts)} texts")
        embeddings = embed_policy_text(texts)

        dim = len(embeddings[0])
        if not all(len(emb) == dim for emb in embeddings):
            raise ValueError("Embedding dimension mismatch among samples")
        logger.debug(f"Generated embeddings with dimension: {dim}")
    except Exception as e:
        logger.error(f"Failed to generate embeddings: {e}")
        raise ValueError(f"Failed to generate embeddings: {e}")

    schema = create_schema(collection_name, dim)
    collection = Collection(name=collection_name, schema=schema)
    logger.info(f"🆕 Created collection: {collection_name}")

    entities = [
        [d["topic_name"] for d in data],
        [emb.tolist() for emb in embeddings],
        texts
    ]

    try:
        collection.insert(entities)
        logger.info(f"📥 Inserted {len(data)} entities into {collection_name}")
    except Exception as e:
        logger.error(f"Failed to insert data into Milvus: {e}")
        raise Exception(f"Failed to insert data into Milvus: {e}")

    index_params = {
        "metric_type": "L2",
        "index_type": "IVF_FLAT",
        "params": {"nlist": 128}
    }

    try:
        collection.create_index(field_name="embedding", index_params=index_params)
        logger.info(f"🔍 Created index on embedding field for {collection_name}")
    except Exception as e:
        logger.error(f"Failed to create index: {e}")
        raise Exception(f"Failed to create index: {e}")

    try:
        collection.load()
        logger.info(f"🚀 Loaded collection {collection_name} into memory")
    except Exception as e:
        logger.error(f"Failed to load collection: {e}")
        raise Exception(f"Failed to load collection: {e}")