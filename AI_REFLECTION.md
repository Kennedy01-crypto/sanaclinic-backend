# AI Reflection

## 1. What I Used AI For Across the Four Sections

- **Section 1 — System design:** I used AI to organize the README's description of the models, components, design decisions, and trade-offs.
- **Section 2 — API implementation:** In this follow-up review, I used AI to compare the booking implementation with the assessment, strengthen booking conflict protection, and add tests for booking, cancellation, rescheduling, and patient appointment history.
- **Section 3 — Deployment and CI/CD:** I used AI to review the deployment and CI/CD documentation against the repository and the public backend endpoints. The GitHub Actions workflow runs checks and tests; Vercel handles deployment from the configured branch.
- **Section 4 — Reflection:** I used AI to structure this reflection and to identify claims that needed correction or personal input.

## 2. An Example Where AI Improved My Work

I asked AI: “critic my system on /backend based on the requirements of the Savannah Informatics Backend Assessment”. The review identified that the application checked for appointment conflicts before saving, but did not enforce the no-overlap rule in the database. I used that finding to add PostgreSQL exclusion constraints and tests for overlapping bookings.

## 3. An Example Where AI Was Wrong or Incomplete

The first review incorrectly said that there was no verified public deployment. The README already listed the backend URL, and checking the deployed backend landing page and OpenAPI schema confirmed that they were reachable. I corrected the reflection and deployment wording rather than repeating the unsupported claim. The review also could not truthfully describe my unaided decisions without asking me, so I supplied those decisions directly.

## 4. Two Decisions I Made Without AI

- **Deploying on Vercel rather than Railway or Render:** I trusted my judgment because I am familiar with Vercel and have deployed multiple projects there before.
- **Adding Swagger API documentation:** I know Swagger UI is effective for communicating API details. Its Authorize feature lets users authenticate and reuse that session while testing multiple endpoints.

I trusted my own judgment on these choices because they were based on my prior deployment experience and my understanding of how developers use API documentation to explore and test an API.
