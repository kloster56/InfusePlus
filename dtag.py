
"""
Simplified PII Tagger - Single Turn, Single Dataset Demo

This script demonstrates PII tagging with minimal token usage:
1. Fetches schema for a specific dataset
2. Single LLM call to classify all fields as PII or not
3. Batch applies tags to identified PII fields
"""

import os
import sys
import json
import warnings

warnings.filterwarnings("ignore")
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage

# DataHub SDK
from datahub.sdk import DataHubClient
from datahub_agent_context import DataHubContext
from datahub_agent_context.mcp_tools import list_schema_fields, add_tags

# --- Configuration ---
DATAHUB_GMS_URL = "http://localhost:8080"
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

# Target dataset - the "users" table in our warehouse
TARGET_DATASET_URN = "urn:li:dataset:(urn:li:dataPlatform:postgres,warehouse.public.users,PROD)"

if not GROQ_API_KEY:
    print("Error: GROQ_API_KEY environment variable is not set.")
    sys.exit(1)

# --- Initialize ---
client = DataHubClient(server=DATAHUB_GMS_URL)
llm = ChatGroq(model="llama-3.3-70b-versatile", api_key=GROQ_API_KEY)

def get_pii_fields_from_llm(fields: list[dict]) -> list[str]:
    """Single LLM call to identify PII fields."""
    
    field_list = [f["fieldPath"] for f in fields]
    
    prompt = f"""Analyze these database column names and identify which ones likely contain PII (Personally Identifiable Information).

Column names: {json.dumps(field_list)}

PII includes: names, emails, phone numbers, addresses, SSN, dates of birth, IP addresses, etc.

Return ONLY a JSON array of column names that are PII. Example: ["email", "name"]
If none are PII, return: []

Your response must be ONLY the JSON array, nothing else."""

    response = llm.invoke([
        SystemMessage(content="You are a data privacy expert. Respond only with valid JSON."),
        HumanMessage(content=prompt)
    ])
    
    # Parse response
    try:
        pii_fields = json.loads(response.content.strip())
        return pii_fields
    except json.JSONDecodeError:
        print(f"Warning: Could not parse LLM response: {response.content}")
        return []

def apply_pii_tags(urn: str, pii_fields: list[str]):
    """Batch apply PII tags to identified fields."""
    
    for field in pii_fields:
        print(f"  Tagging '{field}' as PII...")
        result = add_tags(
            tag_urns=["urn:li:tag:PII"],
            entity_urns=[urn],
            column_paths=[field]
        )
        print(f"  Result: {result}")

def main():
    print("=" * 50)
    print("PII Tagger - Single Turn Demo")
    print("=" * 50)
    
    with DataHubContext(client):
        # Step 1: Fetch schema
        print(f"\n1. Fetching schema for: {TARGET_DATASET_URN}")
        schema_result = list_schema_fields(urn=TARGET_DATASET_URN)
        schema_data = json.loads(schema_result) if isinstance(schema_result, str) else schema_result
        
        fields = schema_data.get("fields", [])
        print(f"   Found {len(fields)} fields: {[f['fieldPath'] for f in fields]}")
        
        # Step 2: Single LLM call
        print("\n2. Asking LLM to identify PII fields...")
        pii_fields = get_pii_fields_from_llm(fields)
        print(f"   LLM identified PII: {pii_fields}")
        
        # Step 3: Batch apply tags
        if pii_fields:
            print(f"\n3. Applying 'PII' tags to {len(pii_fields)} fields...")
            apply_pii_tags(TARGET_DATASET_URN, pii_fields)
            print("\n✓ Done! Check DataHub UI to see the tags.")
        else:
            print("\n   No PII fields identified.")
    
    print("=" * 50)

if __name__ == "__main__":
    main()
