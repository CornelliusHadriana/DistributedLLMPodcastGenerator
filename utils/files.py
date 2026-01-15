from pathlib import Path

def get_file_text(path: str, prompt: str = 'Summarize the following article.') -> str:
    '''
    Given the path to a file containing the text of an article, gets Gemini 2.5 Flash
    to return a summary
    '''
    try:
        p = Path(path)
        if not p.is_file():
            # try resolving relative to project root (two levels up from utils)
            project_root = Path(__file__).resolve().parent.parent
            candidates = [
                project_root / path,
                project_root / 'processing' / path,
                project_root / 'processing' / 'prompts' / path,
            ]
            found = None
            for c in candidates:
                if c.is_file():
                    found = c
                    break
            if found is None:
                raise FileNotFoundError(f"File not found in any location: {path}")
            p = found

        with open(p, 'r') as f:
            return f.read()
    except Exception as e:
        raise Exception(f'Could not read file: {e}')
    
def write_text_to_file(text: str, file_name: str) -> None:
    if not isinstance(text, str):
        raise ValueError('Text must be str.')
    
    try:
        with open(file_name, 'w') as f:
            f.write(text)
    except Exception as e:
        raise Exception(f'Could not write text to file: {e}')