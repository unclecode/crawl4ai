from bs4 import BeautifulSoup
from collections import Counter
import re

# Load the rendered HTML
with open('ms_jobs_full.html', 'r', encoding='utf-8') as f:
    html = f.read()

soup = BeautifulSoup(html, 'html.parser')

# Heuristic: Find all text nodes that look like job titles, locations, or qualifications
# We'll use some common keywords and patterns
job_keywords = ['engineer', 'manager', 'developer', 'lead', 'specialist', 'analyst', 'designer', 'director', 'intern', 'consultant', 'scientist', 'architect', 'product', 'program', 'sales', 'marketing', 'support', 'administrator', 'operations', 'security', 'data', 'cloud', 'ai', 'ml', 'research', 'finance', 'accountant', 'legal', 'business', 'customer', 'service']
location_keywords = ['united states', 'india', 'china', 'germany', 'france', 'canada', 'uk', 'japan', 'remote', 'hybrid', 'onsite', 'location', 'city', 'country', 'state', 'region']
qual_keywords = ['qualification', 'requirements', 'skills', 'experience', 'degree', 'bachelor', 'master', 'phd', 'education', 'certification', 'minimum', 'preferred']

# Helper to check if a string contains any keyword

def contains_keyword(text, keywords):
    text = text.lower()
    return any(kw in text for kw in keywords)

# Find all tags with text that looks like a job title
job_tags = []
location_tags = []
qual_tags = []

for tag in soup.find_all(True):
    text = tag.get_text(strip=True)
    if not text or len(text) > 100:  # skip long or empty
        continue
    if contains_keyword(text, job_keywords):
        job_tags.append(tag)
    if contains_keyword(text, location_keywords):
        location_tags.append(tag)
    if contains_keyword(text, qual_keywords):
        qual_tags.append(tag)

# Find the most common CSS class for each type
job_classes = [" ".join(tag.get("class", [])) for tag in job_tags if tag.get("class")]
location_classes = [" ".join(tag.get("class", [])) for tag in location_tags if tag.get("class")]
qual_classes = [" ".join(tag.get("class", [])) for tag in qual_tags if tag.get("class")]

most_common_job_class = Counter(job_classes).most_common(1)
most_common_location_class = Counter(location_classes).most_common(1)
most_common_qual_class = Counter(qual_classes).most_common(1)

print("Most common job title CSS class:", most_common_job_class)
print("Most common location CSS class:", most_common_location_class)
print("Most common qualifications CSS class:", most_common_qual_class)

# Print a few sample tags for each
print("\nSample job title tags:")
for tag in job_tags[:3]:
    print(tag)
print("\nSample location tags:")
for tag in location_tags[:3]:
    print(tag)
print("\nSample qualifications tags:")
for tag in qual_tags[:3]:
    print(tag)
