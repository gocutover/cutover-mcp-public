# Cutover Reporting Playbook

**Version:** 1.4  
**Last Updated:** February 26, 2026  
**Environment:** Staging (your-tenant.cutover.com)

---

## ⚠️ MANDATORY BRANDING REQUIREMENTS - READ FIRST

**🔴 CRITICAL - NON-NEGOTIABLE: ALL dashboards and reports MUST comply with these EXACT requirements.**

**⚡ AUTO-ENFORCEMENT:** When creating ANY dashboard, visualization, or report, you MUST automatically implement ALL requirements below WITHOUT asking for permission or confirmation. These are MANDATORY defaults, not optional suggestions.

### Pre-Implementation Checklist (MANDATORY - AUTO-APPLY)

Before creating ANY dashboard or report, you WILL automatically implement:

- [ ] ✅ **Official Cutover Logo from CDN** (MANDATORY - NO EXCEPTIONS)
  - **EXACT URL (USE THIS):** `https://cdn.prod.website-files.com/628d04e7099dc5d9a4d46fa9/628e088a063b140502a7f239_Cutover_Logo%20Full%20Color%202.svg`
  - FORBIDDEN: Custom SVG paths, text logos, PNG fallbacks, or any logo modifications
  - REQUIRED: Include in both header AND footer of every dashboard
  - See [Section 12](#12-cutover-design-system--branding) for implementation details

- [ ] ✅ **Official Cutover Color Palette** (EXACT HEX VALUES REQUIRED)
  - **PRIMARY:** `#2A55C3` (Cutover Blue) - Use for headers, buttons, primary elements
  - **BACKGROUND:** `#f0f0f0` (Light Grey) - Use for page background
  - **SUCCESS:** `#27ae60` (Green) - Use for positive metrics, completion
  - **WARNING:** `#f39c12` (Orange) - Use for caution states
  - **DANGER:** `#e74c3c` (Red) - Use for errors, critical items
  - **DARK:** `#16161d` - Use for primary text, headings
  - FORBIDDEN: Purple colors, gradient backgrounds, custom color schemes
  - See [Section 12.2](#color-palette) for complete palette

- [ ] ✅ **System Fonts ONLY** (NO web fonts, NO custom fonts, NO exceptions)
  - **EXACT FONT-FAMILY:** `-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen-Sans, Ubuntu, Cantarell, sans-serif`
  - FORBIDDEN: Google Fonts, custom font files, @font-face declarations

- [ ] ✅ **4px Spacing System** (STRICT MULTIPLES ONLY)
  - ALLOWED: `4px`, `8px`, `12px`, `16px`, `20px`, `24px`, `32px`, `40px`, `48px`
  - FORBIDDEN: Arbitrary values like `15px`, `25px`, `35px`
  - ALL margins, padding, gaps MUST be multiples of 4px

- [ ] ✅ **Official Component Styles** (EXACT SPECIFICATIONS)
  - Border radius: `8px` (cards), `12px` (badges) - NO exceptions
  - Font weight: `600` for headings (NOT 700, NOT bold)
  - Card shadows: `0 1px 3px rgba(0, 0, 0, 0.08)` (subtle)
  - Button padding: `8px 16px` (vertical horizontal)

- [ ] ✅ **Interactive Visualizations** (MANDATORY FOR DASHBOARDS)
  - **HIGH-LEVEL REQUIREMENT**: All dashboards MUST be high-level with graphs and charts
  - Chart.js library: `https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js`
  - Minimum 2-4 charts per dashboard (pie, bar, line, etc.)
  - Charts provide instant insights - NOT optional
  - Dashboards should tell the story visually first, details second
  - See [Section 11](#11-output-formats) for implementation patterns

- [ ] ✅ **PDF Export Functionality** (MANDATORY FOR ALL DASHBOARDS)
  - html2pdf.js library: `https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.10.1/html2pdf.bundle.min.js`
  - Export button in header with "📄 Export PDF" label
  - Exports complete dashboard with all visualizations
  - Preserves Cutover branding in exported PDF
  - See [Section 11](#11-output-formats) for implementation details

- [ ] ✅ **Names Over IDs** (MANDATORY - HUMAN READABILITY)
  - **ALWAYS display names**, not IDs for: runbooks, tasks, users, teams, task types, streams, etc.
  - Fetch name mappings (task types, users, teams) BEFORE generating dashboard
  - IDs are supplementary only (tooltips, secondary columns, technical details)
  - Examples: Show "Milestone Task" NOT "Task Type 39", "john.smith@company.com" NOT "User 273"
  - See [Section 11](#11-output-formats) Rule 2 for implementation details

- [ ] ✅ **Human-Readable Design** (ESSENTIAL FOR USABILITY)
  - Show top 10-15 items by default, add "Show More" for full lists
  - Use tables for 20+ items, not card layouts
  - Include quick summary stats at top of each section
  - Progressive disclosure: hide complexity behind expandable sections
  - See [Section 11](#11-output-formats) for best practices

**🚨 ENFORCEMENT:** Any dashboard created WITHOUT these specifications is non-compliant and MUST be recreated. Reference [Section 12](#12-cutover-design-system--branding) for complete implementation guide.

**✅ REFERENCE IMPLEMENTATION:** Copy structure from `create_cutover_branded_template_dashboard.py` - this is the GOLD STANDARD.

**✅ BEST PRACTICE EXAMPLE:** `create_cutover_recover_live_runs_dashboard.py`
- Demonstrates Chart.js integration (4 interactive charts)
- Shows progressive disclosure (Show More buttons)
- Uses compact table format for large datasets
- Includes quick summary stats per section
- Prioritizes human readability over data completeness

---

## 🎯 Critical Tips - Always Remember

**These are the most common mistakes and their solutions - memorize these:**

1. **🎨 BRANDING ALWAYS COMES FIRST**
   - Logo: `https://cdn.prod.website-files.com/628d04e7099dc5d9a4d46fa9/628e088a063b140502a7f239_Cutover_Logo%20Full%20Color%202.svg`
   - Primary color: `#2A55C3` (Cutover Blue) - NEVER purple, NEVER gradients
   - System fonts: `-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto`
   - Font weight: `600` (NOT 700) for headings

2. **📊 Template Analysis Requires Individual GETs**
   - `source_runbook` relationship NOT available on list endpoints
   - MUST fetch each non-template runbook individually: `GET /core/runbooks/{id}`
   - Budget 0.6s per runbook, save progress every 50 items
   - Expect 70-75% of runbooks to have source_runbook relationships

3. **🔍 Real Stage Values (NOT Documentation)**
   - Use: `planning`, `active`, `complete`, `canceled`
   - IGNORE: `approval`, `scheduled`, `in_progress` (don't exist in real data)

4. **⚠️ API Filters are Unreliable**
   - `filter[workspace_id]=233` returns runbooks from OTHER workspaces
   - ALWAYS verify `relationships.workspace.data.id` in code
   - Post-filter ALL results after fetching

5. **👤 User Attribution via task_actions ONLY**
   - DON'T use action_logs (returns 2022 data!)
   - DO use: `GET /runbooks/{id}/tasks/{id}?include=task_actions`
   - Parse `included` array for `action='start'` to get executor

6. **⏱️ Rate Limiting is Essential**
   - Tasks: 0.6-1.5s delay between requests
   - Individual runbook fetches: 0.6s delay minimum
   - Implement exponential backoff for 429 errors
   - Save progress frequently for long operations

7. **✅ Verification Pattern (Always Use)**
   ```python
   # Verify workspace
   actual_ws = rb['relationships']['workspace']['data']['id']
   if actual_ws != '233': continue
   
   # Verify not template
   if rb['attributes'].get('is_template'): continue
   
   # Verify not archived
   if rb['attributes'].get('archived_at'): continue
   ```

8. **📊 VISUALIZATIONS ARE MANDATORY - NOT OPTIONAL**
   - **HIGH-LEVEL REQUIREMENT**: All dashboards MUST be high-level with graphs and charts
   - **ALWAYS include Chart.js graphs/charts** in dashboards
   - Dashboards should tell the story visually with charts FIRST, then provide details
   - Charts provide instant insights that tables cannot
   - Required charts: Overview pie/doughnut, top items bar chart, trend/comparison charts
   - Use Chart.js CDN: `https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js`
   - Match chart colors to Cutover palette (#2A55C3, #27ae60, #f39c12, #e74c3c)
   - Every dashboard MUST have minimum 2-4 visual charts
   - Visual storytelling takes priority over raw data dumps

9. **👤 DESIGN FOR HUMAN CONSUMPTION - ESSENTIAL**
   - **Concise by default**: Show top 10-15 items, add "Show More" buttons for full lists
   - **Use tables, not cards**: For long lists (100+ items), use compact table format
   - **Quick stats boxes**: Display key metrics at-a-glance before detailed data
   - **Progressive disclosure**: Hide complexity behind expandable sections
   - **Scannable format**: Use consistent column widths, alternating row colors, hover states
   - **Limit initial view**: Never show 1000+ items on page load - paginate or collapse
   - Remember: If users have to scroll for 30 seconds, the dashboard has failed

10. **📝 ALWAYS USE NAMES, NOT IDs - CRITICAL FOR READABILITY**
   - **MANDATORY**: Always display names for runbooks, tasks, users, teams, task types, etc.
   - **NEVER show**: "Task Type 463", "Runbook 8890", "User 273", "Team 45"
   - **ALWAYS show**: "Validation Task", "DR Cutover Runbook", "john.smith@company.com", "Infrastructure Team"
   - **IDs are secondary**: Include IDs only as supplementary info (tooltips, hover text, or secondary columns)
   - **Fetch name mappings**: Use API to get task types, user emails, team names before generating output
   - **Example pattern**: Fetch task_types first, create ID→name lookup dict, use names in all displays
   - **Why**: Humans think in names, not numbers - "Milestone" is instantly meaningful, "39" is not
   - Remember: If users need a reference sheet to understand your dashboard, it has failed

---

## Table of Contents

1. [Quick Reference](#1-quick-reference)
2. [API Configuration](#2-api-configuration)
3. [Critical Bugs & Workarounds](#3-critical-bugs--workarounds)
4. [Template Relationships & Source Runbook Discovery](#4-template-relationships--source-runbook-discovery)
5. [Workspace & Runbook Discovery](#5-workspace--runbook-discovery)
6. [User Attribution (THE BREAKTHROUGH)](#6-user-attribution-the-breakthrough)
7. [Task Data Extraction](#7-task-data-extraction)
8. [Time Calculations & Metrics](#8-time-calculations--metrics)
9. [Rate Limiting & Pagination](#9-rate-limiting--pagination)
   - Rate Limiting Strategy
   - Handling 429 Errors
   - Pagination Patterns
   - ⚡ API Filtering for Efficiency (NEW)
10. [Data Processing Patterns](#10-data-processing-patterns)
11. [Output Formats](#11-output-formats)
   - **Dashboard Design Principles (CRITICAL)**
   - Visualizations First
   - Progressive Disclosure
   - Human-Readable Best Practices
12. [Cutover Design System & Branding](#12-cutover-design-system--branding)
    - **Official Logo Requirements (STRICT - NO CUSTOM LOGOS)**
    - Color Palette
    - Typography
    - Component Patterns
13. [Code Templates](#13-code-templates)
14. [Decision Trees](#14-decision-trees)

---

## 1. Quick Reference

### Common Tasks - TL;DR

```python
# Get all workspaces
GET /core/workspaces

# ⚡ Get completed runbooks in workspace 233 (EFFICIENT - uses API filtering)
GET /core/runbooks?workspace_id=233&stage=complete&archive=false
# Returns only completed, non-archived runbooks (1-2 pages instead of 100+)

# 🎯 Get individual runbook with source_runbook relationship (for template analysis)
GET /core/runbooks/{runbook_id}
# ⚠️ CRITICAL: source_runbook NOT available on list endpoints!
# Must fetch individually for each non-template runbook

# Get task with user attribution
GET /core/runbooks/{runbook_id}/tasks/{task_id}?include=task_actions
# ✓ Parse 'included' array for task_action with action='start'

# Get user details
GET /core/users/{user_id}

# 📖 Full API Reference: https://developer.cutover.com/endpoints
```

### Known Values (Workspace 233)

- **Workspace ID:** `233`
- **Workspace Name:** `02. Cutover Recover`
- **Total Runbooks:** 2,020
  - Templates: 1,767
  - Non-template runbooks: 253
  - Template adoption rate: 73.9% (187 of 253 created from templates)
- **Active Users:** 7 identified (Dhiren, Arty, Max, Melissa, Marcus, Mark, Saif)
- **Typical Runbooks:** 11 completed live runs (InfraSync, RevMax, CloudWatch demos)
- **Total Tasks Analyzed:** 96 tasks
- **Top Template:** Template 5690 (7 runbooks created from it)

### Reference Implementation - Correctly Branded Dashboard

**✅ CORRECT EXAMPLE:** `create_cutover_branded_template_dashboard.py`
- Demonstrates proper implementation of ALL branding requirements
- Official Cutover logo from CDN (header and footer)
- Official color palette (#2A55C3 primary, NOT purple gradients)
- System fonts with 4px spacing system
- Proper component styling following playbook guidelines

**❌ INCORRECT EXAMPLES:** Any dashboard using:
- Purple gradient backgrounds
- Custom SVG logos or text-based logos
- Custom color schemes
- Arbitrary spacing values
- Font weights of 700 instead of 600

**When creating new dashboards:** Copy the structure from `create_cutover_branded_template_dashboard.py` and modify the data/content while keeping the branding intact.

---

## 2. API Configuration

### Base URLs & Authentication

```python
API_BASE = 'https://api.staging.cutover.cloud'
CORE_URL = 'https://your-tenant.cutover.com'
TOKEN = 'REMOVED_FOR_SECURITY'

headers = {
    'Authorization': f'Bearer {TOKEN}',
    'Content-Type': 'application/vnd.api+json',
    'Core-Url': CORE_URL
}
```

### Required Headers

| Header | Value | Required | Notes |
|--------|-------|----------|-------|
| `Authorization` | `Bearer {TOKEN}` | ✅ Yes | API authentication |
| `Core-Url` | `https://your-tenant.cutover.com` | ✅ Yes | Tenant identifier |
| `Content-Type` | `application/vnd.api+json` | ✅ Yes | JSON:API format |

### SSL Verification

```python
# Disable SSL warnings for staging environment
from urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

# All requests should use verify=False
resp = requests.get(url, headers=headers, verify=False)
```

---

## 3. Critical Bugs & Workarounds

### 🚨 TOP ISSUES ENCOUNTERED

#### Issue #1: API Filters Return Wrong Workspace Data

**Problem:**
```python
# This filter DOES NOT WORK correctly
params = {'filter[workspace_id]': '233'}
resp = requests.get(f'{API_BASE}/core/runbooks', params=params)
# Returns runbooks from workspaces 1, 2, 3, 35, 37, etc.
```

**Solution:**
```python
# ✓ ALWAYS verify workspace in response
for runbook in data['data']:
    actual_workspace_id = runbook['relationships']['workspace']['data']['id']
    if actual_workspace_id == '233':
        # This runbook is ACTUALLY in workspace 233
        verified_runbooks.append(runbook)
```

**Verified Bug:** Out of 40 runbooks returned by filter[workspace_id]=233, only 12 actually belonged to workspace 233.

---

#### Issue #2: Action Logs Return Historical Data (2022!)

**Problem:**
```python
# ❌ DON'T USE ACTION LOGS FOR USER ATTRIBUTION
params = {'filter[action]': 'task_start'}
resp = requests.get(f'{API_BASE}/core/action_logs', params=params)
# Returns data from 2022, not recent executions!
# User attribution is WRONG
```

**Discovery Timeline:**
- Initial approach: Used action logs → Found only 1 user (User 596)
- User challenged: "runbook 8648, the user was Melissa Sommer" (User 273)
- Investigation revealed: Action logs had wrong users and old dates

**Solution:** See Section 6 for correct method using task_actions.

---

#### Issue #3: source_runbook Relationship ONLY Available on Individual GET

**Problem:**
```python
# ❌ THIS DOESN'T WORK - include parameter ignored on list endpoints
params = {'include': 'source_runbook'}
resp = requests.get(f'{API_BASE}/core/runbooks', params=params)
# Returns runbooks WITHOUT source_runbook relationship
# Template analysis shows 0% adoption incorrectly
```

**Discovery:**
- List endpoint (`GET /core/runbooks`) does NOT include `source_runbook` relationship
- The `include=source_runbook` parameter is IGNORED on list endpoints
- Only individual GET (`GET /core/runbooks/{id}`) returns `source_runbook`
- This affects template usage analysis and tracking runbook lineage

**Solution:**
```python
# ✓ CORRECT: Fetch individual runbooks to get source_runbook
def enrich_with_source_runbooks(runbooks):
    """
    Enrich runbook data with source_runbook relationships
    Required for template usage analysis
    """
    enriched = []
    
    for rb in runbooks:
        # Skip templates - only non-templates have source_runbook
        if rb['attributes'].get('is_template'):
            enriched.append(rb)
            continue
        
        runbook_id = rb['id']
        
        # Fetch individual runbook to get source_runbook relationship
        resp = requests.get(
            f'{API_BASE}/core/runbooks/{runbook_id}',
            headers=headers,
            verify=False
        )
        
        if resp.status_code == 200:
            detailed_rb = resp.json()['data']
            enriched.append(detailed_rb)
        else:
            enriched.append(rb)  # Fallback to original
        
        # CRITICAL: Rate limit to avoid 429 errors
        time.sleep(0.6)  # 600ms delay recommended
        
        # Save progress every 50 runbooks for long operations
        if len(enriched) % 50 == 0:
            save_progress(enriched)  # Implement checkpoint saving
    
    return enriched
```

**Performance Considerations:**
- 253 non-template runbooks × 0.6s delay = ~2.5 minutes
- Implement progress saving every 50 items to prevent data loss
- Handle 429 errors with exponential backoff if needed
- Cache enriched data to avoid repeated API calls

**Verified:** Workspace 233 analysis showed 187 of 253 non-template runbooks (73.9%) have source_runbook relationships when fetched individually, but 0% when using list endpoint.

---

#### Issue #4: Template/Archived Runbooks Appear in Results

**Problem:**
```python
# Filters don't properly exclude templates and archived runbooks
params = {
    'filter[is_template]': 'false',
    'filter[archived]': 'false'
}
# Still returns templates and archived runbooks
```

**Solution:**
```python
# ✓ Post-filter in code after fetching
for runbook in data['data']:
    attrs = runbook['attributes']
    if (attrs.get('is_template') == False and
        attrs.get('archived_at') is None and
        attrs.get('template_type') == 'off' and
        attrs.get('run_type') == 'live' and
        attrs.get('stage') == 'complete'):
        # This is a genuine completed live run
        valid_runbooks.append(runbook)
```

---

## 4. Template Relationships & Source Runbook Discovery

### 🎯 The source_runbook Breakthrough

**Context:** Analyzing template usage showed 0% adoption despite knowing runbooks were created from templates. Investigation revealed a critical API limitation.

**The Relationship:**
```json
{
  "relationships": {
    "source_runbook": {
      "data": {
        "id": "6927",
        "type": "runbook"
      }
    }
  }
}
```

**Key Facts:**
- Relationship name: `source_runbook` (NOT `template_source`, NOT `template`)
- Only present on runbooks created from templates
- Points to the template runbook that was used as source
- Only available on individual GET, NOT on list endpoints

### Identifying Template vs. Non-Template Runbooks

**Templates are identified by:**
```python
def is_template(runbook):
    """Determine if a runbook is a template"""
    attrs = runbook.get('attributes', {})
    return (
        attrs.get('is_template') == True or
        attrs.get('template_type') != 'off'
    )
```

**Non-template runbooks created from templates:**
```python
def get_source_template(runbook, templates_dict):
    """
    Get the source template for a runbook
    Returns template info if runbook was created from template
    """
    relationships = runbook.get('relationships', {})
    source_runbook = relationships.get('source_runbook', {}).get('data')
    
    if source_runbook and source_runbook.get('id'):
        source_id = source_runbook['id']
        # Verify source is actually a template
        if source_id in templates_dict:
            return {
                'template_id': source_id,
                'template_name': templates_dict[source_id]['name']
            }
    
    return None  # Not created from a template
```

### Template Usage Analysis Pattern

**Complete workflow for accurate template analysis:**

```python
import requests
import time
import json
from collections import defaultdict

def analyze_template_usage(workspace_id='233'):
    """
    Complete template usage analysis with source_runbook enrichment
    """
    # Step 1: Get all runbooks (list endpoint)
    all_runbooks = fetch_all_runbooks(workspace_id)
    
    # Step 2: Identify templates
    templates = {}
    non_templates = []
    
    for rb in all_runbooks:
        if is_template(rb):
            templates[rb['id']] = {
                'id': rb['id'],
                'name': rb['attributes'].get('name', 'Unnamed'),
                'created_at': rb['attributes'].get('created_at')
            }
        else:
            non_templates.append(rb)
    
    print(f"Found {len(templates)} templates")
    print(f"Found {len(non_templates)} non-template runbooks")
    
    # Step 3: Enrich non-templates with source_runbook (CRITICAL)
    enriched_runbooks = enrich_with_source_runbooks(non_templates)
    
    # Step 4: Analyze template usage
    template_usage = defaultdict(lambda: {
        'count': 0,
        'runbooks': []
    })
    
    templated_count = 0
    
    for rb in enriched_runbooks:
        source = get_source_template(rb, templates)
        if source:
            template_id = source['template_id']
            template_usage[template_id]['count'] += 1
            template_usage[template_id]['runbooks'].append({
                'id': rb['id'],
                'name': rb['attributes'].get('name'),
                'created_at': rb['attributes'].get('created_at')
            })
            templated_count += 1
    
    # Step 5: Calculate metrics
    total_runbooks = len(non_templates)
    adoption_rate = (templated_count / total_runbooks * 100) if total_runbooks > 0 else 0
    
    print(f"\nTemplate Adoption: {templated_count}/{total_runbooks} ({adoption_rate:.1f}%)")
    
    # Step 6: Get top templates
    top_templates = sorted(
        template_usage.items(),
        key=lambda x: x[1]['count'],
        reverse=True
    )[:10]
    
    print("\nTop 10 Templates by Usage:")
    for template_id, data in top_templates:
        template_name = templates[template_id]['name']
        print(f"  {template_id}: {template_name} - {data['count']} runbooks")
    
    return {
        'templates': templates,
        'template_usage': dict(template_usage),
        'adoption_rate': adoption_rate,
        'total_runbooks': total_runbooks,
        'templated_runbooks': templated_count
    }

def enrich_with_source_runbooks(runbooks):
    """See Issue #3 for complete implementation"""
    # Implementation in previous section
    pass
```

### Real-World Example: Workspace 233

**Results from enrichment:**
- Total runbooks: 2,020
- Templates: 1,767
- Non-template runbooks: 253
- Runbooks with source_runbook: 187 (73.9%)
- Runbooks without source_runbook: 66 (26.1%)

**Template 6927 (RevMax InfraSync) Example:**
- Template Name: "RevMax - Application Infrastructure Recovery Plan: InfraSync"
- Usage: 5 runbooks created from this template
- Runbooks:
  1. 8419: RevMax - Application Infrastructure Recovery Plan: InfraSync
  2. 9006: MCP test
  3. 8791: RevMax - Application Infrastructure Recovery Plan: InfraSync MW 2
  4. 8790: RevMax - Application Infrastructure Recovery Plan: InfraSync MW
  5. 7009: RevMax - Application Infrastructure Recovery Plan: InfraSync copy

**Top 3 Templates:**
1. Template 5690: 7 runbooks
2. Template 5967: 6 runbooks  
3. Template 6927: 5 runbooks

### Stage Values in Real Data

**Actual stage values in Cutover (NOT documentation):**
- `planning` - Runbook being planned
- `active` - Runbook currently executing
- `complete` - Runbook finished
- `canceled` - Runbook cancelled

**NOT found in real data:**
- `approval`, `scheduled`, `in_progress` (use `active` instead)

```python
# ✓ CORRECT: Use actual stage values
valid_stages = ['planning', 'active', 'complete', 'canceled']

# ❌ INCORRECT: Documentation stages that don't exist
invalid_stages = ['approval', 'scheduled', 'in_progress']
```

### Best Practices for Template Analysis

1. **Always enrich with individual GETs**
   - List endpoints don't include source_runbook
   - Budget ~0.6s per non-template runbook for API calls
   - Cache enriched data to avoid repeated enrichment

2. **Verify source is a template**
   - source_runbook can point to non-template runbooks
   - Always check if source_id exists in templates dictionary

3. **Handle missing relationships**
   - Not all runbooks have source_runbook (manually created)
   - ~25-30% of runbooks may be created without templates

4. **Save progress for large datasets**
   - 250+ runbooks = ~2.5 minutes of API calls
   - Save every 50 items to prevent data loss on errors
   - Implement resume capability for failed enrichments

5. **Rate limiting is critical**
   - Use 0.6s (600ms) delay between individual runbook fetches
   - Monitor for 429 errors and implement backoff if needed
   - Consider parallel fetching with semaphore (max 3 concurrent)

6. **ALWAYS display names, not IDs**
   - Show runbook names: "DR Infrastructure Cutover" NOT "Runbook 8890"
   - Show template names: "Production Release Template" NOT "Template 5690"
   - Show user names/emails: "john.smith@company.com" NOT "User 273"
   - Fetch all name mappings before generating final output
   - Use IDs only for internal lookups or as supplementary data

---

## 5. Workspace & Runbook Discovery

### List All Workspaces

```python
def get_all_workspaces():
    """Get all workspaces in the instance"""
    resp = requests.get(
        f'{API_BASE}/core/workspaces',
        headers=headers,
        verify=False
    )
    
    if resp.status_code == 200:
        workspaces = []
        for ws in resp.json()['data']:
            workspaces.append({
                'id': ws['id'],
                'name': ws['attributes']['name']
            })
        return workspaces
    return []

# Example output for workspace 233:
# {'id': '233', 'name': '02. Cutover Recover'}
```

### Get Completed Runbooks (Correct Method)

```python
def get_completed_runbooks_in_workspace(workspace_id='233'):
    """
    Get all completed live runbooks in a workspace
    Applies post-filtering due to API filter bugs
    """
    all_runbooks = []
    page = 1
    
    while True:
        params = {
            'filter[workspace_id]': workspace_id,
            'filter[stage]': 'complete',
            'page[number]': page,
            'page[size]': 100
        }
        
        resp = requests.get(
            f'{API_BASE}/core/runbooks',
            params=params,
            headers=headers,
            verify=False
        )
        
        if resp.status_code != 200:
            break
        
        data = resp.json()
        runbooks = data.get('data', [])
        
        if not runbooks:
            break
        
        # ✓ CRITICAL: Verify workspace and filter criteria
        for rb in runbooks:
            actual_ws = rb['relationships']['workspace']['data']['id']
            attrs = rb['attributes']
            
            if (actual_ws == workspace_id and
                attrs.get('is_template') == False and
                attrs.get('archived_at') is None and
                attrs.get('template_type') == 'off' and
                attrs.get('run_type') == 'live' and
                attrs.get('stage') == 'complete'):
                
                all_runbooks.append({
                    'id': rb['id'],
                    'name': attrs['name'],
                    'completed_at': attrs.get('completed_at')
                })
        
        # Check for next page
        if not data.get('links', {}).get('next'):
            break
        
        page += 1
        time.sleep(0.5)  # Rate limiting
    
    return all_runbooks
```

### Runbook Attributes Checklist

| Attribute | Value | Meaning |
|-----------|-------|---------|
| `stage` | `'complete'` | Runbook has finished execution |
| `is_template` | `False` | Not a template |
| `template_type` | `'off'` | Confirms not a template |
| `run_type` | `'live'` | Live run (not rehearsal) |
| `archived_at` | `None` | Not archived |

---

## 5. User Attribution (THE BREAKTHROUGH)

### ❌ WRONG METHOD: Action Logs

```python
# DON'T DO THIS - Returns 2022 data!
def get_user_wrong_method(runbook_id, task_id):
    params = {
        'filter[runbook_id]': runbook_id,
        'filter[task_id]': task_id,
        'filter[action]': 'task_start'
    }
    resp = requests.get(
        f'{API_BASE}/core/action_logs',
        params=params,
        headers=headers,
        verify=False
    )
    # Returns historical data, wrong users!
```

### ✅ CORRECT METHOD: Task Actions in Included Array

**Discovery:** User corrected us pointing out "runbook 8648, the user was Melissa Sommer"

**The Breakthrough:**
When fetching individual tasks with `include=task_actions`, the response contains an `included` array with `task_action` objects. The task_action with `action='start'` contains the correct user relationship.

```python
def get_task_with_user(runbook_id, task_id):
    """
    ✓ CORRECT METHOD: Get task with user attribution
    """
    resp = requests.get(
        f'{API_BASE}/core/runbooks/{runbook_id}/tasks/{task_id}',
        params={'include': 'task_actions'},  # ← CRITICAL PARAMETER
        headers=headers,
        verify=False
    )
    
    if resp.status_code != 200:
        return None
    
    data = resp.json()
    task_data = data.get('data', {})
    included = data.get('included', [])  # ← THE KEY!
    
    # Find task_action with action='start'
    user_id = None
    for item in included:
        if item['type'] == 'task_action':
            if item['attributes'].get('action') == 'start':
                user_rel = item.get('relationships', {}).get('user', {})
                user_id = user_rel.get('data', {}).get('id')
                break
    
    return {
        'task_id': task_data['id'],
        'task_name': task_data['attributes'].get('name'),
        'start_actual': task_data['attributes'].get('start_actual'),
        'end_actual': task_data['attributes'].get('end_actual'),
        'user_id': user_id
    }
```

### JSON Response Structure

```json
{
  "data": {
    "id": "2",
    "type": "task",
    "attributes": {
      "name": "Task name",
      "start_actual": "2025-11-13T19:13:00Z",
      "end_actual": "2025-11-13T19:13:05Z"
    },
    "relationships": {
      "task_actions": {
        "data": [
          {"id": "27817", "type": "task_action"}
        ]
      }
    }
  },
  "included": [
    {
      "id": "27817",
      "type": "task_action",
      "attributes": {
        "action": "start",
        "created_at": "2025-11-13T19:13:00Z"
      },
      "relationships": {
        "user": {
          "data": {
            "id": "273",  ← THIS IS THE CORRECT USER ID
            "type": "user"
          }
        }
      }
    }
  ]
}
```

### Get User Details

```python
def get_user_details(user_id):
    """Fetch user name and email"""
    resp = requests.get(
        f'{API_BASE}/core/users/{user_id}',
        headers=headers,
        verify=False
    )
    
    if resp.status_code == 200:
        user_data = resp.json()['data']
        attrs = user_data['attributes']
        return {
            'id': user_id,
            'name': attrs.get('name', 'Unknown'),
            'email': attrs.get('email', 'unknown@email.com')
        }
    return None
```

### Validated Users (Workspace 233)

| User ID | Name | Email | Efficiency |
|---------|------|-------|-----------|
| 39 | Dhiren Mistry | dhiren.mistry@cutover.com | 98.2% |
| 262 | Arty San-Segundo | arty.san-segundo@cutover.com | 82.4% |
| 289 | Max Walmsley | max.walmsley@cutover.com | 55.8% |
| 273 | Melissa Sommer | melissa.sommer@cutover.com | 30.7% |
| 67 | Marcus | marcus@cutover.com | 0.0% |
| 38 | Mark Brewer | mark.brewer@cutover.com | 0.0% |
| 169 | Saif Azmi | saif.azmi@cutover.com | 0.0% |

---

## 6. Task Data Extraction

### Get All Tasks for a Runbook

```python
def get_runbook_tasks(runbook_id):
    """Get all tasks in a runbook with pagination"""
    all_tasks = []
    page = 1
    
    while True:
        params = {
            'page[number]': page,
            'page[size]': 100
        }
        
        resp = requests.get(
            f'{API_BASE}/core/runbooks/{runbook_id}/tasks',
            params=params,
            headers=headers,
            verify=False
        )
        
        if resp.status_code != 200:
            break
        
        data = resp.json()
        tasks = data.get('data', [])
        
        if not tasks:
            break
        
        all_tasks.extend(tasks)
        
        if not data.get('links', {}).get('next'):
            break
        
        page += 1
        time.sleep(0.3)
    
    return all_tasks
```

### Task Attributes

Key attributes to extract:

```python
task_attrs = task_data['attributes']

{
    'name': task_attrs.get('name'),               # Task name
    'start_actual': task_attrs.get('start_actual'), # ISO timestamp
    'end_actual': task_attrs.get('end_actual'),     # ISO timestamp
    'start_ready': task_attrs.get('start_ready'),   # Planned start
    'end_ready': task_attrs.get('end_ready'),       # Planned end
    'stage': task_attrs.get('stage'),              # started, complete, etc.
    'task_type': task_attrs.get('task_type')       # Type of task
}
```

### Filter Executed Tasks

```python
def filter_executed_tasks(tasks):
    """Only include tasks that were actually executed"""
    executed = []
    
    for task in tasks:
        attrs = task['attributes']
        if (attrs.get('start_actual') is not None and
            attrs.get('end_actual') is not None):
            executed.append(task)
    
    return executed
```

---

## 7. Time Calculations & Metrics

### Execution Time (Per Task)

```python
from datetime import datetime

def calculate_execution_time(start_actual, end_actual):
    """
    Calculate task execution time in seconds
    
    Args:
        start_actual: ISO timestamp string (e.g., "2025-11-13T19:13:00Z")
        end_actual: ISO timestamp string
    
    Returns:
        float: Seconds between start and end
    """
    start = datetime.fromisoformat(start_actual.replace('Z', '+00:00'))
    end = datetime.fromisoformat(end_actual.replace('Z', '+00:00'))
    
    duration = (end - start).total_seconds()
    return duration

# Example
duration = calculate_execution_time(
    "2025-11-13T19:13:00Z",
    "2025-11-13T19:13:05Z"
)
# Returns: 5.0 seconds
```

### Inter-Task Time (Gaps Between Tasks)

```python
def calculate_inter_task_time(user_tasks):
    """
    Calculate time gaps between consecutive tasks for a user
    
    Args:
        user_tasks: List of task dicts sorted by start_time
    
    Returns:
        float: Total inter-task time in seconds
    """
    inter_task_seconds = 0
    
    for i in range(len(user_tasks) - 1):
        current_end = user_tasks[i]['end_time']
        next_start = user_tasks[i + 1]['start_time']
        
        gap = (next_start - current_end).total_seconds()
        if gap > 0:
            inter_task_seconds += gap
    
    return inter_task_seconds

# Sort tasks by start time first!
user_tasks.sort(key=lambda x: x['start_time'])
gaps = calculate_inter_task_time(user_tasks)
```

### Efficiency Percentage

```python
def calculate_efficiency(execution_seconds, total_effort_seconds):
    """
    Efficiency = (Execution Time / Total Effort) × 100
    
    Total Effort = Execution Time + Inter-Task Time
    
    High efficiency (≥70%): Focused, continuous execution
    Medium efficiency (30-70%): Some gaps between tasks
    Low efficiency (<30%): Multi-day execution patterns
    """
    if total_effort_seconds == 0:
        return 0.0
    
    efficiency = (execution_seconds / total_effort_seconds) * 100
    return round(efficiency, 1)

# Example: User with 118 minutes execution, 2 minutes gap
efficiency = calculate_efficiency(
    execution_seconds=118 * 60,
    total_effort_seconds=(118 + 2) * 60
)
# Returns: 98.3% (highly efficient)
```

### Task Velocity

```python
def calculate_velocity(task_count, execution_hours):
    """
    Velocity = Tasks per Hour
    
    Measures how quickly a user completes tasks
    """
    if execution_hours == 0:
        return 0.0
    
    velocity = task_count / execution_hours
    return round(velocity, 1)

# Example: 23 tasks in 2 hours
velocity = calculate_velocity(23, 2.0)
# Returns: 11.5 tasks/hour
```

### Metric Summary Template

```python
def calculate_user_metrics(user_tasks):
    """Complete metric calculation for a user"""
    # Sort by time
    user_tasks.sort(key=lambda x: x['start_time'])
    
    # Execution time
    exec_seconds = sum(t['duration'] for t in user_tasks)
    exec_minutes = exec_seconds / 60
    exec_hours = exec_minutes / 60
    
    # Inter-task time
    inter_seconds = calculate_inter_task_time(user_tasks)
    inter_minutes = inter_seconds / 60
    inter_hours = inter_minutes / 60
    
    # Total effort
    total_seconds = exec_seconds + inter_seconds
    total_minutes = total_seconds / 60
    total_hours = total_minutes / 60
    
    # Efficiency
    efficiency = calculate_efficiency(exec_seconds, total_seconds)
    
    # Velocity
    velocity = calculate_velocity(len(user_tasks), exec_hours)
    
    return {
        'tasks': len(user_tasks),
        'execution_seconds': exec_seconds,
        'execution_minutes': exec_minutes,
        'execution_hours': exec_hours,
        'inter_task_seconds': inter_seconds,
        'inter_task_minutes': inter_minutes,
        'inter_task_hours': inter_hours,
        'total_effort_seconds': total_seconds,
        'total_effort_minutes': total_minutes,
        'total_effort_hours': total_hours,
        'efficiency_percent': efficiency,
        'velocity_tasks_per_hour': velocity
    }
```

---

## 8. Rate Limiting & Pagination

### Rate Limiting Strategy

```python
import time

# Recommended delays between API calls
DELAYS = {
    'workspace': 0.5,      # List workspaces
    'runbook': 0.5,        # List runbooks
    'task': 1.5,           # Get individual task (most expensive)
    'user': 0.5,           # Get user details
    'batch': 2.0           # Between batches of operations
}

# Simple delay
time.sleep(1.5)

# Rate-limited session wrapper
class RateLimitedSession:
    def __init__(self, delay=1.0):
        self.session = requests.Session()
        self.delay = delay
        self.last_request_time = 0
    
    def _enforce_delay(self):
        elapsed = time.time() - self.last_request_time
        if elapsed < self.delay:
            time.sleep(self.delay - elapsed)
        self.last_request_time = time.time()
    
    def get(self, url, **kwargs):
        self._enforce_delay()
        kwargs['verify'] = False
        return self.session.get(url, **kwargs)

# Usage
session = RateLimitedSession(delay=1.5)
resp = session.get(f'{API_BASE}/core/runbooks/{rb_id}/tasks/{task_id}')
```

### Handling 429 Errors

```python
def get_with_retry(url, max_retries=3):
    """GET with exponential backoff on 429"""
    for attempt in range(max_retries):
        resp = requests.get(url, headers=headers, verify=False)
        
        if resp.status_code == 200:
            return resp
        
        if resp.status_code == 429:
            wait_time = (2 ** attempt) * 2  # 2s, 4s, 8s
            print(f"Rate limited, waiting {wait_time}s...")
            time.sleep(wait_time)
            continue
        
        # Other error
        return resp
    
    return None
```

### Pagination Patterns

```python
# Pattern 1: page[number] and page[size]
params = {
    'page[number]': 1,
    'page[size]': 100
}

# Pattern 2: page[offset] and page[limit]
params = {
    'page[offset]': 0,
    'page[limit]': 100
}

# Check for next page
data = resp.json()
has_next = bool(data.get('links', {}).get('next'))

# Full pagination loop
def paginate_all(base_url, params=None):
    """Generic pagination handler"""
    all_items = []
    page = 1
    
    while True:
        page_params = params.copy() if params else {}
        page_params['page[number]'] = page
        page_params['page[size]'] = 100
        
        resp = requests.get(base_url, params=page_params, headers=headers, verify=False)
        
        if resp.status_code != 200:
            break
        
        data = resp.json()
        items = data.get('data', [])
        
        if not items:
            break
        
        all_items.extend(items)
        
        if not data.get('links', {}).get('next'):
            break
        
        page += 1
        time.sleep(0.5)
    
    return all_items
```

### ⚡ API Filtering for Efficiency

**CRITICAL:** Always filter data at the API level using query parameters instead of fetching all data and filtering in Python.

#### Query Parameters Reference (Cutover Developer Portal)

Based on [Cutover API Documentation](https://developer.cutover.com/endpoints):

```python
# ❌ INEFFICIENT: Fetch all 2000+ runbooks, then filter in Python
all_runbooks = []
for page in range(1, 100):
    url = f"{API}/core/runbooks?workspace_id=233&page[number]={page}"
    # ... fetch all pages ...
completed = [rb for rb in all_runbooks if rb['attributes']['stage'] == 'complete']

# ✅ EFFICIENT: Filter at API level - reduces 100+ pages to 1-2 pages
url = f"{API}/core/runbooks?workspace_id=233&stage=complete&archive=false"
# Only fetches completed, non-archived runbooks
```

#### Available Query Parameters for GET /core/runbooks

| Parameter | Values | Example | Notes |
|-----------|--------|---------|-------|
| `workspace_id` | Workspace ID | `233` | Filter by workspace |
| `stage` | `draft`, `ready`, `rehearsal`, `live`, `complete`, `paused`, `cancelled` | `complete` | Runbook lifecycle stage |
| `archive` | `true`, `false` | `false` | Exclude archived runbooks |
| `template_type` | `off`, `default`, `snippet` | `off` | Filter by template type |
| `is_template` | `true`, `false` | `false` | Templates vs live runbooks |
| `sort` | `touched_at`, `created_at`, `name` | `touched_at` | Sort order (requires `core_version >= 3.83.0`) |
| `source_runbook_id` | Runbook ID | `8264` | Filter by source template (requires `core_version >= 2025.22.0`) |
| `page[number]` | Integer | `1` | Page number for pagination |
| `page[size]` | Integer (max 100) | `100` | Items per page |

#### Efficiency Examples

```python
# Example 1: Get only completed runbooks in workspace
url = f"{API}/core/runbooks?workspace_id=233&stage=complete&archive=false"
# Reduces API calls from ~100 pages to 1-2 pages

# Example 2: Get only live runbooks created from a specific template
url = f"{API}/core/runbooks?source_runbook_id=8264&stage=live"

# Example 3: Get rehearsal runbooks, sorted by most recently touched
url = f"{API}/core/runbooks?workspace_id=233&stage=rehearsal&sort=touched_at"

# Example 4: Get non-template runbooks only
url = f"{API}/core/runbooks?workspace_id=233&is_template=false&archive=false"
```

#### Performance Impact

| Approach | API Calls | Data Transferred | Time |
|----------|-----------|------------------|------|
| ❌ Fetch all, filter in Python | 100+ requests | 2000+ runbooks | ~2-3 minutes |
| ✅ Filter at API level | 1-2 requests | 10-20 runbooks | ~2-5 seconds |

**Best Practice:** Always use the most specific query parameters available to minimize data transfer and API calls.

#### Additional GET /core/runbooks Filters

```python
# Filter by custom field values (requires proper encoding)
url = f"{API}/core/runbooks?custom_field_values=Environment:Production"

# Combine multiple filters
params = {
    'workspace_id': '233',
    'stage': 'complete',
    'archive': 'false',
    'is_template': 'false',
    'sort': 'touched_at',
    'page[size]': '100'
}
resp = session.get(f"{API}/core/runbooks", params=params)
```

#### Other Endpoints with Filtering

```python
# GET /core/tasks - Filter by runbook_team_id
url = f"{API}/core/runbooks/{runbook_id}/tasks?runbook_team_id={team_id}"

# GET /core/action_logs - Filter by event type and date range
url = f"{API}/core/action_logs?event=task_start&created_after=2026-01-01&created_before=2026-02-01"

# GET /core/users - Sort by email
url = f"{API}/core/users?sort=core_users.email"
```

**Reference:** For complete API schema and all available filters, see:  
📖 [Cutover Developer Portal - API Endpoints](https://developer.cutover.com/endpoints)

---

## 9. Data Processing Patterns

### Grouping Tasks by User

```python
from collections import defaultdict

def group_tasks_by_user(all_task_data):
    """Group executed tasks by user ID"""
    user_tasks = defaultdict(list)
    
    for task in all_task_data:
        if task['user_id']:
            user_tasks[task['user_id']].append(task)
    
    return user_tasks
```

### Aggregating Runbook Metrics

```python
def aggregate_runbook_metrics(runbook_tasks):
    """Calculate summary metrics for a runbook"""
    executed = [t for t in runbook_tasks if t['start_actual'] and t['end_actual']]
    
    total_duration = 0
    user_ids = set()
    
    for task in executed:
        duration = calculate_execution_time(
            task['start_actual'],
            task['end_actual']
        )
        total_duration += duration
        
        if task.get('user_id'):
            user_ids.add(task['user_id'])
    
    return {
        'total_tasks': len(executed),
        'total_seconds': total_duration,
        'total_minutes': total_duration / 60,
        'total_hours': total_duration / 3600,
        'unique_users': len(user_ids)
    }
```

### Filtering by Date Range

```python
from datetime import datetime, timedelta

def filter_by_date_range(tasks, days_ago=90):
    """Filter tasks executed in last N days"""
    cutoff = datetime.now() - timedelta(days=days_ago)
    recent_tasks = []
    
    for task in tasks:
        if task['start_actual']:
            start = datetime.fromisoformat(task['start_actual'].replace('Z', '+00:00'))
            if start > cutoff:
                recent_tasks.append(task)
    
    return recent_tasks
```

---

## 10. Output Formats

### 🎯 Dashboard Design Principles (CRITICAL)

**Dashboards MUST be designed for human consumption, not data dumps.**

**🚨 MANDATORY: All dashboards MUST be high-level with graphs and charts as the primary method of communication.**

#### Rule 1: Visualizations First (HIGH-LEVEL CHARTS REQUIRED)

✅ **REQUIRED: Always include interactive charts - DASHBOARDS ARE VISUAL**
- **HIGH-LEVEL PRINCIPLE**: Tell the story with visuals, support with details
- Minimum 2-4 Chart.js visualizations per dashboard
- Charts provide immediate insights without reading tables
- Users should understand key insights in 5 seconds from charts alone
- Types to use:
  - **Pie/Doughnut**: For proportions and breakdowns
  - **Bar (horizontal)**: For rankings and top items
  - **Line**: For trends over time
  - **Stacked Bar**: For multi-category comparisons

```html
<!-- MANDATORY: Include Chart.js -->
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<!-- MANDATORY: Include html2pdf.js for PDF export -->
<script src="https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.10.1/html2pdf.bundle.min.js"></script>
```

#### Rule 2: Names Over IDs - Human Readability First

✅ **MANDATORY: Always display names, not IDs**
- **Items requiring names**: Runbooks, tasks, users, teams, task types, streams, phases, workspaces
- **Fetch name mappings FIRST**: Get task types, user details, team info before generating dashboard
- **IDs are supplementary**: Show IDs only in tooltips, secondary columns, or technical details

```python
# REQUIRED: Fetch name mappings before analysis
def fetch_task_types():
    """Get task type ID to name mapping"""
    response = requests.get(
        f'{BASE_URL}/task_types',
        headers=headers
    )
    task_types = {}
    for tt in response.json()['data']:
        task_types[tt['id']] = tt['attributes']['name']
    return task_types

# Use names in display
task_type_name = task_types.get(task_type_id, f'Task Type {task_type_id}')
```

❌ **NEVER display**: "Task Type 463", "Runbook 8890", "User 273"  
✅ **ALWAYS display**: "Validation Task", "DR Cutover Runbook", "john.smith@example.com"

**Why**: Users think in names, not numbers. "Milestone" is instantly meaningful; "39" requires a lookup table.

#### Rule 3: Progressive Disclosure

✅ **DO**: Show top 10-15 items by default with "Show More" button
❌ **DON'T**: Show 1,767 templates on initial page load

```javascript
// Show/Hide pattern
function toggleRows(className) {
    const rows = document.querySelectorAll('.' + className);
    const isCollapsed = rows[0].classList.contains('collapsed');
    
    rows.forEach(row => {
        row.classList.toggle('collapsed');
    });
    
    event.target.textContent = isCollapsed ? 'Show Less' : 'Show All';
}
```

#### Rule 4: Tables Over Cards for Large Datasets

✅ **USE TABLES when**: Showing 20+ items
❌ **USE CARDS when**: Showing 1-10 featured items

**Why**: Tables are 5x more scannable than card layouts for large lists

```html
<!-- Good: Compact table format -->
<table class="summary-table">
  <thead>
    <tr>
      <th>#</th>
      <th>Name</th>
      <th>Count</th>
      <th>Status</th>
    </tr>
  </thead>
  <tbody>
    <tr><td>1</td><td>Template Name</td><td>42</td><td>Active</td></tr>
  </tbody>
</table>
```

#### Rule 5: Quick Stats Summaries

✅ **ALWAYS** include summary stat boxes at top of each section

```html
<div class="quick-stats">
    <div class="quick-stat">
        <span>Total Templates:</span>
        <span class="quick-stat-value">1767</span>
    </div>
    <div class="quick-stat">
        <span>Used in Live Runs:</span>
        <span class="quick-stat-value">30 (1.7%)</span>
    </div>
</div>
```

#### Rule 6: Truncate Long Text

```css
.template-name-compact {
    max-width: 400px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}
```

```html
<div class="template-name-compact" title="Full Template Name Here">
    Long Template Name That Gets...
</div>
```

#### Checklist: Human-Readable Dashboard

- [ ] ✅ **HIGH-LEVEL**: Dashboard tells story with graphs/charts first, details second
- [ ] ✅ 2-4 Chart.js visualizations included (pie, bar, line charts)
- [ ] ✅ **PDF Export button** included with html2pdf.js functionality
- [ ] ✅ **NAMES NOT IDs**: All runbooks, tasks, users, teams show actual names (not numeric IDs)
- [ ] ✅ Quick summary stats at top of each section
- [ ] ✅ Default view shows max 10-15 items
- [ ] ✅ "Show More" buttons for full lists
- [ ] ✅ Tables used for 20+ items (not cards)
- [ ] ✅ Long text truncated with ellipsis and tooltips
- [ ] ✅ Color-coded badges for status/metrics
- [ ] ✅ Total counts visible in section headers
- [ ] ✅ No horizontal scrolling required
- [ ] ✅ Page loads in under 2 seconds
- [ ] ✅ Cutover branding (logo, colors, fonts) applied throughout

**Reference Implementation**: `create_cutover_recover_live_runs_dashboard.py` and `create_unassigned_tasks_dashboard.py`

---

### CSV Export

```python
import csv

def export_user_summary_csv(user_metrics, filename='user_summary.csv'):
    """Export user metrics to CSV"""
    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)
        
        # Header
        writer.writerow([
            'User_ID', 'Email', 'Tasks',
            'Execution_Minutes', 'InterTask_Minutes',
            'TotalEffort_Hours', 'Efficiency_Percent'
        ])
        
        # Data rows
        for user_id, metrics in user_metrics.items():
            writer.writerow([
                user_id,
                metrics['email'],
                metrics['tasks'],
                f"{metrics['execution_minutes']:.2f}",
                f"{metrics['inter_task_minutes']:.2f}",
                f"{metrics['total_effort_hours']:.2f}",
                f"{metrics['efficiency_percent']:.1f}"
            ])

def export_task_detail_csv(all_tasks, filename='task_detail.csv'):
    """Export task-level details to CSV"""
    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)
        
        writer.writerow([
            'User_ID', 'Email', 'Runbook_ID', 'Runbook_Name',
            'Task_ID', 'Task_Name', 'Duration_Seconds',
            'Start_Time', 'End_Time'
        ])
        
        for task in all_tasks:
            writer.writerow([
                task['user_id'],
                task['user_email'],
                task['runbook_id'],
                task['runbook_name'],
                task['task_id'],
                task['task_name'],
                task['duration'],
                task['start_actual'],
                task['end_actual']
            ])
```

### HTML Dashboard (Chart.js)

```html
<!DOCTYPE html>
<html>
<head>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
</head>
<body>
    <canvas id="efficiencyChart"></canvas>
    
    <script>
        // Efficiency bar chart
        new Chart(document.getElementById('efficiencyChart'), {
            type: 'bar',
            data: {
                labels: ['Dhiren', 'Arty', 'Max', 'Melissa'],
                datasets: [{
                    label: 'Efficiency %',
                    data: [98.2, 82.4, 55.8, 30.7],
                    backgroundColor: function(context) {
                        const value = context.parsed.y;
                        if (value >= 70) return '#27ae60';  // Green
                        if (value >= 30) return '#f39c12';  // Orange
                        return '#e74c3c';  // Red
                    }
                }]
            },
            options: {
                scales: {
                    y: { beginAtZero: true, max: 100 }
                }
            }
        });
    </script>
</body>
</html>
```

### PDF Export (html2pdf.js) - MANDATORY FOR ALL DASHBOARDS

**🚨 REQUIREMENT**: Every HTML dashboard MUST include PDF export functionality.

#### Implementation Pattern

```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard Name</title>
    
    <!-- MANDATORY: Chart.js for visualizations -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    
    <!-- MANDATORY: html2pdf.js for PDF export -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.10.1/html2pdf.bundle.min.js"></script>
    
    <style>
        /* Your dashboard styles */
    </style>
</head>
<body>
    <div class="header">
        <div class="header-content">
            <img src="https://cdn.prod.website-files.com/628d04e7099dc5d9a4d46fa9/628e088a063b140502a7f239_Cutover_Logo%20Full%20Color%202.svg" 
                 alt="Cutover Logo" class="logo">
            <div class="header-title">
                <h1>Dashboard Title</h1>
                <p>Subtitle or Workspace Name</p>
            </div>
            <div class="header-actions">
                <!-- MANDATORY: Export PDF button -->
                <button class="btn btn-secondary" onclick="exportToPDF()">📄 Export PDF</button>
            </div>
        </div>
    </div>
    
    <!-- Wrap dashboard content in a container with id for PDF export -->
    <div class="container" id="dashboard-content">
        <!-- Your dashboard content here -->
        <div class="metadata">
            <div class="metadata-item">
                <strong>Generated:</strong> 2026-02-26 10:24:47
            </div>
        </div>
        
        <!-- Charts and tables -->
    </div>
    
    <script>
        // Export to PDF function - MANDATORY
        function exportToPDF() {
            const element = document.getElementById('dashboard-content');
            const timestamp = new Date().toISOString().slice(0, 19).replace(/[-:]/g, '').replace('T', '_');
            
            const opt = {
                margin: 10,
                filename: `dashboard_${timestamp}.pdf`,
                image: { type: 'jpeg', quality: 0.98 },
                html2canvas: { scale: 2 },
                jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' }
            };
            
            html2pdf().set(opt).from(element).save();
        }
        
        // Your chart initialization code
    </script>
</body>
</html>
```

#### Key Requirements for PDF Export

✅ **MUST HAVE:**
- html2pdf.js library loaded from CDN
- Export button in header with "📄 Export PDF" label and onclick handler
- Dashboard content wrapped in container with unique id (e.g., `dashboard-content`)
- Dynamic filename with timestamp
- High-quality settings (quality: 0.98, scale: 2)

✅ **BEST PRACTICES:**
- Exclude navigation elements from PDF (keep them outside `dashboard-content`)
- Use A4 portrait format for most dashboards
- Test that charts render correctly in PDF
- Ensure Cutover branding (logo, colors) preserved in export
- Include generation timestamp in PDF

❌ **AVOID:**
- Low quality settings (quality < 0.9)
- Including interactive buttons in PDF content
- Very wide tables that don't fit A4 width
- Missing filename timestamp (prevents overwrites)

#### Example Export Button Styles

```css
.btn-secondary {
    background: rgba(255, 255, 255, 0.2);
    color: white;
    border: 1px solid white;
    padding: 8px 16px;
    border-radius: 8px;
    font-size: 14px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s;
}

.btn-secondary:hover {
    background: rgba(255, 255, 255, 0.3);
}
```

**Reference Implementation**: See `create_unassigned_tasks_dashboard.py` for complete working example.

### PowerPoint Generation (python-pptx)

```python
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE

def create_powerpoint_dashboard(user_metrics, output_file='dashboard.pptx'):
    """Generate PowerPoint with Cutover template"""
    
    # Load Cutover template
    prs = Presentation('Cutover Master Slide Deck - TEMPLATE.pptx')
    
    # Add title slide
    slide = prs.slides.add_slide(prs.slide_layouts[0])
    title = slide.shapes.title
    title.text = "User Activity & Efficiency Analysis"
    
    # Add chart slide
    slide = prs.slides.add_slide(prs.slide_layouts[5])
    title = slide.shapes.title
    title.text = "Efficiency Distribution"
    
    # Create chart data
    chart_data = CategoryChartData()
    chart_data.categories = [m['name'] for m in user_metrics]
    chart_data.add_series('Efficiency %', [m['efficiency'] for m in user_metrics])
    
    # Add chart
    x, y, cx, cy = Inches(1.5), Inches(2), Inches(7), Inches(4.5)
    chart = slide.shapes.add_chart(
        XL_CHART_TYPE.BAR_CLUSTERED, x, y, cx, cy, chart_data
    ).chart
    
    prs.save(output_file)
```

### Color Schemes

```python
# Efficiency color coding
def get_efficiency_color(efficiency_percent):
    """Return color based on efficiency"""
    if efficiency_percent >= 70:
        return '#27ae60'  # Green - High efficiency
    elif efficiency_percent >= 30:
        return '#f39c12'  # Orange - Medium efficiency
    else:
        return '#e74c3c'  # Red - Low efficiency

# Cutover brand colors
CUTOVER_COLORS = {
    'primary': '#667eea',     # Purple
    'secondary': '#764ba2',   # Dark purple
    'success': '#27ae60',     # Green
    'warning': '#f39c12',     # Orange
    'danger': '#e74c3c',      # Red
    'info': '#3498db',        # Blue
}
```

---

## 12. Cutover Design System & Branding

**CRITICAL:** All dashboards, reports, and visualizations MUST use authentic Cutover branding. This ensures consistency across all reports and maintains professional brand standards.

### Official Brand Assets

#### Cutover Logo - STRICT REQUIREMENTS

**⚠️ MANDATORY: Use ONLY Official Cutover Logo Assets**

**DO NOT:**
- ❌ Create custom SVG logos with hand-drawn paths
- ❌ Generate logo approximations or recreations
- ❌ Use text-based logo substitutes
- ❌ Modify, alter, or redesign the official logo in any way

**DO:**
- ✅ Use the official Cutover logo from the CDN
- ✅ Reference the logo via URL or local file
- ✅ Maintain original aspect ratio and proportions
- ✅ Use approved background colors only

**Official Logo Source (REQUIRED):**

```html
<!-- REQUIRED: Official Cutover Logo from CDN -->
<img src="https://cdn.prod.website-files.com/628d04e7099dc5d9a4d46fa9/628e088a063b140502a7f239_Cutover_Logo%20Full%20Color%202.svg" 
     alt="Cutover" 
     style="height: 32px;" />
```

**Alternative Official Sources:**
- Production Logo SVG: `https://cdn.prod.website-files.com/628d04e7099dc5d9a4d46fa9/628e088a063b140502a7f239_Cutover_Logo%20Full%20Color%202.svg`
- Square Logo (PNG): `https://media.glassdoor.com/sqll/3248213/cutover-squareLogo-1627925548047.png`

**Local File Usage (if CDN unavailable):**

```html
<!-- Use official logo file from workspace -->
<img src="cutover_logo.svg" alt="Cutover" class="logo" />
```

**Logo Sizing:**
- Header: 32-40px height
- Footer: 24-32px height  
- Small inline: 16-20px height
- Maintain original aspect ratio (do not distort)

**Acceptable Backgrounds:**
- White (#ffffff)
- Light grey (#f0f0f0, #f5f5f5)
- Cutover dark (#16161d) - if using inverse/white logo variant

**NEVER:**
- Use bright colors, gradients, or patterns as logo background
- Place logo on low-contrast backgrounds
- Overlay logo on busy images or textures
- Resize logo smaller than 16px height (legibility minimum)

---

### Color Palette

All colors extracted from authentic Cutover RevMax dashboard. Use these exact hex values:

#### Primary Colors
```css
--cutover-primary: #2A55C3;        /* Primary Blue - buttons, headers, links, logo */
--cutover-dark: #16161d;           /* Dark Text - headings, body copy, footer */
--cutover-background: #f0f0f0;     /* Page Background - main container */
```

#### Surface Colors
```css
--cutover-skeleton-1: #ebebeb;     /* Panels, cards base */
--cutover-skeleton-2: #f5f5f5;     /* Alternate panels, hover states */
--cutover-card-bg: #ffffff;        /* Card backgrounds */
--cutover-border: #e9ecef;         /* Subtle borders */
```

#### Status Colors
```css
--cutover-success: #27ae60;        /* Green - positive states, high metrics */
--cutover-warning: #f39c12;        /* Orange - caution, medium metrics */
--cutover-danger: #e74c3c;         /* Red - errors, critical states */
--cutover-neutral: #95a5a6;        /* Grey - informational */
```

#### Text Colors
```css
--cutover-text-primary: #16161d;   /* Primary text */
--cutover-text-secondary: #666;    /* Secondary text, labels */
--cutover-text-muted: #999;        /* Disabled, de-emphasized */
--cutover-text-inverse: #ffffff;   /* Text on dark backgrounds */
```

#### Color Usage Examples
```python
def get_efficiency_color(efficiency_percent):
    """Return Cutover-branded color based on efficiency"""
    if efficiency_percent >= 70:
        return '#27ae60'  # Success green
    elif efficiency_percent >= 30:
        return '#f39c12'  # Warning orange
    else:
        return '#e74c3c'  # Danger red

def get_status_badge_color(status):
    """Status badge colors"""
    colors = {
        'complete': '#27ae60',
        'in_progress': '#2A55C3',
        'pending': '#f39c12',
        'skipped': '#e74c3c',
        'blocked': '#95a5a6'
    }
    return colors.get(status, '#95a5a6')
```

---

### Typography

#### Font Stack
```css
font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, 
             Oxygen-Sans, Ubuntu, Cantarell, sans-serif;
```

**CRITICAL:** Use system font stack (NO custom web fonts). This provides:
- Native OS appearance
- Fast loading (no font downloads)
- Excellent readability
- Cross-platform consistency

#### Font Weights & Sizes
```css
/* Headings */
h1, h2, h3 {
    font-weight: 600;  /* NOT 700 - subtle but important */
    color: #16161d;
}

h1 { font-size: 32px; margin: 0 0 24px 0; }
h2 { font-size: 24px; margin: 32px 0 16px 0; }
h3 { font-size: 18px; margin: 24px 0 12px 0; }

/* Body Text */
body {
    font-size: 14px;
    font-weight: 400;
    color: #333;
    line-height: 1.6;
}

/* Labels (uppercase with spacing) */
.label {
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;  /* Critical for uppercase readability */
    color: #666;
}

/* Metric Values */
.metric-value {
    font-size: 36px;
    font-weight: 600;
    color: #16161d;
}
```

---

### Spacing System

Cutover uses a **4px base unit** spacing system. All margins, padding, and gaps MUST be multiples of 4px:

```css
:root {
    --space-1: 4px;
    --space-2: 8px;
    --space-3: 12px;
    --space-4: 16px;
    --space-5: 20px;
    --space-6: 24px;
    --space-8: 32px;
    --space-10: 40px;
    --space-12: 48px;
}

/* Common Usage */
.container { padding: var(--space-6); }           /* 24px */
.section { margin-bottom: var(--space-8); }        /* 32px */
.card { padding: var(--space-4); }                 /* 16px */
.button { padding: var(--space-2) var(--space-4); } /* 8px 16px */
```

**Python Helper:**
```python
def spacing(units):
    """Convert spacing units to pixels"""
    return f"{units * 4}px"

# Usage
container_padding = spacing(6)  # "24px"
section_margin = spacing(8)     # "32px"
```

---

### Border Radius

```css
:root {
    --radius-sm: 4px;    /* Small elements, badges */
    --radius-md: 6px;    /* Buttons, inputs */
    --radius-lg: 8px;    /* Cards, panels */
    --radius-xl: 12px;   /* Pills, status badges */
}

/* Usage */
.card { border-radius: var(--radius-lg); }         /* 8px */
.button { border-radius: var(--radius-md); }       /* 6px */
.badge { border-radius: var(--radius-xl); }        /* 12px */
```

---

### Shadows (Elevation)

```css
:root {
    --shadow-subtle: 0 1px 3px rgba(0, 0, 0, 0.08);
    --shadow-medium: 0 2px 8px rgba(0, 0, 0, 0.1);
    --shadow-hover: 0 4px 12px rgba(0, 0, 0, 0.15);
    --shadow-focus: 0 0 0 3px rgba(42, 85, 195, 0.2);
}

/* Usage */
.card {
    box-shadow: var(--shadow-subtle);
    transition: all 200ms ease;
}

.card:hover {
    box-shadow: var(--shadow-hover);
    transform: translateY(-4px);  /* Subtle lift */
}
```

---

### Component Patterns

#### Metric Cards
```html
<div class="metric-card">
    <div class="metric-label">TOTAL RUNBOOKS</div>
    <div class="metric-value">51</div>
    <div class="metric-subtitle">In workspace</div>
</div>

<style>
.metric-card {
    background: #ffffff;
    border: 1px solid #e9ecef;
    border-radius: 8px;
    padding: 24px;
    text-align: center;
    transition: all 200ms ease;
}

.metric-card:hover {
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    transform: translateY(-4px);
}

.metric-label {
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #666;
    margin-bottom: 12px;
}

.metric-value {
    font-size: 36px;
    font-weight: 600;
    color: #16161d;
    margin-bottom: 8px;
}

.metric-subtitle {
    font-size: 13px;
    color: #999;
}
</style>
```

#### Status Badges
```html
<span class="badge badge-success">Complete</span>
<span class="badge badge-warning">In Progress</span>
<span class="badge badge-danger">Skipped</span>

<style>
.badge {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 12px;
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

.badge-success {
    background: #27ae60;
    color: white;
}

.badge-warning {
    background: #f39c12;
    color: white;
}

.badge-danger {
    background: #e74c3c;
    color: white;
}

.badge-neutral {
    background: #95a5a6;
    color: white;
}
</style>
```

#### Cutover Tables
```html
<table class="cutover-table">
    <thead>
        <tr>
            <th>Runbook Name</th>
            <th>Skipped Tasks</th>
            <th>Status</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td>Migration Runbook</td>
            <td>5</td>
            <td><span class="badge badge-warning">Attention</span></td>
        </tr>
    </tbody>
</table>

<style>
.cutover-table {
    width: 100%;
    border-collapse: collapse;
    background: white;
    border-radius: 8px;
    overflow: hidden;
}

.cutover-table thead th {
    background: #2A55C3;
    color: white;
    padding: 16px;
    text-align: left;
    font-size: 12px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

.cutover-table tbody td {
    padding: 16px;
    border-bottom: 1px solid #e9ecef;
    color: #333;
}

.cutover-table tbody tr:hover {
    background: #f5f5f5;
}

.cutover-table tbody tr:last-child td {
    border-bottom: none;
}
</style>
```

#### Panels/Containers
```html
<div class="panel">
    <h2>Distribution Analysis</h2>
    <div class="panel-content">
        <!-- Content here -->
    </div>
</div>

<style>
.panel {
    background: white;
    border: 1px solid #e9ecef;
    border-radius: 8px;
    padding: 24px;
    margin-bottom: 32px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
}

.panel h2 {
    font-size: 20px;
    font-weight: 600;
    color: #16161d;
    margin: 0 0 16px 0;
}

.panel-content {
    padding: 0;
}
</style>
```

---

### Interactive States

```css
/* Hover States */
.interactive:hover {
    transform: translateY(-4px);  /* Subtle lift, NOT -2px */
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    transition: all 200ms ease;   /* Smooth but quick, NOT 300ms */
}

/* Focus States */
.interactive:focus {
    outline: none;
    box-shadow: 0 0 0 3px rgba(42, 85, 195, 0.2);  /* Primary blue glow */
}

/* Active/Pressed States */
.interactive:active {
    transform: translateY(0);
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
}

/* Disabled States */
.interactive:disabled {
    opacity: 0.5;
    cursor: not-allowed;
    pointer-events: none;
}
```

---

### Complete Dashboard Template

```python
#!/usr/bin/env python3
"""
Generate Cutover-branded HTML dashboard
Uses authentic Cutover design system
"""

def generate_cutover_dashboard(data, title, output_file='dashboard.html'):
    """
    Generate HTML dashboard with complete Cutover branding
    
    Args:
        data: Dict with dashboard data
        title: Dashboard title
        output_file: Output filename
    """
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        /*
        ═══════════════════════════════════════════════════════════════════
        CUTOVER DESIGN SYSTEM
        ═══════════════════════════════════════════════════════════════════
        
        This dashboard uses the authentic Cutover design system extracted
        from the RevMax HTML production dashboard. All colors, typography,
        spacing, and component patterns match Cutover's brand standards.
        
        KEY PRINCIPLES:
        - Use system fonts (no custom font loading)
        - 4px base spacing unit (all spacing is multiples of 4)
        - Primary blue (#2A55C3) for brand elements
        - 600 weight headings (NOT 700)
        - Subtle shadows and interactions (200ms transitions)
        - Border radius: 8px cards, 6px buttons, 12px badges
        
        NEVER modify colors or create custom logos. Cutover branding is
        critically important and must remain consistent across all reports.
        */
        
        :root {{
            /* Colors */
            --cutover-primary: #2A55C3;
            --cutover-dark: #16161d;
            --cutover-background: #f0f0f0;
            --cutover-skeleton-1: #ebebeb;
            --cutover-skeleton-2: #f5f5f5;
            --cutover-card-bg: #ffffff;
            --cutover-border: #e9ecef;
            --cutover-success: #27ae60;
            --cutover-warning: #f39c12;
            --cutover-danger: #e74c3c;
            --cutover-neutral: #95a5a6;
            
            /* Spacing (4px base unit) */
            --space-1: 4px;
            --space-2: 8px;
            --space-4: 16px;
            --space-6: 24px;
            --space-8: 32px;
            --space-10: 40px;
            
            /* Border Radius */
            --radius-sm: 4px;
            --radius-md: 6px;
            --radius-lg: 8px;
            --radius-xl: 12px;
            
            /* Shadows */
            --shadow-subtle: 0 1px 3px rgba(0, 0, 0, 0.08);
            --shadow-medium: 0 2px 8px rgba(0, 0, 0, 0.1);
            --shadow-hover: 0 4px 12px rgba(0, 0, 0, 0.15);
        }}
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, 
                         Oxygen-Sans, Ubuntu, Cantarell, sans-serif;
            background: var(--cutover-background);
            color: #333;
            font-size: 14px;
            line-height: 1.6;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: var(--space-6);
        }}
        
        /* Header */
        .header {{
            background: white;
            padding: var(--space-6);
            border-radius: var(--radius-lg);
            box-shadow: var(--shadow-subtle);
            margin-bottom: var(--space-8);
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}
        
        .logo {{
            height: 40px;
        }}
        
        h1 {{
            font-size: 32px;
            font-weight: 600;
            color: var(--cutover-dark);
            margin: 0;
        }}
        
        h2 {{
            font-size: 20px;
            font-weight: 600;
            color: var(--cutover-dark);
            margin: 0 0 var(--space-4) 0;
        }}
        
        /* Metric Cards */
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: var(--space-6);
            margin-bottom: var(--space-8);
        }}
        
        .metric-card {{
            background: var(--cutover-card-bg);
            border: 1px solid var(--cutover-border);
            border-radius: var(--radius-lg);
            padding: var(--space-6);
            text-align: center;
            transition: all 200ms ease;
        }}
        
        .metric-card:hover {{
            box-shadow: var(--shadow-hover);
            transform: translateY(-4px);
        }}
        
        .metric-label {{
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: #666;
            margin-bottom: var(--space-3);
        }}
        
        .metric-value {{
            font-size: 36px;
            font-weight: 600;
            color: var(--cutover-dark);
            margin-bottom: var(--space-2);
        }}
        
        .metric-subtitle {{
            font-size: 13px;
            color: #999;
        }}
        
        /* Panels */
        .panel {{
            background: white;
            border: 1px solid var(--cutover-border);
            border-radius: var(--radius-lg);
            padding: var(--space-6);
            margin-bottom: var(--space-8);
            box-shadow: var(--shadow-subtle);
        }}
        
        /* Tables */
        .cutover-table {{
            width: 100%;
            border-collapse: collapse;
            background: white;
            border-radius: var(--radius-lg);
            overflow: hidden;
        }}
        
        .cutover-table thead th {{
            background: var(--cutover-primary);
            color: white;
            padding: var(--space-4);
            text-align: left;
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}
        
        .cutover-table tbody td {{
            padding: var(--space-4);
            border-bottom: 1px solid var(--cutover-border);
            color: #333;
        }}
        
        .cutover-table tbody tr:hover {{
            background: var(--cutover-skeleton-2);
        }}
        
        .cutover-table tbody tr:last-child td {{
            border-bottom: none;
        }}
        
        /* Badges */
        .badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: var(--radius-xl);
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}
        
        .badge-success {{ background: var(--cutover-success); color: white; }}
        .badge-warning {{ background: var(--cutover-warning); color: white; }}
        .badge-danger {{ background: var(--cutover-danger); color: white; }}
        .badge-neutral {{ background: var(--cutover-neutral); color: white; }}
        
        /* Footer */
        .footer {{
            background: var(--cutover-dark);
            color: white;
            padding: var(--space-6);
            text-align: center;
            border-radius: var(--radius-lg);
            margin-top: var(--space-8);
        }}
        
        .footer-logo {{
            height: 30px;
            margin-bottom: var(--space-2);
            opacity: 0.9;
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Header with Cutover Logo -->
        <div class="header">
            <svg class="logo" viewBox="0 0 600 120">
                <g fill="#2A55C3">
                    <path d="M30 60 Q30 20 70 20 Q90 20 100 30 L90 45 Q85 35 70 35 Q45 35 45 60 Q45 85 70 85 Q85 85 90 75 L100 90 Q90 100 70 100 Q30 100 30 60"/>
                    <path d="M120 20 L135 20 L135 70 Q135 85 150 85 Q165 85 165 70 L165 20 L180 20 L180 70 Q180 100 150 100 Q120 100 120 70 Z"/>
                    <path d="M200 20 L280 20 L280 35 L247.5 35 L247.5 100 L232.5 100 L232.5 35 L200 35 Z"/>
                    <path d="M300 60 Q300 20 340 20 Q380 20 380 60 Q380 100 340 100 Q300 100 300 60 M315 60 Q315 35 340 35 Q365 35 365 60 Q365 85 340 85 Q315 85 315 60"/>
                    <path d="M400 20 L417.5 20 L440 85 L462.5 20 L480 20 L447.5 100 L432.5 100 Z"/>
                    <path d="M500 20 L570 20 L570 35 L515 35 L515 52.5 L560 52.5 L560 67.5 L515 67.5 L515 85 L570 85 L570 100 L500 100 Z"/>
                    <path d="M590 20 L625 20 Q645 20 645 40 Q645 55 635 58 L648 100 L632 100 L620 60 L605 60 L605 100 L590 100 Z M605 35 L605 47 L622 47 Q630 47 630 41 Q630 35 622 35 Z"/>
                </g>
            </svg>
            <h1>{title}</h1>
        </div>
        
        <!-- Your dashboard content here -->
        
        <!-- Footer -->
        <div class="footer">
            <svg class="footer-logo" viewBox="0 0 600 120">
                <g fill="white">
                    <path d="M30 60 Q30 20 70 20 Q90 20 100 30 L90 45 Q85 35 70 35 Q45 35 45 60 Q45 85 70 85 Q85 85 90 75 L100 90 Q90 100 70 100 Q30 100 30 60"/>
                    <path d="M120 20 L135 20 L135 70 Q135 85 150 85 Q165 85 165 70 L165 20 L180 20 L180 70 Q180 100 150 100 Q120 100 120 70 Z"/>
                    <path d="M200 20 L280 20 L280 35 L247.5 35 L247.5 100 L232.5 100 L232.5 35 L200 35 Z"/>
                    <path d="M300 60 Q300 20 340 20 Q380 20 380 60 Q380 100 340 100 Q300 100 300 60 M315 60 Q315 35 340 35 Q365 35 365 60 Q365 85 340 85 Q315 85 315 60"/>
                    <path d="M400 20 L417.5 20 L440 85 L462.5 20 L480 20 L447.5 100 L432.5 100 Z"/>
                    <path d="M500 20 L570 20 L570 35 L515 35 L515 52.5 L560 52.5 L560 67.5 L515 67.5 L515 85 L570 85 L570 100 L500 100 Z"/>
                    <path d="M590 20 L625 20 Q645 20 645 40 Q645 55 635 58 L648 100 L632 100 L620 60 L605 60 L605 100 L590 100 Z M605 35 L605 47 L622 47 Q630 47 630 41 Q630 35 622 35 Z"/>
                </g>
            </svg>
            <p>Generated: {data.get('generated_date', 'N/A')} | Cutover Platform</p>
        </div>
    </div>
</body>
</html>"""
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"Dashboard saved to {output_file}")
    return output_file
```

### Chart.js with Cutover Colors

```javascript
// Cutover color palette for Chart.js
const CUTOVER_COLORS = {
    primary: '#2A55C3',
    success: '#27ae60',
    warning: '#f39c12',
    danger: '#e74c3c',
    neutral: '#95a5a6'
};

// Efficiency color function
function getEfficiencyColor(value) {
    if (value >= 70) return CUTOVER_COLORS.success;
    if (value >= 30) return CUTOVER_COLORS.warning;
    return CUTOVER_COLORS.danger;
}

// Example: Bar chart with Cutover styling
new Chart(document.getElementById('efficiencyChart'), {
    type: 'bar',
    data: {
        labels: ['User A', 'User B', 'User C'],
        datasets: [{
            label: 'Efficiency %',
            data: [98.2, 65.4, 28.7],
            backgroundColor: function(context) {
                return getEfficiencyColor(context.parsed.y);
            },
            borderRadius: 6,  // Matches Cutover button radius
            borderSkipped: false
        }]
    },
    options: {
        responsive: true,
        plugins: {
            legend: {
                labels: {
                    font: {
                        family: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto',
                        size: 12,
                        weight: 600
                    },
                    color: '#16161d'
                }
            },
            tooltip: {
                backgroundColor: '#16161d',
                titleFont: { size: 12, weight: 600 },
                bodyFont: { size: 11 },
                padding: 12,
                cornerRadius: 6
            }
        },
        scales: {
            y: {
                beginAtZero: true,
                max: 100,
                ticks: {
                    font: { size: 11 },
                    color: '#666'
                },
                grid: {
                    color: '#ebebeb'
                }
            },
            x: {
                ticks: {
                    font: { size: 11, weight: 600 },
                    color: '#16161d'
                },
                grid: {
                    display: false
                }
            }
        }
    }
});

// Example: Pie/Doughnut chart with Cutover colors
new Chart(document.getElementById('distributionChart'), {
    type: 'doughnut',
    data: {
        labels: ['High', 'Medium', 'Low'],
        datasets: [{
            data: [8, 3, 2],
            backgroundColor: [
                CUTOVER_COLORS.success,  // Green for high
                CUTOVER_COLORS.warning,  // Orange for medium
                CUTOVER_COLORS.danger    // Red for low
            ],
            borderWidth: 0
        }]
    },
    options: {
        responsive: true,
        plugins: {
            legend: {
                position: 'bottom',
                labels: {
                    font: { size: 12, weight: 600 },
                    color: '#16161d',
                    padding: 16,
                    usePointStyle: true,
                    pointStyle: 'circle'
                }
            }
        }
    }
});
```

---

### Responsive Design

```css
/* Mobile breakpoint: 768px */
@media (max-width: 768px) {
    .container {
        padding: var(--space-4);  /* 16px on mobile */
    }
    
    .header {
        flex-direction: column;
        text-align: center;
        gap: var(--space-4);
    }
    
    .logo {
        height: 30px;  /* Smaller on mobile */
    }
    
    h1 {
        font-size: 24px;  /* Reduced from 32px */
    }
    
    .metrics-grid {
        grid-template-columns: 1fr;  /* Stack on mobile */
        gap: var(--space-4);
    }
    
    .metric-value {
        font-size: 28px;  /* Reduced from 36px */
    }
    
    .panel {
        padding: var(--space-4);
    }
    
    .cutover-table {
        font-size: 12px;  /* Smaller text on mobile */
    }
    
    .cutover-table thead th,
    .cutover-table tbody td {
        padding: var(--space-2);  /* Reduced padding */
    }
}
```

---

### Design System Checklist

When creating any Cutover dashboard or report, verify:

- ✅ **Logo:** Use `cutover_logo.svg` (never create custom logos)
- ✅ **Colors:** All colors from official palette (exact hex values)
- ✅ **Typography:** System font stack, 600 weight headings (not 700)
- ✅ **Spacing:** All spacing is multiples of 4px
- ✅ **Border Radius:** 8px cards, 6px buttons, 12px badges
- ✅ **Shadows:** Subtle elevation (not heavy drop shadows)
- ✅ **Interactions:** 200ms transitions, -4px hover lift
- ✅ **Tables:** Primary blue (#2A55C3) headers
- ✅ **Charts:** Cutover color palette (success/warning/danger)
- ✅ **Responsive:** Mobile breakpoint at 768px
- ✅ **Footer:** Include Cutover logo and branding

---

## 12. Code Templates

### Template 1: Get All Completed Runbooks in Workspace

```python
#!/usr/bin/env python3
"""Get completed runbooks in workspace 233"""
import requests
import time

API_BASE = 'https://api.staging.cutover.cloud'
TOKEN = 'REMOVED_FOR_SECURITY'
CORE_URL = 'https://your-tenant.cutover.com'

headers = {
    'Authorization': f'Bearer {TOKEN}',
    'Content-Type': 'application/vnd.api+json',
    'Core-Url': CORE_URL
}

def get_completed_runbooks(workspace_id='233'):
    verified_runbooks = []
    page = 1
    
    while True:
        params = {
            'filter[workspace_id]': workspace_id,
            'filter[stage]': 'complete',
            'page[number]': page,
            'page[size]': 100
        }
        
        resp = requests.get(
            f'{API_BASE}/core/runbooks',
            params=params,
            headers=headers,
            verify=False
        )
        
        if resp.status_code != 200:
            break
        
        data = resp.json()
        runbooks = data.get('data', [])
        
        if not runbooks:
            break
        
        # Verify workspace and filters
        for rb in runbooks:
            actual_ws = rb['relationships']['workspace']['data']['id']
            attrs = rb['attributes']
            
            if (actual_ws == workspace_id and
                attrs.get('is_template') == False and
                attrs.get('archived_at') is None and
                attrs.get('run_type') == 'live'):
                
                verified_runbooks.append({
                    'id': rb['id'],
                    'name': attrs['name']
                })
        
        if not data.get('links', {}).get('next'):
            break
        
        page += 1
        time.sleep(0.5)
    
    return verified_runbooks

if __name__ == '__main__':
    runbooks = get_completed_runbooks()
    print(f"Found {len(runbooks)} completed runbooks")
    for rb in runbooks:
        print(f"  {rb['id']}: {rb['name']}")
```

### Template 2: Get User Activity for Runbook

```python
#!/usr/bin/env python3
"""Get user activity for a specific runbook"""
import requests
import time
from datetime import datetime

API_BASE = 'https://api.staging.cutover.cloud'
TOKEN = 'REMOVED_FOR_SECURITY'
CORE_URL = 'https://your-tenant.cutover.com'

headers = {
    'Authorization': f'Bearer {TOKEN}',
    'Content-Type': 'application/vnd.api+json',
    'Core-Url': CORE_URL
}

def get_runbook_user_activity(runbook_id):
    """Get all task executions with user attribution"""
    
    # Get all tasks
    resp = requests.get(
        f'{API_BASE}/core/runbooks/{runbook_id}/tasks',
        params={'page[size]': 100},
        headers=headers,
        verify=False
    )
    
    if resp.status_code != 200:
        return []
    
    tasks = resp.json()['data']
    task_details = []
    
    # Get each task with user info
    for task in tasks:
        task_id = task['id']
        attrs = task['attributes']
        
        # Skip non-executed tasks
        if not attrs.get('start_actual') or not attrs.get('end_actual'):
            continue
        
        # Get task with user attribution
        resp = requests.get(
            f'{API_BASE}/core/runbooks/{runbook_id}/tasks/{task_id}',
            params={'include': 'task_actions'},
            headers=headers,
            verify=False
        )
        time.sleep(1.5)  # Rate limiting
        
        if resp.status_code != 200:
            continue
        
        data = resp.json()
        included = data.get('included', [])
        
        # Find user from task_actions
        user_id = None
        for item in included:
            if item['type'] == 'task_action':
                if item['attributes'].get('action') == 'start':
                    user_rel = item.get('relationships', {}).get('user', {})
                    user_id = user_rel.get('data', {}).get('id')
                    break
        
        # Calculate duration
        start = datetime.fromisoformat(attrs['start_actual'].replace('Z', '+00:00'))
        end = datetime.fromisoformat(attrs['end_actual'].replace('Z', '+00:00'))
        duration = (end - start).total_seconds()
        
        task_details.append({
            'task_id': task_id,
            'task_name': attrs['name'],
            'user_id': user_id,
            'start_time': start,
            'end_time': end,
            'duration_seconds': duration
        })
    
    return task_details

if __name__ == '__main__':
    runbook_id = '8648'  # Example
    tasks = get_runbook_user_activity(runbook_id)
    print(f"Found {len(tasks)} executed tasks")
    for task in tasks:
        print(f"  Task {task['task_id']}: {task['task_name']}")
        print(f"    User: {task['user_id']}, Duration: {task['duration_seconds']}s")
```

### Template 3: Calculate Efficiency Metrics

```python
#!/usr/bin/env python3
"""Calculate efficiency metrics for all users"""
from collections import defaultdict
from datetime import datetime

def calculate_efficiency_metrics(all_task_data):
    """
    Args:
        all_task_data: List of task dicts with user_id, start_time, end_time, duration
    
    Returns:
        Dict of user metrics
    """
    # Group by user
    user_tasks = defaultdict(list)
    for task in all_task_data:
        if task['user_id']:
            user_tasks[task['user_id']].append(task)
    
    user_metrics = {}
    
    for user_id, tasks in user_tasks.items():
        # Sort by time
        tasks.sort(key=lambda x: x['start_time'])
        
        # Execution time
        exec_seconds = sum(t['duration_seconds'] for t in tasks)
        
        # Inter-task time
        inter_seconds = 0
        for i in range(len(tasks) - 1):
            gap = (tasks[i+1]['start_time'] - tasks[i]['end_time']).total_seconds()
            if gap > 0:
                inter_seconds += gap
        
        # Total effort
        total_seconds = exec_seconds + inter_seconds
        
        # Efficiency
        efficiency = (exec_seconds / total_seconds * 100) if total_seconds > 0 else 0
        
        # Velocity
        velocity = len(tasks) / (exec_seconds / 3600) if exec_seconds > 0 else 0
        
        user_metrics[user_id] = {
            'tasks': len(tasks),
            'execution_hours': exec_seconds / 3600,
            'inter_task_hours': inter_seconds / 3600,
            'total_effort_hours': total_seconds / 3600,
            'efficiency_percent': round(efficiency, 1),
            'velocity_tasks_per_hour': round(velocity, 1)
        }
    
    return user_metrics

# Usage
if __name__ == '__main__':
    # Assuming you have task_data from previous template
    metrics = calculate_efficiency_metrics(task_data)
    
    for user_id, m in metrics.items():
        print(f"User {user_id}:")
        print(f"  Tasks: {m['tasks']}")
        print(f"  Efficiency: {m['efficiency_percent']}%")
        print(f"  Velocity: {m['velocity_tasks_per_hour']} tasks/hour")
```

### Template 4: Generate CSV Report

```python
#!/usr/bin/env python3
"""Generate CSV report with user metrics"""
import csv

def generate_user_metrics_csv(user_metrics, user_details, filename='user_report.csv'):
    """
    Args:
        user_metrics: Dict from calculate_efficiency_metrics()
        user_details: Dict mapping user_id to {name, email}
        filename: Output CSV filename
    """
    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)
        
        # Header
        writer.writerow([
            'User_ID',
            'Name',
            'Email',
            'Tasks',
            'Execution_Hours',
            'InterTask_Hours',
            'TotalEffort_Hours',
            'Efficiency_Percent',
            'Velocity_TasksPerHour'
        ])
        
        # Sort by efficiency (highest first)
        sorted_users = sorted(
            user_metrics.items(),
            key=lambda x: x[1]['efficiency_percent'],
            reverse=True
        )
        
        # Data rows
        for user_id, metrics in sorted_users:
            user_info = user_details.get(user_id, {})
            
            writer.writerow([
                user_id,
                user_info.get('name', 'Unknown'),
                user_info.get('email', 'unknown@email.com'),
                metrics['tasks'],
                f"{metrics['execution_hours']:.2f}",
                f"{metrics['inter_task_hours']:.2f}",
                f"{metrics['total_effort_hours']:.2f}",
                f"{metrics['efficiency_percent']:.1f}",
                f"{metrics['velocity_tasks_per_hour']:.1f}"
            ])
    
    print(f"Report saved to {filename}")

# Usage
if __name__ == '__main__':
    # Assuming you have metrics and user_details from previous steps
    generate_user_metrics_csv(user_metrics, user_details)
```

---

## 12. Decision Trees

### Decision Tree: Which API Endpoint Should I Use?

```
START: What data do I need?
│
├─ List all workspaces
│  └─> GET /core/workspaces
│
├─ List runbooks in workspace
│  ├─ All runbooks
│  │  └─> GET /core/runbooks?filter[workspace_id]={id}
│  │     ⚠️ THEN verify relationships.workspace.data.id
│  │
│  └─ Completed runbooks only
│     └─> GET /core/runbooks?filter[workspace_id]={id}&filter[stage]=complete
│        ⚠️ THEN verify workspace + is_template + archived_at + run_type
│
├─ List tasks in runbook
│  └─> GET /core/runbooks/{runbook_id}/tasks
│
├─ Get task with user attribution
│  └─> GET /core/runbooks/{runbook_id}/tasks/{task_id}?include=task_actions
│     ✓ Parse 'included' array for task_action with action='start'
│     ❌ DO NOT use action_logs (returns old data)
│
└─ Get user details
   └─> GET /core/users/{user_id}
```

### Decision Tree: How Do I Filter Runbooks?

```
START: Need to filter runbooks
│
├─ By workspace?
│  ├─ Use filter[workspace_id]={id}
│  └─ ⚠️ MUST verify in response: relationships.workspace.data.id
│
├─ By completion status?
│  ├─ Use filter[stage]=complete
│  └─ Check attributes.stage == 'complete'
│
├─ Exclude templates?
│  ├─ Use filter[is_template]=false (unreliable)
│  └─ ✓ MUST check attributes.is_template == False AND
│         attributes.template_type == 'off'
│
├─ Exclude archived?
│  ├─ Use filter[archived]=false (unreliable)
│  └─ ✓ MUST check attributes.archived_at is None
│
└─ Live runs only (not rehearsal)?
   └─ ✓ MUST check attributes.run_type == 'live'

CONCLUSION: API filters are hints, not guarantees
           Always verify in response attributes/relationships
```

### Decision Tree: How Do I Calculate User Metrics?

```
START: Calculate user metrics
│
1. Get all completed runbooks
   └─> Use workspace filtering + verification
│
2. For each runbook:
   ├─ Get all tasks
   │  └─> GET /core/runbooks/{id}/tasks
   │
   └─ For each task with start_actual & end_actual:
      ├─ Get task with user
      │  └─> GET /core/runbooks/{rb_id}/tasks/{task_id}?include=task_actions
      │     └─> Extract user_id from included array
      │
      └─ Calculate duration
         └─> (end_actual - start_actual).total_seconds()
│
3. Group tasks by user_id
   └─> Use defaultdict(list)
│
4. For each user:
   ├─ Sort tasks by start_time
   │
   ├─ Calculate execution_time
   │  └─> sum(all task durations)
   │
   ├─ Calculate inter_task_time
   │  └─> sum(gaps between consecutive tasks)
   │
   ├─ Calculate total_effort
   │  └─> execution_time + inter_task_time
   │
   ├─ Calculate efficiency
   │  └─> (execution_time / total_effort) × 100
   │
   └─ Calculate velocity
      └─> tasks / (execution_time in hours)
│
5. Export results
   └─> CSV, HTML dashboard, or PowerPoint
```

### Decision Tree: Troubleshooting - I Got Wrong Results

```
START: Results don't match expectations
│
├─ No runbooks found?
│  ├─ Check workspace_id is correct (233 for "02. Cutover Recover")
│  ├─ Check stage filter (should be 'complete')
│  └─ Verify runbooks aren't archived (archived_at is None)
│
├─ Wrong users in results?
│  ├─ Are you using action_logs? ❌ STOP - Use task_actions instead
│  ├─ Did you include 'task_actions' parameter? ✓ Required
│  └─ Are you parsing 'included' array? ✓ User is in task_action.relationships.user
│
├─ Getting 429 errors?
│  ├─ Add delays between requests (1.5s for tasks)
│  ├─ Reduce concurrency
│  └─ Implement exponential backoff
│
├─ Runbooks from wrong workspace?
│  └─ ⚠️ API filter bug - Verify relationships.workspace.data.id manually
│
├─ Metrics seem incorrect?
│  ├─ Check timezone handling (use .replace('Z', '+00:00'))
│  ├─ Ensure tasks are sorted by start_time before gap calculation
│  └─ Verify only executed tasks included (start_actual AND end_actual exist)
│
└─ Missing tasks?
   ├─ Check pagination (use page[size]=100 and loop through pages)
   └─ Verify rate limiting isn't causing timeouts
```

---

## Appendix A: Known Runbooks (Workspace 233)

| Runbook ID | Name | Tasks | Duration | User |
|------------|------|-------|----------|------|
| 6869 | InfraSync - Application Recovery Plan (Pilot Light) | 23 | 118.1m | Dhiren |
| 6996 | RevMax - InfraSync AS2 | 12 | 574.3m | Arty |
| 7129 | CloudWatch Demo - 9th July | 4 | 0.4m | Saif |
| 7145 | Cloudwatch alarm - ANNIE IBM | 5 | 0.6m | Mark |
| 7363 | SNow Ticket | 3 | 0.2m | Saif |
| 8647 | AWS Region outage PP copy | 8 | 0.9m | Melissa |
| 8648 | Demo - Z/P copy | 7 | 0.5m | Melissa |
| 8790 | RevMax - InfraSync MW | 11 | 81.2m | Max |
| 8791 | RevMax - InfraSync MW 2 | 12 | 46.3m | Max |
| 8889 | RTO Example for MS copy | 4 | 0.2m | Marcus |
| 8890 | RTO Example for MS copy 2 | 7 | 0.3m | Marcus |

**Total:** 11 runbooks, 96 tasks, 13.7 hours execution time

---

## Appendix B: Efficiency Benchmarks

Based on analysis of 7 users across 96 tasks:

| Efficiency Range | Classification | User Count | Characteristics |
|-----------------|----------------|------------|-----------------|
| 90-100% | Excellent | 1 | Continuous execution, minimal gaps |
| 70-89% | High | 1 | Focused work with short breaks |
| 30-69% | Medium | 2 | Some gaps, acceptable performance |
| 1-29% | Low | 0 | Significant delays between tasks |
| 0% | Multi-day | 3 | Tasks spread over days/weeks |

**Key Findings:**
- High performers (≥70%): Share best practices, focused execution
- Medium performers (30-70%): Opportunities for optimization
- Low efficiency (0%): Multi-day patterns, investigate blockers

---

## Appendix C: Common Error Codes

| Code | Meaning | Solution |
|------|---------|----------|
| 200 | Success | Continue |
| 401 | Unauthorized | Check token and Core-Url header |
| 404 | Not Found | Verify IDs exist, check permissions |
| 429 | Rate Limited | Add delays, implement backoff |
| 500 | Server Error | Retry with exponential backoff |

---

## Appendix D: File References

### Scripts Created During Analysis

- `api_helpers.py` - Rate-limited session wrapper
- `generate_workspace_233_activity.py` - Workspace-specific report generator
- `analyze_inter_task_duration.py` - Inter-task gap calculator
- `generate_cutover_presentation.py` - PowerPoint generator with template
- `user_efficiency_dashboard.html` - Interactive Chart.js dashboard

### Data Files Generated

- `user_effort_analysis.csv` - User summary metrics
- `user_activity_detail_corrected.csv` - Task-level details (96 tasks)
- `completed_runbooks_summary.csv` - Runbook summaries
- `inter_task_gaps.csv` - Detailed gap analysis
- `Cutover_User_Activity_Dashboard.pptx` - Executive presentation

---

## Change Log

**Version 1.3 - February 23, 2026**
- 🎯 MAJOR: Discovered source_runbook relationship limitation (individual GET only)
- Added comprehensive template relationship analysis section
- Strengthened mandatory branding requirements with auto-enforcement language
- Updated all section numbers to accommodate new template section
- Added real-world template usage example (Template 6927: 5 runbooks)
- Documented actual stage values found in production data
- Added enrichment patterns for large datasets with progress saving
- Updated reference implementation to create_cutover_branded_template_dashboard.py

**Version 1.2 - February 23, 2026**
- Added mandatory branding checklist at document start
- Official Cutover logo requirements from CDN
- Complete color palette specifications
- System fonts and spacing requirements
- Reference implementation pointer

**Version 1.0 - February 19, 2026**
- Initial playbook creation
- Documented all API patterns and workarounds
- Captured user attribution breakthrough
- Added code templates and decision trees
- Included workspace 233 specific data

---

## Quick Start Guide

**To generate a user activity report:**

1. Get completed runbooks: Use Template 1
2. Extract user activity: Use Template 2 for each runbook
3. Calculate metrics: Use Template 3
4. Export to CSV: Use Template 4
5. Create dashboard: Use HTML template or PowerPoint generator

**Remember:**
- ✓ Always verify workspace_id in response
- ✓ Use task_actions for user attribution
- ✓ Add 1.5s delays between task requests
- ✓ Sort tasks by time before calculating gaps
- ✗ Don't trust API filters blindly
- ✗ Don't use action_logs for recent data

---

**End of Playbook**

*For questions or updates, reference this document in all future reporting requests.*
