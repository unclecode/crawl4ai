Here’s a detailed outline for the **JSON-CSS Extraction Strategy** video, covering all key aspects and supported structures in Crawl4AI:

---

### **10.1 JSON-CSS Extraction Strategy**

#### **1. Introduction to JSON-CSS Extraction**
   - JSON-CSS Extraction is used for pulling structured data from pages with repeated patterns, like product listings, article feeds, or directories.
   - This strategy allows defining a schema with CSS selectors and data fields, making it easy to capture nested, list-based, or singular elements.

#### **2. Basic Schema Structure**
   - **Schema Fields**: The schema has two main components:
     - `baseSelector`: A CSS selector to locate the main elements you want to extract (e.g., each article or product block).
     - `fields`: Defines the data fields for each element, supporting various data types and structures.

#### **3. Simple Field Extraction**
   - **Example HTML**:
     ```html
     <div class="product">
         <h2 class="title">Sample Product</h2>
         <span class="price">$19.99</span>
         <p class="description">This is a sample product.</p>
     </div>
     ```
   - **Schema**:
     ```python
     schema = {
         "baseSelector": ".product",
         "fields": [
             {"name": "title", "selector": ".title", "type": "text"},
             {"name": "price", "selector": ".price", "type": "text"},
             {"name": "description", "selector": ".description", "type": "text"}
         ]
     }
     ```
   - **Explanation**: Each field captures text content from specified CSS selectors within each `.product` element.

#### **4. Supported Field Types: Text, Attribute, HTML, Regex**
   - **Field Type Options**:
     - `text`: Extracts visible text.
     - `attribute`: Captures an HTML attribute (e.g., `src`, `href`).
     - `html`: Extracts the raw HTML of an element.
     - `regex`: Allows regex patterns to extract part of the text.

   - **Example HTML** (including an image):
     ```html
     <div class="product">
         <h2 class="title">Sample Product</h2>
         <img class="product-image" src="image.jpg" alt="Product Image">
         <span class="price">$19.99</span>
         <p class="description">Limited time offer.</p>
     </div>
     ```
   - **Schema**:
     ```python
     schema = {
         "baseSelector": ".product",
         "fields": [
             {"name": "title", "selector": ".title", "type": "text"},
             {"name": "image_url", "selector": ".product-image", "type": "attribute", "attribute": "src"},
             {"name": "price", "selector": ".price", "type": "regex", "pattern": r"\$(\d+\.\d+)"},
             {"name": "description_html", "selector": ".description", "type": "html"}
         ]
     }
     ```
   - **Explanation**:
     - `attribute`: Extracts the `src` attribute from `.product-image`.
     - `regex`: Extracts the numeric part from `$19.99`.
     - `html`: Retrieves the full HTML of the description element.

#### **5. Nested Field Extraction**
   - **Use Case**: Useful when content contains sub-elements, such as an article with author details within it.
   - **Example HTML**:
     ```html
     <div class="article">
         <h1 class="title">Sample Article</h1>
         <div class="author">
             <span class="name">John Doe</span>
             <span class="bio">Writer and editor</span>
         </div>
     </div>
     ```
   - **Schema**:
     ```python
     schema = {
         "baseSelector": ".article",
         "fields": [
             {"name": "title", "selector": ".title", "type": "text"},
             {"name": "author", "type": "nested", "selector": ".author", "fields": [
                 {"name": "name", "selector": ".name", "type": "text"},
                 {"name": "bio", "selector": ".bio", "type": "text"}
             ]}
         ]
     }
     ```
   - **Explanation**:
     - `nested`: Extracts `name` and `bio` within `.author`, grouping the author details in a single `author` object.

#### **6. List and Nested List Extraction**
   - **List**: Extracts multiple elements matching the selector as a list.
   - **Nested List**: Allows lists within lists, useful for items with sub-lists (e.g., specifications for each product).
   - **Example HTML**:
     ```html
     <div class="product">
         <h2 class="title">Product with Features</h2>
         <ul class="features">
             <li class="feature">Feature 1</li>
             <li class="feature">Feature 2</li>
             <li class="feature">Feature 3</li>
         </ul>
     </div>
     ```
   - **Schema**:
     ```python
     schema = {
         "baseSelector": ".product",
         "fields": [
             {"name": "title", "selector": ".title", "type": "text"},
             {"name": "features", "type": "list", "selector": ".features .feature", "fields": [
                 {"name": "feature", "type": "text"}
             ]}
         ]
     }
     ```
   - **Explanation**:
     - `list`: Captures each `.feature` item within `.features`, outputting an array of features under the `features` field.

#### **7. Transformations for Field Values**
   - Transformations allow you to modify extracted values (e.g., converting to lowercase).
   - Supported transformations: `lowercase`, `uppercase`, `strip`.
   - **Example HTML**:
     ```html
     <div class="product">
         <h2 class="title">Special Product</h2>
     </div>
     ```
   - **Schema**:
     ```python
     schema = {
         "baseSelector": ".product",
         "fields": [
             {"name": "title", "selector": ".title", "type": "text", "transform": "uppercase"}
         ]
     }
     ```
   - **Explanation**: The `transform` property changes the `title` to uppercase, useful for standardized outputs.

#### **8. Full JSON-CSS Extraction Example**
   - Combining all elements in a single schema example for a comprehensive crawl:
   - **Example HTML**:
     ```html
     <div class="product">
         <h2 class="title">Featured Product</h2>
         <img class="product-image" src="product.jpg">
         <span class="price">$99.99</span>
         <p class="description">Best product of the year.</p>
         <ul class="features">
             <li class="feature">Durable</li>
             <li class="feature">Eco-friendly</li>
         </ul>
     </div>
     ```
   - **Schema**:
     ```python
     schema = {
         "baseSelector": ".product",
         "fields": [
             {"name": "title", "selector": ".title", "type": "text", "transform": "uppercase"},
             {"name": "image_url", "selector": ".product-image", "type": "attribute", "attribute": "src"},
             {"name": "price", "selector": ".price", "type": "regex", "pattern": r"\$(\d+\.\d+)"},
             {"name": "description", "selector": ".description", "type": "html"},
             {"name": "features", "type": "list", "selector": ".features .feature", "fields": [
                 {"name": "feature", "type": "text"}
             ]}
         ]
     }
     ```
   - **Explanation**: This schema captures and transforms each aspect of the product, illustrating the JSON-CSS strategy’s versatility for structured extraction.

#### **9. Wrap Up & Next Steps**
   - Summarize JSON-CSS Extraction’s flexibility for structured, pattern-based extraction.
   - Tease the next video: **10.2 LLM Extraction Strategy**, focusing on using language models to extract data based on intelligent content analysis.

---

This outline covers each JSON-CSS Extraction option in Crawl4AI, with practical examples and schema configurations, making it a thorough guide for users.