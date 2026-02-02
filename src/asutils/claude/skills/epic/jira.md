---
allowed-tools: Bash(jira:*), Bash(curl:*)
description: JIRA issue management for MLS and RNG/EDA teams. Use for viewing, creating, updating, and organizing work items.
---

# JIRA Management Skill

## Environment Setup

The JIRA CLI uses the `JIRA_API_TOKEN` environment variable for authentication.
- Server: https://epicgames.atlassian.net
- Default Project: EML
- User: alex.spies@epicgames.com

## Key Reference Data

### Team Members (Account IDs for API calls)
| Name | Email | Account ID |
|------|-------|------------|
| Alex Spies | alex.spies@epicgames.com | 712020:7b9673b2-0ee0-4b65-9793-aeff72781428 |
| Zhenhao Li | zhenhao.li@epicgames.com | 63c844dd0036340dcb5d08d7 |

### Active Sprints
| Sprint | ID | Team |
|--------|-----|------|
| MLS Chatbots 26-2 | 1628 | Chatbots |

To find current sprints: `jira sprint list --plain | grep -i <team>`

### Priority Values
Priorities must use the exact format with number prefix:
- `0 - Blocker`
- `1 - Critical`
- `2 - Major`
- `3 - Minor`
- `4 - Trivial`
- `TBD` (default if not set)

## Project Contexts

### MLS Team - Text-Chatbot-Service
- **Project**: EML
- **Focus**: Backend ML services, text-deva-service, model training/deployment
- **Key Epics**:
  - EML-5113: Build text-deva-service for Verse VSCode assistant
  - EML-6201: Train and deploy Verse code completion model
  - EML-6202: Verse VSCode Extension development and integration

### RNG Team - EDA (Editor AI Assistant)
- **Jira Spaces**: RND (primary), EDCDEV, UE
- **Initiative**: RND-263 (UE Editor AI Assistant)
- **Required Component**: "AI - Assistant" (must be on ALL items)
- **Labels for filtering by software component**:
  - `AIAssistantUEPlugins` - UE plugins
  - `AIAssistantFrontend` - Web Frontend
  - `AIAssistantBackend` - Backend services

## Work Item Hierarchy

```
Initiative (RND-263: UE Editor AI Assistant)
  └── Deliverable (milestones within initiative)
       └── Epic (weeks/months of work)
            └── Task / Bug (hours/days of work)
```

## Common Commands

### View Issues
```bash
# My open issues
jira issue list --assignee "alex.spies@epicgames.com" -s~Done -s~Closed -s~"Won't Do" --plain

# Issues in specific status
jira issue list -s"In Progress" --plain

# View specific issue (shows links, sprint, etc.)
jira issue view EML-1234 --plain

# Open in browser
jira open EML-1234
```

### Create Issues
```bash
# Full task creation with all fields
jira issue create \
  -tTask \
  -P EML-6202 \
  -s"[Frontend] Task Title" \
  -a"alex.spies@epicgames.com" \
  -lAIAssistantFrontend \
  -C"AI - Assistant" \
  -y"2 - Major" \
  -b"Description here" \
  --no-input --raw

# Create bug
jira issue create -tBug -s"Bug summary" -y"1 - Critical"
```

### Update Issues
```bash
# Set priority (must use exact format!)
jira issue edit EML-1234 -y"2 - Major" --no-input

# Add label
jira issue edit EML-1234 -lAIAssistantFrontend --no-input

# Add component
jira issue edit EML-1234 -C"AI - Assistant" --no-input

# Move to status
jira issue move EML-1234 "In Progress"
jira issue move EML-1234 "Code Review"
jira issue move EML-1234 "Done"

# Assign
jira issue assign EML-1234 "alex.spies@epicgames.com"

# Add comment
jira issue comment add EML-1234 "Comment text"
```

### Setting Reporter (requires REST API)
The CLI doesn't support editing reporter. Use curl with account ID:
```bash
TOKEN="$JIRA_API_TOKEN"
AUTH=$(printf 'alex.spies@epicgames.com:%s' "$TOKEN" | base64)
curl -s -X PUT \
  -H "Authorization: Basic $AUTH" \
  -H "Content-Type: application/json" \
  -d '{"fields":{"reporter":{"accountId":"63c844dd0036340dcb5d08d7"}}}' \
  "https://epicgames.atlassian.net/rest/api/3/issue/EML-1234"
```

### Finding User Account IDs
```bash
TOKEN="$JIRA_API_TOKEN"
AUTH=$(printf 'alex.spies@epicgames.com:%s' "$TOKEN" | base64)
curl -s -G \
  -H "Authorization: Basic $AUTH" \
  --data-urlencode "query=firstname.lastname" \
  "https://epicgames.atlassian.net/rest/api/3/user/search" | jq '.[0]'
```

### Sprint Management
```bash
# List sprints (find ID)
jira sprint list --plain | grep -i chatbot

# Add multiple issues to sprint
jira sprint add 1628 EML-1234 EML-1235 EML-1236

# Current sprint issues
jira sprint list --current
```

### Linking Issues
```bash
# Create "Blocks" relationship (issue1 blocks issue2)
jira issue link EML-1234 EML-1235 Blocks

# Link types: Blocks, Relates, Duplicates, Clones
```

### Epic Management
```bash
# List epics
jira epic list --plain

# View epic with children
jira epic list EML-6202 --plain

# Create task under epic (use -P flag)
jira issue create -tTask -P EML-6202 -s"Task title"
```

## Filing Issues Best Practices (RNG/EDA)

When creating issues for the EDA project:

1. **Check for duplicates first** using search
2. **Create in RND space** (unless directed otherwise)
3. **Required fields**:
   - Clear title summarizing the issue
   - Detailed description for team action
   - Component: "AI - Assistant"
   - Labels: `AIAssistantUEPlugins`, `AIAssistantFrontend`, or `AIAssistantBackend`
   - Priority (use exact format like "2 - Major")
   - Reporter: Set via REST API if not the creator
4. **Add to sprint** after creation
5. **Set up dependency links** if blocked by other work

## Batch Operations

### Create multiple linked tasks
```bash
# Create tasks (capture IDs from --raw output)
ID1=$(jira issue create -tTask -P EML-6202 -s"Task 1" --no-input --raw | jq -r '.key')
ID2=$(jira issue create -tTask -P EML-6202 -s"Task 2" --no-input --raw | jq -r '.key')

# Link them
jira issue link $ID1 $ID2 Blocks

# Add all to sprint
jira sprint add 1628 $ID1 $ID2
```

### Update reporter on multiple issues
```bash
TOKEN="$JIRA_API_TOKEN"
AUTH=$(printf 'alex.spies@epicgames.com:%s' "$TOKEN" | base64)
for issue in EML-1234 EML-1235 EML-1236; do
  curl -s -X PUT \
    -H "Authorization: Basic $AUTH" \
    -H "Content-Type: application/json" \
    -d '{"fields":{"reporter":{"accountId":"63c844dd0036340dcb5d08d7"}}}' \
    "https://epicgames.atlassian.net/rest/api/3/issue/$issue" &
done
wait
```

## Quick Reference

| Action | Command |
|--------|---------|
| My issues | `jira issue list --assignee "alex.spies@epicgames.com" -s~Done --plain` |
| View issue | `jira issue view EML-1234 --plain` |
| Open in browser | `jira open EML-1234` |
| Create task under epic | `jira issue create -tTask -P EML-6202 -s"Summary" -C"AI - Assistant" -lAIAssistantFrontend -y"2 - Major" --no-input --raw` |
| Set priority | `jira issue edit EML-1234 -y"2 - Major" --no-input` |
| Link issues | `jira issue link EML-1234 EML-1235 Blocks` |
| Add to sprint | `jira sprint add 1628 EML-1234` |
| Find sprint ID | `jira sprint list --plain \| grep -i chatbot` |
| List epic children | `jira epic list EML-6202 --plain` |
