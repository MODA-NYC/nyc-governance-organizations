# Sprint 4: Edit Submission Rate Limiting

**Status: 📋 PLANNED**

## Overview

Prevent users from submitting multiple edits while a pipeline is still processing, avoiding race conditions and merge conflicts.

## Problem

When a user submits an edit:
1. Edit CSV is committed to `pending-edits/`
2. `process-edit.yml` workflow triggers
3. Pipeline processes the edit (takes 1-3 minutes)
4. Changes are committed and released

If a user submits another edit before step 4 completes, it could cause:
- Merge conflicts
- Race conditions
- Duplicate or lost edits

## Solution

Check GitHub Actions API before allowing submission. If a workflow is running, show a message and disable the submit button.

## Implementation

### 1. Add workflow status check function

In `js/app.js` or new `js/workflow.js`:

```javascript
async function isWorkflowRunning() {
    const repos = [
        'MODA-NYC/nycgo-admin-ui',
        'MODA-NYC/nyc-governance-organizations'
    ];

    for (const repo of repos) {
        const response = await fetch(
            `https://api.github.com/repos/${repo}/actions/runs?status=in_progress`,
            {
                headers: {
                    'Accept': 'application/vnd.github.v3+json'
                }
            }
        );

        if (!response.ok) {
            console.warn(`Could not check workflow status for ${repo}`);
            continue;
        }

        const data = await response.json();
        if (data.total_count > 0) {
            return {
                running: true,
                repo: repo,
                workflow: data.workflow_runs[0]?.name,
                started: data.workflow_runs[0]?.created_at
            };
        }
    }

    return { running: false };
}
```

### 2. Update submit button handler

Before allowing submission:

```javascript
async function handleSubmit() {
    const status = await isWorkflowRunning();

    if (status.running) {
        const started = new Date(status.started).toLocaleTimeString();
        showError(`A pipeline is currently running (started ${started}). Please wait a few minutes and try again.`);
        return;
    }

    // Proceed with submission...
}
```

### 3. Add visual indicator (optional)

Show a status badge in the UI:
- 🟢 Ready to submit
- 🟡 Pipeline running (started X minutes ago)
- 🔴 Pipeline failed (link to Actions)

### 4. Polling option (optional)

Auto-refresh status every 30 seconds while on the edit page:

```javascript
setInterval(async () => {
    const status = await isWorkflowRunning();
    updateStatusIndicator(status);
}, 30000);
```

## API Rate Limits

GitHub API allows 60 requests/hour for unauthenticated requests. With 30-second polling, that's 120 requests/hour per user - would exceed the limit.

Options:
1. **Authenticated requests** (5000/hour) - requires user to have GitHub token
2. **Check only on submit** - no polling, just check when user clicks submit
3. **Longer polling interval** - check every 2 minutes instead of 30 seconds

**Recommendation**: Start with option 2 (check only on submit). Simple, no rate limit concerns.

## Files to Modify

- `nycgo-admin-ui/js/app.js` - Add workflow check before submission
- `nycgo-admin-ui/index.html` - Add status indicator (optional)
- `nycgo-admin-ui/css/styles.css` - Style for status indicator (optional)

## Testing

1. Start a workflow (submit an edit)
2. Try to submit another edit immediately
3. Should see error message and be prevented from submitting
4. Wait for workflow to complete
5. Should be able to submit again

## Definition of Done

- [ ] Submit button checks workflow status before allowing submission
- [ ] Clear error message shown when workflow is running
- [ ] Works for both admin-ui and pipeline repo workflows
- [ ] No rate limit issues
- [ ] Tested end-to-end
