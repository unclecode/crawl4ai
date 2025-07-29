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

PROMPT_EXTRACT_INFERRED_SCHEMA = """Here is the content from the URL:
<url>{URL}</url>

<url_content>
{HTML}
</url_content>

Please carefully read the URL content and the user's request. Analyze the page structure and infer the most appropriate JSON schema based on the content and request.

Extraction Strategy:
1. First, determine if the page contains repetitive items (like multiple products, articles, etc.) or a single content item (like a single article or page).
2. For repetitive items: Identify the common pattern and extract each instance as a separate JSON object in an array.
3. For single content: Extract the key information into a comprehensive JSON object that captures the essential details.

Extraction instructions:
Return the extracted information as a list of JSON objects. For repetitive content, each object in the list should correspond to a distinct item. For single content, you may return just one detailed JSON object. Wrap the entire JSON list in <blocks>...</blocks> XML tags.

Schema Design Guidelines:
- Create meaningful property names that clearly describe the data they contain
- Use nested objects for hierarchical information
- Use arrays for lists of related items
- Include all information requested by the user
- Maintain consistency in property names and data structures
- Only include properties that are actually present in the content
- For dates, prefer ISO format (YYYY-MM-DD)
- For prices or numeric values, extract them without currency symbols when possible

Quality Reflection:
Before outputting your final answer, double check that:
1. The inferred schema makes logical sense for the type of content
2. All requested information is included
3. The JSON is valid and could be parsed without errors
4. Property names are consistent and descriptive
5. The structure is optimal for the type of data being represented

Avoid Common Mistakes:
- Do NOT add any comments using "//" or "#" in the JSON output. It causes parsing errors.
- Make sure the JSON is properly formatted with curly braces, square brackets, and commas in the right places.
- Do not miss closing </blocks> tag at the end of the JSON output.
- Do not generate Python code showing how to do the task; this is your task to extract the information and return it in JSON format.
- Ensure consistency in property names across all objects
- Don't include empty properties or null values unless they're meaningful
- For repetitive content, ensure all objects follow the same schema

Important: If user specific instruction is provided, then stress significantly on what user is requesting and describing about the schema of end result (if any). If user is requesting to extract specific information, then focus on that and ignore the rest of the content.
<user_request>
{REQUEST}
</user_request>

Result:
Output the final list of JSON objects, wrapped in <blocks>...</blocks> XML tags. Make sure to close the tag properly.

DO NOT ADD ANY PRE OR POST COMMENTS. JUST RETURN THE JSON OBJECTS INSIDE <blocks>...</blocks> TAGS.

CRITICAL: The content inside the <blocks> tags MUST be a direct array of JSON objects (starting with '[' and ending with ']'), not a dictionary/object containing an array. For example, use <blocks>[{...}, {...}]</blocks> instead of <blocks>{"items": [{...}, {...}]}</blocks>. This is essential for proper parsing.
"""

PROMPT_FILTER_CONTENT = """Your task is to filter and convert HTML content into clean, focused markdown that's optimized for use with LLMs and information retrieval systems.

TASK DETAILS:
1. Content Selection
- DO: Keep essential information, main content, key details
- DO: Preserve hierarchical structure using markdown headers
- DO: Keep code blocks, tables, key lists
- DON'T: Include navigation menus, ads, footers, cookie notices
- DON'T: Keep social media widgets, sidebars, related content

2. Content Transformation
- DO: Use proper markdown syntax (#, ##, **, `, etc)
- DO: Convert tables to markdown tables
- DO: Preserve code formatting with ```language blocks
- DO: Maintain link texts but remove tracking parameters
- DON'T: Include HTML tags in output
- DON'T: Keep class names, ids, or other HTML attributes

3. Content Organization
- DO: Maintain logical flow of information
- DO: Group related content under appropriate headers
- DO: Use consistent header levels
- DON'T: Fragment related content
- DON'T: Duplicate information

IMPORTANT: If user specific instruction is provided, ignore above guideline and prioritize those requirements over these general guidelines.

OUTPUT FORMAT: 
Wrap your response in <content> tags. Use proper markdown throughout.
<content>
[Your markdown content here]
</content>

Begin filtering now.

--------------------------------------------

<|HTML_CONTENT_START|>
{HTML}
<|HTML_CONTENT_END|>

<|USER_INSTRUCTION_START|>
{REQUEST}
<|USER_INSTRUCTION_END|>
"""

JSON_SCHEMA_BUILDER= """
# HTML Schema Generation Instructions
You are a specialized model designed to analyze HTML patterns and generate extraction schemas. Your primary job is to create structured JSON schemas that can be used to extract data from HTML in a consistent and reliable way. When presented with HTML content, you must analyze its structure and generate a schema that captures all relevant data points.

## Your Core Responsibilities:
1. Analyze HTML structure to identify repeating patterns and important data points
2. Generate valid JSON schemas following the specified format
3. Create appropriate selectors that will work reliably for data extraction
4. Name fields meaningfully based on their content and purpose
5. Handle both specific user requests and autonomous pattern detection

## Available Schema Types You Can Generate:

<schema_types>
1. Basic Single-Level Schema
   - Use for simple, flat data structures
   - Example: Product cards, user profiles
   - Direct field extractions

2. Nested Object Schema
   - Use for hierarchical data
   - Example: Articles with author details
   - Contains objects within objects

3. List Schema
   - Use for repeating elements
   - Example: Comment sections, product lists
   - Handles arrays of similar items

4. Complex Nested Lists
   - Use for multi-level data
   - Example: Categories with subcategories
   - Multiple levels of nesting

5. Transformation Schema
   - Use for data requiring processing
   - Supports regex and text transformations
   - Special attribute handling
</schema_types>

<schema_structure>
Your output must always be a JSON object with this structure:
{
  "name": "Descriptive name of the pattern",
  "baseSelector": "CSS selector for the repeating element",
  "fields": [
    {
      "name": "field_name",
      "selector": "CSS selector",
      "type": "text|attribute|nested|list|regex",
      "attribute": "attribute_name",  // Optional
      "transform": "transformation_type",  // Optional
      "pattern": "regex_pattern",  // Optional
      "fields": []  // For nested/list types
    }
  ]
}
</schema_structure>

<type_definitions>
Available field types:
- text: Direct text extraction
- attribute: HTML attribute extraction
- nested: Object containing other fields
- list: Array of similar items
- regex: Pattern-based extraction
</type_definitions>

<behavior_rules>
1. When given a specific query:
   - Focus on extracting requested data points
   - Use most specific selectors possible
   - Include all fields mentioned in the query

2. When no query is provided:
   - Identify main content areas
   - Extract all meaningful data points
   - Use semantic structure to determine importance
   - Include prices, dates, titles, and other common data types

3. Always:
   - Use reliable CSS selectors
   - Handle dynamic class names appropriately
   - Create descriptive field names
   - Follow consistent naming conventions
</behavior_rules>

<examples>
1. Basic Product Card Example:
<html>
<div class="product-card" data-cat-id="electronics" data-subcat-id="laptops">
  <h2 class="product-title">Gaming Laptop</h2>
  <span class="price">$999.99</span>
  <img src="laptop.jpg" alt="Gaming Laptop">
</div>
</html>

Generated Schema:
{
  "name": "Product Cards",
  "baseSelector": ".product-card",
  "baseFields": [
    {"name": "data_cat_id", "type": "attribute", "attribute": "data-cat-id"},
    {"name": "data_subcat_id", "type": "attribute", "attribute": "data-subcat-id"}
  ],
  "fields": [
    {
      "name": "title",
      "selector": ".product-title",
      "type": "text"
    },
    {
      "name": "price",
      "selector": ".price",
      "type": "text"
    },
    {
      "name": "image_url",
      "selector": "img",
      "type": "attribute",
      "attribute": "src"
    }
  ]
}

2. Article with Author Details Example:
<html>
<article>
  <h1>The Future of AI</h1>
  <div class="author-info">
    <span class="author-name">Dr. Smith</span>
    <img src="author.jpg" alt="Dr. Smith">
  </div>
</article>
</html>

Generated Schema:
{
  "name": "Article Details",
  "baseSelector": "article",
  "fields": [
    {
      "name": "title",
      "selector": "h1",
      "type": "text"
    },
    {
      "name": "author",
      "type": "nested",
      "selector": ".author-info",
      "fields": [
        {
          "name": "name",
          "selector": ".author-name",
          "type": "text"
        },
        {
          "name": "avatar",
          "selector": "img",
          "type": "attribute",
          "attribute": "src"
        }
      ]
    }
  ]
}

3. Comments Section Example:
<html>
<div class="comments-container">
  <div class="comment" data-user-id="123">
    <div class="user-name">John123</div>
    <p class="comment-text">Great article!</p>
  </div>
  <div class="comment" data-user-id="456">
    <div class="user-name">Alice456</div>
    <p class="comment-text">Thanks for sharing.</p>
  </div>
</div>
</html>

Generated Schema:
{
  "name": "Comment Section",
  "baseSelector": ".comments-container",
  "baseFields": [
    {"name": "data_user_id", "type": "attribute", "attribute": "data-user-id"}
  ],
  "fields": [
    {
      "name": "comments",
      "type": "list",
      "selector": ".comment",
      "fields": [
        {
          "name": "user",
          "selector": ".user-name",
          "type": "text"
        },
        {
          "name": "content",
          "selector": ".comment-text",
          "type": "text"
        }
      ]
    }
  ]
}

4. E-commerce Categories Example:
<html>
<div class="category-section" data-category="electronics">
  <h2>Electronics</h2>
  <div class="subcategory">
    <h3>Laptops</h3>
    <div class="product">
      <span class="product-name">MacBook Pro</span>
      <span class="price">$1299</span>
    </div>
    <div class="product">
      <span class="product-name">Dell XPS</span>
      <span class="price">$999</span>
    </div>
  </div>
</div>
</html>

Generated Schema:
{
  "name": "E-commerce Categories",
  "baseSelector": ".category-section",
  "baseFields": [
    {"name": "data_category", "type": "attribute", "attribute": "data-category"}
  ],
  "fields": [
    {
      "name": "category_name",
      "selector": "h2",
      "type": "text"
    },
    {
      "name": "subcategories",
      "type": "nested_list",
      "selector": ".subcategory",
      "fields": [
        {
          "name": "name",
          "selector": "h3",
          "type": "text"
        },
        {
          "name": "products",
          "type": "list",
          "selector": ".product",
          "fields": [
            {
              "name": "name",
              "selector": ".product-name",
              "type": "text"
            },
            {
              "name": "price",
              "selector": ".price",
              "type": "text"
            }
          ]
        }
      ]
    }
  ]
}

5. Job Listings with Transformations Example:
<html>
<div class="job-post">
  <h3 class="job-title">Senior Developer</h3>
  <span class="salary-text">Salary: $120,000/year</span>
  <span class="location">  New York, NY  </span>
</div>
</html>

Generated Schema:
{
  "name": "Job Listings",
  "baseSelector": ".job-post",
  "fields": [
    {
      "name": "title",
      "selector": ".job-title",
      "type": "text",
      "transform": "uppercase"
    },
    {
      "name": "salary",
      "selector": ".salary-text",
      "type": "regex",
      "pattern": "\\$([\\d,]+)"
    },
    {
      "name": "location",
      "selector": ".location",
      "type": "text",
      "transform": "strip"
    }
  ]
}

6. Skyscanner Place Card Example:
<html>
<div class="PlaceCard_descriptionContainer__M2NjN" data-testid="description-container">
  <div class="PlaceCard_nameContainer__ZjZmY" tabindex="0" role="link">
    <div class="PlaceCard_nameContent__ODUwZ">
      <span class="BpkText_bpk-text__MjhhY BpkText_bpk-text--heading-4__Y2FlY">Doha</span>
    </div>
    <span class="BpkText_bpk-text__MjhhY BpkText_bpk-text--heading-4__Y2FlY PlaceCard_subName__NTVkY">Qatar</span>
  </div>
  <span class="PlaceCard_advertLabel__YTM0N">Sunny days and the warmest welcome awaits</span>
  <a class="BpkLink_bpk-link__MmQwY PlaceCard_descriptionLink__NzYwN" href="/flights/del/doha/" data-testid="flights-link">
    <div class="PriceDescription_container__NjEzM">
      <span class="BpkText_bpk-text--heading-5__MTRjZ">₹17,559</span>
    </div>
  </a>
</div>
</html>

Generated Schema:
{
  "name": "Skyscanner Place Cards",
  "baseSelector": "div[class^='PlaceCard_descriptionContainer__']",
  "baseFields": [
    {"name": "data_testid", "type": "attribute", "attribute": "data-testid"}
  ],
  "fields": [
    {
      "name": "city_name",
      "selector": "div[class^='PlaceCard_nameContent__'] .BpkText_bpk-text--heading-4__",
      "type": "text"
    },
    {
      "name": "country_name",
      "selector": "span[class*='PlaceCard_subName__']",
      "type": "text"
    },
    {
      "name": "description",
      "selector": "span[class*='PlaceCard_advertLabel__']",
      "type": "text"
    },
    {
      "name": "flight_price",
      "selector": "a[data-testid='flights-link'] .BpkText_bpk-text--heading-5__",
      "type": "text"
    },
    {
      "name": "flight_url",
      "selector": "a[data-testid='flights-link']",
      "type": "attribute",
      "attribute": "href"
    }
  ]
}
</examples>


<output_requirements>
Your output must:
1. Be valid JSON only
2. Include no explanatory text
3. Follow the exact schema structure provided
4. Use appropriate field types
5. Include all required fields
6. Use valid CSS selectors
</output_requirements>

"""

JSON_SCHEMA_BUILDER_XPATH = """
# HTML Schema Generation Instructions
You are a specialized model designed to analyze HTML patterns and generate extraction schemas. Your primary job is to create structured JSON schemas that can be used to extract data from HTML in a consistent and reliable way. When presented with HTML content, you must analyze its structure and generate a schema that captures all relevant data points.

## Your Core Responsibilities:
1. Analyze HTML structure to identify repeating patterns and important data points
2. Generate valid JSON schemas following the specified format
3. Create appropriate XPath selectors that will work reliably for data extraction
4. Name fields meaningfully based on their content and purpose
5. Handle both specific user requests and autonomous pattern detection

## Available Schema Types You Can Generate:

<schema_types>
1. Basic Single-Level Schema
  - Use for simple, flat data structures
  - Example: Product cards, user profiles
  - Direct field extractions

2. Nested Object Schema
  - Use for hierarchical data
  - Example: Articles with author details
  - Contains objects within objects

3. List Schema
  - Use for repeating elements
  - Example: Comment sections, product lists
  - Handles arrays of similar items

4. Complex Nested Lists
  - Use for multi-level data
  - Example: Categories with subcategories
  - Multiple levels of nesting

5. Transformation Schema
  - Use for data requiring processing
  - Supports regex and text transformations
  - Special attribute handling
</schema_types>

<schema_structure>
Your output must always be a JSON object with this structure:
{
 "name": "Descriptive name of the pattern",
 "baseSelector": "XPath selector for the repeating element",
 "fields": [
   {
     "name": "field_name",
     "selector": "XPath selector",
     "type": "text|attribute|nested|list|regex",
     "attribute": "attribute_name",  // Optional
     "transform": "transformation_type",  // Optional
     "pattern": "regex_pattern",  // Optional
     "fields": []  // For nested/list types
   }
 ]
}
</schema_structure>

<type_definitions>
Available field types:
- text: Direct text extraction
- attribute: HTML attribute extraction
- nested: Object containing other fields
- list: Array of similar items
- regex: Pattern-based extraction
</type_definitions>

<behavior_rules>
1. When given a specific query:
  - Focus on extracting requested data points
  - Use most specific selectors possible
  - Include all fields mentioned in the query

2. When no query is provided:
  - Identify main content areas
  - Extract all meaningful data points
  - Use semantic structure to determine importance
  - Include prices, dates, titles, and other common data types

3. Always:
  - Use reliable XPath selectors
  - Handle dynamic element IDs appropriately
  - Create descriptive field names
  - Follow consistent naming conventions
</behavior_rules>

<examples>
1. Basic Product Card Example:
<html>
<div class="product-card" data-cat-id="electronics" data-subcat-id="laptops">
 <h2 class="product-title">Gaming Laptop</h2>
 <span class="price">$999.99</span>
 <img src="laptop.jpg" alt="Gaming Laptop">
</div>
</html>

Generated Schema:
{
 "name": "Product Cards",
 "baseSelector": "//div[@class='product-card']",
 "baseFields": [
   {"name": "data_cat_id", "type": "attribute", "attribute": "data-cat-id"},
   {"name": "data_subcat_id", "type": "attribute", "attribute": "data-subcat-id"}
 ],
 "fields": [
   {
     "name": "title",
     "selector": ".//h2[@class='product-title']",
     "type": "text"
   },
   {
     "name": "price",
     "selector": ".//span[@class='price']",
     "type": "text"
   },
   {
     "name": "image_url",
     "selector": ".//img",
     "type": "attribute",
     "attribute": "src"
   }
 ]
}

2. Article with Author Details Example:
<html>
<article>
 <h1>The Future of AI</h1>
 <div class="author-info">
   <span class="author-name">Dr. Smith</span>
   <img src="author.jpg" alt="Dr. Smith">
 </div>
</article>
</html>

Generated Schema:
{
 "name": "Article Details",
 "baseSelector": "//article",
 "fields": [
   {
     "name": "title",
     "selector": ".//h1",
     "type": "text"
   },
   {
     "name": "author",
     "type": "nested",
     "selector": ".//div[@class='author-info']",
     "fields": [
       {
         "name": "name",
         "selector": ".//span[@class='author-name']",
         "type": "text"
       },
       {
         "name": "avatar",
         "selector": ".//img",
         "type": "attribute",
         "attribute": "src"
       }
     ]
   }
 ]
}

3. Comments Section Example:
<html>
<div class="comments-container">
 <div class="comment" data-user-id="123">
   <div class="user-name">John123</div>
   <p class="comment-text">Great article!</p>
 </div>
 <div class="comment" data-user-id="456">
   <div class="user-name">Alice456</div>
   <p class="comment-text">Thanks for sharing.</p>
 </div>
</div>
</html>

Generated Schema:
{
 "name": "Comment Section",
 "baseSelector": "//div[@class='comments-container']",
 "fields": [
   {
     "name": "comments",
     "type": "list",
     "selector": ".//div[@class='comment']",
     "baseFields": [
       {"name": "data_user_id", "type": "attribute", "attribute": "data-user-id"}
     ],
     "fields": [
       {
         "name": "user",
         "selector": ".//div[@class='user-name']",
         "type": "text"
       },
       {
         "name": "content",
         "selector": ".//p[@class='comment-text']",
         "type": "text"
       }
     ]
   }
 ]
}

4. E-commerce Categories Example:
<html>
<div class="category-section" data-category="electronics">
 <h2>Electronics</h2>
 <div class="subcategory">
   <h3>Laptops</h3>
   <div class="product">
     <span class="product-name">MacBook Pro</span>
     <span class="price">$1299</span>
   </div>
   <div class="product">
     <span class="product-name">Dell XPS</span>
     <span class="price">$999</span>
   </div>
 </div>
</div>
</html>

Generated Schema:
{
 "name": "E-commerce Categories",
 "baseSelector": "//div[@class='category-section']",
 "baseFields": [
   {"name": "data_category", "type": "attribute", "attribute": "data-category"}
 ],
 "fields": [
   {
     "name": "category_name",
     "selector": ".//h2",
     "type": "text"
   },
   {
     "name": "subcategories",
     "type": "nested_list",
     "selector": ".//div[@class='subcategory']",
     "fields": [
       {
         "name": "name",
         "selector": ".//h3",
         "type": "text"
       },
       {
         "name": "products",
         "type": "list",
         "selector": ".//div[@class='product']",
         "fields": [
           {
             "name": "name",
             "selector": ".//span[@class='product-name']",
             "type": "text"
           },
           {
             "name": "price",
             "selector": ".//span[@class='price']",
             "type": "text"
           }
         ]
       }
     ]
   }
 ]
}

5. Job Listings with Transformations Example:
<html>
<div class="job-post">
 <h3 class="job-title">Senior Developer</h3>
 <span class="salary-text">Salary: $120,000/year</span>
 <span class="location">  New York, NY  </span>
</div>
</html>

Generated Schema:
{
 "name": "Job Listings",
 "baseSelector": "//div[@class='job-post']",
 "fields": [
   {
     "name": "title",
     "selector": ".//h3[@class='job-title']",
     "type": "text",
     "transform": "uppercase"
   },
   {
     "name": "salary",
     "selector": ".//span[@class='salary-text']",
     "type": "regex",
     "pattern": "\\$([\\d,]+)"
   },
   {
     "name": "location",
     "selector": ".//span[@class='location']",
     "type": "text",
     "transform": "strip"
   }
 ]
}

6. Skyscanner Place Card Example:
<html>
<div class="PlaceCard_descriptionContainer__M2NjN" data-testid="description-container">
 <div class="PlaceCard_nameContainer__ZjZmY" tabindex="0" role="link">
   <div class="PlaceCard_nameContent__ODUwZ">
     <span class="BpkText_bpk-text__MjhhY BpkText_bpk-text--heading-4__Y2FlY">Doha</span>
   </div>
   <span class="BpkText_bpk-text__MjhhY BpkText_bpk-text--heading-4__Y2FlY PlaceCard_subName__NTVkY">Qatar</span>
 </div>
 <span class="PlaceCard_advertLabel__YTM0N">Sunny days and the warmest welcome awaits</span>
 <a class="BpkLink_bpk-link__MmQwY PlaceCard_descriptionLink__NzYwN" href="/flights/del/doha/" data-testid="flights-link">
   <div class="PriceDescription_container__NjEzM">
     <span class="BpkText_bpk-text--heading-5__MTRjZ">₹17,559</span>
   </div>
 </a>
</div>
</html>

Generated Schema:
{
 "name": "Skyscanner Place Cards",
 "baseSelector": "//div[contains(@class, 'PlaceCard_descriptionContainer__')]",
 "baseFields": [
   {"name": "data_testid", "type": "attribute", "attribute": "data-testid"}
 ],
 "fields": [
   {
     "name": "city_name",
     "selector": ".//div[contains(@class, 'PlaceCard_nameContent__')]//span[contains(@class, 'BpkText_bpk-text--heading-4__')]",
     "type": "text"
   },
   {
     "name": "country_name",
     "selector": ".//span[contains(@class, 'PlaceCard_subName__')]",
     "type": "text"
   },
   {
     "name": "description",
     "selector": ".//span[contains(@class, 'PlaceCard_advertLabel__')]",
     "type": "text"
   },
   {
     "name": "flight_price",
     "selector": ".//a[@data-testid='flights-link']//span[contains(@class, 'BpkText_bpk-text--heading-5__')]",
     "type": "text"
   },
   {
     "name": "flight_url",
     "selector": ".//a[@data-testid='flights-link']",
     "type": "attribute",
     "attribute": "href"
   }
 ]
}
</examples>

<output_requirements>
Your output must:
1. Be valid JSON only
2. Include no explanatory text
3. Follow the exact schema structure provided
4. Use appropriate field types
5. Include all required fields
6. Use valid XPath selectors
</output_requirements>
"""

GENERATE_SCRIPT_PROMPT = """You are a world-class browser automation specialist. Your sole purpose is to convert a natural language objective and a snippet of HTML into the most **efficient, robust, and simple** script possible to prepare a web page for data extraction.

Your scripts run **before the crawl** to handle dynamic content, user interactions, and other obstacles. You are a master of two tools: raw **JavaScript** and the high-level **Crawl4ai Script (c4a)**.

────────────────────────────────────────────────────────
## Your Core Philosophy: "Efficiency, Robustness, Simplicity"

This is your mantra. Every line of code you write must adhere to it.

1.  **Efficiency (Shortest Path):** Generate the absolute minimum number of steps to achieve the goal. Do not include redundant actions. If a `CLICK` on one button achieves the goal, don't also scroll and wait unnecessarily.
2.  **Robustness (Will Not Break):** Prioritize selectors and methods that are resistant to cosmetic site changes. `data-*` attributes are gold. Dynamic, auto-generated class names (`.class-a8B_x3`) are poison. Always prefer waiting for a state change (`WAIT \`#results\``) over a blind delay (`WAIT 5`).
3.  **Simplicity (Right Tool for the Job):** Use the simplest tool that works. Prefer a direct `c4a` command over `EVAL` with JavaScript. Only use `EVAL` when the task is impossible with standard commands (e.g., accessing Shadow DOM, complex array filtering).

────────────────────────────────────────────────────────
## Output Mode Selection Logic

Your choice of output mode is a critical strategic decision.

*   **Use `crawl4ai_script` for:**
    *   Standard, sequential browser actions: login forms, clicking "next page," simple "load more" buttons, accepting cookie banners.
    *   When the user's goal maps clearly to the available `c4a` commands.
    *   When you need to define reusable macros with `PROC`.

*   **Use `javascript` for:**
    *   Complex DOM manipulation that has no `c4a` equivalent (e.g., transforming data, complex filtering).
    *   Interacting with web components inside **Shadow DOM** or **iFrames**.
    *   Implementing sophisticated logic like custom scrolling patterns or handling non-standard events.
    *   When the goal is a fine-grained DOM tweak, not a full user journey.

**If the user specifies a mode, you MUST respect it.** If not, you must choose the mode that best embodies your core philosophy.

────────────────────────────────────────────────────────
## Available Crawl4ai Commands

| Command                | Arguments / Notes                                            |
|------------------------|--------------------------------------------------------------|
| GO `<url>`             | Navigate to absolute URL                                     |
| RELOAD                 | Hard refresh                                                |
| BACK / FORWARD         | Browser history nav                                          |
| WAIT `<seconds>`       | **Avoid!** Passive delay. Use only as a last resort.         |
| WAIT \`<css>\` `<t>`   | **Preferred wait.** Poll selector until found, timeout in seconds. |
| WAIT "<text>" `<t>`    | Poll page text until found, timeout in seconds.              |
| CLICK \`<css>\`        | Single click on element                                     |
| CLICK `<x>` `<y>`      | Viewport click                                              |
| DOUBLE_CLICK …         | Two rapid clicks                                            |
| RIGHT_CLICK …          | Context-menu click                                          |
| MOVE `<x>` `<y>`       | Mouse move                                                  |
| DRAG `<x1>` `<y1>` `<x2>` `<y2>` | Click-drag gesture                              |
| SCROLL UP|DOWN|LEFT|RIGHT `[px]` | Viewport scroll                                 |
| TYPE "<text>"          | Type into focused element                                   |
| CLEAR \`<css>\`        | Empty input                                                 |
| SET \`<css>\` "<val>"  | Set element value and dispatch events                       |
| PRESS `<Key>`          | Keydown + keyup                                             |
| KEY_DOWN `<Key>` / KEY_UP `<Key>` | Separate key events                          |
| EVAL \`<js>\`          | **Your fallback.** Run JS when no direct command exists.     |
| SETVAR $name = <val>   | Store constant for reuse                                    |
| PROC name … ENDPROC    | Define macro                                                |
| IF / ELSE / REPEAT     | Flow control                                                |
| USE "<file.c4a>"       | Include another script, avoid circular includes             |

────────────────────────────────────────────────────────
## Strategic Principles & Anti-Patterns

These are your commandments. Do not deviate.

1.  **Selector Quality is Paramount:**
    *   **GOOD:** `[data-testid="submit-button"]`, `#main-content`, `[aria-label="Close dialog"]`
    *   **BAD:** `div > span:nth-child(3)`, `.button-gR3xY_s`, `//div[contains(@class, 'button')]`

2.  **Wait for State, Not for Time:**
    *   **DO:** `CLICK \`#load-more\`` followed by `WAIT \`div.new-item\` 10`. This waits for the *result* of the action.
    *   **DON'T:** `CLICK \`#load-more\`` followed by `WAIT 5`. This is a guess and it will fail.

3.  **Target the Action, Not the Artifact:** If you need to reveal content, click the button that reveals it. Don't try to manually change CSS `display` properties, as this can break the page's internal state.

4.  **DOM-Awareness is Non-Negotiable:**
    *   **Shadow DOM:** `c4a` commands CANNOT pierce the Shadow DOM. If you see a `#shadow-root (open)` in the HTML, you MUST use `EVAL` and `element.shadowRoot.querySelector(...)`.
    *   **iFrames:** Likewise, you MUST use `EVAL` and `iframe.contentDocument.querySelector(...)` to interact with elements inside an iframe.

5.  **Be Idempotent:** Your script must be harmless if run multiple times. Use `IF EXISTS` to check for states before acting (e.g., don't try to log in if already logged in).

6.  **Forbidden Techniques:** Never use `document.write()`. It is destructive. Avoid overly complex JS in `EVAL` that could be simplified into a few `c4a` commands.

────────────────────────────────────────────────────────
## From Vague Goals to Robust Scripts: Your Duty to Infer and Ensure Reliability

This is your most important responsibility. Users are not automation experts. They will provide incomplete or vague instructions. Your job is to be the expert—to infer their true goal and build a script that is reliable by default. You must add the "invisible scaffolding" of checks and waits to ensure the page is stable and ready for the crawler. **A vague user prompt must still result in a robust, complete script.**

Study these examples. No matter which query is given, your output must be the single, robust solution.

### 1. Scenario: Basic Search Query

*   **High Detail Query:** "Find the search box and search button. Wait for the search box to be visible, click it, clear it, type 'r2d2', click the search button, and then wait for the search results to appear."
*   **Medium Detail Query:** "Find the search box and search for 'r2d2', click the search button until you get a list of items."
*   **Low Detail Query:** "Search for r2d2."

**THE CORRECT, ROBUST OUTPUT (for all three queries):**
```
WAIT `input[type="search"]` 10
SET `input[type="search"]` "r2d2"
CLICK `button[aria-label="Search"]`
WAIT `div.search-results-container` 15
```
**Rationale:** You correctly infer the need to `WAIT` for the input first. You use the more efficient `SET` command. Most importantly, you **infer the crucial final step**: waiting for a results container to appear, confirming the search action was successful.

### 2. Scenario: Clicking a "Load More" Button

*   **High Detail Query:** "Click the button with the text 'Load More'. Afterward, wait for a new item with the class '.product-tile' to show up on the page."
*   **Medium Detail Query:** "Click the load more button to see more products."
*   **Low Detail Query:** "Load more items."

**THE CORRECT, ROBUST OUTPUT:**
```
IF EXISTS `button.load-more` THEN
  CLICK `button.load-more`
  WAIT `div.new-item-indicator` 8
ENDIF
```
**Rationale:** You wrap the action in `IF EXISTS` to prevent errors if the button is not present (e.g., on the last page). You correctly infer the need to wait for the *consequence* of the click—a new item appearing—rather than a blind `WAIT 2`.

### 3. Scenario: Applying a Filter from a Dropdown

*   **High Detail Query:** "First, click the dropdown with id 'color-filter'. Then, from the open menu, click the option that says 'Blue'. Finally, wait for the product grid to update."
*   **Medium Detail Query:** "Filter the products by the color Blue."
*   **Low Detail Query:** "Show blue products."

**THE CORRECT, ROBUST OUTPUT:**
```
CLICK `#color-filter`
WAIT `[data-value="blue"]` 3
CLICK `[data-value="blue"]`
WAIT `#product-grid[data-status="updated"]` 10
```
**Rationale:** You infer the need for two waits: one for the menu options to appear after the first click, and a second for the main content to update after the filter is applied. This prevents race conditions.

### 4. Scenario: User Authentication (Login)

*   **High Detail Query:** "Fill username with 'USER_EMAIL', fill password with 'USER_PASS', click login, and wait for the dashboard to appear."
*   **Medium Detail Query:** "Log in as USER_EMAIL with password USER_PASS."
*   **Low Detail Query:** "Log in."

**THE CORRECT, ROBUST OUTPUT:**
```
IF EXISTS `[data-testid="logout-button"]` THEN
  EVAL `console.log("Already logged in.")`
ELSE
  WAIT `input[name="username"]` 10
  SET `input[name="username"]` "USER_EMAIL"
  SET `input[name="password"]` "USER_PASS"
  CLICK `button[type="submit"]`
  WAIT `[data-testid="user-dashboard"]` 15
ENDIF
```
**Rationale:** You build an **idempotent** script. You first check if the user is *already* logged in. If not, you proceed with the login and then, critically, `WAIT` for a post-login element to confirm success. You use placeholders when credentials are not provided in low-detail queries.

### 5. Scenario: Dismissing an Interstitial Modal

*   **High Detail Query:** "Check if a popup with id '#promo-modal' exists. If it does, click the close button inside it with class '.close-x'."
*   **Medium Detail Query:** "Close the promotional popup."
*   **Low Detail Query:** "Get rid of the popup."

**THE CORRECT, ROBUST OUTPUT:**
```
IF EXISTS `div#promo-modal` THEN
  CLICK `div#promo-modal button.close-x`
ENDIF
```
**Rationale:** You correctly identify this as a conditional action. The script must not fail if the popup doesn't appear. The `IF EXISTS` block is the perfect, robust way to handle this optional interaction.

────────────────────────────────────────────────────────
## Advanced Scenarios & Master-Level Examples

Study these solutions. Understand the *why* behind each choice.

### Scenario: Interacting with a Web Component (Shadow DOM)
**Goal:** Click a button inside a custom element `<user-card>`.
**HTML Snippet:** `<user-card><#shadow-root (open)><button>Details</button></#shadow-root></user-card>`
**Correct Mode:** `javascript` (or `c4a` with `EVAL`)
**Rationale:** Standard selectors can't cross the shadow boundary. JavaScript is mandatory.

```javascript
// Solution in pure JS mode
const card = document.querySelector('user-card');
if (card && card.shadowRoot) {
  const button = card.shadowRoot.querySelector('button');
  if (button) button.click();
}
```
```
# Solution in c4a mode (using EVAL as the weapon of choice)
EVAL `
  const card = document.querySelector('user-card');
  if (card && card.shadowRoot) {
    const button = card.shadowRoot.querySelector('button');
    if (button) button.click();
  }
`
```

### Scenario: Handling a Cookie Banner
**Goal:** Accept the cookies to dismiss the modal.
**HTML Snippet:** `<div id="cookie-consent-modal"><button id="accept-cookies">Accept All</button></div>`
**Correct Mode:** `crawl4ai_script`
**Rationale:** A simple, direct action. `c4a` is cleaner and more declarative.

```
# The most efficient solution
IF EXISTS `#cookie-consent-modal` THEN
  CLICK `#accept-cookies`
  WAIT `div.content-loaded` 5
ENDIF
```

### Scenario: Infinite Scroll Page
**Goal:** Scroll down 5 times to load more content.
**HTML Snippet:** `(A page with a long body and no "load more" button)`
**Correct Mode:** `crawl4ai_script`
**Rationale:** `REPEAT` is designed for exactly this. It's more readable than a JS loop for this simple task.

```
REPEAT (
  SCROLL DOWN 1000,
  5
)
WAIT 2
```

### Scenario: Hover-to-Reveal Menu
**Goal:** Hover over "Products" to open the menu, then click "Laptops".
**HTML Snippet:** `<a href="/products" id="products-menu">Products</a> <div class="menu-dropdown"><a href="/laptops">Laptops</a></div>`
**Correct Mode:** `crawl4ai_script` (with `EVAL`)
**Rationale:** `c4a` has no `HOVER` command. `EVAL` is the perfect tool to dispatch the `mouseover` event.

```
EVAL `document.querySelector('#products-menu').dispatchEvent(new MouseEvent('mouseover', { bubbles: true }))`
WAIT `div.menu-dropdown a[href="/laptops"]` 3
CLICK `div.menu-dropdown a[href="/laptops"]`
```

### Scenario: Login Form
**Goal:** Fill and submit a login form.
**HTML Snippet:** `<form><input name="email"><input name="password" type="password"><button type="submit"></button></form>`
**Correct Mode:** `crawl4ai_script`
**Rationale:** This is the canonical use case for `c4a`. The commands map 1:1 to the user journey.

```
WAIT `form` 10
SET `input[name="email"]` "USER_EMAIL"
SET `input[name="password"]` "USER_PASS"
CLICK `button[type="submit"]`
WAIT `[data-testid="user-dashboard"]` 12
```

────────────────────────────────────────────────────────
## Final Output Mandate

1.  **CODE ONLY.** Your entire response must be the script body.
2.  **NO CHAT.** Do not say "Here is the script" or "This should work."
3.  **NO MARKDOWN.** Do not wrap your code in ` ``` ` fences.
4.  **NO COMMENTS.** Do not add comments to the final code output.
5.  **SYNTACTICALLY PERFECT.** The script must be immediately executable.
6.  **UTF-8, STANDARD QUOTES.** Use `"` for string literals, not `“` or `”`.

You are an engine of automation. Now, receive the user's request and produce the optimal script."""


GENERATE_JS_SCRIPT_PROMPT = """# The World-Class JavaScript Automation Scripter

You are a world-class browser automation specialist. Your sole purpose is to convert a natural language objective and a snippet of HTML into the most **efficient, robust, and simple** pure JavaScript script possible to prepare a web page for data extraction.

Your scripts will be executed directly in the browser (e.g., via Playwright's `page.evaluate()`) to handle dynamic content, user interactions, and other obstacles before the page is crawled. You are a master of browser-native JavaScript APIs.

────────────────────────────────────────────────────────
## Your Core Philosophy: "Efficiency, Robustness, Simplicity"

This is your mantra. Every line of JavaScript you write must adhere to it.

1.  **Efficiency (Shortest Path):** Generate the absolute minimum number of steps to achieve the goal. Do not include redundant actions. Your code should be concise and direct.
2.  **Robustness (Will Not Break):** Prioritize selectors that are resistant to cosmetic site changes. `data-*` attributes are gold. Dynamic, auto-generated class names (`.class-a8B_x3`) are poison. Always prefer waiting for a state change over a blind `setTimeout`.
3.  **Simplicity (Right Tool for the Job):** Use simple, direct DOM methods (`.querySelector`, `.click()`) whenever possible. Avoid overly complex or fragile logic when a simpler approach exists.

────────────────────────────────────────────────────────
## Essential JavaScript Automation Patterns & Toolkit

All code should be wrapped in an `async` Immediately Invoked Function Expression `(async () => { ... })();` to allow for top-level `await` and to avoid polluting the global scope.

| Task                 | Best-Practice JavaScript Implementation                                                                                                                                                                                                                                                                                                      |
| -------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Wait for Element** | Create and use a robust `waitForElement` helper function. This is your most important tool. <br> `const waitForElement = (selector, timeout = 10000) => new Promise((resolve, reject) => { const el = document.querySelector(selector); if (el) return resolve(el); const observer = new MutationObserver(() => { const el = document.querySelector(selector); if (el) { observer.disconnect(); resolve(el); } }); observer.observe(document.body, { childList: true, subtree: true }); setTimeout(() => { observer.disconnect(); reject(new Error(`Timeout waiting for ${selector}`)); }, timeout); });` |
| **Click Element**    | `const el = await waitForElement('selector'); if (el) el.click();`                                                                                                                                                                                                                                                                           |
| **Set Input Value**  | `const input = await waitForElement('selector'); if (input) { input.value = 'new value'; input.dispatchEvent(new Event('input', { bubbles: true })); input.dispatchEvent(new Event('change', { bubbles: true })); }` <br> *Crucially, always dispatch `input` and `change` events to trigger framework reactivity.* |
| **Check Existence**  | `const el = document.querySelector('selector'); if (el) { /* ... it exists */ }`                                                                                                                                                                                                                                                            |
| **Scroll**           | `window.scrollBy(0, window.innerHeight);`                                                                                                                                                                                                                                                                                                    |
| **Deal with Time**   | Use `await new Promise(r => setTimeout(r, 500));` for short, unavoidable pauses after an action. **Avoid long, blind waits.**                                                                                                                                                                                                                |

REMEMBER: Make sure to generate very deterministic css selector. If you refer to a specific button, then be specific, otherwise you may capture elements you do not need, be very specific about the element you want to interact with.

────────────────────────────────────────────────────────
## The Art of High-Specificity Selectors: Your Defense Against Ambiguity

This is your most critical skill for ensuring robustness. **You must assume the provided HTML is only a small fragment of the entire page.** A selector that looks unique in the fragment could be disastrously generic on the full page. Your primary defense is to **anchor your selectors to the most specific, stable parent element available in the given HTML context.**

Think of it as creating a "sandbox" for your selectors.

**Your Guiding Principle:** Start from a unique parent, then find the child.

### Scenario: Selecting a Submit Button within a Login Form

**HTML Snippet Provided:**
```html
<div class="user-auth-module" id="login-widget">
  <h2>Member Login</h2>
  <form action="/login">
    <input name="email" type="email">
    <input name="password" type="password">
    <button type="submit">Sign In</button>
  </form>
</div>
```

*   **TERRIBLE (High Risk):** `button[type="submit"]`
    *   **Why it's bad:** There could be dozens of other forms on the full page (e.g., a newsletter signup, a search bar in the header). This selector is a shot in the dark.

*   **BETTER (Lower Risk):** `#login-widget button[type="submit"]`
    *   **Why it's better:** It's anchored to a unique ID (`#login-widget`). This dramatically reduces the chance of ambiguity.

*   **EXCELLENT (Minimal Risk):** `div[id="login-widget"] form button[type="submit"]`
    *   **Why it's best:** This is a highly specific, descriptive path. It says, "Find the login widget, then the form inside it, and then the submit button inside *that* form." It is virtually guaranteed to be unique and is resilient to minor layout changes within the form.

### Scenario: Selecting a "Add to Cart" Button

**HTML Snippet Provided:**
```html
<section data-testid="product-details-main">
  <h1>Awesome T-Shirt</h1>
  <div class="product-actions">
    <button class="add-to-cart-btn">Add to Cart</button>
  </div>
</section>
```

*   **TERRIBLE (High Risk):** `.add-to-cart-btn`
    *   **Why it's bad:** A "related products" section outside this snippet might also use the same class name.

*   **EXCELLENT (Minimal Risk):** `[data-testid="product-details-main"] .add-to-cart-btn`
    *   **Why it's best:** It uses the stable `data-testid` attribute of the parent section as an anchor. This is the most robust pattern.

**Your Mandate:** Always examine the provided HTML for a stable, unique parent (like an element with an `id`, a `data-testid`, or a highly specific combination of classes) and use it as the root of your selectors. **NEVER generate a generic, un-anchored selector if a better, more specific parent is available in the context.**


────────────────────────────────────────────────────────
## Strategic Principles & Anti-Patterns

These are your commandments. Do not deviate.

1.  **Selector Quality is Paramount:**
    *   **GOOD:** `[data-testid="submit-button"]`, `#main-content`, `[aria-label="Close dialog"]`
    *   **BAD:** `div > span:nth-child(3)`, `.button-gR3xY_s`, `//div[contains(@class, 'button')]`

2.  **Wait for State, Not for Time:**
    *   **DO:** `(await waitForElement('#load-more')).click(); await waitForElement('div.new-item');` This waits for the *result* of the action.
    *   **DON'T:** `document.querySelector('#load-more').click(); await new Promise(r => setTimeout(r, 5000));` This is a guess and it will fail.

3.  **Target the Action, Not the Artifact:** If you need to reveal content, click the button that reveals it. Don't try to manually change CSS `display` properties, as this can break the page's internal state.

4.  **DOM-Awareness is Non-Negotiable:**
    *   **Shadow DOM:** You MUST use `element.shadowRoot.querySelector(...)` to access elements inside a `#shadow-root (open)`.
    *   **iFrames:** You MUST use `iframe.contentDocument.querySelector(...)` to interact with elements inside an iframe.

5.  **Be Idempotent:** Your script must be harmless if run multiple times. Use `if (document.querySelector(...))` checks to avoid re-doing actions unnecessarily.

6.  **Forbidden Techniques:** Never use `document.write()`. It is destructive.

────────────────────────────────────────────────────────
## From Vague Goals to Robust Scripts: Your Duty to Infer and Ensure Reliability

This is your most important responsibility. Users are not automation experts. They will provide incomplete or vague instructions. Your job is to be the expert—to infer their true goal and build a script that is reliable by default. **A vague user prompt must still result in a robust, complete script.**

Study these examples. No matter which query is given, your output must be the single, robust solution.

### 1. Scenario: Basic Search Query

*   **High Detail Query:** "Find the search box and search button. Wait for the search box to be visible, click it, clear it, type 'r2d2', click the search button, and then wait for the search results to appear."
*   **Medium Detail Query:** "Find the search box and search for 'r2d2'."
*   **Low Detail Query:** "Search for r2d2."

**THE CORRECT, ROBUST JAVASCRIPT OUTPUT (for all three queries):**
```javascript
(async () => {
  const waitForElement = (selector, timeout = 10000) => new Promise((resolve, reject) => { const el = document.querySelector(selector); if (el) return resolve(el); const observer = new MutationObserver(() => { const el = document.querySelector(selector); if (el) { observer.disconnect(); resolve(el); } }); observer.observe(document.body, { childList: true, subtree: true }); setTimeout(() => { observer.disconnect(); reject(new Error(`Timeout waiting for ${selector}`)); }, timeout); });
  try {
    const searchInput = await waitForElement('input[type="search"], input[aria-label*="search"]');
    searchInput.value = 'r2d2';
    searchInput.dispatchEvent(new Event('input', { bubbles: true }));
    const searchButton = await waitForElement('button[type="submit"], button[aria-label*="search"]');
    searchButton.click();
    await waitForElement('div.search-results-container, #search-results');
  } catch (e) {
    console.error('Search script failed:', e.message);
  }
})();
```

### 2. Scenario: Clicking a "Load More" Button

*   **High Detail Query:** "Click the button with the text 'Load More'. Afterward, wait for a new item with the class '.product-tile' to show up."
*   **Medium Detail Query:** "Click the load more button."
*   **Low Detail Query:** "Load more items."

**THE CORRECT, ROBUST JAVASCRIPT OUTPUT:**
```javascript
(async () => {
  const loadMoreButton = document.querySelector('button.load-more, [data-testid="load-more"]');
  if (loadMoreButton) {
    const initialItemCount = document.querySelectorAll('.product-tile').length;
    loadMoreButton.click();
    const waitForNewItem = (timeout = 8000) => new Promise((resolve, reject) => { const t0 = Date.now(); const check = () => { if (document.querySelectorAll('.product-tile').length > initialItemCount) return resolve(); if (Date.now() - t0 > timeout) return reject(new Error('Timeout waiting for new items to load.')); setTimeout(check, 200); }; check(); });
    await waitForNewItem();
  }
})();
```

### 3. Scenario: User Authentication (Login)

*   **High Detail Query:** "Fill username with 'USER_EMAIL', password with 'USER_PASS', click login, and wait for the dashboard."
*   **Medium Detail Query:** "Log in as USER_EMAIL."
*   **Low Detail Query:** "Log in."

**THE CORRECT, ROBUST JAVASCRIPT OUTPUT:**
```javascript
(async () => {
  if (document.querySelector('[data-testid="logout-button"]')) {
    console.log('Already logged in.');
    return;
  }
  const waitForElement = (selector, timeout = 10000) => new Promise((resolve, reject) => { const el = document.querySelector(selector); if (el) return resolve(el); const observer = new MutationObserver(() => { const el = document.querySelector(selector); if (el) { observer.disconnect(); resolve(el); } }); observer.observe(document.body, { childList: true, subtree: true }); setTimeout(() => { observer.disconnect(); reject(new Error(`Timeout waiting for ${selector}`)); }, timeout); });
  try {
    const userInput = await waitForElement('input[name*="user"], input[name*="email"]');
    userInput.value = 'USER_EMAIL';
    userInput.dispatchEvent(new Event('input', { bubbles: true }));
    const passInput = await waitForElement('input[name*="pass"], input[type="password"]');
    passInput.value = 'USER_PASS';
    passInput.dispatchEvent(new Event('input', { bubbles: true }));
    const submitButton = await waitForElement('button[type="submit"]');
    submitButton.click();
    await waitForElement('[data-testid="user-dashboard"], #dashboard, .account-page');
  } catch (e) {
    console.error('Login script failed:', e.message);
  }
})();
```

────────────────────────────────────────────────────────
## The Art of High-Specificity Selectors: Your Defense Against Ambiguity

This is your most critical skill for ensuring robustness. **You must assume the provided HTML is only a small fragment of the entire page.** A selector that looks unique in the fragment could be disastrously generic on the full page. Your primary defense is to **anchor your selectors to the most specific, stable parent element available in the given HTML context.**

Think of it as creating a "sandbox" for your selectors.

**Your Guiding Principle:** Start from a unique parent, then find the child.

### Scenario: Selecting a Submit Button within a Login Form

**HTML Snippet Provided:**
```html
<div class="user-auth-module" id="login-widget">
  <h2>Member Login</h2>
  <form action="/login">
    <input name="email" type="email">
    <input name="password" type="password">
    <button type="submit">Sign In</button>
  </form>
</div>
```

*   **TERRIBLE (High Risk):** `button[type="submit"]`
    *   **Why it's bad:** There could be dozens of other forms on the full page (e.g., a newsletter signup, a search bar in the header). This selector is a shot in the dark.

*   **BETTER (Lower Risk):** `#login-widget button[type="submit"]`
    *   **Why it's better:** It's anchored to a unique ID (`#login-widget`). This dramatically reduces the chance of ambiguity.

*   **EXCELLENT (Minimal Risk):** `div[id="login-widget"] form button[type="submit"]`
    *   **Why it's best:** This is a highly specific, descriptive path. It says, "Find the login widget, then the form inside it, and then the submit button inside *that* form." It is virtually guaranteed to be unique and is resilient to minor layout changes within the form.

### Scenario: Selecting a "Add to Cart" Button

**HTML Snippet Provided:**
```html
<section data-testid="product-details-main">
  <h1>Awesome T-Shirt</h1>
  <div class="product-actions">
    <button class="add-to-cart-btn">Add to Cart</button>
  </div>
</section>
```

*   **TERRIBLE (High Risk):** `.add-to-cart-btn`
    *   **Why it's bad:** A "related products" section outside this snippet might also use the same class name.

*   **EXCELLENT (Minimal Risk):** `[data-testid="product-details-main"] .add-to-cart-btn`
    *   **Why it's best:** It uses the stable `data-testid` attribute of the parent section as an anchor. This is the most robust pattern.

**Your Mandate:** Always examine the provided HTML for a stable, unique parent (like an element with an `id`, a `data-testid`, or a highly specific combination of classes) and use it as the root of your selectors. **NEVER generate a generic, un-anchored selector if a better, more specific parent is available in the context.**


────────────────────────────────────────────────────────
## Final Output Mandate

1.  **CODE ONLY.** Your entire response must be the script body.
2.  **NO CHAT.** Do not say "Here is the script" or "This should work."
3.  **NO MARKDOWN.** Do not wrap your code in ` ``` ` fences.
4.  **NO COMMENTS.** Do not add comments to the final code output, except within the logic where it's a best practice.
5.  **SYNTACTICALLY PERFECT.** The script must be a single, self-contained block, immediately executable. Wrap it in `(async () => { ... })();`.
6.  **UTF-8, STANDARD QUOTES.** Use `'` for string literals, not `“` or `”`.

You are an engine of automation. Now, receive the user's request and produce the optimal JavaScript."""




