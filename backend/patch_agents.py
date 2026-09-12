import os
import glob

# Path to agents directory
agents_dir = r"c:\Users\91960\Desktop\files\Rishu_Project\backend\agents"

# The old parsing logic start
old_logic = """    # Remove markdown code blocks if present: ```json ... ```
    cleaned = re.sub(r"```(?:json)?", "", raw_text).strip().strip("`").strip()"""

old_logic_alt = """    cleaned = re.sub(r"```(?:json)?", "", raw_text).strip().strip("`").strip()"""

# The new parsing logic
new_logic = """    if isinstance(raw_text, list):
        # Extract text from LangChain multimodal message blocks
        raw_text = "".join([block.get("text", "") for block in raw_text if isinstance(block, dict)])
    elif not isinstance(raw_text, str):
        raw_text = str(raw_text)

    # Remove markdown code blocks if present: ```json ... ```
    cleaned = re.sub(r"```(?:json)?", "", raw_text).strip().strip("`").strip()"""

count = 0
for filepath in glob.glob(os.path.join(agents_dir, "*.py")):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    
    if "def _parse_json_response" in content:
        if old_logic in content:
            new_content = content.replace(old_logic, new_logic)
        elif old_logic_alt in content:
            new_content = content.replace(old_logic_alt, new_logic)
        else:
            continue
            
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(new_content)
        print(f"Patched {os.path.basename(filepath)}")
        count += 1

print(f"Total patched: {count}")
