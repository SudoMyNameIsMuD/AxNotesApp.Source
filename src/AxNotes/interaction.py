from .models import EntryType,TaskState
COMMANDS=("today","week","search","reindex","sync","help","quit")
def normalize_entry(raw):
 value=raw.strip()
 if not value or value=="-": raise ValueError("Entry text cannot be empty.")
 state=None
 for marker,s in (("[ ]",TaskState.OPEN),("[x]",TaskState.DONE),("[X]",TaskState.DONE),("[/]",TaskState.IN_PROGRESS),("[>]",TaskState.MIGRATED),("[-]",TaskState.CANCELED)):
  if value.startswith(marker): state=s; value=value[len(marker):].strip(); break
 if state is None and value.startswith("["): state=TaskState.OPEN; value=value[1:].lstrip(" ]").strip()
 low=value.lower()
 if low.endswith("[x]"): state=TaskState.DONE; value=value[:-3].rstrip()
 elif low.endswith("[x"): state=TaskState.DONE; value=value[:-2].rstrip()
 if state is not None:
  if not value: raise ValueError("Task text cannot be empty.")
  return EntryType.TASK,value,state
 if value.startswith("!") or value.endswith("!"): return EntryType.IMPORTANT,value.removeprefix("!").removesuffix("!").strip(),None
 if value.startswith("?") or value.endswith("?"): return EntryType.QUESTION,value.removeprefix("?").removesuffix("?").strip(),None
 return EntryType.NOTE,value,None
def normalize_detail(raw):
 value=raw.strip()
 if value.startswith(">"): return value[1:].strip() or None
 if value.endswith(">"): return value[:-1].strip() or None
 return None
