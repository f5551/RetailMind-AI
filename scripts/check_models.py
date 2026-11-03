import sys
sys.stdout.reconfigure(line_buffering=True)

import truststore
truststore.inject_into_ssl()

import os
from dotenv import load_dotenv
load_dotenv()
from google import genai
from google.genai import types

print("Initializing Gemini client...", flush=True)
client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))

print("Querying models...", flush=True)
models = list(client.models.list())
names = [m.name.replace("models/", "") for m in models]
flash_models = [m for m in names if "flash" in m.lower()]
print(f"Total models: {len(names)}", flush=True)
print(f"Available flash models: {flash_models}", flush=True)

# Test candidate models for function calling
candidates = ["gemini-2.5-flash-lite", "gemini-flash-latest", "gemini-2.5-flash", "gemini-1.5-flash"]
for model_id in candidates:
    print(f"\nTesting model: {model_id} ...", flush=True)
    decl = types.FunctionDeclaration(
        name="add",
        description="Add two numbers",
        parameters={
            "type": "OBJECT",
            "properties": {"a": {"type": "INTEGER"}, "b": {"type": "INTEGER"}},
            "required": ["a", "b"],
        },
    )
    cfg = types.GenerateContentConfig(
        tools=[types.Tool(function_declarations=[decl])],
        temperature=0.1,
    )
    try:
        resp = client.models.generate_content(
            model=model_id,
            contents="What is 5 + 7? Call the add tool with arguments a=5, b=7.",
            config=cfg,
        )
        fc = resp.function_calls
        print(f"  -> SUCCESS! Function calls: {[(f.name, f.args) for f in fc] if fc else 'None'}", flush=True)
        print(f"  -> Tokens: {resp.usage_metadata.prompt_token_count} in, {resp.usage_metadata.candidates_token_count} out", flush=True)
        print(f"RECOMMENDED MODEL: {model_id}", flush=True)
        break
    except Exception as e:
        print(f"  -> FAILED: {type(e).__name__}: {str(e)[:150]}", flush=True)
