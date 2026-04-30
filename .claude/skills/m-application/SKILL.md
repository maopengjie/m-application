```markdown
# m-application Development Patterns

> Auto-generated skill from repository analysis

## Overview

This skill provides a comprehensive guide to contributing to the `m-application` monorepo, a TypeScript-based Vue project. It documents the repository's coding conventions, commit patterns, and the main workflows for updating dependencies, developing features, refactoring, UI component management, routing, and code formatting. It also covers testing patterns and provides ready-to-use commands for common tasks.

## Coding Conventions

### File Naming

- **CamelCase** is used for file names.
  - Example: `userProfile.ts`, `MainLayout.vue`

### Import Style

- Mixed import styles are used, including both named and default imports.
  ```ts
  import { ref, computed } from 'vue';
  import useUser from './useUser';
  ```

### Export Style

- **Named exports** are preferred.
  ```ts
  // Good
  export function useAuth() { ... }
  export const USER_ROLE = 'admin';

  // Avoid default exports
  // export default function() { ... }
  ```

### Commit Patterns

- **Conventional commits** with the following prefixes:
  - `chore:`, `feat:`, `fix:`, `perf:`
- Example:
  ```
  feat: add dark mode toggle
  fix: correct user role validation
  chore: update deps
  ```

## Workflows

### Update Dependencies and Monorepo Packages

**Trigger:** When dependencies or package versions need to be updated across the monorepo.  
**Command:** `/update-deps`

1. Update root `package.json` and `pnpm-lock.yaml`.
2. Update `internal/*/package.json` and/or `tsconfig.json`.
3. Update `packages/*/package.json` and/or `tsconfig.json`.
4. Update `apps/*/package.json` as needed.
5. Commit with a message like `chore: update deps`.

**Example:**
```sh
pnpm install -r
git add package.json pnpm-lock.yaml internal/**/package.json packages/**/package.json apps/**/package.json
git commit -m "chore: update deps"
```

---

### Feature Development with Types and Locales

**Trigger:** When adding a new feature or configuration affecting UI, types, or localization.  
**Command:** `/new-feature`

1. Update or add implementation files (Vue components, config, or logic).
2. Update types in `packages/@core/shared/typings` or related files.
3. Update or add entries in `packages/locales/src/langs/*.yaml`.
4. Update or add config files if needed.
5. Update UI components to reflect the new feature.
6. Commit with a `feat:` message.

**Example:**
```ts
// packages/@core/shared/typings/src/user.ts
export interface UserProfile {
  id: string;
  name: string;
}
```
```yaml
# packages/locales/src/langs/en-US.yaml
user:
  profile: "User Profile"
```
```sh
git commit -am "feat: add user profile feature"
```

---

### Refactor or Rename Package or Directory

**Trigger:** When renaming a package, directory, or refactoring structure.  
**Command:** `/refactor-package`

1. Move or rename directories and files.
2. Update import paths and references across the codebase.
3. Update related `package.json` and `tsconfig.json`.
4. Update workspace files (`pnpm-workspace.yaml`, `.code-workspace`).
5. Commit with a `refactor:` or `chore:` message.

**Example:**
```sh
mv packages/@vben-core packages/@core
# Update all imports from '@vben-core' to '@core'
git commit -am "refactor: rename @vben-core to @core"
```

---

### Add or Update UI Component

**Trigger:** When adding or updating a UI component in the UI kit.  
**Command:** `/add-ui-component`

1. Add or update `.vue` component in `packages/@core/uikit/*/src/components/`.
2. Update or add `index.ts` to export the component.
3. Update styles if needed (`index.scss`).
4. Update `package.json` if new dependencies or exports are needed.
5. Commit with a `feat:` or `fix:` message.

**Example:**
```vue
<!-- packages/@core/uikit/button/src/components/Button.vue -->
<template>
  <button :class="type">{{ label }}</button>
</template>
<script lang="ts">
export default {
  props: { label: String, type: String }
}
</script>
```
```ts
// packages/@core/uikit/button/src/index.ts
export { default as Button } from './components/Button.vue';
```
```sh
git commit -am "feat: add Button component"
```

---

### Add or Update Router and Views

**Trigger:** When adding a new route, fallback page, or updating routing logic.  
**Command:** `/add-route`

1. Add or update route definition in `apps/*/src/router/routes/**`.
2. Add or update corresponding view component in `apps/*/src/views/**`.
3. Update `router/index.ts` or `guard.ts` as needed.
4. Commit with a `feat:` or `fix:` message.

**Example:**
```ts
// apps/admin/src/router/routes/user.ts
export default {
  path: '/user',
  component: () => import('@/views/User.vue')
};
```
```vue
<!-- apps/admin/src/views/User.vue -->
<template>
  <div>User Page</div>
</template>
```
```sh
git commit -am "feat: add user route and view"
```

---

### Format Codebase

**Trigger:** When applying code formatting across the repository.  
**Command:** `/format-code`

1. Run code formatter (e.g., Prettier) on codebase.
2. Update `.vue`, `.ts`, `.scss`, and config files.
3. Commit with `chore: format code`.

**Example:**
```sh
pnpm prettier --write .
git commit -am "chore: format code"
```

---

## Testing Patterns

- **Framework:** [Vitest](https://vitest.dev/)
- **Test file pattern:** `*.test.ts`
- **Example:**
  ```ts
  // packages/@core/shared/typings/src/user.test.ts
  import { describe, it, expect } from 'vitest';
  import { getUser } from './user';

  describe('getUser', () => {
    it('returns user data', () => {
      expect(getUser('123')).toEqual({ id: '123', name: 'Alice' });
    });
  });
  ```

## Commands

| Command            | Purpose                                                      |
|--------------------|--------------------------------------------------------------|
| /update-deps       | Update dependencies and sync package versions across monorepo |
| /new-feature       | Start a new feature, updating types and locales as needed    |
| /refactor-package  | Refactor or rename a package or directory                    |
| /add-ui-component  | Add or update a UI component in the UI kit                   |
| /add-route         | Add or update a route and corresponding view                  |
| /format-code       | Format the codebase for style consistency                    |
```
