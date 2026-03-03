FIRST_KV_PATTERN = re.compile(r"'([^']+)'\s*:\s*'([^']+)'")

# Regex pattern
REC_PATTERN = re.compile(r"\{\s*'Rec'\s*:\s*\{(.*?)\}\s*\}", re.DOTALL)