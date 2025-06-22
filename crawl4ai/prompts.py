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
