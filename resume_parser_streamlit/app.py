REC_PATTERN = re.compile(r"'Rec'\s*:\s*\{(.*?)\}\s*\}", re.DOTALL)

FIRST_KV_PATTERN = re.compile(r"'([^']+)'\s*:\s*'([^']+)'")