# AI_USAGE.md

## HostelFix --- AI Usage Record

**Project:** HostelFix --- Hostel Maintenance and Housekeeping Portal for IIT Dharwad

**Course:** Course Project 2026 --- Build, Test and Ship an AI-Enabled Web Application

**Theme:** Theme 3 --- Campus services portal

**Team:**

-   Narasimha Reddy Boggula --- CS26MT002
-   Aakash Saran V --- CS26MT018
-   Suru Rakesh --- CS26MT022

## 1. Purpose

This document records how AI tools were used during the development of
HostelFix across all six milestones.

The course permitted the use of AI coding assistants while requiring the
students to remain responsible for every submitted part of the project.
The team therefore used AI as an assistance tool for design,
implementation, debugging, testing support, technical explanations, and
documentation, while retaining responsibility for the final
architecture, code, design decisions, testing, verification, reports,
presentation, and submission.

AI-generated output was treated as an initial aid rather than as an
authoritative source or automatically correct solution. The team
reviewed, modified, tested, and, where necessary, rejected AI-generated
suggestions before retaining them in the project.

------------------------------------------------------------------------

## 2. AI Tools Used

### 2.1 ChatGPT

ChatGPT was used as the general-purpose AI assistant throughout the
HostelFix project.

Its uses included:

-   Understanding technical concepts and implementation approaches.
-   Generating and improving FastAPI backend code.
-   Assisting with SQLAlchemy models and database-related code.
-   Assisting with Pydantic schemas and API contracts.
-   Generating frontend HTML, CSS, and JavaScript code.
-   Helping with authentication and authorization implementation.
-   Generating validation and error-handling logic.
-   Assisting with Docker and Docker Compose configuration.
-   Assisting with pytest tests and test setup.
-   Explaining errors, stack traces, framework behaviour, and
    implementation choices.
-   Debugging API, backend, frontend, database, Docker, and testing
    problems.
-   Reviewing code structure and suggesting improvements.
-   Assisting with documentation and technical explanations.
-   Generating and structuring the final presentation and final report.
-   Assisting with the design-document template used at the beginning of
    the project.

ChatGPT was used as a development and documentation assistant; it was
not the runtime model powering the SmartReport feature.

### 2.2 Gemini

Gemini was used as the runtime AI provider for the HostelFix SmartReport
feature.

It was not used as the team's general coding assistant.

The HostelFix application calls the Gemini API from the FastAPI backend.
SmartReport uses Gemini to transform a student's natural-language
description, optionally accompanied by an image, into an editable
complaint draft.

The generated draft is validated by the application and presented to the
student for review and editing. Gemini does not directly submit a
complaint.

The Gemini API key is kept server-side and is not exposed to the
browser.

### 2.3 Claude

Claude (Anthropic) was used in the final milestone (MS-6) through the claude.ai chat. It was used to read the repository, re-measure the test and coverage figures by running the test suite, export `docs/openapi.yaml` from the running application, and draft the final report and the final presentation. Claude was not used at runtime by HostelFix.

------------------------------------------------------------------------

## 3. AI Usage by Milestone

## 3.1 MS-1 --- Problem Statement and Design Document

### AI assistance

At the beginning of the project, ChatGPT was used to generate the
**initial design-document template/structure** for the HostelFix MS-1
deliverable.

The AI-assisted starting structure was used to organize the document
into the required sections and provide a useful format for presenting
the project idea.

### Human contribution

The team did not submit the generated template as the final design
document.

The team manually replaced and edited the content throughout the
document, including the actual HostelFix problem statement, target
users, features, pages, user stories, project requirements, AI feature
proposal, and other project-specific details.

The final design document represents the team's own project decisions
and requirements rather than the generic AI-generated template.

### Verification

The team compared the completed design document with the course MS-1
requirements and the intended HostelFix system before using it as the
basis for later milestones.

The approved design document then became the reference for the clickable
prototype, API/backend work, and later implementation.

------------------------------------------------------------------------

## 3.2 MS-2 --- Clickable Prototype and ER Diagram

> **Note on milestone naming:** The team's locally stored AI-usage files
> use milestone names differently from the course handout. The uploaded
> `AI_USAGE_MS2.md` corresponds to the course MS-2 clickable prototype
> and ER-diagram milestone.

### AI assistance

ChatGPT was used as an AI design/prototyping assistant.

AI assistance included:

-   Planning the screen structure and navigation flow.
-   Translating the design document and milestone requirements into
    prototype screens.
-   Reviewing required pages, user roles, and navigation.
-   Supporting the SmartReport-related screens and interaction flow.
-   Structuring the clickable prototype so the major user journeys could
    be demonstrated.
-   Reviewing prototype behaviour and identifying interaction problems.
-   Refining the prototype against the project's actual requirements.

The prototype included major HostelFix screens such as:

-   Login and Registration
-   Dashboard
-   Report an Issue
-   SmartReport interaction
-   Community Issues
-   Issue Details
-   My Reports
-   Profile
-   Staff Dashboard
-   Admin Dashboard

### Example of AI output that required correction

The initial AI-assisted prototype contained navigation/interaction
problems. Some buttons and links did not correctly connect to the
intended pages or did not behave as expected.

The team caught these issues by manually navigating through the
clickable prototype and comparing each transition with the intended
HostelFix sitemap and user flow.

The team then:

1.  Checked important buttons and navigation elements manually.
2.  Compared their destinations with the intended user flow.
3.  Fixed incorrect or missing links.
4.  Corrected button actions.
5.  Rechecked the prototype after making the changes.

This was a direct example of why AI output was treated as an initial aid
rather than as the final source of truth.

### Human contribution

All three team members participated in reviewing and refining the
prototype. The team made the final decisions regarding the included
screens, navigation, SmartReport flow, interaction behaviour, and
visual/functional corrections.

------------------------------------------------------------------------

## 3.3 MS-3 --- API Contract, Backend and Database

> **Note on milestone naming:** The team's uploaded `AI_USAGE_MS1.md`
> corresponds to the course MS-3 milestone. It was named `MS1` in the
> team's local AI-usage documentation.

### AI assistance

ChatGPT was used as a software-development assistant while building and
integrating the HostelFix backend and API.

Assistance included:

-   FastAPI backend development.
-   FastAPI routers.
-   Pydantic request and response schemas.
-   SQLAlchemy ORM concepts and database operations.
-   Alembic migration concepts and implementation support.
-   MySQL integration.
-   REST API design.
-   API validation and error handling.
-   OpenAPI structure and API specifications.
-   Docker and Docker Compose configuration.
-   Supporting scripts and configuration.
-   Debugging Python and FastAPI errors.
-   Understanding API test failures.
-   Diagnosing Docker and database integration issues.
-   Reviewing incorrect API behaviour.
-   Suggesting possible fixes.

### Human contribution

The generated schemas and backend suggestions were manually reviewed and
adapted to the actual HostelFix requirements, codebase, dependencies,
and runtime behaviour.

In particular:

-   Generated schemas were reviewed and modified where necessary.
-   Backend implementation was adapted to the actual project structure.
-   API behaviour was checked against the implemented application.
-   Configuration and integration code was adjusted for the actual
    development environment.
-   AI suggestions that did not match the project requirements were
    changed or rejected.

### Verification

The team verified the AI-assisted implementation by:

-   Running the FastAPI application.
-   Running the application with Docker Compose.
-   Connecting the backend to MySQL.
-   Running Alembic migrations.
-   Running the seed process.
-   Testing API endpoints.
-   Running automated tests.
-   Checking API request and response behaviour.
-   Reviewing OpenAPI definitions.
-   Inspecting application errors and correcting implementation issues.

Only reviewed and suitable changes were retained.

------------------------------------------------------------------------

## 3.4 MS-4 --- Testing, CI and a Running Website

### AI assistance

ChatGPT was used during the implementation and testing phase to assist
with:

-   Generating initial versions of Python/FastAPI backend code.
-   Improving API-related code.
-   Generating frontend HTML, CSS, and JavaScript code.
-   Generating and improving pytest test cases.
-   Explaining errors encountered during development.
-   Suggesting fixes for failing tests.
-   Explaining Docker and Docker Compose configuration.
-   Explaining FastAPI and SQLAlchemy behaviour.
-   Explaining GitHub Actions configuration.
-   Reviewing code structure.
-   Preparing technical documentation and explanations.

### Backend

AI assistance was used for:

-   FastAPI route implementation.
-   Pydantic request/response schemas.
-   SQLAlchemy database operations.
-   Complaint ownership checks.
-   Complaint status handling.
-   Location and problem-type validation.
-   API error handling.
-   Docker and environment configuration.
-   Integration between routers, database sessions, and the frontend.

The final implementation was manually adapted to the existing HostelFix
architecture and requirements.

### Frontend

ChatGPT assisted with initial implementation and improvement of frontend
functionality.

The team manually modified frontend behaviour to match the actual
application, including:

-   Complaint forms and interaction flow.
-   API request handling.
-   Complaint edit and delete behaviour.
-   SmartReport-related frontend behaviour.
-   Complaint status and information display.
-   Existing page structure and UI details.
-   Error handling and user-facing messages.

The team tested the frontend against the running backend rather than
assuming the generated code was correct.

### Testing

ChatGPT was also used to generate and improve automated tests.

The generated test code and ideas were reviewed and modified to match
the actual HostelFix API and database setup.

Tests covered functionality such as:

-   Health endpoint behaviour.
-   Hostel and location APIs.
-   Complaint creation and listing.
-   Profile and catalogue APIs.
-   Staff account creation.
-   Problem-type and location validation.
-   Complaint editing by the reporter.
-   Complaint deletion by the reporter.
-   Restrictions after complaint acknowledgement.
-   Prevention of another user editing or deleting someone else's
    complaint.

### Verification

AI-assisted code was verified through:

-   Manual code review.
-   Running the application locally.
-   Running pytest.
-   Running Ruff linting.
-   Checking frontend JavaScript syntax.
-   Testing API requests and responses.
-   Running Docker Compose.
-   Running the GitHub Actions CI pipeline.
-   Reviewing test coverage.

The team retained responsibility for deciding which generated
suggestions were appropriate and for fixing issues that appeared during
local and CI execution.

------------------------------------------------------------------------

## 3.5 MS-5 --- Authentication and AI Feature on the Live System

### AI assistance

ChatGPT continued to be used as a general development assistant for the
live HostelFix system.

Its assistance included:

-   Backend and frontend implementation guidance.
-   Authentication and authorization implementation.
-   API schemas and validation.
-   Debugging authentication and frontend issues.
-   Reviewing application logic.
-   Testing support.
-   Documentation.
-   SmartReport integration and surrounding application logic.

The team also manually changed parts of the authentication system and
frontend after reviewing the AI-assisted suggestions so that they
matched the actual HostelFix architecture and required behaviour.

### SmartReport

The actual runtime AI feature, SmartReport, uses Gemini rather than
ChatGPT.

SmartReport follows this general workflow:

1.  The student enters a natural-language complaint description.
2.  The student may provide an optional image.
3.  The request is sent to the HostelFix backend.
4.  The backend applies input limits and privacy-oriented processing.
5.  The backend calls the Gemini API.
6.  Gemini returns structured complaint information.
7.  The backend validates the response.
8.  The student receives an editable draft.
9.  The student reviews and modifies the draft if necessary.
10. Only the student's explicit submission creates the actual complaint.

Gemini therefore does not directly create or submit a complaint.

The application also provides a local text-based fallback when Gemini is
unavailable, not configured, times out, or when the applicable daily
Gemini allowance has already been used.

### Responsible AI and privacy

The SmartReport implementation treats model output as untrusted input.

The project includes safeguards such as:

-   Server-side storage of the Gemini API key.
-   No direct Gemini API call from the browser.
-   Privacy-oriented redaction of apparent email addresses, phone
    numbers, and roll-number-like information before the Gemini request.
-   No persistence of SmartReport images by HostelFix.
-   Structured validation of AI output before it is used to populate the
    complaint form.
-   Checks intended to prevent invented exact hostel, floor, wing, or
    area information.
-   Input limits and rate/usage controls.
-   Editable AI-generated content that remains subject to normal backend
    validation.

The student remains in control of the final complaint submission.

### AI evaluation

The project contains an AI evaluation set with 40 inputs covering
different kinds of input, including clear complaints, shorthand
descriptions, Hinglish, typographical errors, vague descriptions, and
prompt-injection attempts.

The recorded **22/40 (55%)** result documented in the project refers to
the **local fallback behaviour**, not to Gemini's accuracy. The team did
not present this value as a Gemini accuracy score.

------------------------------------------------------------------------

## 3.6 MS-6 --- Final Presentation and Final Report

### AI assistance

For MS-6, ChatGPT and Claude were used to generate the initial content
and structure for:

-   The final HostelFix PowerPoint presentation.
-   The final project report.

Claude was also used to re-measure the test and coverage figures by
running the test suite and to export the OpenAPI file from the running
application. The AI assistance was used to organize technical information, present
the project's architecture and implementation, structure the
presentation/report sections, and produce an initial draft efficiently.

### Human contribution

The initial AI-generated presentation and report were **substantially
reviewed and manually edited by the team**.

Manual work included:

-   Replacing generic material with the actual HostelFix implementation
    details.
-   Correcting technical descriptions where necessary.
-   Adjusting project-specific terminology.
-   Updating architecture, database, API, authentication, SmartReport,
    testing, and deployment details.
-   Adding and modifying project results and measured values.
-   Adjusting diagrams, figures, tables, and presentation content.
-   Removing content that did not correspond to the implemented system.
-   Improving the final presentation flow and report structure.
-   Ensuring that the submitted material accurately represented the
    final project.

The final report describes the actual implemented system, including the
three-container Docker architecture, FastAPI backend, MySQL database,
Nginx frontend, authentication system, SmartReport integration, API,
database, testing, and CI. The final report also records that
SmartReport produces an editable draft rather than automatically
submitting a complaint.

### Verification

The team checked the final PPT and report against the implemented
project and the other milestone deliverables.

The final documents were therefore not treated as unedited AI-generated
submissions. They were AI-assisted drafts that were extensively adapted,
corrected, and finalized by the project team.

------------------------------------------------------------------------

## 4. AI-Assisted Development Workflow

Across the milestones, the general workflow was:

``` text
Project requirement / problem
            ↓
Discuss the requirement with ChatGPT
            ↓
Generate an initial approach, code, design, or documentation
            ↓
Review the AI output against HostelFix requirements
            ↓
Manually modify and integrate the output
            ↓
Run the application / prototype / tests
            ↓
Identify errors, mismatches, or missing requirements
            ↓
Correct the implementation manually
            ↓
Re-test and verify
            ↓
Retain only the reviewed result
```

This workflow was especially important for backend code, schemas,
frontend behaviour, authentication, testing, prototype navigation, and
final documentation.

------------------------------------------------------------------------

## 5. Examples of AI Output That Required Correction

The project provides multiple examples showing that AI-generated output
was not accepted without validation.

### 5.1 Prototype navigation errors

During the clickable prototype milestone, some AI-assisted buttons and
links did not connect to the intended pages.

The team discovered this by manually navigating the prototype and
comparing the transitions against the required user flow. The links and
button actions were then corrected manually and tested again.

### 5.2 Backend and schema adaptation

AI-generated FastAPI schemas and backend suggestions did not always
match the exact HostelFix database structure, API contract,
dependencies, or runtime behaviour.

The team identified these differences through code review, application
execution, API testing, and error investigation. The affected schemas
and backend code were manually modified to fit the actual project.

### 5.3 Authentication and frontend corrections

During the later authentication/live-system work, AI-assisted
suggestions for parts of the authentication system and frontend did not
directly match the final HostelFix behaviour.

The team identified the mismatch through manual review and integration
testing, changed the affected implementation manually, and tested the
revised behaviour again.

These examples demonstrate why AI output was treated as assistance
rather than as the final authority.

------------------------------------------------------------------------

## 6. Human Responsibility

The team remained responsible for the complete submitted project.

The team made the final decisions regarding:

-   Project architecture.
-   Feature selection.
-   Database structure.
-   API contract and behaviour.
-   Frontend structure and behaviour.
-   Authentication and authorization.
-   SmartReport integration.
-   Security and privacy decisions.
-   Test design and acceptance.
-   CI configuration and verification.
-   Prototype interactions.
-   Final report content.
-   Final presentation content.
-   Submission decisions.

AI assistance did not transfer responsibility for any of these decisions
to the AI tool.

Every team member remains responsible for understanding the submitted
implementation and being able to explain, modify, debug, and defend it
during the project evaluation and viva.

------------------------------------------------------------------------

## 7. Git and GitHub

ChatGPT was not used as the authority for Git/GitHub workflow decisions.

Repository management, commits, branches, pull requests, reviews,
merging, and related GitHub operations were handled by the project team.

AI-assisted suggestions were incorporated only after the team reviewed
and accepted the corresponding project changes.

------------------------------------------------------------------------

## 8. Testing and Verification of AI-Assisted Work

The team used actual project execution rather than assuming that
generated output was correct.

Verification included, as applicable across the milestones:

-   Manual prototype navigation.
-   Manual code review.
-   Running the FastAPI application.
-   Running Docker Compose.
-   Connecting the backend to MySQL.
-   Running Alembic migrations.
-   Running seed scripts.
-   Testing API endpoints.
-   Checking request and response behaviour.
-   Reviewing OpenAPI definitions.
-   Running pytest.
-   Running pytest coverage.
-   Running Ruff.
-   Checking frontend JavaScript.
-   Running GitHub Actions CI.
-   Testing authentication and authorization behaviour.
-   Testing SmartReport behaviour and failure handling.
-   Reviewing the final report and presentation against the actual
    implementation.

Only output that was reviewed, corrected where necessary, and found
suitable for the project was retained.

------------------------------------------------------------------------

## 9. Privacy and Security

The team did not intentionally provide passwords, API keys, database
credentials, private authentication tokens, or other confidential
secrets to ChatGPT.

Project code and configuration could be shared with ChatGPT when
necessary for debugging, code generation, or explanation, but
confidential secrets were not intentionally included in prompts.

For SmartReport, the Gemini API key remains server-side and is not
exposed to the browser.

The project also applies privacy-oriented handling to SmartReport inputs
and does not persist SmartReport images.

------------------------------------------------------------------------

## 10. AI-Assisted Documentation

ChatGPT was used to assist with project documentation during
development, and Claude was used for the MS-6 final report and
presentation drafts.

This included assistance with:

-   README material.
-   Technical explanations.
-   Architecture descriptions.
-   API documentation.
-   Development/setup documentation.
-   Milestone documentation.
-   AI_USAGE documentation.
-   Final project report.
-   Final presentation.

Documentation generated with AI was reviewed and adapted so that it
represented the actual HostelFix implementation rather than a generic
application.

The final report and presentation in MS-6 received substantial manual
changes after the initial AI generation.

------------------------------------------------------------------------

## 11. AI-Assisted Development vs. Runtime AI Feature

These two uses of AI should not be confused.

### ChatGPT

ChatGPT was used by the team as a development and documentation
assistant. It helped with planning, coding, debugging, testing support,
explanations, prototype work, and final documentation/presentation.

### Gemini

Gemini was integrated into HostelFix as the runtime AI provider for
SmartReport.

SmartReport is an application feature that helps a student turn a
natural-language problem description into an editable complaint draft.

ChatGPT is **not** the model running SmartReport.

------------------------------------------------------------------------

## 12. Summary by Milestone

  --------------------------------------------------------------------------------------
  Milestone         AI Tool / Use     Main AI-Assisted Work    Human Action
  ----------------- ----------------- ------------------------ -------------------------
  MS-1 --- Problem  ChatGPT           Initial design-document  Team replaced and
  Statement and                       template/structure       substantially edited the
  Design Document                                              template content and
                                                               finalized the
                                                               project-specific document

  MS-2 ---          ChatGPT           Prototype planning,      Team reviewed the
  Clickable                           screen structure,        prototype and manually
  Prototype and ER                    navigation and           corrected buttons, links,
  Diagram                             SmartReport flow         transitions, and design
                                                               details

  MS-3 --- API      ChatGPT           FastAPI, schemas,        Team adapted
  Contract, Backend                   SQLAlchemy, API/OpenAPI, schemas/backend code and
  and Database                        Docker, debugging and    verified implementation
                                      technical guidance       through execution and
                                                               testing

  MS-4 --- Testing, ChatGPT           Backend/frontend code,   Team modified generated
  CI and Running                      pytest, debugging,       code/tests and verified
  Website                             Docker, CI and           locally and through CI
                                      documentation support    

  MS-5 ---          ChatGPT + Gemini  ChatGPT for development; Team manually corrected
  Authentication                      Gemini for SmartReport   authentication/frontend
  and AI Feature                      runtime AI               work and validated
                                                               SmartReport; Gemini
                                                               output remained editable
                                                               and validated

  MS-6 --- Final    ChatGPT           Initial PPT and          Team substantially
  Presentation and                    final-report             edited, corrected,
  Report                              generation/structuring   project-specificized, and
                                                               finalized both
                                                               deliverables
  --------------------------------------------------------------------------------------

------------------------------------------------------------------------

Note: in the MS-6 row, the AI tools were ChatGPT and Claude.

## 13. Overall Responsibility Statement

AI was used throughout HostelFix to accelerate development, design,
debugging, testing support, and documentation.

The project should **not** be considered an entirely AI-generated
project.

The team designed the final system, selected the final features, adapted
the implementation to the actual requirements, made manual code and
design changes, tested the application, corrected AI-generated errors,
verified the final behaviour, and finalized the presentation and report.

The final HostelFix implementation and all submitted deliverables remain
the responsibility of:

-   Narasimha Reddy Boggula --- CS26MT002
-   Aakash Saran V --- CS26MT018
-   Suru Rakesh --- CS26MT022

The team accepts responsibility for understanding, reviewing, modifying,
testing, verifying, and submitting the final work.
