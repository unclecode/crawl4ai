import re

def apply_png_predictor(data, width, bits, color_channels):
    """Decode PNG predictor (PDF 1.5+ filter)"""
    bytes_per_pixel = (bits * color_channels) // 8
    if (bits * color_channels) % 8 != 0:
        bytes_per_pixel += 1
        
    stride = width * bytes_per_pixel
    scanline_length = stride + 1  # +1 for filter byte
    
    if len(data) % scanline_length != 0:
        raise ValueError("Invalid scanline structure")
    
    num_lines = len(data) // scanline_length
    output = bytearray()
    prev_line = b'\x00' * stride
    
    for i in range(num_lines):
        line = data[i*scanline_length:(i+1)*scanline_length]
        filter_type = line[0]
        filtered = line[1:]
        
        if filter_type == 0:  # None
            decoded = filtered
        elif filter_type == 1:  # Sub
            decoded = bytearray(filtered)
            for j in range(bytes_per_pixel, len(decoded)):
                decoded[j] = (decoded[j] + decoded[j - bytes_per_pixel]) % 256
        elif filter_type == 2:  # Up
            decoded = bytearray([(filtered[j] + prev_line[j]) % 256 
                               for j in range(len(filtered))])
        elif filter_type == 3:  # Average
            decoded = bytearray(filtered)
            for j in range(len(decoded)):
                left = decoded[j - bytes_per_pixel] if j >= bytes_per_pixel else 0
                up = prev_line[j]
                avg = (left + up) // 2
                decoded[j] = (decoded[j] + avg) % 256
        elif filter_type == 4:  # Paeth
            decoded = bytearray(filtered)
            for j in range(len(decoded)):
                left = decoded[j - bytes_per_pixel] if j >= bytes_per_pixel else 0
                up = prev_line[j]
                up_left = prev_line[j - bytes_per_pixel] if j >= bytes_per_pixel else 0
                paeth = paeth_predictor(left, up, up_left)
                decoded[j] = (decoded[j] + paeth) % 256
        else:
            raise ValueError(f"Unsupported filter type: {filter_type}")
        
        output.extend(decoded)
        prev_line = decoded
    
    return bytes(output)

def paeth_predictor(a, b, c):
    p = a + b - c
    pa = abs(p - a)
    pb = abs(p - b)
    pc = abs(p - c)
    if pa <= pb and pa <= pc:
        return a
    elif pb <= pc:
        return b
    else:
        return c

import re
import html

def clean_pdf_text_to_html(page_number, text):
    # Decode Unicode escapes and handle surrogate pairs
    try:
        decoded = text.encode('latin-1').decode('unicode-escape')
        decoded = decoded.encode('utf-16', 'surrogatepass').decode('utf-16')
    except Exception as e:
        decoded = text  # Fallback if decoding fails
    
    article_title_detected = False
    # decoded = re.sub(r'\.\n', '.\n\n', decoded)
    # decoded = re.sub(r'\.\n', '<|break|>', decoded)
    lines = decoded.split('\n')
    output = []
    current_paragraph = []
    in_header = False
    email_pattern = re.compile(r'\{.*?\}')
    affiliation_pattern = re.compile(r'^†')
    quote_pattern = re.compile(r'^["“]')
    author_pattern = re.compile(
        r'^\s*[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*\s*(?:[†*0-9]+)?'
        r'(?:,\s*[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*\s*(?:[†*0-9]+)?)*'
        r'(?:,\s*(?:and|&)\s+[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*\s*(?:[†*0-9]+)?)?\s*$'
    )
    
    def flush_paragraph():
        if current_paragraph:
            para = ' '.join(current_paragraph)
            para = re.sub(r'\s+', ' ', para).strip()
            if para:
                # escaped_para = html.escape(para)
                escaped_para = para
                # escaped_para = re.sub(r'\.\n', '.\n\n', escaped_para)
                # Split escaped_para by <|break|> to avoid HTML escaping
                escaped_para = escaped_para.split('.\n\n')
                # Wrap each part in <p> tag
                escaped_para = [f'<p>{part}</p>' for part in escaped_para]
                output.append(f'<div class="paragraph">{"".join(escaped_para)}</div><hr/>')
            current_paragraph.clear()
    
    for i, line in enumerate(lines):
        line = line.strip()
        
        # Handle empty lines
        if not line:
            flush_paragraph()
            continue
            
        # Detect article title (first line with reasonable length)
        if not article_title_detected and i == 0 and 3 <= len(line.split()) <= 8 and len(lines) > 1:
            flush_paragraph()
            escaped_line = html.escape(line)
            output.append(f'<h2>{escaped_line}</h2>')
            article_title_detected = True
            continue
            
        # Detect numbered headers like "2.1 Background"
        numbered_header = re.match(r'^(\d+(?:\.\d+)*)\s+(.+)$', line)
        if i > 0 and not lines[i-1].strip() and numbered_header:
            flush_paragraph()
            level = numbered_header.group(1).count('.') + 1
            header_text = numbered_header.group(2)
            md_level = min(level + 1, 6)
            escaped_header = html.escape(header_text)
            output.append(f'<h{md_level}>{escaped_header}</h{md_level}>')
            in_header = True
            continue
            
        # Detect authors
        if page_number == 1 and author_pattern.match(line):
            authors = re.sub(r'[†â€]', '', line)
            authors = re.split(r', | and ', authors)
            formatted_authors = []
            for author in authors:
                if author.strip():
                    parts = [p for p in author.strip().split() if p]
                    formatted = ' '.join(parts)
                    escaped_author = html.escape(formatted)
                    formatted_authors.append(f'<strong>{escaped_author}</strong>')
            
            if len(formatted_authors) > 1:
                joined = ', '.join(formatted_authors[:-1]) + ' and ' + formatted_authors[-1]
            else:
                joined = formatted_authors[0]
            
            output.append(f'<p>{joined}</p>')
            continue
            
        # Detect affiliation
        if affiliation_pattern.match(line):
            escaped_line = html.escape(line)
            output.append(f'<p><em>{escaped_line}</em></p>')
            continue
            
        # Detect emails
        if email_pattern.match(line):
            escaped_line = html.escape(line)
            output.append(f'<p><code>{escaped_line}</code></p>')
            continue
            
        # Detect section headers
        if re.match(r'^(Abstract|\d+\s+[A-Z]|References|Appendix|Figure|Table)', line):
            flush_paragraph()
            escaped_line = html.escape(line)
            output.append(f'<h2 class="section-header"><em>{escaped_line}</em></h2>')
            in_header = True
            continue
            
        # Handle quotes
        if quote_pattern.match(line):
            flush_paragraph()
            escaped_line = html.escape(line)
            output.append(f'<blockquote><p>{escaped_line}</p></blockquote>')
            continue
            
        # Handle hyphenated words
        if line.endswith('-'):
            current_paragraph.append(line[:-1].strip())
        else:
            current_paragraph.append(line)
            
        # Handle paragraph breaks after headers
        if in_header and not line.endswith(('.', '!', '?')):
            flush_paragraph()
            in_header = False
    
    flush_paragraph()
    
    # Post-process HTML
    html_output = '\n'.join(output)
    
    # Fix common citation patterns
    html_output = re.sub(r'\(([A-Z][a-z]+ et al\. \d{4})\)', r'<cite>\1</cite>', html_output)
    
    # Fix escaped characters
    html_output = html_output.replace('\\ud835', '').replace('\\u2020', '†')
    
    # Remove leftover hyphens and fix spacing
    html_output = re.sub(r'\s+-\s+', '', html_output)
    html_output = re.sub(r'\s+([.,!?)])', r'\1', html_output)
    
    return html_output

def clean_pdf_text(page_number, text):
    # Decode Unicode escapes and handle surrogate pairs
    try:
        decoded = text.encode('latin-1').decode('unicode-escape')
        decoded = decoded.encode('utf-16', 'surrogatepass').decode('utf-16')
    except Exception as e:
        decoded = text  # Fallback if decoding fails
    
    article_title_detected = False
    decoded = re.sub(r'\.\n', '.\n\n', decoded)
    lines = decoded.split('\n')
    output = []
    current_paragraph = []
    in_header = False
    email_pattern = re.compile(r'\{.*?\}')
    affiliation_pattern = re.compile(r'^†')
    quote_pattern = re.compile(r'^["“]')
    author_pattern = re.compile(
        r'^\s*[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*\s*(?:[†*0-9]+)?'
        r'(?:,\s*[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*\s*(?:[†*0-9]+)?)*'
        r'(?:,\s*(?:and|&)\s+[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*\s*(?:[†*0-9]+)?)?\s*$'
    )
    
    def flush_paragraph():
        if current_paragraph:
            para = ' '.join(current_paragraph)
            para = re.sub(r'\s+', ' ', para).strip()
            if para:
                output.append(para)
            current_paragraph.clear()
    
    for i, line in enumerate(lines):
        line = line.strip()
        
        # Handle special patterns
        if not line:
            flush_paragraph()
            continue
            
        # Detect headline (first line, reasonable length, surrounded by empty lines)
        if not article_title_detected and i == 0 and 3 <= len(line.split()) <= 8 and (len(lines) > 1):
            flush_paragraph()
            output.append(f'## {line}')
            continue
            
        # Detect paragraph breaks for ALL paragraphs
        if not line and current_paragraph:
            flush_paragraph()
            output.append('')  # Add empty line between paragraphs
            continue
                    
        # Detect numbered headers like "2.1 Background"
        numbered_header = re.match(r'^(\d+(?:\.\d+)*)\s+(.+)$', line)
        if not lines[i-1].strip() and numbered_header:
            flush_paragraph()
            level = numbered_header.group(1).count('.') + 1  # Convert 2.1 → level 2
            header_text = numbered_header.group(2)
            # Never go beyond ### for subsections
            md_level = min(level + 1, 6)   # 1 → ##, 2 → ###, 3 → #### etc
            output.append(f'{"#" * md_level} {header_text}')
            in_header = True
            continue            
            
                    
        # Detect authors
        if page_number == 1 and author_pattern.match(line):
            # Clean and format author names
            authors = re.sub(r'[†â€]', '', line)  # Remove affiliation markers
            authors = re.split(r', | and ', authors)
            formatted_authors = []
            for author in authors:
                if author.strip():
                    # Handle "First Last" formatting
                    parts = [p for p in author.strip().split() if p]
                    formatted = ' '.join(parts)
                    formatted_authors.append(f'**{formatted}**')
            
            # Join with commas and "and"
            if len(formatted_authors) > 1:
                joined = ', '.join(formatted_authors[:-1]) + ' and ' + formatted_authors[-1]
            else:
                joined = formatted_authors[0]
            
            output.append(joined)
            continue
            
        # Detect affiliation
        if affiliation_pattern.match(line):
            output.append(f'*{line}*')
            continue
            
        # Detect emails
        if email_pattern.match(line):
            output.append(f'`{line}`')
            continue
            
        # Detect section headers
        if re.match(r'^(Abstract|\d+\s+[A-Z]|References|Appendix|Figure|Table)', line):
            flush_paragraph()
            output.append(f'_[{line}]_')
            in_header = True
            continue
            
           
        # Handle quotes
        if quote_pattern.match(line):
            flush_paragraph()
            output.append(f'> {line}')
            continue
            
        # Handle hyphenated words
        if line.endswith('-'):
            current_paragraph.append(line[:-1].strip())
        else:
            current_paragraph.append(line)
            
        # Handle paragraph breaks after headers
        if in_header and not line.endswith(('.', '!', '?')):
            flush_paragraph()
            in_header = False
    
    flush_paragraph()
    
    # Post-processing
    markdown = '\n\n'.join(output)
    
    # Fix common citation patterns
    markdown = re.sub(r'\(([A-Z][a-z]+ et al\. \d{4})\)', r'[\1]', markdown)
    
    # Fix escaped characters
    markdown = markdown.replace('\\ud835', '').replace('\\u2020', '†')
    
    # Remove leftover hyphens and fix spacing
    markdown = re.sub(r'\s+-\s+', '', markdown)  # Join hyphenated words
    markdown = re.sub(r'\s+([.,!?)])', r'\1', markdown)  # Fix punctuation spacing
    
    
    return markdown
