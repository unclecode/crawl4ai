<!-- ---
!-- Timestamp: 2025-05-31 23:59:07
!-- Author: ywatanabe
!-- File: /home/ywatanabe/.dotfiles/.claude/to_claude/guidelines/programming_common/IMPORTANT-test-driven-workflow.md
!-- --- -->

## !!! IMPORTANT !!! Test-Driven Development (TDD) Workflow !!! IMPORTANT !!!
The most important guideline in this document is that we adopt test-driven development workflow explained below.

1. **Start with tests**
   - **PRIORITIZE TEST OVER SOURCE**
     - The quality of test is the quality of the project
   - We strictly follow **TEST-DRIVEN DEVELOPMENT**
   - Write MEANINGFUL tests BEFORE implementing source code
   - Write MEANINGFUL tests BASED ON EXPECTED INPUT/OUTPUT PAIRS
   - AVOID MOCK IMPLEMENTATIONS
   - In this stage, TESTS SHOULD TARGET FUNCTIONALITY THAT DOESN'T EXIST YET
   - Focus on isolated, small testing units.
   - Use `./run_tests.sh --debug` for running tests
   - Also, read `./docs/guidelines/IMPORTANT-guidelines-programming-Elisp-CI-Framework-Rules.md` and follow the rules for pure environments if the project is Elisp-based.
   - Test code should have expected directory structure based on project goals and conventions in the used language

2. **Verify test failures**
   - Run the tests to confirm they fail first
     - Our aim is now clear; all we need is to solve the failed tests
   - Not to write implementation code yet

3. **Git commit test files**
   - Review the tests for completeness to satisfy the project goals and requirements
     - Not determine the qualities of test files based on source files
       - Prioritize test code over source code
       - Thus, test code MUST BE SOLID
   - Commit the tests when satisfied

4. **Implement functionality**
   - If the above steps 1-3 completed, now you are allowed to implement source code that passes the tests
   - !!! IMPORTANT !!! NOT TO MODIFY THE TEST FILES IN THIS STEP
   - Iterate until all tests pass

5. **Verify implementation quality**
   - Use independent subagents to check if implementation overfits to tests
   - Ensure solution meets broader requirements beyond tests

6. **Summarize the current iteration by listing:**
   - What were verified
   - What are not verified yet
     - Reasons why they are not verified if not expected

7. **Commit implementation**
   - Commit the source code once satisfied

## About `./run_tests.sh`
- `./run_tests.sh` MUST BE VERSATILE AMONG PROJECTS.
  - THUS, NEVER USE PROJECT-SPECIFIC INFORMATION, SUCH AS DIRECTORY STRUCTURE, IN THE SCRIPT.
  - It is expected that test codes are located under `./tests`.
  - In `./run_tests.sh`, paths must be added to source and test codes recursively, without considering project-specific factors.
- Log file (`./.run_tests.sh.log`) may catch errors

## Test in Elisp Projects
- Read the report `./*REPORT*.org`
- THINK next steps based on test results and project progress
- ~~Known issues are often related to path settings in `./src` and `./test`~~

## Test in Python Projects
- In Python projects, `./run_tests.sh -s` will synchronize `./tests` directories: test structure is validated and the corresponding source code is embedded as comments
- Since I am not familiar with `mock` tests, do not use it. Instead, write simple tests.
- Custom tests should be placed under `./tests/custom`. Otherwise, test code with no corresponding source script will be automatically removed.

## Test Code Quality Checklist
- Are test code SPLIT INTO SMALL TEST FUNCTIONS?
- Are test functions explain the functionality in their names?
- Are test code MEANINGFUL to check required functionalities?
- Are test code not obsolete?
- Are test code mirrors source code in its structure?

## Your Understanding Check
Did you understand the guideline? If yes, please say:
`CLAUDE UNDERSTOOD: <THIS FILE PATH HERE>`

<!-- EOF -->