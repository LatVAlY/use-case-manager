CHUNK_SIZE = 6000  # ~tokens (chars / 4)
CHUNK_OVERLAP = 500  # preserve context across boundaries


def chunk_transcript(text: str) -> list[str]:
    """
    Split on double-newline paragraph boundaries.
    Keeps an overlap tail from the previous chunk to catch cross-boundary ideas.
    """
    paragraphs = text.split("\n\n")
    chunks, current, current_len = [], [], 0

    for para in paragraphs:
        para_len = len(para) // 4  # rough token estimate
        if current_len + para_len > CHUNK_SIZE and current:
            chunks.append("\n\n".join(current))
            # Keep overlap from end of current chunk
            overlap_text = "\n\n".join(current)[-CHUNK_OVERLAP * 4 :]
            current = [overlap_text, para]
            current_len = CHUNK_OVERLAP + para_len
        else:
            current.append(para)
            current_len += para_len

    if current:
        chunks.append("\n\n".join(current))
    return chunks
