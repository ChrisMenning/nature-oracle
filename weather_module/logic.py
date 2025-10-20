from datetime import date

def season_dates(today=None):
    today = today or date.today()
    year = today.year
    spring = date(year, 3, 20)
    summer = date(year, 6, 21)
    fall = date(year, 9, 22)
    winter = date(year, 12, 21)

    if today < spring:
        return "Winter", date(year-1, 12, 21), spring, "Spring Equinox"
    elif today < summer:
        return "Spring", spring, summer, "Summer Solstice"
    elif today < fall:
        return "Summer", summer, fall, "Fall Equinox"
    elif today < winter:
        return "Fall", fall, winter, "Winter Solstice"
    else:
        return "Winter", winter, date(year+1, 3, 20), "Spring Equinox"

def season_progress(start, end, today=None):
    today = today or date.today()
    total = (end - start).days
    elapsed = (today - start).days
    return elapsed / total * 100 if total > 0 else 0

def ascii_bar(percentage, length=30):
    filled_length = round((percentage / 100) * length)
    empty_length = length - filled_length
    bar = '█' * filled_length + '░' * empty_length
    return f"[{bar}]"

def wrap_text_into_slides(text, max_chars=33, max_lines_per_slide=8):
    paragraphs = text.split("\n")
    wrapped_lines = []

    for para in paragraphs:
        words = para.split()
        current_line = []
        current_len = 0
        for word in words:
            if current_len + len(word) + (1 if current_line else 0) > max_chars:
                wrapped_lines.append(" ".join(current_line))
                current_line = [word]
                current_len = len(word)
            else:
                current_line.append(word)
                current_len += len(word) + (1 if current_line else 0)
        if current_line:
            wrapped_lines.append(" ".join(current_line))
        if not para.strip():
            wrapped_lines.append("")

    slides = []
    for i in range(0, len(wrapped_lines), max_lines_per_slide):
        slides.append("\n".join(wrapped_lines[i:i + max_lines_per_slide]))
    return slides
