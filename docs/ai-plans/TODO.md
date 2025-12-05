# AI Video Analyzer - Todo List

Enhancements for the current local implementation. For scaled/enterprise features (database backend, containerization, observability, etc.), see [FUTURE_ENHANCEMENTS.md](FUTURE_ENHANCEMENTS.md).

---

## High Priority

### Code Quality & Refactoring

- [ ] **Refactor Rubric Loading**: Extract `load_rubric_safely()` helper function to eliminate duplication across Home.py, 3_View_Rubric.py, and 5_Import_Rubric.py
- [ ] **Create Metric Display Component**: Build `display_rubric_metrics()` component for consistent 3-column metric layouts used in multiple files
- [ ] **Extract Category Display Logic**: Create `display_categories_criteria()` component for category/criteria display logic in 3_View_Rubric.py and 3_View_Edit_Rubric.py
- [ ] **Implement Save Helper**: Add `save_rubric_with_feedback()` helper for validation/saving pattern across 4 files (4_Create_Rubric.py, 5_Import_Rubric.py, 6_Edit_Rubric.py, rubric_helper.py)
- [ ] **Session State Management**: Create `initialize_undo_state()` helper for session state management in 3_View_Edit_Rubric.py and 6_Edit_Rubric.py
- [ ] **Statistics Calculation**: Extract `calculate_rubric_stats()` function for statistics calculations used in multiple locations

### UI/UX Improvements

- [ ] **Loading States**: Implement spinners and progress bars for long-running operations like video processing
- [ ] **Enhanced Error Handling**: Create user-friendly error messages with actionable guidance instead of technical stack traces
- [ ] **Data Visualization**: Use charts and graphs for evaluation results instead of plain text output
- [ ] **Search & Filter**: Allow users to search through rubrics and filter evaluation results
- [ ] **Theming Support**: Implement dark/light mode toggle and consistent color schemes
- [ ] **Data Loss Prevention**: Implement change detection and warnings for rubric editing to prevent loss of unsaved form changes when structural modifications trigger page reruns

### Performance

- [ ] **Streamlit Caching**: Use `@st.cache_data` for expensive operations like rubric loading and validation to improve performance

---

## Medium Priority

### Core Features

- [ ] **Score Override System**: Allow reviewers to manually adjust AI-generated scores with audit trail and save/load presets
- [ ] **Escalation Hook**: Auto-route to paid APIs based on confidence thresholds (< 80% average confidence)
- [ ] **Cost Estimator**: Add usage tracking and cost estimation for API calls
- [ ] **PII Detection & Redaction**: Add PII detection and redaction for privacy compliance

### Quality Improvements

- [ ] **Advanced Vision Analysis**: Enhance multimodal alignment checks with better frame analysis
- [ ] **Transcription Quality Improvements**: Add word-level confidence scoring and better error detection
- [ ] **Calibration Dataset**: Build calibration dataset for model tuning and accuracy improvement

### User Experience

- [ ] **Progress Indicators**: Improve progress reporting for long-running evaluations
- [ ] **Result Comparison**: Add tools to compare results across multiple runs
- [ ] **JSON Export**: Re-enable JSON export button for easier data portability

---

## Low Priority (Nice to Have)

- [ ] **Accessibility Features**: Ensure proper ARIA labels, keyboard navigation, and screen reader support
- [ ] **Keyboard Shortcuts**: Add hotkeys for common actions like saving, undo, and navigation

---

## Completed ✅

- [x] Local Whisper transcription (free, privacy-preserving)
- [x] Rubric scoring with JSON output
- [x] Multimodal alignment checks
- [x] Auto-summaries and highlights
- [x] CLI and web UI (Streamlit)
- [x] Multiple evaluation rubrics
- [x] Qualitative feedback generation
- [x] Auto-save results with timestamps
- [x] URL support (YouTube, Vimeo, direct links)
- [x] Translation to English (Whisper-based)
- [x] Transcription quality metrics
- [x] Pagination for long CLI outputs
- [x] Progress reporting in UI terminal
- [x] Wide layout for results page
- [x] Separate results view after analysis

---

## Notes

- **Architecture**: Local-first design with JSON file storage — simple and effective for current use case
- **Cost Optimization**: Free local components (Whisper, ffmpeg) with optional paid API escalation
- **Future Scaling**: See [FUTURE_ENHANCEMENTS.md](FUTURE_ENHANCEMENTS.md) for database, containerization, and cloud deployment options

---

_Last Updated: December 4, 2025_
