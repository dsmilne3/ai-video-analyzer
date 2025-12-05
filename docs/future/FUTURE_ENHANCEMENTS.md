# AI Video Analyzer - Future Enhancements

This document describes features and architectural changes that would be valuable for **scaled deployments**, **multi-user environments**, or **enterprise use cases**. These are not needed for the current local/small-team implementation but are documented here for future reference.

> **Note**: The current JSON file-based architecture is perfectly adequate for local deployment and small teams. These enhancements should only be considered when the use case genuinely requires them.

---

## When to Consider These Enhancements

| Trigger                                   | Consider                         |
| ----------------------------------------- | -------------------------------- |
| Multiple concurrent users editing rubrics | Database Backend                 |
| Need to query across 100+ evaluations     | Database Backend                 |
| Non-technical users creating rubrics      | AI-Powered Rubric Creation       |
| Deploying to cloud for remote access      | Containerization, Infrastructure |
| Need operational visibility at scale      | Observability (Grafana/Alloy)    |
| Building integrations with other systems  | API Development                  |
| Regulatory/compliance requirements        | Audit logging, PII detection     |

---

## Database Backend (SQLite/PostgreSQL)

**When needed**: Multiple concurrent users, complex queries across evaluations, audit requirements

### Schema Design

- [ ] **Database Schema**: Design normalized schema for rubrics, evaluations, scores, overrides, and audit history
- [ ] **Rubrics Table**: Store rubric definitions with versioning (rubric_id, version, name, description, categories JSON, thresholds, created_at, updated_at, status)
- [ ] **Evaluations Table**: Store analysis results (evaluation_id, submitter info, source_file, rubric_id, transcript, quality_metrics, overall_score, pass_status, created_at)
- [ ] **Scores Table**: Store individual criterion scores (score_id, evaluation_id, criterion_id, ai_score, confidence, note)
- [ ] **Overrides Table**: Audit trail for score modifications (override_id, score_id, original_score, override_score, reason, override_by, override_timestamp)
- [ ] **Audit Log Table**: Track all significant actions (log_id, action_type, entity_type, entity_id, user, timestamp, details JSON)

### Data Access Layer

- [ ] **Repository Pattern**: Create `RubricRepository`, `EvaluationRepository`, `OverrideRepository` classes to abstract database operations
- [ ] **Migration System**: Use Alembic or similar for database schema migrations
- [ ] **SQLite for Development**: Default to SQLite file (`data/video_analyzer.db`) for easy local development
- [ ] **PostgreSQL for Production**: Support PostgreSQL via connection string for production deployments

### Migration from JSON Files

- [ ] **Import Script**: Create script to migrate existing `rubrics/*.json` files to database
- [ ] **Results Migration**: Import existing `results/*.json` files preserving all data including overrides
- [ ] **Backward Compatibility**: Support reading from both JSON and database during transition period

### Features Enabled by Database

- [ ] **Query Override History**: View all overrides across evaluations, filter by reviewer, date range, or criterion
- [ ] **Rubric Usage Analytics**: Track which rubrics are used most, average scores per rubric
- [ ] **Submitter History**: View all evaluations for a submitter/partner over time
- [ ] **Score Trend Analysis**: Analyze score patterns across evaluations to identify common weaknesses
- [ ] **Full-Text Search**: Search transcripts and feedback across all evaluations

### Dependencies

- SQLite (built-in) for development
- PostgreSQL + psycopg2/asyncpg for production
- Alembic for migrations

---

## AI-Powered Rubric Creation (Natural Language)

**When needed**: Non-technical users creating rubrics, high rubric creation frequency, complex rubric requirements

### Core Functionality

- [ ] **Conversational Rubric Builder**: Replace form-based creation with chat interface where users describe rubrics in natural language
- [ ] **System Prompt Design**: Create robust prompt that understands rubric schema, asks clarifying questions, and outputs valid JSON
- [ ] **Iterative Refinement**: Support follow-up requests like "add a section for objections handling" or "increase weight of communication skills"
- [ ] **Live Preview Panel**: Show rubric structure updating in real-time as conversation progresses
- [ ] **Validation Layer**: Auto-validate AI output (weights sum to 1.0, points match, valid schema) before presenting to user

### Smart Features

- [ ] **Template References**: "Create a rubric like sales-demo but for technical deep-dives" — AI adapts existing rubrics
- [ ] **Clarifying Questions**: AI asks "What does excellent look like for product knowledge?" to improve criteria descriptions
- [ ] **Conflict Detection**: Warn when criteria may conflict (e.g., "brevity" and "thoroughness" both weighted highly)
- [ ] **Example Generation**: Generate sample scores showing what 3/10 vs 8/10 looks like for each criterion

### UI/UX

- [ ] **Split-Pane Interface**: Chat panel on left, rubric preview on right
- [ ] **Diff View**: Show changes between iterations with highlighted additions/removals
- [ ] **Manual Override Escape Hatch**: "Switch to manual editor" button pre-populates form with AI draft
- [ ] **Conversation History**: Save chat history with rubric for audit trail and future reference

### Conversation State Machine

- [ ] **State Management**: Track states (initial_description → clarifying → draft_review → refinement → finalization)
- [ ] **Context Preservation**: Maintain full conversation history for coherent multi-turn refinement
- [ ] **Approval Workflow**: Require explicit "Looks good, save it" before persisting to repository

### Integration

- [ ] **Database Storage**: Save to PostgreSQL with generation_method='ai', original_prompt, conversation_history
- [ ] **Regenerate from Prompt**: Enable "recreate from original description" for existing AI-generated rubrics
- [ ] **Fallback to Manual**: Keep existing form-based creation as "Advanced" option for power users

### Dependencies

- Uses existing OpenAI/Anthropic keys
- Recommend GPT-4o-mini or Claude Haiku for cost-effective iteration

---

## Observability (Grafana Cloud via Alloy)

**When needed**: Production deployment, operational visibility requirements, performance optimization

### Auto-Instrumentation

Install packages and run with `opentelemetry-instrument`:

- [ ] **OpenTelemetry Setup**: Install `opentelemetry-distro`, `opentelemetry-exporter-otlp` and configure OTLP export to Grafana Alloy
- [ ] **OpenAI Tracing**: Add `opentelemetry-instrumentation-openai` for automatic tracing of GPT API calls (latency, tokens, model)
- [ ] **Anthropic Tracing**: Add `opentelemetry-instrumentation-httpx` to trace Claude API calls via httpx client
- [ ] **HTTP Client Tracing**: Add `opentelemetry-instrumentation-requests` and `opentelemetry-instrumentation-urllib3` for general HTTP observability
- [ ] **Grafana Alloy Collector**: Deploy Alloy as local collector to receive OTLP, enrich with resource attributes, and forward to Grafana Cloud (Tempo for traces, Mimir for metrics, Loki for logs)

### Manual Instrumentation Required

- [ ] **Whisper Transcription Spans**: Add manual spans around `whisper_model.transcribe()` calls to track transcription duration, model used, device (CPU/MPS), and audio length
- [ ] **Video Processing Spans**: Instrument `_extract_audio_from_video()` and `_extract_frames()` with manual spans for ffmpeg/OpenCV operations
- [ ] **Rubric Evaluation Spans**: Add spans around `evaluate_transcript_with_rubric()` to track evaluation time per category/criterion
- [ ] **Custom Metrics**: Create counters for videos_analyzed, evaluations_passed/failed, api_calls_by_provider; histograms for transcription_duration, evaluation_duration
- [ ] **Structured Logging**: Replace print statements with `logging` module configured to emit JSON logs; forward to Loki via Alloy

### Grafana Cloud Dashboards

- [ ] **Application Dashboard**: Build Grafana dashboard showing analysis throughput, latency percentiles (p50/p95/p99), error rates, and LLM token usage
- [ ] **Cost Tracking Dashboard**: Visualize API costs over time using token metrics from OpenAI/Anthropic instrumentation

### Dependencies

- Grafana Cloud account (free tier available)
- Alloy binary or container

---

## Infrastructure & Deployment

**When needed**: Remote users, team distribution, production deployment

### Containerization

- [ ] **Dockerfile**: Create production-ready Dockerfile with Whisper model pre-downloaded
- [ ] **docker-compose.yml**: Multi-container setup (app + optional PostgreSQL + optional Alloy)
- [ ] **GPU Support**: Document nvidia-docker setup for CUDA acceleration
- [ ] **Health Checks**: Implement proper health check endpoints

### Cloud Deployment Options

- [ ] **AWS EC2 with GPU**: Document g4dn.xlarge deployment with auto-stop for cost savings
- [ ] **Mac Mini Deployment**: Document always-on deployment with Cloudflare Tunnel for remote access
- [ ] **Serverless GPU**: Explore Modal/RunPod for pay-per-second transcription

### Configuration Management

- [ ] **Environment-based Config**: Support different configurations for dev/staging/prod
- [ ] **Secrets Management**: Document AWS Secrets Manager, HashiCorp Vault integration
- [ ] **Feature Flags**: Implement feature flags for gradual rollout of new features

---

## API & Integration

**When needed**: External system integration, programmatic access, automation

### REST API

- [ ] **API Development**: Create FastAPI/Flask endpoints for programmatic access to evaluation results
- [ ] **Authentication**: Implement API key or OAuth2 authentication
- [ ] **Rate Limiting**: Add rate limiting for API endpoints
- [ ] **Webhook Support**: Send notifications when evaluations complete

### Dashboard Integration

- [ ] **Web Dashboard**: Build separate dashboard for trend analysis and score visualization
- [ ] **Embedding**: Allow embedding evaluation results in other applications
- [ ] **Export Formats**: Support CSV, Excel, PDF export of results

### Automated Workflows

- [ ] **Automated Reporting**: Generate weekly/monthly summary reports and email stakeholders
- [ ] **CI/CD Integration**: Trigger evaluations from CI/CD pipelines
- [ ] **Slack/Teams Integration**: Post evaluation summaries to chat channels

---

## Advanced Translation

**When needed**: International users, multi-language feedback requirements

- [ ] **Multi-Language Translation**: Implement GPT/Claude translation for languages other than English
- [ ] **Native Language Feedback**: Generate feedback in submitter's native language
- [ ] **Translation Options**: Add support for dedicated translation libraries (deep-translator, argostranslate)

---

## Production ASR

**When needed**: Higher accuracy requirements, speaker diarization, enterprise SLAs

- [ ] **Production ASR Integration**: Integrate AssemblyAI/Deepgram for production-grade ASR with diarization
- [ ] **Speaker Identification**: Track who said what in multi-speaker videos
- [ ] **Real-time Transcription**: Support live video evaluation

### Dependencies

- AssemblyAI or Deepgram API accounts
- Additional API costs

---

## Low Priority Enhancements

These are nice-to-have features that could improve user experience but aren't critical for core functionality.

- [ ] **Enable per-user rubric defaults**: Allow users to set and persist their preferred default rubric across sessions, with unique defaults per user in multi-user environments.
- [ ] **Track override authors**: Record who made score overrides for audit purposes in multi-user scenarios.

---

## Implementation Priority

When you're ready to implement these features, consider this order:

1. **Containerization** — Enables all other deployment options
2. **Database Backend** — Required for multi-user and advanced queries
3. **API Development** — Enables integrations and automation
4. **Observability** — Important for production operations
5. **AI Rubric Creation** — Nice-to-have for user experience
6. **Advanced Translation** — Only if international users are a priority

---

_Last Updated: December 1, 2025_
