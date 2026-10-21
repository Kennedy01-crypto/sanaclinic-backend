# AI Reflection



## Part 1: What I Used AI For

### Section 1: Organizing the backend README

I used AI to reorganize the backend documentation into system design, models and components, key decisions, and trade-offs. This made the backend architecture and its scope easier to scan.

### Section 2: Summarizing the existing backend

I used AI to help turn the existing Django apps, models, authentication settings, and API routes into a concise overview. I checked the summary against the backend files so that it described the current implementation.

### Section 3: Documenting deployment status

I used AI to add a public application URL placeholder and a CI/CD section. I treated deployment details as unconfigured because no deployment workflow or production setup was present in the submitted backend folder.

### Section 4: Structuring this reflection

I used AI to create a reflection outline and express the documentation work clearly. The reflection is scoped to this documentation task rather than making claims about the history of the application code.

## Part 2: Where AI Suggestions Improved My Work

AI helped group related backend details in a consistent structure and made the README more useful as a standalone document. In particular, separating implemented behavior from planned CI/CD details makes it less likely that a reader will mistake a proposed deployment process for an active one.

## Part 3: Where AI Output Was Wrong, How I Caught It

I did not identify a specific incorrect factual claim in the AI-generated documentation for this task. The main risk was treating a typical CI/CD setup as though it were already configured. I checked the project files and found no deployment workflow or verified public deployment, so I documented CI/CD as proposed and used a URL placeholder. I also checked the model definitions and settings before describing the data model, PostgreSQL requirement, authentication, and schedule rules.

## Part 4: Decisions I Made Without AI

I kept the documentation limited to behavior that could be confirmed from the backend source. I chose to label the `main` deployment trigger and pipeline as proposed, retained the URL as a placeholder, and avoided making claims about production readiness or unverified booking protections.

### Why I Trusted My Own Judgement

The submitted source code and configuration are the evidence for what the backend currently does; AI-generated suggestions are not proof that a feature or workflow exists. Checking those files helped me keep the submission accurate and distinguish current implementation from future plans.
