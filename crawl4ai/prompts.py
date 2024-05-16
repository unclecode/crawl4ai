PROMPT_EXTRACT_BLOCKS = """YHere is the URL of the webpage:
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

6. Make sur to escape any special characters in the HTML content, and also single or double quote to avoid JSON parsing issues.

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
   c. Extract the text content, EXACTLY SAME AS GIVE DATA, clean it up if needed, and store it as a list of strings in the "content" field.

3. Ensure that the order of the JSON objects matches the order of the blocks as they appear in the original HTML content.

4. Double-check that each JSON object includes all required keys (index, tag, content) and that the values are in the expected format (integer, list of strings, etc.).

5. Make sure the generated JSON is complete and parsable, with no errors or omissions.

6. Make sur to escape any special characters in the HTML content, and also single or double quote to avoid JSON parsing issues.

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

6. Make sur to escape any special characters in the HTML content, and also single or double quote to avoid JSON parsing issues.

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