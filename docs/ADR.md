# Architecture Decision Record (ADR)

**Project:** Smart Inventory Assistant  
**Date:** March 17, 2026  
**Status:** Accepted

---

## ADR-001: Monolith vs Microservices

### Status
**Accepted**

### Context
We need to decide on the application architecture style for the Smart Inventory Assistant - a healthcare inventory management system with AI capabilities.

### Decision
We will use a **Modular Monolith** architecture with clear layer separation.

### Rationale
- **Team size:** Small team (1-3 developers) - microservices overhead unjustified
- **AI integration:** LangGraph/LangChain requires tight coupling between agent and database
- **Simplicity:** Faster development velocity, easier debugging, simpler deployment
- **Future migration:** Clear module boundaries allow extracting services later if needed

### Alternatives Rejected

| Alternative | Rejection Reason |
|-------------|------------------|
| Microservices | Overhead of service discovery, distributed tracing, network latency |
| Serverless (Lambda) | Cold start issues with LangGraph, limited control over AI inference |
| Pure Monolithic | Would lead to code entanglement; modularity ensures maintainability |

### Tradeoffs
- **Pro:** Single deployment unit, simpler CI/CD
- **Pro:** Shared database - no distributed transactions
- **Con:** Scaling requires scaling entire application
- **Con:** Fault isolation limited to module level

---

## ADR-002: SQL vs NoSQL Database

### Status
**Accepted**

### Context
We need a primary database for transactional inventory data (locations, items, transactions, requisitions).

### Decision
We will use **SQLite** for development and **PostgreSQL** for production.

### Rationale
- **Relational data:** Inventory transactions, requisitions have clear relational structure
- **ACID compliance:** Financial/stock data requires transactional integrity
- **SQLite:** Zero config, perfect for development/prototyping
- **PostgreSQL:** Proven reliability, JSON support for flexibility, production-ready

### Alternatives Rejected

| Alternative | Rejection Reason |
|-------------|------------------|
| MongoDB | No complex joins needed; overcomplicates simple schemas |
| DynamoDB | Vendor lock-in; expensive for this use case |
| NoSQL (general) | Inventory data is highly relational |

### Tradeoffs
- **Pro:** Strong consistency, complex queries
- **Pro:** Mature tooling, expertise available
- **Con:** Vertical scaling limits (addressed by PostgreSQL in prod)
- **Con:** Schema migrations required for changes

---

## ADR-003: Vector Database for AI Memory

### Status
**Accepted**

### Context
The AI chatbot needs semantic memory to recall relevant context from past conversations.

### Decision
We will use **ChromaDB** for vector storage alongside SQLite.

### Rationale
- **Semantic search:** Enables "find similar past conversations" capability
- **Local persistence:** No external service needed, simple deployment
- **LangChain integration:** Native support, minimal glue code
- **Lightweight:** Embedded mode available for production

### Alternatives Rejected

| Alternative | Rejection Reason |
|-------------|------------------|
| Pinecone | External service, cost, overkill for this scale |
| Weaviate | More complex setup, steeper learning curve |
| Elasticsearch | Heavy resource requirements |
| Skip vector store | Lose cross-session semantic recall capability |

### Tradeoffs
- **Pro:** Simple Python library, no external dependencies
- **Pro:** Enables powerful AI memory features
- **Con:** Another data store to maintain
- **Con:** Embedding model selection affects quality

---

## ADR-004: REST vs GraphQL API

### Status
**Accepted**

### Context
We need to define the API paradigm for frontend-backend communication.

### Decision
We will use **REST** APIs.

### Rationale
- **Team familiarity:** FastAPI natively supports REST
- **Simplicity:** No complex query planning, easier to cache
- **Standard practices:** Well-documented, extensive tooling
- **Frontend needs:** Not complex enough to need GraphQL's flexibility

### Alternatives Rejected

| Alternative | Rejection Reason |
|-------------|------------------|
| GraphQL | Overhead of schema definition, N+1 query risks |
| gRPC | No real-time needs, unnecessary complexity |
| WebSocket-only | Not suitable for CRUD operations |

### Tradeoffs
- **Pro:** Clear resource boundaries, HTTP caching
- **Pro:** Easy to document with OpenAPI/Swagger
- **Con:** Multiple endpoints for complex queries
- **Con:** Over-fetching in some cases (acceptable tradeoff)

---

## ADR-005: Backend Framework

### Status
**Accepted**

### Context
We need a Python web framework for the API backend.

### Decision
We will use **FastAPI**.

### Rationale
- **Performance:** Async support, one of the fastest Python frameworks
- **Type safety:** Pydantic integration, automatic OpenAPI docs
- **AI ecosystem:** Native LangChain/LangGraph compatibility
- **Developer experience:** Auto-docs, validation, dependency injection

### Alternatives Rejected

| Alternative | Rejection Reason |
|-------------|------------------|
| Django | Heavy, slower, overkill for our needs |
| Flask | Less structure, more manual wiring |
| Falcon | Smaller ecosystem, less AI library support |

### Tradeoffs
- **Pro:** Built-in async, excellent for I/O-bound operations
- **Pro:** Automatic request validation
- **Con:** Newer framework, smaller community than Django
- **Con:** Requires understanding async patterns

---

## ADR-006: Frontend Stack

### Status
**Accepted**

### Context
We need a frontend framework for the management UI.

### Decision
We will use **React + Vite + Tailwind CSS**.

### Rationale
- **React:** Industry standard, large ecosystem
- **Vite:** Fast dev server, optimized builds
- **Tailwind:** Rapid UI development, consistent styling
- **Team knowledge:** Familiar to most developers

### Alternatives Rejected

| Alternative | Rejection Reason |
|-------------|------------------|
| Vue.js | Less market share, smaller ecosystem |
| Angular | Overcomplicated for our needs |
| Svelte | Smaller job market, less libraries |
| Plain HTML/jQuery | Not maintainable at scale |

### Tradeoffs
- **Pro:** Large community, abundant resources
- **Pro:** Component reusability
- **Con:** JavaScript fatigue, many choices to make
- **Con:** Client-side only (SEO concern, not relevant here)

---

## ADR-007: AI Provider

### Status
**Accepted**

### Context
We need an LLM provider for the AI chatbot agent.

### Decision
We will use **Groq** (OpenAI-compatible endpoint) as the primary provider.

### Rationale
- **Speed:** Groq provides fast inference for real-time chat
- **Compatibility:** OpenAI-compatible API, minimal code changes
- **Cost:** Competitive pricing
- **Fallback:** Can swap to OpenAI/Anthropic if needed

### Alternatives Rejected

| Alternative | Rejection Reason |
|-------------|------------------|
| OpenAI (direct) | Higher latency, cost concerns |
| Anthropic | No direct LangChain integration at time of decision |
| Local LLM | Hardware requirements, latency issues |
| Ollama | Not suitable for production real-time use |

### Tradeoffs
- **Pro:** Fast inference, low latency
- **Pro:** Easy to switch providers
- **Con:** Dependency on external API
- **Con:** Rate limits, availability concerns

---

## ADR-008: Speech-to-Text

### Status
**Accepted**

### Context
We need speech-to-text for voice input to the AI chatbot.

### Decision
We will use **Sarvam AI** for speech transcription.

### Rationale
- **Indian languages:** Specifically designed for Indian language speech
- **Translation:** Translates to English automatically
- **API simplicity:** Easy integration, good documentation

### Alternatives Rejected

| Alternative | Rejection Reason |
|-------------|------------------|
| Whisper (OpenAI) | Doesn't translate, higher cost |
| Google Cloud STT | Expensive, complex setup |
| AWS Transcribe | Vendor lock-in |

### Tradeoffs
- **Pro:** Multi-language support, translation built-in
- **Con:** External dependency
- **Con:** Limited to Indian languages coverage

---

## Summary

| Decision | Choice |
|----------|--------|
| Architecture | Modular Monolith |
| Primary Database | SQLite → PostgreSQL |
| Vector Database | ChromaDB |
| API Style | REST |
| Backend Framework | FastAPI |
| Frontend | React + Vite + Tailwind |
| LLM Provider | Groq |
| Speech-to-Text | Sarvam AI |
