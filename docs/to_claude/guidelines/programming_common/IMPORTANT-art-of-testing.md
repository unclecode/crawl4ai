<!-- ---
!-- Timestamp: 2025-05-25 23:21:33
!-- Author: ywatanabe
!-- File: /ssh:sp:/home/ywatanabe/.claude/to_claude/guidelines/programming_common/art-of-testing.md
!-- --- -->

# Testing: Comprehensive Guidelines for Coding Agents

## Overview

This document provides comprehensive testing guidelines synthesized from industry best practices and foundational testing literature. These guidelines enable coding agents to create robust, maintainable test suites that give confidence in code quality and behavior.

## Core Testing Philosophy

### The Testing Mindset
- **Tests are specifications** - They document expected behavior
- **Tests enable change** - Good tests make refactoring safe
- **Tests provide feedback** - They catch regressions quickly
- **Tests build confidence** - They reduce fear of making changes

### Quality Metrics
- **Coverage is necessary but not sufficient** - Aim for high coverage but focus on quality
- **Test value over test count** - Fewer, high-quality tests are better than many poor tests
- **Fast feedback loops** - Tests should run quickly and frequently

## The Testing Pyramid

```
        E2E Tests (Few)
       /              \
    Integration Tests (Some)
   /                        \
Unit Tests (Many)
```

### Distribution Guidelines
- **Unit Tests**: 70% - Fast, isolated, test single units of functionality
- **Integration Tests**: 20% - Test component interactions and contracts
- **End-to-End Tests**: 10% - Test complete user workflows and critical paths

### Pyramid Principles
1. **More lower-level tests** - Unit tests are fastest and most reliable
2. **Each level has different purposes** - Don't duplicate testing across levels
3. **Balance cost and confidence** - Higher-level tests cost more but provide integration confidence

## FIRST Principles (Foundational)

- **Fast**: Tests should run in milliseconds, not seconds
- **Independent**: Tests should not depend on each other or external state
- **Repeatable**: Tests should produce consistent results in any environment
- **Self-validating**: Tests should have clear pass/fail outcomes without manual inspection
- **Timely**: Tests should be written at the right time (preferably before production code)

## Test-Driven Development (TDD)

### Red-Green-Refactor Cycle
1. **Red**: Write a failing test that specifies desired behavior
2. **Green**: Write minimal code to make the test pass
3. **Refactor**: Improve code quality while keeping tests green

### TDD Benefits
- **Better design** - Forces thinking about interfaces before implementation
- **Comprehensive coverage** - Every line of code has a reason to exist
- **Living documentation** - Tests serve as executable specifications
- **Regression protection** - Changes that break behavior are caught immediately

### TDD Best Practices
1. **Write the smallest failing test possible**
2. **Make it pass with minimal code**
3. **Refactor ruthlessly** while keeping tests green
4. **Don't skip the refactor step** - technical debt accumulates quickly
5. **Write tests for behavior, not implementation**

## Test Structure and Organization

### AAA Pattern (Arrange-Act-Assert)
```javascript
describe('UserService.createUser', () => {
  it('should create user with valid email and password', async () => {
    // Arrange
    const userData = {
      email: 'john.doe@example.com',
      password: 'SecurePassword123!'
    };
    const mockRepository = createMockRepository();
    const userService = new UserService(mockRepository);
    
    // Act
    const result = await userService.createUser(userData);
    
    // Assert
    expect(result).toMatchObject({
      id: expect.any(Number),
      email: userData.email
    });
    expect(mockRepository.save).toHaveBeenCalledWith(
      expect.objectContaining(userData)
    );
  });
});
```

### Test Naming Conventions
- **Use descriptive names** that explain the scenario and expected outcome
- **Follow pattern**: `should [expected behavior] when [condition]`
- **Be specific** about the context and expected result
- **Avoid technical jargon** in favor of business language

### Directory Structure
```
src/
├── components/
│   ├── UserService.js
│   └── __tests__/
│       ├── UserService.test.js
│       └── UserService.integration.test.js
├── utils/
│   ├── validation.js
│   └── __tests__/
│       └── validation.test.js
└── __tests__/
    ├── e2e/
    │   └── user-registration.e2e.test.js
    └── integration/
        └── api-contracts.test.js
```

## Unit Testing Best Practices

### Core Principles
1. **Test one thing at a time** - Each test should verify a single behavior
2. **Use meaningful test data** - Avoid generic or nonsensical values
3. **Mock external dependencies** - Isolate the unit under test
4. **Test edge cases** - Include boundary conditions and error scenarios
5. **Keep tests simple** - Test code should be simpler than production code

### Effective Mocking Strategies
```javascript
// Good: Mock external dependencies
jest.mock('../repositories/UserRepository');
const mockUserRepository = require('../repositories/UserRepository');

beforeEach(() => {
  mockUserRepository.findById.mockReset();
  mockUserRepository.save.mockReset();
});

it('should handle repository errors gracefully', async () => {
  // Arrange
  mockUserRepository.save.mockRejectedValue(new Error('Database connection failed'));
  
  // Act & Assert
  await expect(userService.createUser(validUserData))
    .rejects
    .toThrow('Failed to create user');
});
```

### Test Data Management

#### Builder Pattern
```javascript
class UserTestDataBuilder {
  constructor() {
    this.userData = {
      name: 'John Doe',
      email: 'john.doe@example.com',
      age: 30,
      role: 'user'
    };
  }
  
  withName(name) {
    this.userData.name = name;
    return this;
  }
  
  withEmail(email) {
    this.userData.email = email;
    return this;
  }
  
  withAge(age) {
    this.userData.age = age;
    return this;
  }
  
  asAdmin() {
    this.userData.role = 'admin';
    return this;
  }
  
  build() {
    return { ...this.userData };
  }
}

// Usage
const adminUser = new UserTestDataBuilder()
  .withName('Admin User')
  .withEmail('admin@example.com')
  .asAdmin()
  .build();
```

#### Object Mother Pattern
```javascript
class UserMother {
  static validUser() {
    return {
      name: 'John Doe',
      email: 'john.doe@example.com',
      password: 'SecurePassword123!',
      age: 30
    };
  }
  
  static userWithInvalidEmail() {
    return {
      ...this.validUser(),
      email: 'invalid-email-format'
    };
  }
  
  static underageUser() {
    return {
      ...this.validUser(),
      age: 15
    };
  }
  
  static adminUser() {
    return {
      ...this.validUser(),
      role: 'admin',
      permissions: ['read', 'write', 'delete']
    };
  }
}
```

## Integration Testing Guidelines

### API Integration Tests
```javascript
describe('User API Integration', () => {
  let app;
  let testDb;
  
  beforeAll(async () => {
    testDb = await createTestDatabase();
    app = createApp({ database: testDb });
  });
  
  afterAll(async () => {
    await closeTestDatabase(testDb);
  });
  
  beforeEach(async () => {
    await cleanTestData(testDb);
  });
  
  it('should create user and return 201 with user data', async () => {
    const userData = {
      name: 'John Doe',
      email: 'john@example.com',
      password: 'SecurePassword123!'
    };
    
    const response = await request(app)
      .post('/api/users')
      .send(userData)
      .expect(201);
    
    expect(response.body).toMatchObject({
      id: expect.any(Number),
      name: userData.name,
      email: userData.email
    });
    expect(response.body.password).toBeUndefined(); // Should not return password
    
    // Verify data was actually saved
    const savedUser = await testDb.users.findById(response.body.id);
    expect(savedUser).toBeTruthy();
  });
});
```

### Database Integration Tests
```javascript
describe('UserRepository Integration', () => {
  let repository;
  let testDb;
  
  beforeAll(async () => {
    testDb = await createTestDatabase();
    repository = new UserRepository(testDb);
  });
  
  afterEach(async () => {
    await testDb.users.deleteAll();
  });
  
  it('should handle concurrent user creation', async () => {
    const userData1 = UserMother.validUser();
    const userData2 = { ...UserMother.validUser(), email: 'jane@example.com' };
    
    // Act: Create users concurrently
    const [user1, user2] = await Promise.all([
      repository.create(userData1),
      repository.create(userData2)
    ]);
    
    // Assert: Both users should be created with unique IDs
    expect(user1.id).toBeDefined();
    expect(user2.id).toBeDefined();
    expect(user1.id).not.toBe(user2.id);
    
    const allUsers = await repository.findAll();
    expect(allUsers).toHaveLength(2);
  });
});
```

## Error Handling and Edge Case Testing

### Exception Testing
```javascript
describe('Error Handling', () => {
  it('should throw specific error with helpful message', () => {
    expect(() => {
      calculator.divide(10, 0);
    }).toThrow('Division by zero is not allowed');
  });
  
  it('should handle async errors properly', async () => {
    mockRepository.findById.mockRejectedValue(new Error('Database connection lost'));
    
    await expect(userService.getUserById(1))
      .rejects
      .toThrow('Failed to retrieve user data');
  });
  
  it('should validate input parameters', () => {
    expect(() => {
      userService.createUser(null);
    }).toThrow('User data is required');
    
    expect(() => {
      userService.createUser({});
    }).toThrow('Email is required');
  });
});
```

### Boundary and Edge Cases
```javascript
describe('Edge Cases', () => {
  it('should handle empty input gracefully', () => {
    expect(sumArray([])).toBe(0);
    expect(findMaxValue([])).toBeNull();
  });
  
  it('should handle null and undefined values', () => {
    expect(formatUserName(null)).toBe('');
    expect(formatUserName(undefined)).toBe('');
    expect(formatUserName('')).toBe('');
  });
  
  it('should handle extreme values', () => {
    expect(calculateInterest(Number.MAX_SAFE_INTEGER, 0.01)).toBeDefined();
    expect(calculateInterest(0, 100)).toBe(0);
    expect(calculateInterest(-1000, 0.05)).toBe(0); // No negative principal
  });
  
  it('should handle unicode and special characters', () => {
    const unicodeName = '김철수';
    const emojiName = 'John 😀 Doe';
    
    expect(validateName(unicodeName)).toBe(true);
    expect(validateName(emojiName)).toBe(true);
  });
});
```

## Asynchronous Testing Patterns

### Promise-based Testing
```javascript
describe('Async Operations', () => {
  it('should handle successful async operations', async () => {
    const result = await fetchUserData(1);
    expect(result).toMatchObject({
      id: 1,
      name: expect.any(String)
    });
  });
  
  it('should handle async rejections', async () => {
    await expect(fetchUserData(-1))
      .rejects
      .toThrow('User not found');
  });
  
  it('should timeout long-running operations', async () => {
    jest.setTimeout(5000);
    
    await expect(verySlowOperation())
      .rejects
      .toThrow('Operation timed out');
  }, 6000);
});
```

### Callback Testing
```javascript
describe('Callback-based Operations', () => {
  it('should handle successful callbacks', (done) => {
    getUserData(1, (error, user) => {
      try {
        expect(error).toBeNull();
        expect(user.id).toBe(1);
        done();
      } catch (testError) {
        done(testError);
      }
    });
  });
  
  it('should handle callback errors', (done) => {
    getUserData(-1, (error, user) => {
      try {
        expect(error).toEqual(expect.objectContaining({
          message: 'User not found'
        }));
        expect(user).toBeUndefined();
        done();
      } catch (testError) {
        done(testError);
      }
    });
  });
});
```

## Testing Anti-Patterns to Avoid

### 1. Testing Implementation Details
```javascript
// Bad: Testing internal implementation
it('should call getUserFromDatabase method', () => {
  const spy = jest.spyOn(userService, 'getUserFromDatabase');
  userService.getUser(1);
  expect(spy).toHaveBeenCalled();
});

// Good: Testing behavior
it('should return user data when valid ID is provided', async () => {
  const user = await userService.getUser(1);
  expect(user).toMatchObject({
    id: 1,
    name: expect.any(String)
  });
});
```

### 2. Fragile Tests
```javascript
// Bad: Test depends on specific order
it('should return users in creation order', () => {
  const users = userService.getAllUsers();
  expect(users[0].name).toBe('Alice');
  expect(users[1].name).toBe('Bob');
});

// Good: Test the important behavior
it('should return all active users', () => {
  const users = userService.getAllUsers();
  expect(users).toHaveLength(2);
  expect(users.every(user => user.status === 'active')).toBe(true);
  
  const names = users.map(u => u.name);
  expect(names).toContain('Alice');
  expect(names).toContain('Bob');
});
```

### 3. Over-Mocking
```javascript
// Bad: Mocking everything
it('should process user data', () => {
  const mockValidator = jest.mock();
  const mockFormatter = jest.mock();
  const mockLogger = jest.mock();
  // ... too many mocks make the test meaningless
});

// Good: Mock only external dependencies
it('should process user data', () => {
  // Only mock external service, test real validation and formatting
  mockExternalService.fetchUserData.mockResolvedValue(rawUserData);
  
  const result = userProcessor.process(userId);
  expect(result).toMatchObject(expectedProcessedData);
});
```

### 4. Mystery Guest (Hidden Test Data)
```javascript
// Bad: Mysterious test data
it('should validate user', () => {
  const result = validator.validate(testUser); // Where does testUser come from?
  expect(result).toBe(true);
});

// Good: Clear test data
it('should validate user with all required fields', () => {
  const validUser = {
    name: 'John Doe',
    email: 'john@example.com',
    age: 30
  };
  
  const result = validator.validate(validUser);
  expect(result).toBe(true);
});
```

## Test Maintenance and Refactoring

### Keeping Tests DRY
```javascript
describe('UserService', () => {
  let userService;
  let mockRepository;
  
  beforeEach(() => {
    mockRepository = createMockRepository();
    userService = new UserService(mockRepository);
  });
  
  const validUserData = UserMother.validUser();
  
  describe('createUser', () => {
    it('should create user with valid data', async () => {
      mockRepository.save.mockResolvedValue({ id: 1, ...validUserData });
      
      const result = await userService.createUser(validUserData);
      
      expect(result.id).toBeDefined();
      expect(result.email).toBe(validUserData.email);
    });
    
    it('should validate email format', async () => {
      const invalidUser = { ...validUserData, email: 'invalid-format' };
      
      await expect(userService.createUser(invalidUser))
        .rejects
        .toThrow('Invalid email format');
    });
  });
});
```

### Test Evolution with Code
```javascript
// When refactoring from sync to async
// Before
class UserService {
  createUser(userData) {
    return this.repository.save(userData);
  }
}

// After
class UserService {
  async createUser(userData) {
    await this.validator.validate(userData);
    return await this.repository.save(userData);
  }
}

// Update tests accordingly
describe('createUser', () => {
  it('should create user successfully', async () => { // Add async
    mockRepository.save.mockResolvedValue(expectedUser); // Use mockResolvedValue
    
    const result = await userService.createUser(validUserData); // Add await
    
    expect(result).toEqual(expectedUser);
  });
});
```

## Performance and Load Testing

### Performance Testing
```javascript
describe('Performance Tests', () => {
  it('should process large datasets efficiently', () => {
    const largeDataset = generateTestData(10000);
    
    const startTime = performance.now();
    const result = dataProcessor.process(largeDataset);
    const endTime = performance.now();
    
    expect(result).toHaveLength(10000);
    expect(endTime - startTime).toBeLessThan(1000); // Should complete in under 1 second
  });
  
  it('should handle concurrent requests', async () => {
    const concurrentRequests = Array.from({ length: 100 }, (_, i) => 
      userService.getUserById(i + 1)
    );
    
    const startTime = performance.now();
    const results = await Promise.all(concurrentRequests);
    const endTime = performance.now();
    
    expect(results).toHaveLength(100);
    expect(results.every(user => user.id)).toBe(true);
    expect(endTime - startTime).toBeLessThan(5000); // Should handle 100 concurrent requests in under 5 seconds
  });
});
```

## Security Testing

### Input Validation Testing
```javascript
describe('Security Tests', () => {
  it('should prevent SQL injection attempts', async () => {
    const maliciousInput = "'; DROP TABLE users; --";
    
    await expect(userService.searchUsers(maliciousInput))
      .not.toThrow(); // Should handle gracefully, not crash
    
    // Verify no actual damage was done
    const usersStillExist = await userService.getAllUsers();
    expect(usersStillExist).toBeDefined();
  });
  
  it('should sanitize HTML input', () => {
    const htmlInput = '<script>alert("xss")</script>';
    const result = sanitizeInput(htmlInput);
    
    expect(result).not.toContain('<script>');
    expect(result).not.toContain('alert');
  });
  
  it('should validate file upload types', () => {
    const executableFile = { name: 'malware.exe', type: 'application/octet-stream' };
    
    expect(() => {
      fileUploadService.validateFile(executableFile);
    }).toThrow('File type not allowed');
  });
});
```

## Test Coverage and Quality Metrics

### Coverage Guidelines
- **Aim for 80-90% code coverage** as a baseline
- **Focus on critical path coverage** - ensure important features are tested
- **Don't chase 100% coverage** at the expense of test quality
- **Use coverage to find untested code**, not as the primary quality metric

### Quality Metrics
```javascript
// Example: Testing critical business logic thoroughly
describe('PaymentProcessor', () => {
  describe('processPayment', () => {
    // Happy path
    it('should process valid payment successfully', () => {});
    
    // Error cases
    it('should reject payment with insufficient funds', () => {});
    it('should reject payment with expired card', () => {});
    it('should reject payment with invalid CVV', () => {});
    
    // Edge cases
    it('should handle exactly zero amount', () => {});
    it('should handle maximum allowed amount', () => {});
    it('should handle international transactions', () => {});
    
    // Security
    it('should not log sensitive payment data', () => {});
    it('should handle PCI compliance requirements', () => {});
  });
});
```

## Testing Tools and Frameworks

### Popular Testing Frameworks by Language
- **JavaScript**: Jest, Vitest, Mocha, Cypress, Playwright
- **Python**: pytest, unittest, nose2, Hypothesis
- **Java**: JUnit 5, TestNG, Mockito, AssertJ
- **C#**: xUnit, NUnit, MSTest, Moq
- **Ruby**: RSpec, Test::Unit, FactoryBot
- **Go**: testing package, Testify, Ginkgo
- **Rust**: Built-in test framework, proptest
- **Swift**: XCTest, Quick + Nimble

### Essential Testing Utilities
- **Mocking**: Jest mocks, Sinon.js, Mockito, unittest.mock
- **Assertions**: Chai, Should.js, Hamcrest, AssertJ
- **Test Data Generation**: Faker.js, Factory Bot, Hypothesis
- **Coverage Tools**: Istanbul, nyc, JaCoCo, Coverage.py
- **Load Testing**: Artillery, k6, JMeter

## Best Practices Summary

### The Testing Commandments
1. **Write tests first** (TDD approach when possible)
2. **Test behavior, not implementation**
3. **Keep tests simple and focused**
4. **Use descriptive test names**
5. **Mock external dependencies appropriately**
6. **Test edge cases and error conditions**
7. **Maintain test independence**
8. **Keep test code clean and maintainable**
9. **Run tests frequently and fix failures immediately**
10. **Review and refactor tests regularly**

### Test Quality Checklist
- [ ] Tests have clear, descriptive names
- [ ] Tests follow AAA pattern (Arrange-Act-Assert)
- [ ] Each test verifies one specific behavior
- [ ] External dependencies are properly mocked
- [ ] Edge cases and error conditions are covered
- [ ] Tests run fast and don't depend on external services
- [ ] Test data is meaningful and realistic
- [ ] Tests are independent of each other
- [ ] Code coverage is adequate for critical paths
- [ ] Tests serve as living documentation

## Advanced Testing Patterns

### Contract Testing
```javascript
// API Contract Tests
describe('User API Contract', () => {
  it('should match expected response schema', async () => {
    const response = await request(app)
      .get('/api/users/1')
      .expect(200);
    
    expect(response.body).toMatchSchema({
      type: 'object',
      properties: {
        id: { type: 'number' },
        name: { type: 'string' },
        email: { type: 'string', format: 'email' },
        createdAt: { type: 'string', format: 'date-time' }
      },
      required: ['id', 'name', 'email', 'createdAt']
    });
  });
});
```

### Property-Based Testing
```javascript
// Using fast-check for property-based testing
describe('String utilities', () => {
  it('should preserve length when reversing strings', () => {
    fc.assert(
      fc.property(fc.string(), (str) => {
        const reversed = reverseString(str);
        return reversed.length === str.length;
      })
    );
  });
  
  it('should be idempotent when applied twice', () => {
    fc.assert(
      fc.property(fc.string(), (str) => {
        const doubleReversed = reverseString(reverseString(str));
        return doubleReversed === str;
      })
    );
  });
});
```

## References

This guide synthesizes best practices from:
- "The Art of Unit Testing" by Roy Osherove
- "Unit Testing Principles, Practices, and Patterns" by Vladimir Khorikov (Manning, 2020)
- "Growing Object-Oriented Software, Guided by Tests" by Steve Freeman & Nat Pryce
- "How Google Tests Software" by James Whittaker, Jason Arbon & Jeff Carollo
- "Effective Unit Testing" by Lasse Koskela
- "xUnit Test Patterns: Refactoring Test Code" by Gerard Meszaros
- Industry best practices from Google, Microsoft, and other leading software organizations

<!-- EOF -->