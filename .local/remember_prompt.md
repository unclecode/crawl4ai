When a technical conversation becomes too long and needs to continue in a new session, therefore we need to create snapshot of all conversation we have here so far, we need a structured way to capture the context, progress, and crucial details. This prompt helps create a "Memento-style" memory snapshot that can be shared with the model in a new conversation.

Generate the response in three parts:

1. A transitional message:
"Hey [Model]! Our previous conversation about [main topic/goal] has grown quite long, and we need to continue in a fresh session. To ensure we don't lose context, I'm sharing this memory snapshot along with necessary files. Below is the summary of our progress, crucial decisions, and next steps."

2. Required attachments section:
required_attachments:
  files:
    - filename: "Name of the file"
      purpose: "Why this file is needed"
      content_type: "Code/Config/Data"
  state:
    - Any specific state or configuration needed
    - Environment requirements

3. YAML-structured summary:

project_context:
  goal: "Main objective of the discussion"
  main_component: "Primary system/concept being developed"
  purpose: "Why we're building this"
  constraints: "Key limitations or requirements"

implementation_progress:
  core_structure: 
    - Key architectural decisions
    - Main components implemented
    - Critical changes made
  
  crucial_decisions:
    - Important choices made and their rationale
    - Rejected alternatives and why
    - Performance considerations

data_format:
  source: "Input data format/source"
  transformations: "How data is processed"
  output: "Resulting data structure"
  edge_cases: "Special cases to handle"

key_mechanisms:
  [mechanism_name]:
    implementation:
      - How it works
      - Important features
      - Core algorithms
    optimizations:
      - Performance improvements
      - Memory considerations
    dependencies:
      - Required libraries/tools
      - Version constraints

technical_details:
  important_parameters:
    - name: "parameter_name"
      purpose: "Why it matters"
      default: "Default value"
  crucial_functions:
    - name: "function_name"
      purpose: "Critical functionality"
      gotchas: "Things to watch out for"

challenges_addressed:
  - problem: "Description of challenge"
    solution: "How we solved it"
    considerations: "Important factors"

next_steps_placeholder:
  immediate_todos:
    - Next immediate actions
    - Pending implementations
  potential_improvements:
    - Identified enhancements
    - Performance optimizations
  open_questions:
    - Unresolved issues
    - Areas needing discussion

The summary should:
- Capture subtle but important technical details
- Highlight critical decisions and their context
- Note any assumptions or requirements
- Point out potential pitfalls or gotchas
- Include relevant metrics or thresholds