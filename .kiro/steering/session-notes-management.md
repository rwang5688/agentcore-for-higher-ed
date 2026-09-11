# Session Notes Management

## Purpose

Maintain continuity across working sessions and between different machines (laptop, WorkSpaces, etc.) by recording session notes in a centralized location.

## Directory Structure

All session notes are organized by **year/month** under `.kiro/session-notes/`:

```
.kiro/session-notes/
├── 2025/
│   └── 12/
│       ├── 20251204-session-notes.md
│       ├── 20251205-session-notes.md
│       └── 20251206-session-notes.md
└── 2026/
    └── 06/
        └── 20260611-session-notes.md
```

## Naming Convention

- **Directory path**: `.kiro/session-notes/YYYY/MM/`
- **File name**: `YYYYMMDD-session-notes.md`
- **Date**: Represents the session date (not feature date)
- **Example**: `.kiro/session-notes/2026/06/20260611-session-notes.md`

## Usage Guidelines

### Creating Session Notes Files

1. **New Session**: Create a new session notes file for today's date if it doesn't exist
2. **Same Day Sessions**: Append to or update the existing session notes file for today
3. **Cross-Machine Work**: Use the same date-based file across different machines
4. **New Month**: Create the `YYYY/MM/` directory as needed

### What to Include

Session notes should capture:
- **What We're Working On**: Current feature, bug fix, or enhancement
- **Key Decisions Made**: Important choices and their rationale
- **Implementation Approach**: Patterns being followed, files being modified
- **Test Data**: Sample files or data being used
- **Next Steps**: What needs to be done next
- **Open Questions**: Unresolved issues or decisions pending

## Example Session Notes Structure

```markdown
# Session Notes - YYYYMMDD

## Work Completed
- Task X.Y: Description of work
- Task X.Z: Description of work

## Problems Encountered
- Problem description and solution

## Testing Results
- What was tested
- Results and findings

## Files Modified
- List of files changed

## Next Steps
- What to do in next session
```
