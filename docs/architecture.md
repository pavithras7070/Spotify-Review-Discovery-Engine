# Architecture: AI-Powered Review Discovery Engine

This document outlines the detailed, phase-wise architecture for building the Review Discovery Engine, based on the objectives and requirements outlined in the Problem Statement.

---

## 🏗️ Phase 1: Data Ingestion & Aggregation

**Goal:** Establish reliable data pipelines to continuously collect user feedback from diverse public channels.

*   **Components:**
    *   **App Store Scrapers/APIs:** Integration with Apple App Store API and Google Play Developer API to fetch user reviews, ratings, and app versions.
    *   **Social Listening Agents:** 
        *   Reddit API integration (listening to subreddits like r/spotify, r/truespotify).
        *   Web scraping modules for community forums (Spotify Community).
        *   Social media firehose APIs (e.g., X/Twitter APIs) for broader conversations.
    *   **Ingestion Queue:** A message broker (e.g., Apache Kafka, AWS SQS) to handle high-throughput incoming text streams without dropping data.
    *   **Raw Data Lake:** Cloud storage (e.g., AWS S3, Google Cloud Storage) to dump raw, unprocessed JSON/text blobs for archival and replayability.

## 🧹 Phase 2: Data Pre-processing & Normalization

**Goal:** Clean, deduplicate, and standardize the raw text for AI consumption.

*   **Components:**
    *   **Data Cleaner:** Scripts to remove boilerplate text, emojis (if irrelevant), PII (Personal Identifiable Information), and spam bots.
    *   **Deduplication Engine:** Hashing and similarity algorithms (e.g., MinHash, Locality-Sensitive Hashing) to remove duplicate posts (e.g., identical complaints spammed across forums).
    *   **Metadata Extractor:** Standardizes timestamps, source platforms, user handles (anonymized), and associated ratings.
    *   **Structured Database (Staging):** Relational or NoSQL database (e.g., PostgreSQL, MongoDB) to hold the clean, structured text ready for analysis.

## 🧠 Phase 3: Advanced NLP & AI Analysis Engine

**Goal:** Transform structured text into semantic insights using Large Language Models (LLMs) and NLP techniques. We will be using the **Groq API** (specifically `llama-3.3-70b-versatile`) for incredibly fast inference.

*   **API Constraints & MVP Scope:** 
    *   To respect the Groq free-tier limits (30 RPM, 12K TPM, 100K TPD), the MVP will process a capped subset of **1,000 reviews**.
    *   The pipeline implements **batching** (sending multiple reviews per prompt) and **exponential backoff** (`tenacity`) to gracefully handle rate-limits without crashing.

*   **Components:**
    *   **Sentiment Analysis Module:** Classifies the emotional tone of the feedback (Positive, Neutral, Negative, Frustrated, Delighted) using Groq.
    *   **Topic Modeling & Clustering:** Utilizes vector embeddings and clustering algorithms (e.g., HDBSCAN) to group similar feedback (e.g., "algorithm is repetitive", "keep hearing the same songs").
    *   **Theme & Entity Extraction:** Identifies specific features mentioned (e.g., "Discover Weekly", "Release Radar", "Shuffle button") using Groq.
    *   **User Segmentation Tagger:** Heuristics and ML classifiers to estimate user persona (e.g., "Casual Listener" vs. "Power User") based on the vocabulary and depth of the review.

## 🔬 Phase 4: Insight Synthesis & Storage

**Goal:** Aggregate the granular NLP outputs into high-level, actionable product insights.

*   **Components:**
    *   **Insight Synthesizer:** An LLM-powered summarization pipeline (using **Groq**) that reads clusters of feedback and generates human-readable summaries (e.g., "Users feel Discover Weekly has become an echo chamber over the last 3 months").
    *   **Evidence Linking:** Maps the generated insights back to the most representative, high-quality user quotes for evidence.
    *   **Vector Database:** A specialized database (e.g., Pinecone, Weaviate, Milvus) to store embeddings of reviews and insights, enabling semantic search.
    *   **Analytical Data Warehouse:** A columnar database (e.g., Snowflake, Google BigQuery) to store aggregated metrics (e.g., sentiment trends over time, volume of complaints per feature).

## 💻 Phase 5: Knowledge Base & Presentation Layer

**Goal:** Provide an interactive, explorable interface for product managers and researchers.

*   **Components:**
    *   **Search & Query API:** A backend service (Node.js/Python FastAPI) that translates user queries into vector searches or SQL queries.
    *   **Dashboard UI:** A modern web application (React/Next.js) featuring:
        *   **Trend Graphs:** Visualizing sentiment and topic volume over time.
        *   **Insight Cards:** Highlighting top recurring pain points and feature requests.
        *   **Semantic Search Bar:** Allowing researchers to ask natural language questions (e.g., "Why do users dislike the new home feed?").
        *   **Quote Explorer:** A drill-down view to see the raw user feedback supporting a specific insight.

## 🚀 Phase 6: Cloud Deployment & Hosting

**Goal:** Make the MVP accessible to external stakeholders and evaluators via a public URL.

*   **Components:**
    *   **Version Control (GitHub):** The codebase, alongside the pre-processed `staging.db` database, is hosted in a public Git repository. Environment variables and API keys are strictly excluded.
    *   **Streamlit Community Cloud:** A PaaS (Platform as a Service) environment that directly links to the GitHub repository. It installs dependencies from the root `requirements.txt` and automatically rebuilds the dashboard upon new commits.
    *   **Secrets Management:** API keys for the Groq LLM are securely injected into the Streamlit cloud environment at runtime via the Streamlit Secrets manager (TOML format), completely bypassing version control.

---

## 📐 High-Level Architecture Diagram Flow

`[External Sources]` ➡️ `[Ingestion Queue]` ➡️ `[Raw Data Lake]` 
⬇️
`[Pre-processing Worker]` ➡️ `[Staging DB]`
⬇️
`[NLP / LLM Engine (Embeddings, Sentiment, Clustering)]` 
⬇️
`[Vector DB]` & `[Analytical Data Warehouse]`
⬇️
`[Backend API]` ➡️ `[Frontend Knowledge Base UI]` ➡️ `[Streamlit Cloud (Public URL)]`
