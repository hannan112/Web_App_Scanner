# Shared Utilities and Hooks

This directory contains shared utilities, hooks, and components to reduce code duplication across the application.

## Structure

```
src/lib/
├── utils.ts              # Centralized utility functions
├── hooks/                # Custom React hooks
│   ├── useProjectData.ts # Hook for fetching project data
│   └── useScansData.ts   # Hook for fetching scans data
└── README.md            # This file
```

## Utilities (`utils.ts`)

### `formatDuration(ms: number): string`
Formats milliseconds into human-readable duration (e.g., "2h 30m", "45s")

### `formatDate(dateString: string): string`
Formats date strings to localized format

### `getStatusBadgeClass(status: string): string`
Returns CSS classes for status badges based on scan status

### `getScanActionLink(scan: any): { href: string; text: string }`
Returns the appropriate action link and text for a scan based on its status

### `capitalizeFirst(str: string): string`
Capitalizes the first letter of a string

## Hooks

### `useProjectData({ projectId }: UseProjectDataProps)`
Handles project data fetching with authentication checks.

**Returns:**
- `project`: Project data
- `loading`: Loading state
- `error`: Error state

### `useScansData({ projectId, enabled }: UseScansDataProps)`
Handles scans data fetching for a specific project.

**Returns:**
- `scans`: Array of scans
- `loading`: Loading state
- `error`: Error state

## Usage Examples

```tsx
import { formatDuration, getStatusBadgeClass } from '@/lib/utils';
import { useProjectData } from '@/lib/hooks/useProjectData';

function MyComponent({ projectId }: { projectId: string }) {
  const { project, loading, error } = useProjectData({ projectId });
  
  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;
  
  return (
    <div>
      <h1>{project.name}</h1>
      <span className={getStatusBadgeClass(project.status)}>
        {project.status}
      </span>
    </div>
  );
}
```

## Migration Guide

When refactoring existing components:

1. Replace local utility functions with imports from `@/lib/utils`
2. Replace repeated data fetching logic with custom hooks
3. Use the `ScanTable` component for scan listings
4. Remove duplicate code and backup files

## Best Practices

- Always use these shared utilities instead of creating local duplicates
- Add new utilities here if they're used in multiple places
- Keep hooks focused on a single responsibility
- Document any new utilities or hooks added 