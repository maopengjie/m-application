```markdown
# m-application Development Patterns

> Auto-generated skill from repository analysis

## Overview
This skill teaches best practices and coding conventions for contributing to the `m-application` TypeScript codebase. It covers file organization, import/export styles, commit message patterns, and testing conventions, ensuring consistency and maintainability across the project.

## Coding Conventions

### File Naming
- Use **kebab-case** for all file names.
  - Example: `user-profile.ts`, `data-service.test.ts`

### Import Style
- Use **relative imports** for referencing modules within the project.
  - Example:
    ```typescript
    import { fetchData } from './data-service';
    ```

### Export Style
- Use **named exports** for all modules.
  - Example:
    ```typescript
    // Good
    export const fetchData = () => { ... };

    // Bad
    export default fetchData;
    ```

### Commit Messages
- Follow **Conventional Commits** with prefixes such as `build`.
  - Example:
    ```
    build: update dependencies to latest versions
    ```

## Workflows

### Build Workflow
**Trigger:** When you need to build the project for deployment or testing  
**Command:** `/build`

1. Ensure all dependencies are installed.
2. Run the build command (e.g., `npm run build` or `yarn build`).
3. Verify the output in the build directory.

### Commit Workflow
**Trigger:** When making any code changes  
**Command:** `/commit`

1. Stage your changes (`git add .`).
2. Write a commit message using the conventional commit format.
   - Example: `build: refactor data-service for performance`
3. Commit your changes (`git commit -m "build: ..."`).

## Testing Patterns

- Test files use the pattern `*.test.*` (e.g., `user-profile.test.ts`).
- The testing framework is **unknown**, but tests should follow standard TypeScript testing practices.
- Example test file structure:
  ```typescript
  import { fetchData } from './data-service';

  describe('fetchData', () => {
    it('should return data', () => {
      // test implementation
    });
  });
  ```

## Commands
| Command   | Purpose                                      |
|-----------|----------------------------------------------|
| /build    | Build the project for deployment or testing  |
| /commit   | Commit changes using conventional commits    |
```
