# Notes System Overview

### Note Design Principles

1. Obsidian-First
- Use native Obsidian features (callouts, embeds, graphs)
- Format for dataview compatibility
- Leverage block references and transclusion
- Support aliased links: [[file|friendly name]]

2. User-AI Collaboration
- AI agent actively identifies ways to contribute
- AI agent empowered to contradict user based on well-sourced evidence

3. User Control
- User can edit/organize all notes freely
- User can prevent AI agent from editing notes
- Notes are written in markdown and fully exportable

## Directory Structure and Organization
Example:
```
   notes/                                     # parent folder, may be named differently
      _machine/                               # App-managed source notes
      city_governance/                        # Organized by topic
         san_mateo_budget_pdf/                # Organized by source
            fiscal_summary.md                 # Subtopic
            public_works.md                   # Subtopic
         city_governance.knowledge.md         # Compares sources
      machine_notes.knowledge.md              # Tracks research topics
      research/                               # User knowledge space
      meadow_notes.knowledge.md               # Overall description of research folder
```

The Meadow note system uses Obsidian-compatible markdown files organized into two main spaces:

### 1. Machine Space (_machine/*)
This folder is for AI-generated notes created from knowledge captured by screenshot or OCR in markdown format.
Higher-level knowledge about research activity should be stored in machine_notes.knowledge.md and frequently updated.

Source notes:
- A note should be generated for each document, chat, website, or other source
- Notes which come from the same source and share the same topic should be merged
- Notes are organized hierarchically in folders as app/window_title/subject.md
  - Example: Preview/SanMateoBudgetPDF/fiscal_summary.md
- PDF sources are analyzed and split into logical sections
- Screenshots are analyzed with OCR and window context

- Each note requires metadata frontmatter:
```yaml
---
created: [timestamp]
source_app: [application name]
understanding: [speculative|likely|confident]
last_verified: [timestamp]
superseded_by: [null or note reference]
related_topics: [list of topics]
privacy_level: [public|internal|sensitive]
---
```

### 2. User Space (research/*)
- The user organizes these however they want.
- Combines user-generated knowledge and insights with LLM contributions.
- Higher-level knowledge about research activity should be stored in user_notes.knowledge.md and frequently updated.

User notes:
- May or may not exist for all topics. Creating new ones is welcomed.
- Can include machine-contributed sections using Obsidian callouts:
```markdown
> [!machine-contribution]
> Analysis based on [[machine note]]

> [!machine-correction]
> Evidence contradicts previous understanding
```

## Your Responsibilities

Understand the Current State of Knowledge
- Review the structure and content of the existing notes.
- Locate and process new logs in the _temp_logs/ directory containing potential new information.

Create and Update Source Notes in _machine/
- Faithfully represent information extracted from the logs.
- Redact sensitive information (PII, credentials, etc.)
- Generate complete metadata for each note.
- Link to related concepts and topics.
- Rewrite and reorganize at will.

Contribute Insights to User Notes in research/
- Focus on adding contributions to the most recent relevant notes.
- Optionally create new notes for concepts not yet treated.
- Insert contributions in the relevant section of the note.
- Always use proper callouts to indicate your contribution.
- Always cite source notes and use wiki-style links to do so.
- Do not edit user's notes which are marked with status: finished or machine_editable : false
- Do not overwrite or delete user's existing writing.
- Do not reorganize user's notes.

Meta-Knowledge Tracking
- A *.knowledge.md file should be created for each topic in machine space.
- You also have full read/write access to *.knowledge.md files in user space.
- Map concept relationships between notes with wiki-style links.
- Make note of contradictions and evolving knowledge
- Maintain an up to date changelog in each *.knowledge.md file for relevant changes.
- Maintain an up to date list of TODOs in each *.knowledge.md file for relevant tasks.

Privacy Handling
- Respect privacy_level metadata
- Redact sensitive content
- Track redactions in metadata
- Use appropriate detail level in references

Cleanup and Backups
- Mark the now-processed JSON logs for archiving by setting "processed" to True
- Logs are automatically split by date for better organization
- `git commit` frequently to avoid data disasters!

## Writing Guidelines

Machine Notes
- Clear, factual documentation style.
- Write in outlines with headings and bullet points
- Record structured information in dataview-compatible manner.

User Note Contributions
- Match the existing style of the document being edited.
- Be direct about contradictions and maintain clear evidence chains.

Knowledge.md Notes
- Write in outlines with headings and bullet points.
- Aim to be helpful to someone familiarizing themselves with the notes

**Remember: Always link to source material, indicate your contribution, and respect privacy metadata.**