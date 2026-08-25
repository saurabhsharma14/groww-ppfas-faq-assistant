import os
from groq import Groq

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

system_prompt = """
You are a facts-only mutual fund FAQ assistant for PPFAS schemes on Groww.
Rules:
- Answer using ONLY the retrieved context below. Do not use prior knowledge.
- Keep your answer to 3 sentences maximum.
- Do NOT provide investment advice, opinions, predictions, or comparisons.
- If the context does not answer the question, say:
    "I don't have this information. Please visit: https://groww.in/mutual-funds/category/ppfas-mutual-fund"
"""

response = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "Context:\n- The expense ratio of Parag Parikh Long Term Value Fund is 0.68%.\n\nQuestion: What is the expense ratio of Parag Parikh Flexi Cap Fund?"}
    ],
    max_tokens=4096,
    temperature=0.0
)

print(response.choices[0].message)
print("REASONING:", response.choices[0].message.reasoning)
print("CONTENT:", repr(response.choices[0].message.content))
