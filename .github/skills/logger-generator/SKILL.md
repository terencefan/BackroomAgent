---
name: logger-generator
description: Generates production-grade, high-availability logging modules for any programming language (Python, TypeScript, Go, etc.). Enforces best practices like rotation, formatting, and minimal dependencies.
---

# Logger Generator Skill

This skill guides the creation of robust, "out-of-the-box" logging utilities for any software project. It ensures that generated logging modules meet production standards for observability, reliability, and ease of use, regardless of the target programming language.

## When to Use This Skill

Use this skill when:
- Setting up a new project (Python, Node.js, Go, Rust, etc.) and need a reliable logger.
- Replacing simple `print` or `console.log` statements with a proper logging system.
- The user asks for a "logging module", "log util", or "logger setup".
- You need to standardize log collection across different services in a polyglot repository.

## Core Requirements Checklist

Any logger generated using this skill MUST satisfy the following criteria unless explicitly overridden:

1.  **Stand-alone Module**: Must be a single, portable file (e.g., `logger.py`, `logger.ts`, `logger.go`).
2.  **Dual Channel Output**:
    - **Console**: With COLOR coding for log levels (Human readable).
    - **File**: Plain text, structured, standard encoding (Machine readable).
3.  **Complete Log Levels**: `DEBUG`, `INFO`, `WARN/WARNING`, `ERROR`, `FATAL/CRITICAL`.
4.  **Standardized Format**:
    - Timestamp (ISO-like or `YYYY-MM-DD HH:MM:SS.mmm`).
    - Log Level (Aligned).
    - Source Location (File + Line Number).
    - Component/Module Name.
    - Message.
5.  **Log Rotation**:
    - Automatic rotation (Time-based/Daily or Size-based).
    - Automatic cleanup (Retention policy, e.g., keep last 30 days).
6.  **Configuration**:
    - Support default "Zero Config" (Global Singleton).
    - Support custom instances (Configurable paths, levels).
    - Support UTF-8/Unicode characters specifically.
7.  **Robustness**:
    - Thread-safe / Async-safe where applicable.
    - No external dependencies if possible (prefer Standard Lib). If external libs are needed (e.g., Node.js), minimize them.
8.  **Traceability**:
    - Error logs must support printing Stack Traces / Tracebacks.

## Language-Specific Implementation Guides

### Python
- **Library**: `logging` (Standard Lib).
- **Rotation**: `logging.handlers.TimedRotatingFileHandler`.
- **Colors**: ANSI escape codes in a custom `logging.Formatter`.
- **Pattern**: Singleton instance with `getLogger()`.

### TypeScript / Node.js
- **Library**: Prefer `winston` for robust features, or a custom wrapper around `fs` + `console` for zero-dependency needs.
- **Rotation**: `winston-daily-rotate-file` (if using winston).
- **Colors**: `chalk` or simple ANSI codes.
- **Pattern**: Export a `Logger` class and a default `logger` instance.

### Go (Golang)
- **Library**: `log/slog` (Standard Lib > 1.21) or `zap` (High perf).
- **Rotation**: Go stdlib does not rotate. Use `gopkg.in/natefinch/lumberjack.v2` for file rotation.
- **Pattern**: `MultiWriter` for splitting output to `os.Stdout` and file.

## Example Output Format
```text
2024-03-20 10:15:30.123 | INFO     | main.py:45       | auth_service | Server started on port 8080
2024-03-20 10:15:32.456 | ERROR    | db.py:102        | db_pool      | Connection failed (Retrying...)
```

## Generation Protocol

1.  **Identify Language**: Confirm the target language (Python, TS, Go, etc.).
2.  **Select Strategy**: Choose between "Standard Library Only" (preferred for simple scripts) or "Industry Standard Package" (preferred for large apps).
3.  **Generate Code**: Write the module implementing the [Core Requirements Checklist].
4.  **Verify**: Ensure usage examples cover:
    - Basic usage (Global logger).
    - Configuration (Custom file paths).
    - Exception handling (Try-Catch logging).
