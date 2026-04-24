# Job Match CV: A Retrieval-Augmented Job Recommendation and Resume Tailoring Prototype

## 1. Business problem

Our project addresses a practical problem for students and recent graduates: turning a broad, noisy LinkedIn profile into a short list of jobs worth applying to, then turning the chosen job description into an actionable resume rewrite plan. We focus on this problem because labor-market friction for early-career candidates is real. The Federal Reserve Bank of New York reported that labor-market conditions for recent college graduates worsened in **2025 Q4**, with unemployment at **5.7%** and underemployment at **42.5%**, the highest level since 2020 ([New York Fed](https://www.newyorkfed.org/research/college-labor-market?os=__)). LinkedIn also reported in January 2026 that **65%** of people say finding a job has become harder, with uncertainty about fit and skills gaps as major hurdles; applicants per U.S. open role have doubled since spring 2022 ([LinkedIn Research 2026](https://news.linkedin.com/2026/LinkedIn-Research-Talent-2026)).

The implication is not simply that there are not enough jobs. The deeper problem is matching and self-presentation. Students often have relevant experience, but they struggle to translate it into the language of a specific job description. That matters because resume signals affect employer behavior. In a resume audit published in *Labour Economics*, Nunley et al. found that internship experience increased interview rates by **14%** in business-related job openings ([Nunley et al., 2016](https://econpapers.repec.org/RePEc:eee:labeco:v:38:y:2016:i:c:p:37-46)).

Our business hypothesis is therefore narrow and testable: for New York-based students and recent graduates applying to analytics, business, and adjacent knowledge-work roles, reducing search friction in one workflow can improve job discovery and application quality. The workflow is: **LinkedIn paste -> top-5 recommended roles -> chosen-job CV guide**.

This is not a claim that LinkedIn or resume tooling has no overlap with our product. LinkedIn already offers AI-powered job search and AI-powered resume tips ([AI job search](https://www.linkedin.com/help/linkedin/answer/a8078917), [AI resume tips](https://www.linkedin.com/help/linkedin/answer/a6865810)). However, LinkedIn's own help pages show constraints that matter to our use case: its AI job search does **not** currently support searches like "jobs I'm qualified for" based directly on profile details, and its resume tips feature is a Premium, desktop-only flow that starts after the user has already opened a posting and uploaded a resume. Our differentiation is therefore workflow compression, not novelty of the underlying primitives.

## 2. AI methods and system design

The system uses AI at two different stages, with different responsibilities, and this maps closely to concepts from class.

First, we transform observations into representations. The raw input is messy copied text from a LinkedIn page, including useful signals plus UI junk, duplicated sections, posts, and irrelevant metadata. We use an LLM (`gpt-4o-mini`) to extract a structured profile with fields such as target roles, skills, industries, seniority, preferred locations, education, and short evidence-backed highlights. The same step also produces a compact `search_text`, optimized for retrieval rather than human reading. In other words, the system begins by converting an unstructured observation into a machine-usable representation.

Second, we perform similarity-based retrieval rather than using the LLM to pick jobs directly. Jobs from Adzuna are embedded with `BAAI/bge-base-en-v1.5` and stored in ChromaDB. Each job vector is built from `title + company + description`, while the user-side `search_text` is embedded with the same model. This means that both users and jobs are represented in the same vector space. Chroma then returns the nearest jobs, and because embeddings are normalized, retrieval effectively behaves like cosine-similarity search over semantic vectors. This directly reflects class concepts on representation, similarity, and recommendation systems: recommendation is produced by distance in vector space rather than by hard-coded rules.

This architecture is intentionally a **retrieval-augmented generation** pipeline rather than an end-to-end LLM recommender. The LLM does not inspect the whole vector store. The application retrieves candidates from ChromaDB and then uses the selected job as context for generation. That separation makes the system easier to debug, cheaper to run, and more interpretable.

For generation, we use the LLM again only after the user selects one of the five recommended jobs. The backend fetches fuller job text and passes the LinkedIn text, extracted profile, Adzuna snippet, and fuller job page text into a CV-guidance prompt. The output is not a finished resume; it is a rewrite plan with six parts: skills to highlight, experience bullets to emphasize, gaps to address honestly, a tailored summary, ATS keywords, and an action plan.

## 3. Technical choices and justification

We chose a lightweight full-stack architecture: **Next.js** for the frontend, **FastAPI** for the backend, **ChromaDB** for the vector store, **SQLite** for relational logging, **Adzuna** for live job data, and the **OpenAI API** for extraction and generation.

These choices were pragmatic. ChromaDB is appropriate because this is a content-based recommender prototype with a small to medium retrieval corpus; after the latest refresh, the local store contains **915 unique New York jobs** from live Adzuna queries and serves as the retrieval layer. SQLite is appropriate because our immediate goal is not multi-user scale, but logging recommendation sessions and selections so that later we can analyze behavior and build a learned reranker. At the moment, the local database contains only a small number of profiles, sessions, and selections, which is too small for supervised learning but already enough to validate the event schema.

We also made a deliberate choice to keep recommendation generation mostly deterministic. The top-5 jobs are not hallucinated by the LLM; they come from semantic nearest-neighbor retrieval. This reduces one major failure mode of generative systems in hiring contexts: confident but weakly grounded recommendations. The LLM is used where it adds the most value, namely abstraction of noisy input and language generation for resume guidance.

Another important design choice concerns Adzuna data. Adzuna's search API explicitly notes that it returns only a **snippet** of the job description, not the full posting ([Adzuna Search docs](https://developer.adzuna.com/docs/search)). For recommendation, that is acceptable. For resume tailoring, it is not. We therefore implemented a second-stage fetch that tries to retrieve fuller text only for the job the user actually selects.

In development, AI coding assistants were useful for scaffolding and fast iteration, but the key decisions remained manual: data flow, retrieval-versus-generation boundaries, prompt behavior, and testing.

## 4. Evaluation, responsible AI, and next steps

Our current evaluation is appropriate for a prototype, but still limited. We validated the system in four ways: end-to-end execution of the pipeline, build and import checks, manual inspection of recommendation plausibility on realistic LinkedIn text, and verification that selection events are stored in SQLite.

The right long-term evaluation metrics are not "does the demo look good?" but a combination of retrieval and product metrics. On the retrieval side, suitable metrics include **Precision@5** and qualitative fit of the retrieved roles. On the product side, suitable metrics include click-through rate, selection rate by rank position, and downstream usefulness of the generated CV guide. Our logging schema is designed to support that transition.

Responsible AI considerations are important here because the application operates close to employment decisions. The system is a decision-support tool, not an autonomous hiring filter. The CV guide explicitly encourages honest framing of missing qualifications instead of fabrication. Because copied LinkedIn text may contain personal information, production deployment would require stricter data-retention and privacy controls than our classroom prototype. We should also evaluate bias carefully before scaling, because the current job store is seeded from a limited set of keywords and the profile extractor is LLM-based.

Our next technical step is clear: keep collecting session and selection data, then use it to add a reranking layer. The reason we store `profiles`, `recommendation_sessions`, and `job_selections` in SQLite is precisely to create a future supervised-learning dataset. Once enough users interact with the system, we can estimate the probability of selection from features such as embedding similarity, role family match, salary proximity, location match, and profile-role overlap. At that stage, class concepts from data science such as logistic regression, tree-based models, or learning-to-rank would become justified. Right now, however, the data volume is too small, so a retrieval-first architecture is the correct decision.

## Assumptions

- The initial target user is a New York-based student or recent graduate applying to entry-level or early-career knowledge-work roles.
- A pasted LinkedIn profile is a realistic low-friction input because many students maintain LinkedIn before they maintain a tailored resume.
- The current seeded role families are a useful pilot scope, but not a complete labor-market representation.
- The product is being evaluated as a prototype for decision support, not as a production hiring system.

## References

- Federal Reserve Bank of New York. "The Labor Market for Recent College Graduates." Updated 2025 Q4. [https://www.newyorkfed.org/research/college-labor-market?os=__](https://www.newyorkfed.org/research/college-labor-market?os=__)
- LinkedIn. "LinkedIn Research: Nearly 80% of people feel unprepared to find a job in 2026." January 7, 2026. [https://news.linkedin.com/2026/LinkedIn-Research-Talent-2026](https://news.linkedin.com/2026/LinkedIn-Research-Talent-2026)
- LinkedIn Help. "Discover new opportunities with AI-powered job search." [https://www.linkedin.com/help/linkedin/answer/a8078917](https://www.linkedin.com/help/linkedin/answer/a8078917)
- LinkedIn Help. "AI-powered resume tips." [https://www.linkedin.com/help/linkedin/answer/a6865810](https://www.linkedin.com/help/linkedin/answer/a6865810)
- Nunley, John, Adam Pugh, Nicholas Romero, and Richard Seals. "College major, internship experience, and employment opportunities: Estimates from a resume audit." *Labour Economics* 38 (2016): 37-46. [https://econpapers.repec.org/RePEc:eee:labeco:v:38:y:2016:i:c:p:37-46](https://econpapers.repec.org/RePEc:eee:labeco:v:38:y:2016:i:c:p:37-46)
- Adzuna Developer Docs. "Search ads." [https://developer.adzuna.com/docs/search](https://developer.adzuna.com/docs/search)
