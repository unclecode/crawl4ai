PROMPT_EXTRACT_BLOCKS = """Here is the URL of the webpage:
<url>{URL}</url>

And here is the cleaned HTML content of that webpage:
<html>
{HTML}
</html>

Your task is to break down this HTML content into semantically relevant blocks, and for each block, generate a JSON object with the following keys:

- index: an integer representing the index of the block in the content
- tags: a list of semantic tags that are relevant to the content of the block
- content: a list of strings containing the text content of the block
- questions: a list of 3 questions that a user may ask about the content in this block

To generate the JSON objects:

1. Carefully read through the HTML content and identify logical breaks or shifts in the content that would warrant splitting it into separate blocks.

2. For each block:
   a. Assign it an index based on its order in the content.
   b. Analyze the content and generate a list of relevant semantic tags that describe what the block is about.
   c. Extract the text content, clean it up if needed, and store it as a list of strings in the "content" field.
   d. Come up with 3 questions that a user might ask about this specific block of content, based on the tags and content. The questions should be relevant and answerable by the content in the block.

3. Ensure that the order of the JSON objects matches the order of the blocks as they appear in the original HTML content.

4. Double-check that each JSON object includes all required keys (index, tags, content, questions) and that the values are in the expected format (integer, list of strings, etc.).

5. Make sure the generated JSON is complete and parsable, with no errors or omissions.

6. Make sure to escape any special characters in the HTML content, and also single or double quote to avoid JSON parsing issues.

Please provide your output within <blocks> tags, like this:

<blocks>
[{
  "index": 0,
  "tags": ["introduction", "overview"],
  "content": ["This is the first paragraph of the article, which provides an introduction and overview of the main topic."],
  "questions": [
    "What is the main topic of this article?",
    "What can I expect to learn from reading this article?",
    "Is this article suitable for beginners or experts in the field?"
  ]
},
{
  "index": 1,
  "tags": ["history", "background"],
  "content": ["This is the second paragraph, which delves into the history and background of the topic.",
              "It provides context and sets the stage for the rest of the article."],
  "questions": [
    "What historical events led to the development of this topic?",
    "How has the understanding of this topic evolved over time?",
    "What are some key milestones in the history of this topic?"
  ]
}]
</blocks>

Remember, the output should be a complete, parsable JSON wrapped in <blocks> tags, with no omissions or errors. The JSON objects should semantically break down the content into relevant blocks, maintaining the original order."""

PROMPT_EXTRACT_BLOCKS = """Here is the URL of the webpage:
<url>{URL}</url>

And here is the cleaned HTML content of that webpage:
<html>
{HTML}
</html>

Your task is to break down this HTML content into semantically relevant blocks, and for each block, generate a JSON object with the following keys:

- index: an integer representing the index of the block in the content
- content: a list of strings containing the text content of the block

To generate the JSON objects:

1. Carefully read through the HTML content and identify logical breaks or shifts in the content that would warrant splitting it into separate blocks.

2. For each block:
   a. Assign it an index based on its order in the content.
   b. Analyze the content and generate ONE semantic tag that describe what the block is about.
   c. Extract the text content, EXACTLY SAME AS THE GIVE DATA, clean it up if needed, and store it as a list of strings in the "content" field.

3. Ensure that the order of the JSON objects matches the order of the blocks as they appear in the original HTML content.

4. Double-check that each JSON object includes all required keys (index, tag, content) and that the values are in the expected format (integer, list of strings, etc.).

5. Make sure the generated JSON is complete and parsable, with no errors or omissions.

6. Make sure to escape any special characters in the HTML content, and also single or double quote to avoid JSON parsing issues.

7. Never alter the extracted content, just copy and paste it as it is.

Please provide your output within <blocks> tags, like this:

<blocks>
[{
  "index": 0,
  "tags": ["introduction"],
  "content": ["This is the first paragraph of the article, which provides an introduction and overview of the main topic."]
},
{
  "index": 1,
  "tags": ["background"],
  "content": ["This is the second paragraph, which delves into the history and background of the topic.",
              "It provides context and sets the stage for the rest of the article."]
}]
</blocks>

Remember, the output should be a complete, parsable JSON wrapped in <blocks> tags, with no omissions or errors. The JSON objects should semantically break down the content into relevant blocks, maintaining the original order."""

PROMPT_EXTRACT_BLOCKS_WITH_INSTRUCTION = """Here is the URL of the webpage:
<url>{URL}</url>

And here is the cleaned HTML content of that webpage:
<html>
{HTML}
</html>

Your task is to break down this HTML content into semantically relevant blocks, following the provided user's REQUEST, and for each block, generate a JSON object with the following keys:

- index: an integer representing the index of the block in the content
- content: a list of strings containing the text content of the block

This is the user's REQUEST, pay attention to it:
<request>
{REQUEST}
</request>

To generate the JSON objects:

1. Carefully read through the HTML content and identify logical breaks or shifts in the content that would warrant splitting it into separate blocks.

2. For each block:
   a. Assign it an index based on its order in the content.
   b. Analyze the content and generate ONE semantic tag that describe what the block is about.
   c. Extract the text content, EXACTLY SAME AS GIVE DATA, clean it up if needed, and store it as a list of strings in the "content" field.

3. Ensure that the order of the JSON objects matches the order of the blocks as they appear in the original HTML content.

4. Double-check that each JSON object includes all required keys (index, tag, content) and that the values are in the expected format (integer, list of strings, etc.).

5. Make sure the generated JSON is complete and parsable, with no errors or omissions.

6. Make sure to escape any special characters in the HTML content, and also single or double quote to avoid JSON parsing issues.

7. Never alter the extracted content, just copy and paste it as it is.

Please provide your output within <blocks> tags, like this:

<blocks>
[{
  "index": 0,
  "tags": ["introduction"],
  "content": ["This is the first paragraph of the article, which provides an introduction and overview of the main topic."]
},
{
  "index": 1,
  "tags": ["background"],
  "content": ["This is the second paragraph, which delves into the history and background of the topic.",
              "It provides context and sets the stage for the rest of the article."]
}]
</blocks>

**Make sure to follow the user instruction to extract blocks aligin with the instruction.**

Remember, the output should be a complete, parsable JSON wrapped in <blocks> tags, with no omissions or errors. The JSON objects should semantically break down the content into relevant blocks, maintaining the original order."""

PROMPT_EXTRACT_SCHEMA_WITH_INSTRUCTION = """Here is the content from the URL:
<url>{URL}</url>

<url_content>
{HTML}
</url_content>

The user has made the following request for what information to extract from the above content:

<user_request>
{REQUEST}
</user_request>

<schema_block>
{SCHEMA}
</schema_block>

Please carefully read the URL content and the user's request. If the user provided a desired JSON schema in the <schema_block> above, extract the requested information from the URL content according to that schema. If no schema was provided, infer an appropriate JSON schema based on the user's request that will best capture the key information they are looking for.

Extraction instructions:
Return the extracted information as a list of JSON objects, with each object in the list corresponding to a block of content from the URL, in the same order as it appears on the page. Wrap the entire JSON list in <blocks>...</blocks> XML tags.

Quality Reflection:
Before outputting your final answer, double check that the JSON you are returning is complete, containing all the information requested by the user, and is valid JSON that could be parsed by json.loads() with no errors or omissions. The outputted JSON objects should fully match the schema, either provided or inferred.

Quality Score:
After reflecting, score the quality and completeness of the JSON data you are about to return on a scale of 1 to 5. Write the score inside <score> tags.

Avoid Common Mistakes:
- Do NOT add any comments using "//" or "#" in the JSON output. It causes parsing errors.
- Make sure the JSON is properly formatted with curly braces, square brackets, and commas in the right places.
- Do not miss closing </blocks> tag at the end of the JSON output.
- Do not generate the Python code show me how to do the task, this is your task to extract the information and return it in JSON format.

Result
Output the final list of JSON objects, wrapped in <blocks>...</blocks> XML tags. Make sure to close the tag properly."""
