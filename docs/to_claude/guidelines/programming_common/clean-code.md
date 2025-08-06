<!-- ---
!-- Timestamp: 2025-05-25 23:21:34
!-- Author: ywatanabe
!-- File: /ssh:sp:/home/ywatanabe/.claude/to_claude/guidelines/programming_common/clean-code.md
!-- --- -->

# Clean Code Rules

Code is clean if it can be understood easily – by everyone on the team. Clean code can be read and enhanced by a developer other than its original author. With understandability comes readability, changeability, extensibility and maintainability.

## Table of Contents
- [General Rules](#general-rules)
- [Design Rules](#design-rules)
- [Understandability Tips](#understandability-tips)
- [Names Rules](#names-rules)
- [Functions Rules](#functions-rules)
- [Comments Rules](#comments-rules)
- [Source Code Structure](#source-code-structure)
- [Objects and Data Structures](#objects-and-data-structures)
- [Tests](#tests)
- [Code Smells](#code-smells)
- [Examples](#examples)
  - [Naming Examples](#naming-examples)
  - [Functions Examples](#functions-examples)
  - [Comments Examples](#comments-examples)

## General Rules
1. Follow standard conventions.
2. Keep it simple stupid. Simpler is always better. Reduce complexity as much as possible.
3. Boy scout rule. Leave the campground cleaner than you found it.
4. Always find root cause. Always look for the root cause of a problem.

## Design Rules
1. Keep configurable data at high levels.
2. Prefer polymorphism to if/else or switch/case.
3. Separate multi-threading code.
4. Prevent over-configurability.
5. Use dependency injection.
6. Follow Law of Demeter. A class should know only its direct dependencies.

## Understandability Tips
1. Be consistent. If you do something a certain way, do all similar things in the same way.
2. Use explanatory variables.
3. Encapsulate boundary conditions. Boundary conditions are hard to keep track of. Put the processing for them in one place.
4. Prefer dedicated value objects to primitive type.
5. Avoid logical dependency. Don't write methods which works correctly depending on something else in the same class.
6. Avoid negative conditionals.

## Names Rules
1. Choose descriptive and unambiguous names.
2. Make meaningful distinction.
3. Use pronounceable names.
4. Use searchable names.
5. Replace magic numbers with named constants.
6. Avoid encodings. Don't append prefixes or type information.

## Functions Rules
1. Small.
2. Do one thing.
3. Use descriptive names.
4. Prefer fewer arguments.
5. Have no side effects.
6. Don't use flag arguments. Split method into several independent methods that can be called from the client without the flag.

## Comments Rules
1. Always try to explain yourself in code.
2. Don't be redundant.
3. Don't add obvious noise.
4. Don't use closing brace comments.
5. Don't comment out code. Just remove.
6. Use as explanation of intent.
7. Use as clarification of code.
8. Use as warning of consequences.

## Source Code Structure
1. Separate concepts vertically.
2. Related code should appear vertically dense.
3. Declare variables close to their usage.
4. Dependent functions should be close.
5. Similar functions should be close.
6. Place functions in the downward direction.
7. Keep lines short.
8. Don't use horizontal alignment.
9. Use white space to associate related things and disassociate weakly related.
10. Don't break indentation.

## Objects and Data Structures
1. Hide internal structure.
2. Prefer data structures.
3. Avoid hybrids structures (half object and half data).
4. Should be small.
5. Do one thing.
6. Small number of instance variables.
7. Base class should know nothing about their derivatives.
8. Better to have many functions than to pass some code into a function to select a behavior.
9. Prefer non-static methods to static methods.

## Tests
1. One assert per test.
2. Readable.
3. Fast.
4. Independent.
5. Repeatable.

## Code Smells
1. Rigidity. The software is difficult to change. A small change causes a cascade of subsequent changes.
2. Fragility. The software breaks in many places due to a single change.
3. Immobility. You cannot reuse parts of the code in other projects because of involved risks and high effort.
4. Needless Complexity.
5. Needless Repetition.
6. Opacity. The code is hard to understand.

## Examples

### Naming Examples

| ❌ DO NOT | ✅ DO |
|-----------|------|
| ```python
# Unclear variable names
d = 5  # elapsed time in days
def calc(a, b, c):
    return (a * b) + c
``` | ```python
# Descriptive variable names
days_elapsed = 5
def calculate_total_price(base_price, tax_rate, shipping_cost):
    return (base_price * tax_rate) + shipping_cost
``` |
| ```python
# Non-searchable names
e = 3.14159
def fn(x, y):
    return x + y * 23
``` | ```python
# Searchable names
PI = 3.14159
TAX_MULTIPLIER = 23
def calculate_sum(first_value, second_value):
    return first_value + second_value * TAX_MULTIPLIER
``` |
| ```python
# Hungarian notation and type encoding
strName = "John"
intAge = 25
bIsActive = True
``` | ```python
# Clean names without type encoding
name = "John"
age = 25
is_active = True
``` |

### Functions Examples

| ❌ DO NOT | ✅ DO |
|-----------|------|
| ```python
# Function that does multiple things
def process_data(data):
    # Validate data
    if not data:
        return None
    
    # Transform data
    result = []
    for item in data:
        result.append(item * 2)
    
    # Save to database
    save_to_db(result)
    
    # Send notification
    send_notification("Data processed")
    
    return result
``` | ```python
# Functions that do one thing
def process_data(data):
    validated_data = validate_data(data)
    if not validated_data:
        return None
    
    transformed_data = transform_data(validated_data)
    save_data(transformed_data)
    notify_process_complete()
    
    return transformed_data

def validate_data(data):
    return data if data else None

def transform_data(data):
    return [item * 2 for item in data]

def save_data(data):
    save_to_db(data)

def notify_process_complete():
    send_notification("Data processed")
``` |
| ```python
# Function with flag argument
def render_page(is_admin):
    if is_admin:
        # Render admin view
        return "Admin Page"
    else:
        # Render user view
        return "User Page"
``` | ```python
# Separate functions instead of flag
def render_admin_page():
    # Render admin view
    return "Admin Page"

def render_user_page():
    # Render user view
    return "User Page"
``` |
| ```python
# Function with too many arguments
def create_user(name, email, password, age, address, phone, role, status):
    # Create user with all these parameters
    pass
``` | ```python
# Using a class or dictionary to group parameters
class UserData:
    def __init__(self, name, email, password, age, address, phone, role, status):
        self.name = name
        self.email = email
        self.password = password
        self.age = age
        self.address = address
        self.phone = phone
        self.role = role
        self.status = status

def create_user(user_data):
    # Create user with data from user_data object
    pass
``` |

### Comments Examples

| ❌ DO NOT | ✅ DO |
|-----------|------|
| ```python
# This function adds a and b
def add(a, b):
    return a + b
``` | ```python
def add(a, b):
    return a + b
``` |
| ```python
def complex_calculation(data):
    # Loop through data
    for item in data:
        # Process each item
        item.process()
    # Return result
    return data
``` | ```python
def complex_calculation(data):
    """
    Applies specialized business logic to transform financial data
    according to regulation X42-J.
    """
    for item in data:
        item.process()
    return data
``` |
| ```python
# commented out code
# def old_function():
#     # This used to do something
#     pass

def new_function():
    pass
``` | ```python
def new_function():
    pass
``` |
| ```python
def process_data():
    # Begin data processing
    result = []
    # Loop through each item
    for i in range(10):
        # Add item to result
        result.append(i)
    # End of processing
    return result
} # end function
``` | ```python
def process_data():
    result = []
    for i in range(10):
        result.append(i)
    return result
``` |

<!-- EOF -->