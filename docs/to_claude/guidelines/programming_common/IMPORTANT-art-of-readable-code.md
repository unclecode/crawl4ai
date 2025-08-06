<!-- ---
!-- Timestamp: 2025-05-25 23:31:54
!-- Author: ywatanabe
!-- File: /ssh:sp:/home/ywatanabe/.claude/to_claude/guidelines/programming_common/art-of-readable-code.md
!-- --- -->


Code should minimize the time and effort needed for others to understand it. Readable code directly improves maintainability, reduces bugs, and enhances team productivity.
_____________________________________

## Core Philosophy
1. Code should be easy to understand for humans.
2. Readability is more important than being clever.
3. The measure of good code is how long it takes someone else to understand it.
4. Simplicity trumps familiarity.

## Naming Rules
1. Use specific, precise names that convey meaning.
2. Choose names at appropriate level of abstraction.
3. Add prefixes/suffixes when they add vital information.
4. Establish consistent naming patterns within your codebase.
5. Use descriptive verbs for function names.
6. Avoid ambiguous abbreviations and acronyms.
7. Prioritize clarity over brevity.

### Variable and Function Naming

**DO NOT**
```python
def get_data(d, t, fl):
    r = []
    for i in d:
        if i['tp'] == t and i['age'] > 30 and i['act'] == fl:
            r.append(i)
    return r
```

**DO**
```python
def filter_active_users_by_type(users, user_type, is_active):
    """Return users of specified type who are active and over 30."""
    filtered_users = []
    for user in users:
        if (user['type'] == user_type and 
            user['age'] > 30 and 
            user['active'] == is_active):
            filtered_users.append(user)
    return filtered_users
```

### Machine Learning Code Naming

**DO NOT**
```python
def proc(X, y, f=10, a=0.01, i=1000):
    m = len(X)
    w = np.zeros(X.shape[1])
    b = 0
    for _ in range(i):
        z = np.dot(X, w) + b
        p = 1 / (1 + np.exp(-z))
        g_w = (1/m) * np.dot(X.T, (p - y))
        g_b = (1/m) * np.sum(p - y)
        if _ % f == 0:
            c = (-1/m) * np.sum(y*np.log(p) + (1-y)*np.log(1-p))
            print(f"Cost: {c}")
        w -= a * g_w
        b -= a * g_b
    return w, b
```

**DO**
```python
def train_logistic_regression(features, labels, print_every=10, 
                             learning_rate=0.01, max_iterations=1000):
    """Train a logistic regression model using gradient descent.
    
    Args:
        features: Training features matrix (n_samples, n_features)
        labels: Target binary labels (n_samples,)
        print_every: Print cost every n iterations
        learning_rate: Step size for gradient descent
        max_iterations: Maximum number of training iterations
        
    Returns:
        weights, bias: Trained model parameters
    """
    num_samples = len(features)
    weights = np.zeros(features.shape[1])
    bias = 0
    
    for iteration in range(max_iterations):
        # Forward pass
        linear_predictions = np.dot(features, weights) + bias
        predictions = 1 / (1 + np.exp(-linear_predictions))
        
        # Compute gradients
        weight_gradient = (1/num_samples) * np.dot(features.T, (predictions - labels))
        bias_gradient = (1/num_samples) * np.sum(predictions - labels)
        
        # Print cost if needed
        if iteration % print_every == 0:
            cost = (-1/num_samples) * np.sum(
                labels * np.log(predictions) + 
                (1-labels) * np.log(1-predictions)
            )
            print(f"Iteration {iteration}, Cost: {cost:.6f}")
            
        # Update parameters
        weights -= learning_rate * weight_gradient
        bias -= learning_rate * bias_gradient
        
    return weights, bias
```

## Aesthetics
1. Use consistent formatting throughout the codebase.
2. Break code into logical "paragraphs" separated by blank lines.
3. Align code with similar structure when it helps identify patterns.
4. Use whitespace strategically to group related items.
5. Keep lines short enough to be easily scanned.
6. Maintain consistent indentation.

### Code Formatting

**DO NOT**
```python
def calculate_total(items,tax,discount):
    result=0;
    for i in range(len(items)):result+=items[i]
    if discount:result*=0.9
    return result*(1+tax)
```

**DO**
```python
def calculate_total(items, tax, apply_discount):
    """Calculate the total price with tax and optional discount."""
    subtotal = 0
    
    # Sum all item prices
    for item in items:
        subtotal += item
    
    # Apply discount if needed
    if apply_discount:
        subtotal *= 0.9  # 10% discount
    
    # Add tax and return
    return subtotal * (1 + tax)
```

### Configuration Formatting

**DO NOT**
```python
DEFAULT_SETTINGS={"timeout":30,"retries":3,"log_level":"INFO","cache_size":100,"max_connections":5,"debug":False,"user_agent":"MyApp/1.0","ssl_verify":True,"chunk_size":8192,"base_url":"https://api.example.com/v1","poll_interval":5}
```

**DO**
```python
DEFAULT_SETTINGS = {
    # Connection settings
    "timeout": 30,
    "retries": 3,
    "max_connections": 5,
    "poll_interval": 5,
    
    # Server configuration
    "base_url": "https://api.example.com/v1",
    "ssl_verify": True,
    
    # Request settings
    "user_agent": "MyApp/1.0",
    "chunk_size": 8192,
    
    # Debugging options
    "log_level": "INFO",
    "debug": False,
    
    # Cache configuration
    "cache_size": 100,
}
```

## Comments Rules
1. Focus on explaining "why" not "what" in comments.
2. Document assumptions, edge cases, and non-obvious constraints.
3. Use "director commentary" to explain tricky sections.
4. Add summary comments for complex blocks of code.
5. Avoid redundant comments that repeat the code.
6. Use markers like TODO, FIXME consistently.
7. Update comments when code changes.

### Basic Comments

**DO NOT**
```python
# This function adds a and b
def add(a, b):
    return a + b  # Return the sum

# Loop through array
for i in range(len(data)):
    # Get the current item
    item = data[i]
    # Process item
    process(item)
```

**DO**
```python
# Apply Gaussian blur using a 9-step approximation
# instead of the full algorithm for performance reasons
def fast_gaussian_blur(image_data, radius):
    # Early return for edge case - no blur needed
    if radius < 1:
        return image_data
    
    # Implementation works in-place to avoid extra allocations
    # which is critical for large images
    # ... implementation ...
    
    return image_data
```

### API Documentation

**DO NOT**
```python
def authenticate(username, password):
    """Authenticates a user."""
    # Code to check password
    if check_password(username, password):
        token = generate_token(username)
        return token
    else:
        return None
```

**DO**
```python
def authenticate(username, password):
    """Authenticate a user and generate an access token.
    
    Args:
        username: The user's username (case-sensitive)
        password: The user's plain-text password
        
    Returns:
        str: A JWT token that's valid for 24 hours if authentication succeeds
        None: If authentication fails
        
    Raises:
        RateLimitError: If too many failed attempts from this IP address
        LockoutError: If account is locked due to multiple failed attempts
        
    Security note:
        While this function accepts plain-text passwords, they're never stored
        in raw form. Passwords are verified against salted bcrypt hashes in the
        database with work factor 12.
    """
    # Verify credentials
    if check_password(username, password):
        token = generate_token(username)
        return token
    else:
        record_failed_attempt(username)
        return None
```

## Simplification Rules
1. Break down complex expressions into simpler components.
2. Use named variables to document intermediate values.
3. Simplify boolean expressions when possible.
4. Avoid double negatives in conditions.
5. Use early returns to reduce nesting.
6. Replace complex loops with helper functions.
7. Eliminate unnecessary variables and code.

### Boolean Logic Simplification

**DO NOT**
```python
if not(not(user.is_active) or not(user.has_permission("admin"))):
    # Complex logic with double negatives
    do_something_for_active_admins()

def process_data(data):
    temp1 = 0
    for i in range(len(data)):
        temp2 = data[i] * 2
        if temp2 > 10:
            temp1 += temp2
    return temp1
```

**DO**
```python
if user.is_active and user.has_permission("admin"):
    do_something_for_active_admins()

def process_data(data):
    sum_of_valid_doubles = 0
    for value in data:
        doubled = value * 2
        if doubled > 10:
            sum_of_valid_doubles += doubled
    return sum_of_valid_doubles
``` |

### Regex Simplification

**DO NOT**
```python
def is_valid_email(email):
    # Overly complex regex that's hard to understand and maintain
    pattern = r'^(([^<>()\[\]\\.,;:\s@"]+(\.[^<>()\[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$'
    return re.match(pattern, email) is not None
```

**DO**
```python
def is_valid_email(email):
    """Validate an email address format.
    
    Validates that the string:
    1. Contains a username and domain separated by '@'
    2. Username doesn't start/end with a period
    3. Domain has at least one period
    4. Only contains allowed characters
    
    A more complete validation would require actually sending
    an email to verify the address exists.
    """
    # Split regex into named components for clarity
    username_pattern = r'[a-zA-Z0-9_.+-]+'
    domain_pattern = r'[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+' 
    pattern = f'^{username_pattern}@{domain_pattern}$'
    
    # Basic format check
    if not re.match(pattern, email):
        return False
        
    # Additional checks that are easier to express in code than regex
    username, domain = email.split('@')
    
    if username.startswith('.') or username.endswith('.'):
        return False
    
    if '.' not in domain:
        return False
    
    return True
```

## Function Rules
1. Functions should do one thing well.
2. Extract unrelated subproblems into separate functions.
3. Keep functions small and focused.
4. Functions should operate at a single level of abstraction.
5. Choose argument order thoughtfully and consistently.
6. Minimize the number of function parameters.
7. Consider creating wrapper functions for common use cases.

### Function Design

**DO NOT**
```python
def process_user_data(user_id, update_profile=False, send_email=False, reset_password=False):
    user = get_user(user_id)
    
    if update_profile:
        # Update user profile logic
        user.name = request.form.get('name')
        user.email = request.form.get('email')
        user.save()
    
    if send_email:
        # Send email logic
        template = get_email_template('welcome')
        send_mail(user.email, template, {})
    
    if reset_password:
        # Reset password logic
        new_password = generate_password()
        user.set_password(new_password)
        user.save()
        send_mail(user.email, 'password_reset', {'password': new_password})
    
    return user
```

**DO**
```python
def get_user(user_id):
    return User.find(user_id)

def update_user_profile(user, profile_data):
    user.name = profile_data.get('name', user.name)
    user.email = profile_data.get('email', user.email)
    user.save()
    return user

def send_welcome_email(user):
    template = get_email_template('welcome')
    send_mail(user.email, template, {})

def reset_user_password(user):
    new_password = generate_password()
    user.set_password(new_password)
    user.save()
    send_mail(user.email, 'password_reset', {'password': new_password})
    return new_password
```

### Abstraction Level Mixing

**DO NOT**
```python
def analyze_text(text, lang="en"):
    # Low-level string operations mixed with high-level analysis
    text = text.lower().strip()
    text = re.sub(r'[^\w\s]', '', text)
    words = text.split()
    word_count = len(words)
    
    # Load language-specific stopwords
    if lang == "en":
        stopwords_file = open("data/stopwords/english.txt", "r")
        stopwords = set([w.strip() for w in stopwords_file.readlines()])
        stopwords_file.close()
    elif lang == "fr":
        stopwords_file = open("data/stopwords/french.txt", "r")
        stopwords = set([w.strip() for w in stopwords_file.readlines()])
        stopwords_file.close()
    else:
        stopwords = set()
    
    # Filter content words and count frequencies
    content_words = [w for w in words if w not in stopwords]
    freq = {}
    for word in content_words:
        if word in freq:
            freq[word] += 1
        else:
            freq[word] = 1
    
    # Calculate sentiment using third-party library
    sentiment_analyzer = SentimentIntensityAnalyzer()
    sentiment = sentiment_analyzer.polarity_scores(text)
    
    # Return all statistics at once
    return {
        "word_count": word_count,
        "content_word_count": len(content_words),
        "frequencies": freq,
        "sentiment": sentiment
    }
```

**DO**
```python
def preprocess_text(text):
    """Convert text to lowercase, remove punctuation and return words."""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s]', '', text)
    return text.split()

def load_stopwords(language="en"):
    """Load stopwords for the specified language."""
    languages = {
        "en": "english.txt",
        "fr": "french.txt",
        # More languages can be added here
    }
    
    filename = languages.get(language)
    if not filename:
        return set()
        
    filepath = f"data/stopwords/{filename}"
    with open(filepath, "r") as file:
        return set(line.strip() for line in file)

def calculate_word_frequencies(words):
    """Count frequency of each word in a list."""
    frequencies = {}
    for word in words:
        frequencies[word] = frequencies.get(word, 0) + 1
    return frequencies

def analyze_text(text, language="en"):
    """Analyze text and return statistics about it."""
    # Each step uses a single level of abstraction
    words = preprocess_text(text)
    stopwords = load_stopwords(language)
    content_words = [word for word in words if word not in stopwords]
    
    # Analyze the text
    word_frequencies = calculate_word_frequencies(content_words)
    sentiment = SentimentIntensityAnalyzer().polarity_scores(text)
    
    # Return the analysis results
    return {
        "word_count": len(words),
        "content_word_count": len(content_words),
        "frequencies": word_frequencies,
        "sentiment": sentiment
    }
```

## Control Flow Rules
1. Minimize nesting depth in code.
2. Prefer positive conditionals over negative ones.
3. Handle the most common code path first.
4. Return early from functions when possible.
5. Avoid "clever" shortcuts that reduce readability.
6. Structure conditionals to minimize cognitive load.

### Nesting and Early Returns

**DO NOT**
```python
def process_order(order):
    if order is not None:
        if order.is_valid():
            if len(order.get_items()) > 0:
                if order.get_customer().has_valid_payment():
                    # Process the order
                    execute_order(order)
                    send_confirmation(order)
                    update_inventory(order)
                else:
                    raise PaymentException("Invalid payment")
            else:
                raise OrderException("Empty order")
        else:
            raise ValidationException("Invalid order")
    else:
        raise ValueError("Order is None")

```

**DO**
```python
def process_order(order):
    if order is None:
        raise ValueError("Order is None")
    
    if not order.is_valid():
        raise ValidationException("Invalid order")
    
    if not order.get_items():
        raise OrderException("Empty order")
    
    if not order.get_customer().has_valid_payment():
        raise PaymentException("Invalid payment")
    
    # Process the valid order
    execute_order(order)
    send_confirmation(order)
    update_inventory(order)
```

### Complex Conditionals

**DO NOT**
```python
def check_eligibility(user):
    # Hard-to-follow nested conditions with mixed logic
    if user.age >= 18:
        if user.is_active and user.subscription.status == "paid":
            if not user.has_flag("banned") and not user.has_flag("suspended"):
                if user.last_login and (user.last_login > (datetime.now() - timedelta(days=30))):
                    if user.profile_completion > 80 or user.is_legacy_user:
                        return True
    return False
```

**DO**
```python
def check_eligibility(user):
    """Check if user is eligible for premium content access."""
    # Validate basic requirements first
    if user.age < 18:
        return False
        
    if not user.is_active:
        return False
        
    if user.subscription.status != "paid":
        return False
    
    # Check disqualifying flags
    if user.has_flag("banned") or user.has_flag("suspended"):
        return False
    
    # Check activity requirements
    if not user.last_login:
        return False
        
    one_month_ago = datetime.now() - timedelta(days=30)
    if user.last_login <= one_month_ago:
        return False
    
    # Check profile completion requirement (with Exception for legacy users)
    if user.profile_completion <= 80 and not user.is_legacy_user:
        return False
    
    # If all checks passed, user is eligible
    return True
```

## Data Structure Rules
1. Use the simplest data structure that does the job.
2. Reduce variable scope as much as possible.
3. Prefer constants and immutable data when possible.
4. Define variables close to where they're used.
5. Make interfaces to your code "narrow and deep".
6. Design data structures that prevent errors.
7. Document expectations about data with assertions.

### Generic Dict vs. Classes

**DO NOT**
```python
def process_user_data(user_data):
    # Using general-purpose dict with inconsistent structure
    result = {}
    
    if user_data["type"] == "employee":
        result["name"] = user_data["name"]
        result["salary"] = user_data.get("salary", 0)
        result["department"] = user_data["dept"]
        # Might forget to handle other properties
    elif user_data["type"] == "customer":
        result["name"] = user_data["name"]
        result["total_purchases"] = user_data.get("purchases", 0)
        result["last_purchase_date"] = user_data["last_purchase"]
        # Different structure for different types
    
    return result
```

**DO**
```python
class Employee:
    def __init__(self, data):
        self.name = data["name"]
        self.salary = data.get("salary", 0)
        self.department = data["dept"]
        self.start_date = data.get("start_date")
    
    def get_annual_cost(self):
        """Calculate total annual cost including benefits."""
        return self.salary * 1.25  # Including benefits

class Customer:
    def __init__(self, data):
        self.name = data["name"]
        self.total_purchases = data.get("purchases", 0)
        self.last_purchase_date = data["last_purchase"]
        self.loyalty_points = data.get("loyalty_points", 0)
    
    def get_value_score(self):
        """Calculate customer value based on purchase history."""
        return self.total_purchases * 0.1 + self.loyalty_points * 0.5

def create_user_from_data(user_data):
    if user_data["type"] == "employee":
        return Employee(user_data)
    elif user_data["type"] == "customer":
        return Customer(user_data)
    raise ValueError(f"Unknown user type: {user_data['type']}")
```

### Data Validation

**DO NOT**
```python
def create_account(data):
    # Data format isn't enforced, values could be missing or wrong type
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    
    # No validation of data, errors will occur later
    account = {
        'username': username,
        'email': email,
        'password_hash': hash_password(password),
        'created_at': datetime.now(),
        'is_active': True,
        'login_count': 0,
        'last_login': None
    }
    
    save_to_database(account)
    return account
```

**DO**
```python
from dataclasses import dataclass, field
from datetime import datetime
import re
from typing import Optional

@dataclass
class AccountCreationRequest:
    """Data required to create a new user account."""
    username: str
    email: str
    password: str
    
    def validate(self):
        """Validate all fields meet requirements."""
        errors = []
        
        # Username validation
        if not self.username or len(self.username) < 3:
            errors.append("Username must be at least 3 characters")
        if not re.match(r'^[a-zA-Z0-9_]+$', self.username):
            errors.append("Username can only contain letters, numbers, and underscores")
            
        # Email validation
        if not self.email or '@' not in self.email:
            errors.append("Valid email is required")
            
        # Password validation
        if not self.password or len(self.password) < 8:
            errors.append("Password must be at least 8 characters")
            
        if errors:
            raise ValidationError(errors)

@dataclass
class Account:
    """User account with enforced types and defaults."""
    username: str
    email: str
    password_hash: str
    created_at: datetime = field(default_factory=datetime.now)
    is_active: bool = True
    login_count: int = 0
    last_login: Optional[datetime] = None

def create_account(request: AccountCreationRequest) -> Account:
    """Create a new account from validated request data."""
    # Validate incoming data
    request.validate()
    
    # Create account with properly typed fields and defaults
    account = Account(
        username=request.username,
        email=request.email,
        password_hash=hash_password(request.password)
    )
    
    save_to_database(account)
    return account
```

## Organization Rules
1. Organize code from high level to low level.
2. Keep related actions together, unrelated actions separate.
3. Use consistent patterns for similar functionality.
4. Minimize state changes and side effects.
5. Place helper functions after the code that uses them.
6. Group related functions together.

### Code Organization

**DO NOT**
```python
def process_data():
    # Mix of high-level and low-level operations
    data = []
    file = open('data.csv', 'r')
    lines = file.readlines()
    file.close()
    
    for line in lines:
        if line.strip():
            parts = line.strip().split(',')
            if len(parts) >= 3:
                name = parts[0]
                age = int(parts[1])
                salary = float(parts[2])
                
                # Complex business logic mixed with parsing
                if age > 30 and salary < 50000:
                    tax_rate = 0.15
                else:
                    tax_rate = 0.2
                
                net_salary = salary * (1 - tax_rate)
                data.append({'name': name, 'age': age, 'net_salary': net_salary})
    
    return data
```

**DO**
```python
def read_csv_file(file_path):
    """Read data from CSV file and return as list of lines."""
    with open(file_path, 'r') as file:
        return [line.strip() for line in file.readlines() if line.strip()]

def parse_employee_data(line):
    """Parse a CSV line into employee data dictionary."""
    parts = line.split(',')
    if len(parts) < 3:
        return None
    
    return {
        'name': parts[0],
        'age': int(parts[1]),
        'salary': float(parts[2])
    }

def calculate_tax_rate(employee):
    """Determine tax rate based on employee criteria."""
    if employee['age'] > 30 and employee['salary'] < 50000:
        return 0.15
    return 0.2

def calculate_net_salary(employee):
    """Calculate employee's net salary after taxes."""
    tax_rate = calculate_tax_rate(employee)
    return employee['salary'] * (1 - tax_rate)

def process_data():
    """Main function to process employee data."""
    lines = read_csv_file('data.csv')
    employees = []
    
    for line in lines:
        employee = parse_employee_data(line)
        if employee:
            employee['net_salary'] = calculate_net_salary(employee)
            employees.append(employee)
    
    return employees
```

### UI Organization

**DO NOT**
```python
# Event handlers scattered throughout file and mixed with business logic
def initialize_app():
    window = create_window("My App", 800, 600)
    
    # Button click handlers
    def on_save_button_click():
        data = get_form_data()
        validate_data(data)
        save_to_database(data)
        show_success_message("Data saved successfully!")
    
    def validate_data(data):
        if not data["name"]:
            show_error("Name is required")
            return False
        if len(data["description"]) > 200:
            show_error("Description too long")
            return False
        return True
    
    save_button = create_button("Save", on_save_button_click)
    
    def on_clear_button_click():
        clear_form()
    
    clear_button = create_button("Clear", on_clear_button_click)
    
    # More UI setup code...
    
    # Database functions mixed in
    def save_to_database(data):
        conn = get_database_connection()
        # ... database code ...
        conn.close()
**DO**
```python
# Organized by logical layers
class DataValidator:
    """Validates form data before processing."""
    
    @staticmethod
    def validate_save_data(data):
        """Validate data for saving."""
        if not data["name"]:
            return False, "Name is required"
            
        if len(data["description"]) > 200:
            return False, "Description too long"
            
        return True, ""
        
class DatabaseService:
    """Handles database operations."""
    
    @staticmethod
    def save_data(data):
        """Save data to database."""
        with get_database_connection() as conn:
            # ... database code ...
            return True

class EventHandlers:
    """All event handlers for the application UI."""
    
    def __init__(self, ui, validator, db_service):
        self.ui = ui
        self.validator = validator
        self.db_service = db_service
        self.current_file = None
    
    def on_save_button_click(self):
        """Handle save button click."""
        data = self.ui.get_form_data()
        
        # Validate data
        valid, error_message = self.validator.validate_save_data(data)
        if not valid:
            self.ui.show_error(error_message)
            return
            
        # Save data
        if self.db_service.save_data(data):
            self.ui.show_success_message("Data saved successfully!")
        else:
            self.ui.show_error("Failed to save data")

def initialize_app():
    """Initialize the application."""
    # Create services
    validator = DataValidator()
    db_service = DatabaseService()
    
    # Create UI
    ui = ApplicationUI()
    
    # Create event handlers
    handlers = EventHandlers(ui, validator, db_service)
    
    # Connect UI events to handlers
    ui.connect("save_button", handlers.on_save_button_click)
```

## Error Handling Rules
1. Handle error cases explicitly.
2. Make error messages specific and actionable.
3. Fail early at the source of the problem.
4. Use defensive programming for unexpected inputs.
5. Add redundant checks for critical code.

### Basic Error Handling

**DO NOT**
```python
def save_user_data(user):
    try:
        # Vague error handling
        database.save(user)
    except Exception as e:
        print("Error")
```

**DO**
```python
def save_user_data(user):
    if user is None:
        raise ValueError("Cannot save None user")
    
    try:
        database.save(user)
    except DatabaseConnectionError as e:
        logger.error(f"Database connection failed while saving user {user.id}: {e}")
        raise ServiceError("Unable to save user due to database connection issue") from e
    except ValidationError as e:
        logger.warning(f"User validation failed for user {user.id}: {e}")
        raise InvalidUserDataError(f"User data is invalid: {e}") from e
    except Exception as e:
        logger.error(f"Unexpected error while saving user {user.id}", exc_info=True)
        raise ServiceError("User save operation failed") from e
```

### Configuration Processing

**DO NOT**
```python
def process_config_file(filename):
    # Doesn't handle errors specifically
    with open(filename, 'r') as f:
        config = json.load(f)
    
    host = config['database']['host']
    port = config['database']['port']
    username = config['database']['credentials']['username']
    password = config['database']['credentials']['password']
    
    return connect_to_database(host, port, username, password)
```

**DO**
```python
def process_config_file(filename):
    """Process configuration file and establish database connection.
    
    Args:
        filename: Path to the configuration JSON file
        
    Returns:
        Database connection object
        
    Raises:
        ConfigError: When file has missing or invalid configuration
        ConnectionError: When database connection fails
    """
    # File existence and permission checks
    if not os.path.exists(filename):
        raise ConfigError(f"Configuration file not found: {filename}")
        
    if not os.access(filename, os.R_OK):
        raise ConfigError(f"No permission to read configuration file: {filename}")
    
    # File opening and parsing
    try:
        with open(filename, 'r') as f:
            try:
                config = json.load(f)
            except json.JSONDecodeError as e:
                raise ConfigError(f"Invalid JSON in configuration file: {e}") from e
    except IOError as e:
        raise ConfigError(f"Unable to read configuration file: {e}") from e
        
    # Configuration validation
    try:
        database_config = config.get('database')
        if not database_config:
            raise ConfigError("Missing 'database' section in config")
            
        host = database_config.get('host')
        if not host:
            raise ConfigError("Missing database host in config")
            
        port = database_config.get('port')
        if not isinstance(port, int):
            raise ConfigError(f"Invalid database port: {port}")
            
        credentials = database_config.get('credentials', {})
        username = credentials.get('username')
        password = credentials.get('password')
        
        if not username or not password:
            raise ConfigError("Missing database credentials in config")
    except Exception as e:
        if not isinstance(e, ConfigError):
            raise ConfigError(f"Error processing configuration: {e}") from e
        raise
        
    # Connection attempt with specific error handling
    try:
        return connect_to_database(host, port, username, password)
    except ConnectionRefusedError:
        raise ConnectionError(f"Database refused connection at {host}:{port}")
    except AuthenticationError:
        raise ConnectionError("Invalid database credentials")
    except Exception as e:
        raise ConnectionError(f"Failed to connect to database: {e}") from e
```

## Testing Rules
1. Write tests for both expected and edge cases.
2. Make test failures easy to diagnose.
3. Test with realistic data.
4. Test the interface, not the implementation.
5. Write self-testing code where practical.

### Basic Testing

**DO NOT**
```python
def test_user_registration():
    user = register_user("john", "password123", "john@example.com")
    assert user is not None

```
**DO**
```python
def test_user_registration_with_valid_data():
    # Arrange
    username = "john_doe"
    password = "password123"
    email = "john@example.com"
    
    # Act
    user = register_user(username, password, email)
    
    # Assert
    assert user.username == username
    assert user.email == email
    assert user.is_active is True
    assert user.id is not None

def test_user_registration_with_duplicate_username():
    # Arrange - create a user first
    existing_username = "existing_user"
    User.objects.create(username=existing_username, email="existing@example.com")
    
    # Act & Assert
    with pytest.raises(DuplicateUsernameError) as excinfo:
        register_user(existing_username, "password123", "new@example.com")
    
    assert "Username already exists" in str(excinfo.value)
```

### Test Organization

**DO NOT**
```python
def test_payment():
    # Multiple things tested in one test
    payment = Payment(100, "USD", "credit_card")
    assert payment.amount == 100
    assert payment.validate() is True
    
    processed = payment.process()
    assert processed is True
    
    refunded = payment.refund()
    assert refunded is True
```

**DO**
```python
class TestPaymentCreation:
    """Tests for payment object creation and validation."""
    
    def test_payment_initialized_with_correct_amount(self):
        payment = Payment(100, "USD", "credit_card")
        assert payment.amount == 100
        assert payment.currency == "USD"
        assert payment.method == "credit_card"
    
    def test_payment_validates_with_valid_data(self):
        payment = Payment(100, "USD", "credit_card")
        assert payment.validate() is True
    
    def test_payment_validation_fails_with_negative_amount(self):
        payment = Payment(-50, "USD", "credit_card")
        assert payment.validate() is False
        assert "amount must be positive" in payment.validation_errors

class TestPaymentProcessing:
    """Tests for payment processing operations."""
    
    def setup_method(self):
        """Set up a valid payment for each test."""
        self.payment = Payment(100, "USD", "credit_card")
        self.payment.card_number = "4111111111111111"
        self.payment.expiry = "12/25"
        self.payment.cvv = "123"
    
    def test_valid_payment_processes_successfully(self):
        assert self.payment.process() is True
        assert self.payment.status == "processed"
        assert self.payment.transaction_id is not None
```

## Optimization Rules
1. Optimize for readability first, performance second.
2. Profile before optimizing.
3. Comment on non-obvious optimization techniques.
4. Keep optimized (less readable) code isolated.
5. Document performance goals and constraints.

### Basic Optimization

**DO NOT**
```python
# Unnecessarily complex optimization without explanation
def find_closest_points(points, target, k=5):
    return sorted(points, key=lambda p: (p[0]-target[0])**2+(p[1]-target[1])**2)[:k]
```

**DO**
```python
def find_closest_points(points, target, k=5):
    """Find k points closest to target point using Euclidean distance.
    
    Implementation notes:
    - We avoid using sqrt() in the distance calculation as it's unnecessary
      for comparison and improves performance by ~40%
    - For large point sets (>10000), consider using a KD-tree instead
      which would change time complexity from O(n log n) to O(k log n)
    """
    def squared_distance(p):
        # Avoid unnecessary sqrt calculation for performance
        return (p[0] - target[0])**2 + (p[1] - target[1])**2
    
    # Sort by squared distance and return k closest points
    return sorted(points, key=squared_distance)[:k]
```

### Premature Optimization

**DO NOT**
```python
def calculate_statistics(values):
    """Calculate mean, median, and mode of a dataset."""
    # Premature micro-optimization with complex one-liners
    # and unnecessary caching that reduces readability
    _len = len(values)  # Cache length to avoid multiple calls
    _sorted = sorted(values) if _len > 0 else []  # Pre-sort once for both median and mode
    
    # Complex one-liner for mean
    mean = sum(values) / _len if _len > 0 else 0
    
    # Complex calculation of median to avoid creating temporary lists
    median = (_sorted[_len//2] if _len % 2 == 1 else 
             (_sorted[_len//2-1] + _sorted[_len//2]) / 2) if _len > 0 else 0
    
    # Manual frequency counting to avoid Counter overhead
    _freq = {}
    for v in values:
        _freq[v] = _freq.get(v, 0) + 1
    
    # Find mode with max() for performance
    mode = max(_freq.items(), key=lambda x: x[1])[0] if _freq else None
    
    return {"mean": mean, "median": median, "mode": mode}

```
    
**DO**
```python
def calculate_statistics(values):
    """Calculate mean, median, and mode of a dataset.
    
    This implementation prioritizes readability over micro-optimizations.
    Performance testing showed it handles datasets of up to 100,000 elements
    in under 50ms, which is sufficient for our current needs.
    
    For larger datasets, consider using NumPy's statistical functions which
    are implemented in optimized C code.
    
    Args:
        values: List of numeric values
        
    Returns:
        Dict containing mean, median, and mode
    """
    if not values:
        return {"mean": 0, "median": 0, "mode": None}
    
    # Calculate mean
    mean = sum(values) / len(values)
    
    # Calculate median
    sorted_values = sorted(values)
    n = len(sorted_values)
    
    if n % 2 == 1:
        # Odd number of values
        median = sorted_values[n // 2]
    else:
        # Even number of values
        middle_right = n // 2
        middle_left = middle_right - 1
        median = (sorted_values[middle_left] + sorted_values[middle_right]) / 2
    
    # Calculate mode using Counter
    from collections import Counter
    value_counts = Counter(values)
    mode_value, mode_count = value_counts.most_common(1)[0]
    
    # If all values appear the same number of times, there's no mode
    if mode_count == 1 and len(values) > 1:
        mode = None
    else:
        mode = mode_value
    
    return {"mean": mean, "median": median, "mode": mode}
```

## Key Takeaways

1. **Optimize for human understanding**: Write code for people first, computers second. The primary measure of code quality is how quickly another developer can understand it.

2. **Meaningful names reveal intent**: Choose descriptive, specific names for variables, functions, and classes. Good names act as documentation and make code self-explanatory.

3. **Consistent formatting enhances readability**: Use consistent spacing, indentation, and line breaks to visually organize code into logical groups.

4. **Comments explain "why" not "what"**: Focus on explaining reasoning, edge cases, and non-obvious constraints rather than restating what the code does.

5. **Simple is better than clever**: Avoid complex expressions and "clever" tricks. Break complexity into simpler components with clear names.

6. **Functions should do one thing well**: Keep functions small, focused, and operating at a single level of abstraction. Extract unrelated operations into separate functions.

7. **Early returns reduce nesting**: Use guard clauses and early returns to handle edge cases first, keeping the main logic path clean and less nested.

8. **Strong typing prevents errors**: Use typed data structures, validation, and assertions to catch errors early and make expectations explicit.

9. **Organize code by logical layers**: Separate concerns by grouping related functionality. Structure code from high-level to low-level within each file.

10. **Specific error handling is actionable**: Handle error cases explicitly with descriptive messages that guide toward resolution.

11. **Test interfaces, not implementations**: Write tests that verify behavior from the user's perspective rather than internal implementation details.

12. **Prioritize readability over premature optimization**: Focus on making code correct and clear first. Only optimize after profiling identifies actual bottlenecks.

<!-- EOF -->