---
name: ado-bug-report
description: >
  Create professional, clear and reproducible Azure DevOps bug reports from user-provided issues,
  screenshots, test results or descriptions, then file them in Azure DevOps with the screenshots
  captured, annotated, attached and embedded inline. Uses the azure-devops MCP to create and update
  the Bug and the Playwright MCP to capture evidence and upload attachments through the work item
  Attachments tab, with no token handling. Trigger on "write a bug", "log a bug", "file this bug in
  Azure DevOps", "create a bug report", "attach the screenshots to the bug", "embed the evidence",
  "reformat this bug".
---

# Azure DevOps Bug Report Skill

## Before you start

**Production is read-only.** Reproducing a bug never justifies a write on a
client-production system (see [Production Systems](#production-systems)). If a repro
step appears to require one, stop and ask.

**A difference is not a defect.** Where a difference is the subject of the bug, first
confirm it against the requirement (REQ / spec / acceptance criteria) or the agreed
Source system. If nothing says which value is right, ask before filing - a withdrawn
finding costs more credibility than the finding would have earned.

## Tools this skill uses (link-qc plugin)

| Job | Tool |
|---|---|
| Create the Bug | azure-devops MCP `wit_work_item_write` (action `create`, workItemType `Bug`; title in `System.Title`, body in `Microsoft.VSTS.TCM.ReproSteps` with format `Html`) |
| Link to the parent story | azure-devops MCP `wit_work_item_link_write` (Parent) |
| Capture screenshots | Playwright MCP `browser_take_screenshot`, saved into the evidence folder |
| Annotate | Before capturing, use Playwright `browser_evaluate` to draw a red outline around the value and add a caption strip below the area; remove it afterwards. Static images: skill 6's Pillow annotation when installed |
| Attach | Playwright MCP on the work item page: **Attachments** tab, **Add attachment**, `browser_file_upload` with the absolute file paths, **Save** (see [Attachment mechanics](#attachment-mechanics)) |
| Verify attachments | azure-devops MCP `wit_work_item` (action `get`, expand `Relations`): one `AttachedFile` relation per file name |
| Embed inline | azure-devops MCP `wit_work_item_write` (action `update`) rewriting the Evidence section of `ReproSteps` with `<img src="{AttachedFile url}" width="900">` per screenshot |

The azure-devops MCP can **download** attachments but cannot **upload** them, so the upload
always goes through the work item's Attachments UI in the user's signed-in browser.
If the Playwright browser is not signed in to Azure DevOps, ask the user to sign in there
and wait. Never handle a token.

---

## Purpose

This skill helps create high-quality Azure DevOps Bug work items.

The goal is to transform a reported issue into a clear, concise, reproducible, and professional bug report that developers, business analysts, and QA engineers can understand and act upon.

---

# Core Rules

When creating a bug report:

1. Do not invent information that was not provided.
2. Keep the title concise and descriptive.
3. Clearly distinguish between:
   - Actual Result
   - Expected Result
4. Write reproducible Steps to Reproduce whenever enough information is available.
5. Use professional QA terminology.
6. Focus on observable system behavior.
7. Avoid assumptions about the root cause unless explicitly requested.
8. Do not include implementation suggestions unless requested.
9. Preserve exact field names, labels, page names, and system terminology provided by the user.
10. Write the bug in clear professional English.
11. **Evidence first.** Never file a bug before its evidence is captured and annotated. A bug without evidence is not ready to file.
12. **Always name a representative example** — the exact project/record, the relevant item or task, and the exact Source → Target values. Population counts alone are not a bug report.
13. **Steps to Reproduce must work on that named example**, so a reader can open it and confirm the defect directly.
14. **Re-check every finding against live data before finalizing.** Correct or withdraw false positives; update scope, title and severity when the evidence changes.
15. Keep descriptions and repro steps structured and non-redundant — state each fact once.
16. **Visual Evidence Rule.** When a bug claim depends on what a user can **see** in the UI,
    DOM/`innerText` is **supporting evidence only**. The captured screenshot must itself visibly
    contain the relevant element or value. If the value exists in the DOM but falls outside the
    captured viewport, **re-capture with the relevant content visible** — never present the DOM
    reading as proof of what is on screen. Detail in [Evidence Rules](#evidence-rules).
17. **Minimal by default.** A bug is a pointer to the defect, not the full investigation. Detail in [Minimalism](#minimalism).
18. **Default sections: Title, Steps to Reproduce, Expected Result, Actual Result, Evidence.**
    Evidence is mandatory whenever a screenshot exists, and the screenshots are **embedded
    inline** in it, not just attached. Add Description, Representative Example or
    Preconditions only when the default sections alone would leave a reader unable to find,
    reproduce or verify the defect. Detail in [The Default Sections](#the-four-section-default).
19. **One action per step.** Every navigation, click, input, selection, toggle and Save/Submit is
    its own numbered step. Never chain several actions in one step. Include the setup: one
    "Fill the mandatory fields" step and the Save/Submit click, plus a step for each field that
    matters to the defect. Detail in [Steps to Reproduce Rules](#steps-to-reproduce-rules).
20. **Expected Result and Actual Result are separate bold sections, bulleted inside, with a
    blank line between them.** Never lump them together, and never put an expected value inside
    the Actual section or vice versa.
21. **One defect per bug.** Unrelated symptoms on the same page (e.g. checkbox display vs a
    cost field's number format) are separate bugs, even when found in one session. If a request
    says "put these into one issue" and the items have different fixes, confirm before merging.

*(Rules 19-21 and the inline-Evidence part of rule 18 were set by Mohamed, 2026-10-20, after BUG
1122972, and refined 2026-10-21 from Mohamed's own edit of that bug, which is the accepted
shape: generic "Fill the mandatory fields" step, "the newly added" record, blank line between
Expected and Actual. They override anything below that suggests a shorter shape.)*

---

# The Four-Section Default

The default bug has five sections: **Title, Steps to Reproduce, Expected Result,
Actual Result, Evidence**. Evidence is captured, annotated and attached as files (see
[Evidence Rules](#evidence-rules)), and then **embedded inline** in the Evidence section of the
body, one `<img>` per screenshot with a one-line caption. Drop the Evidence section only when the
bug truly has no screenshot (API/DB-only), and then say why in one line.

Carry the representative example inline in the steps: name the view, the field and the exact
value at the step where it's used, rather than restating them in a separate "Representative
Example" block:

```
## Title
Project Information – Performance Bond Cleared and On Hold show "No" when saved as Yes

## Steps to Reproduce
1. Navigate to **Projects**.
2. Click **Add New Project**.
3. Select **Project Type** = DGE Project.
4. Fill the mandatory fields.
5. Tick **Performance Bond Cleared**.
6. Tick **On Hold**.
7. Click **Save**.
8. Open **the newly added Project** from the Projects list.
9. Click the **Project Information** tab.
10. Check **Performance Bond Cleared** and **On Hold**.

## Expected Result
- **Performance Bond Cleared:** Yes
- **On Hold:** Yes
                                  ← blank line (<div><br></div>) before Actual Result
## Actual Result
- **Performance Bond Cleared:** No
- **On Hold:** No (the header badge still shows "On Hold")

## Evidence
1. Add New Project form - both boxes ticked before Save
   <img src="…attachment url…">
2. Project Information - both fields show "No"
   <img src="…attachment url…">
```

That is a complete, filable bug — the accepted shape (BUG 1122972 as edited by Mohamed,
2026-10-21). The field, the view and the values are each stated once, in the step or result
that needs them. The test record's own name goes in System Info and the evidence captions, not
in the steps.

**Add a section only when the default ones don't carry enough on their own:**

| Add | When |
|---|---|
| **Description** | The defect needs one sentence of framing the title and steps can't carry — e.g. it spans several related fields and the reader needs the connecting fact before the steps make sense. |
| **Representative Example** | The finding spans a population and one record must be singled out as *the* example the evidence matches — naming it inline in step 1 is not enough because the bug also claims a scope beyond that record. |
| **Preconditions** | Reproducing needs a state that isn't the default signed-in view — a specific role, a specific filter, data that must exist first. |
Adding a section is not free — each one is something a reviewer has to read past to find the
defect. Add only the section that's actually carrying weight the default ones can't.

---

# Steps to Reproduce Rules

- **One action per numbered step**: navigate, click, select, enter, tick/untick, Save/Submit,
  open a tab, observe. A `→` is allowed only inside one step for a single menu path
  (e.g. "Projects → **Add New Project**"). Opening a record and clicking a tab are two steps.
- **Mandatory fields are one step: "Fill the mandatory fields."** Don't list each mandatory
  field and its value. Give a field its own step only when its value matters to the defect
  (the ticked checkboxes, the selected Project Type), then the Save/Submit click.
- **Refer to a record the steps created generically:** "Open **the newly added Project** from
  the Projects list", not the test record's name. An existing record the reader must find
  (a migrated project, a named risk) is still named in full, per "Name it fully".
- **Use the exact on-screen labels** for buttons, tabs and fields (read them from the page,
  e.g. **Add New Project**, not "the add button").
- **The last step says what to look at**, so the Expected/Actual sections line up with it.
- Preconditions (role, existing data) go in a Preconditions section, not as step 1.

---

# Minimalism

**Default to one representative example.** One named record, one Source → Target pair, is
normally the entire bug. A second worked example, a "worst cases" table, or a root-cause
narrative belongs in a comment or an attachment, not the initial body — and often does not
belong anywhere, because it does not change what gets fixed.

**Population goes in an attachment, not inline.** "13 projects, 110 assignments" in the body is
enough. The full per-project breakdown is a `.txt`/`.csv` attachment (see Evidence staging), never
a multi-row table pasted into the description. A reviewer scans a bug; they do not study it.

**Character bands as a sanity check, not a target** — measure Title + Description + Steps +
Actual + Expected as plain text (tags stripped), before attachments:

| Band | Read as |
|---|---|
| 150–400 chars | Simple UI/text bug — one-line description, 2-4 repro steps, one-line actual/expected |
| 400–900 chars | The normal case — one named example with a Source → Target pair, numbered steps, actual/expected |
| 900–2,000 chars | Justified only when the bug spans a real population and needs one table beyond the single example |
| 2,000+ chars | Justified only when several distinct measures are reported together (e.g. Work + ActualWork + RemainingWork) — and even then the population detail should already be in an attachment, not inline |

Landing above 2,000 is a signal to re-read the draft and ask: does every sentence change what the
developer does? If not, cut it or move it to an attachment.

**One bug, one fix.** If a second observation traces to the same root cause (the arithmetic
reconciles, the population is the same), it does not need a second worked example in the same
bug — one line naming the additional surface is enough. See "Correcting a filed bug" below for
how to add it after the bug already exists.

**Do not pad a comment either.** The same restraint applies when adding detail after filing —
a short comment naming the fact and the value is more useful than a comment that re-derives the
whole mechanism a second time.

---

# Bug Title Rules

The title should follow this format:

[Module/Page] – [Incorrect behavior]

Examples:

- Issues and Risks – Severity values overlap with the dropdown
- Project Initiation – Read-only fields are incorrectly marked as mandatory
- Contract Plan – Negative values are accepted in the budget field
- Projects Report – Incorrect owning entity is displayed for projects

The title should:

- Clearly identify the affected area
- Describe the problem
- Avoid vague wording such as:
  - Issue found
  - Bug in system
  - Not working
  - Error

---

# Bug Report Template

The four sections below — Title, Steps to Reproduce, Actual Result, Expected Result — are
the default for every bug; see [The Four-Section Default](#the-four-section-default).
Description, Representative Example, Preconditions and a written Evidence section are
optional extras, used only when one of them is actually carrying weight the other four
can't (see the table above). Don't add a section out of habit.

## Title

[Module/Page] – [Clear description of the issue]

---

## Description (optional — see above)

Provide a short explanation of the problem.

---

## Representative Example (optional — see above)

Needed when the bug also claims a population beyond the one record shown, so the reader
must be told which record the evidence matches. Otherwise, name the record inline in step 1
of Steps to Reproduce instead of repeating it here.

State:

- The exact project / record name, plus a stable identifier (GUID or ID) where one exists
- The relevant item, task, list or field
- The **Source value** and the **Target value**, side by side

Example:

**Project:** A1 - Data Exchange Platform (DXP) (`projuid ecc6365b-…`)
**List / item:** Risks, item ID 1 - "PR Cycle Suspension Impacting on Awarding"

| Field | Source | Target |
|---|---|---|
| Risk Rating | 3D | **D** |
| Current Risk Level | 3D Medium | **D** |

When a finding spans many records, still pick **one** representative for the example and screenshots, and attach the full affected list (see Evidence). Do not inline a second or third example "for completeness" — one representative example is the default; see [Minimalism](#minimalism).

---

## Preconditions (optional — see above)

Include only when the required state isn't the default signed-in view.

Example:

- User is logged into the system.
- User has access to the Project Management module.

---

## Steps to Reproduce

1. Navigate to **[Module/Page]**.
2. Perform **[Action]**.
3. Select or enter **[Data]**.
4. Observe the behavior.

Use numbered steps.

Do not create unnecessary steps.

---

## Actual Result

Clearly describe what currently happens.

Example:

The system allows the user to enter negative values in the budget field.

---

## Expected Result

Clearly describe what should happen.

Example:

The system should reject negative values and display appropriate validation.

---

## Evidence

- Embed each screenshot inline (`<img src="<attachment url>" width="900">`), numbered, with a
  one-line caption saying what it shows (environment + record + value).
- Do not describe visual details that are not clearly visible.
- Where a field is hidden by default, say how to make it visible (add the column, open the display form, or the read-only API path).
- Do not claim a value is visible on screen unless the attached screenshot shows it — see the **Visual Evidence Rule**.

---

# Evidence Rules

**Prefer Portal UI screenshots.** If the issue is visible to a user in the portal, a UI screenshot is required. API responses are supporting evidence — acceptable as the *only* evidence just when no safe UI surface exposes the field, and the bug should say so.

**Capture a matched pair:** the same record on Source and on Target, same view.

**Annotate every screenshot.** Box the exact affected values and caption the reading (e.g. `Risk Rating = 3D` / `Risk Rating = D`). An unannotated screenshot makes the reader hunt.

## The Visual Evidence Rule

**When a bug claim depends on what a user can see in the UI, the captured screenshot must itself
visibly contain the relevant element or value.** DOM and `innerText` readings are **supporting
evidence only** — they corroborate a screenshot, they never substitute for one. This is the single
most common way evidence fails review, and it fails silently.

- **DOM presence is not visual proof.** Finding the value with `innerText`, `querySelector`, or a
  grid's read accessors tells you the value is *in the page*. It does not tell you the value is *in
  the picture*. Virtualized grids, columns past the right edge, collapsed panes and lazy-rendered
  rows all put content in the DOM that the capture never sees.
- **If the value is in the DOM but outside the captured viewport, re-capture it** with the relevant
  content visible. Do not crop, do not annotate an arrow pointing off-frame, and do not quote the
  DOM reading in place of the missing pixels.
- **Open the saved file and look at the pixels** before accepting it. Confirm the named record's row
  is in frame, and that the compared column is in frame with a readable value. If you cannot confirm
  it by looking, the screenshot is not evidence.
- **Re-capture wider rather than cropping tighter.** When a column sits off-screen, widen the
  viewport (1680x1000 works for most admin grids) and take it again. Note in the repro steps that
  the column needs a wider window, so the reader is not misled into reading a hidden column as an
  empty one.
- **A wrong screenshot is worse than a missing one** — it invites a reviewer to close the bug as
  unreproducible. If you cannot capture the value, say so and name the surface where it can be read.

**Place annotations so they never cover the evidence.** Box the value; put the caption in a strip
appended *below* the image, not on top of it. Badges and labels sit clear of the box they point at —
a badge overlapping the value it marks hides the exact pixels the bug depends on. Use colour
consistently and state the key in the bug: for a source/target pair, green for the correct source
value, red for the wrong target value, and a neutral colour for identity (the record name or ID that
proves both images show the same record).

**Box the controls, not just the value,** when the reading depends on context — the ribbon's view
selector, the group-by header, the filter state. A boxed value with no visible context is arguable.

**Playwright MCP captures the evidence.** Screenshots come from `browser_take_screenshot`
after the annotation is drawn (see [Tools this skill uses](#tools-this-skill-uses-link-qc-plugin)).
On production, use it only for reading and screenshots, never for a write. An MCP accessibility
snapshot is a DOM-level reading and falls under the rule above: supporting only.

**Attach an affected-project/record list** whenever a finding spans more than one record. Screenshots stay with the one representative; the list carries the full set, with per-record Source → Target values where they vary.

---

# Filing Workflow

1. **Capture and annotate evidence** for the representative example.
2. **Create the bug** with the named example and Source → Target values.
3. **Rename evidence files to the ADO Bug ID** once it exists:
   `BUG-<ID>-<sequence>-<description>.png` — e.g. `BUG-1234567-01-SOURCE-Alpha-RiskRating-3D.png`.
   Keep un-annotated originals alongside as `RAW-*` for audit; they are not attached.
4. **Update `ATTACHMENT-MAP.md`** — every bug ID mapped to all its screenshots and lists. Generate it from the evidence folder so it stays accurate; it is the checklist for attaching and for spotting gaps.
5. **Attach all evidence**, then **verify** both that the upload succeeded *and* that the work-item relation exists — re-read the work item and confirm the `AttachedFile` relations. An upload that returns success but leaves no relation is not attached.
6. **Embed the evidence inline.** Read the work item with expand `Relations`, take each file's
   `AttachedFile` URL, and update `Microsoft.VSTS.TCM.ReproSteps` so the Evidence section has
   one numbered caption and one `<img src="{url}" width="900">` per screenshot. Never embed a
   file that is not attached yet. Re-read the body afterwards and confirm every image is present.

## Evidence staging

Stage the finished, annotated files one folder per bug, named by bug ID:

```
evidence/ado-bugs/BUG-<ID>/BUG-<ID>-<n>-<environment>-<what-it-shows>.png
```

e.g. `evidence/ado-bugs/BUG-1234567/BUG-1234567-1-production-Active-No.png`. The environment and the
reading belong in the filename, so an attachment list is self-describing without opening the images.
Keep un-annotated originals outside this folder as `RAW-*`; they are for audit, not for attaching.

Attachment tooling reads this convention, and so does a human finishing the job by hand.

## Attachment mechanics

- **The azure-devops MCP cannot upload attachments** (it only downloads them). Upload through
  the work item's Attachments UI with the Playwright MCP, as described below.
- **If the project has its own attachment tool**, you may use it instead, as long as it needs no
  token handling by you.
- **Attachment scripts must be idempotent** — safe to re-run, skipping files already attached to that work item rather than creating duplicates.
- **Azure DevOps `/_apis` authenticates with bearer tokens, not cookies.** A `fetch` issued from a
  signed-in `dev.azure.com` page carries the cookies but no bearer token, so the API answers as the
  **anonymous** identity — `TF400813: The user 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa' is not
  authorized`. A 401 from an attachment script in a browser that is plainly signed in usually means
  this, not an expired session. **Do not respond by extracting a token.** Reading, storing or
  logging a bearer token is forbidden regardless of how convenient it is.
- **Default route, no token: drive the work item's own Attachments UI.** On the modern work
  item form: click the Attachments tab, click **Add attachment**, hand the file chooser the staged
  paths (the hidden `input[type=file]` accepts multiple), then **Save**. The form title gains a `*`
  while the work item is dirty and loses it once saved — that asterisk is the cheapest confirmation
  the save landed. This runs entirely as the signed-in user with no credential handling.
- If no authorized upload path exists, say so plainly, keep the evidence named and mapped, and hand over the map rather than filing bugs with no evidence.

## Verifying an attachment

**Upload success is not proof.** Re-read the work item with relations expanded and confirm an
`AttachedFile` relation exists for each file, matching by `name`. Verify per bug, not per batch —
a partial failure in the middle of a run is exactly what this check is for.

## Correcting a filed bug

**Exception: a restructure the user asks for.** When the user asks for a bug's body to be
reformatted, split or completed (e.g. missing steps), back up the current body locally, rewrite
it with `wit_work_item_write` (action `update`), and re-read it. When splitting, the original ID keeps
one defect, and each other defect becomes a new bug with its own evidence, linked to the original
as Related.

Once a bug body has been reviewed and is correct, **do not rewrite the whole field to fix a detail**
such as a filename or a stale note. Most APIs replace the entire field, so a full retype risks
corrupting text that is already right. Add a **comment** that states the correction and supersedes
the stale line. Comments are additive, cannot damage the body, and leave an auditable trail of what
changed and why.

**Your own comment is the exception to "comment, don't rewrite".** When your own
earlier comment is superseded or duplicated, edit that comment in place instead
of stacking a new one: back up its HTML locally, PATCH it, re-read it. Never
edit or delete anyone else's comment, and never rewrite the bug body.

**Reading ADO when a route is down:** the Playwright browser closed or signed out
means ask the user to sign in there again; the ADO MCP server answering
"Personal Access Token has expired" means read the work item in the browser instead
and tell the user to renew the PAT (link-qc skill 1's `set-azure-devops-pat.ps1`,
then fully restart the editor).

**Retest comments are not written here.** A comment that reports a retest result (fixed, still
failing, blocked, withdrawn) belongs to `link-qc-9-retesting` - status header with `X ➔ Y`
inline, 2-4 emoji bullets, evidence blockquote last. The
evidence rules in this file still govern the screenshots that go in that blockquote.

---

# Session and Credentials

Attaching evidence needs an authenticated Azure DevOps session. Obtaining one is **the user's job,
never yours.**

- **Reuse the session the user established.** Work inside the browser profile or MCP connection they
  already signed in to. Do not open a login flow.
- **Never type, read, store or log a credential** — password, MFA code, cookie, PAT or bearer token —
  into any field, file, script, artifact, commit or log. This holds even when a token would trivially
  unblock the work, and even when the user offers one.
- **Nothing credential-shaped goes in the repository.** Not in the skill, not in a script, not in a
  config file, not in an evidence pack.
- **Session persistence comes from the browser profile, not from stored secrets.** A long-lived
  signed-in profile (a persistent user-data directory the user controls) survives restarts without
  anything being written to the repo. If the session lapses mid-run, stop and ask the user to sign in
  again — do not work around it.
- **Distinguish an expired session from a missing token.** A redirect to a sign-in page means
  expired. A 401 from `/_apis` inside a page that still renders normally means the request lacked a
  bearer token (see Attachment mechanics) — a different problem with a different, token-free fix.

# Production Systems

When the source or target is a live production system:

- **Never** save, publish, check out, check in, submit, or take any action that changes stored data, configuration or shared state.
- **Read-only API (GET) and pure display pages only.** Display forms (`DispForm.aspx`), list views and library views are safe.
- **Avoid UI navigation known to trigger edit mode or a check-out** — "Edit", settings forms with OK/Cancel, and PDP edit pages. A Schedule ribbon **View** switch is allowed only when the user authorizes it in the session, on a Checked-in project, with `inEditMode: false` and still Checked-in confirmed afterwards.
- If state is changed accidentally: stop, verify the extent against the read-only API (compare `LastSavedDate` / `LastPublishedDate` to confirm whether data changed or only a lock was taken), and report it to the owner immediately. Do not "fix" it with another write unless authorized.

---

# Before Marking Complete

Verify for every bug:

- [ ] Bug created, title concise and specific
- [ ] Severity and priority match the real impact
- [ ] Linked to the correct parent work item
- [ ] Representative example named, with identifier
- [ ] Exact Source → Target values stated
- [ ] Repro steps verifiable on that example
- [ ] One action per step; "Fill the mandatory fields" + Save/Submit included; exact on-screen labels
- [ ] A record the steps created is "the newly added …", not its test name
- [ ] Expected and Actual are separate bold sections, bulleted, with a blank line between them
- [ ] One defect per bug — unrelated symptoms split into separate bugs
- [ ] Screenshots embedded inline under Evidence (not only attached)
- [ ] Evidence attached, and the `AttachedFile` relation confirmed per bug by re-reading the work item
- [ ] Evidence matches the description — same project, same values
- [ ] **Visual Evidence Rule satisfied** — every screenshot opened and looked at, with the named
      record and the compared value actually visible in the image, not merely present in the page DOM
- [ ] Annotations box the value and never cover it; captions sit below the image
- [ ] Filenames carry the bug ID and say which environment and which reading they show
- [ ] No credential of any kind was typed, stored or logged
- [ ] **Minimal** — one representative example (not several), population in an attachment (not an
      inline table), no root-cause narrative beyond what changes the fix; see [Minimalism](#minimalism)

**If any of these cannot be satisfied, report the blocker explicitly and leave the bug marked
incomplete.** Never mark a bug done on the strength of an upload that was not verified, or a
screenshot that was not looked at. Saying "the uploader is unavailable, evidence is staged at
`<path>`" is a correct outcome; quietly closing without evidence is not.

## Field values are schema-specific

Custom fields reject values that look obviously valid. `Impact` may not accept `Security`, for
instance, even for a bug with a security consequence — fall back to a supported value such as
`Functionality` and describe the security consequence in the body. When a field is rejected, take the
nearest supported value rather than dropping the bug, and say in the body what you could not express
in the field.

---

# Writing Style

## Write it short — for a reader with ten seconds (ADHD-friendly)

Set by Mohamed, 2026-10-06. Applies to the bug body **and** every comment.

- **One fact per line.** No paragraphs. A sentence that wraps is too long.
- **Numbers in bold, as `Production X ➔ QC Y`.** Never "the value differs".
- **Bold label first:** `**Expected:** …`, `**Example:** …`.
- **3+ comparable items → a small table** (e.g. one row per group: Production | QC), not a comma list.
- **One example.** Pick the one that shows the main failure mode.
- **Name it fully, and say what each name is.** No abbreviations or nicknames
  ("A1 Audit") — use the exact name as it appears in the system. Put a label in
  front of every name and add its ID, one per line (set 2026-10-06, BUG 1094901):
  ```
  **Project:** A1 Abu Dhabi Government Data Management Audit Framework Development
  **Risk:** "BSI Engagement /Responsibility" (Risks list, item ID 1, PRJ-RSK-1)
  ```
  Labels to use: `Project:`, `Task:` (+ outline / ID), `Risk:` / `Issue:` / `List item:`
  (+ list name + item ID), `User:`, `Group:`, `Field:`, `View:`. Quote item titles.
  Same rule for screenshot captions and filenames.
- **Population → attached file.** Inline only the count.
- **No methodology, no "how we measured", no "Sign in" steps** — the reader is already signed in.
- **Cut test:** if a line doesn't change what the developer does, delete it.

Before / after (same bug):

```
Before: Actual: security group membership differs in QC for 322 of the 418 people who are
in any group - most lost EPM Prod, Project Managers, Portfolio Viewers or DGE Portfolio Role
and were added to Team Members, which grew from 94 members to 412.

After:  **Actual:** 127 users lost a group.
        | Group            | Production | QC  |
        | EPM Prod         | 309        | 208 |
        | Project Managers | 332        | 271 |
        **Example:** Abedalaziz Khalaf Ahmed — Production: EPM Prod + Project Managers ➔ QC: Team Members only
```

Use:

- Clear language
- Professional QA terminology
- Short sentences
- Objective descriptions
- System-focused wording

Prefer:

"The system displays..."

"The user is able to..."

"The application allows..."

"The value is incorrectly..."

"The field should..."

Avoid:

"I found..."

"It looks weird..."

"This is wrong..."

"The developer needs to..."

"Please fix..."

---

# Validation Issues

For validation-related bugs, explicitly identify:

1. The affected field
2. Invalid input
3. Actual behavior
4. Expected validation behavior

Example:

## Title

Contract Plan – Negative values are accepted in the Amount field

## Steps to Reproduce

1. Navigate to Contract Plan.
2. Enter a negative value in the Amount field.
3. Submit the form.

## Actual Result

The system accepts the negative value and allows the form to be submitted.

## Expected Result

The system should reject negative values and display appropriate validation.

---

# UI Issues

For UI issues, clearly describe:

- Affected page
- Affected component
- Incorrect visual behavior

Do not use subjective wording such as "looks bad".

Example:

## Actual Result

The spacing between table rows is inconsistent.

## Expected Result

The spacing between table rows should be consistent across the table.

---

# Mandatory Field Issues

When a read-only field is marked as mandatory:

## Expected Result

Read-only fields should not display a mandatory indicator because users cannot modify their values.

---

# Filter Issues

When filter behavior is incorrect:

Clearly identify:

- Current filter state
- Incorrect icon/button behavior
- Expected behavior

Example:

## Actual Result

The Clear Filter icon is displayed even when no filter is applied.

## Expected Result

The Clear Filter icon should only be displayed when at least one filter is applied.

---

# Data Issues

For incorrect calculations or displayed data:

Always include:

- Input data
- Displayed result
- Expected result

Do not calculate or assume missing values unless the user provides enough information.

---

# Security / Authorization Issues

Clearly identify:

- User access level
- Restricted functionality
- Actual access behavior
- Expected authorization behavior

Example:

## Actual Result

The user can access the restricted page directly using the URL without the required permission.

## Expected Result

The system should prevent unauthorized users from accessing the page and display an appropriate access restriction response.

---

# Output Format

Default sections — see [The Default Sections](#the-four-section-default):

# Title

[Bug Title]

## Steps to Reproduce

1. [one action]
2. [one action]

## Expected Result

- **[Field]:** [value]

## Actual Result

- **[Field]:** [value]

## Evidence

1. [caption]
   [inline image]

Add Description, Representative Example, or Preconditions only when one of them is
carrying weight the default sections can't (see the table in The Default Sections) — not as
a matter of course. When one is needed, it goes in immediately after Title, in this order:

# Title

[Bug Title]

## Description

[Brief description]

## Representative Example

[Project / record + identifier, item, and Source → Target values.]

## Preconditions

[Only if required]

## Steps to Reproduce

1. ...
2. ...

## Expected Result

...

## Actual Result

...

## Evidence

[Attached screenshots; affected-record list when the finding spans multiple records]