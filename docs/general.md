# File Entity and Document Architecture

The File concept is introduced to simplify DEPS architecture and reduce hard dependencies between services.
Historically, many flows were tightly coupled around Documents, which increased cross-service complexity and made changes expensive.

## Overview

A **File** is a primary entity that can later become either:

- a **Document** (after successful classification and document type assignment), or
- part of a **Batch** (after splitting).

This model allows groups and batches to work with files directly and remain independent from document lifecycle details.

## Core Rule

A **Document must always have a document type**.

- If an entity has a document type, it is a Document.
- If an entity has no document type, it is treated as a File.
- A document without a document type is invalid by design.

## Why This Change Was Introduced

The previous dependency graph between services became difficult to maintain due to many direct integrations.
Introducing File as a first-class concept helps to:

- reduce dependency density between services,
- decouple Group and Batch subdomains from Document internals,
- support flexible processing before document typing is known,
- make lifecycle transitions explicit and easier to reason about.

## File Lifecycle Scenarios

### 1) Upload for Classification

1. A file is uploaded for classification.
2. Classification tries to determine the document type.
3. If classification succeeds, the file becomes a document.
4. If classification fails, it remains a file.

### 2) Upload for Splitting

1. A file is uploaded for splitting.
2. Splitting produces a batch of files.
3. Resulting entities continue through batch-oriented flows.

### 3) Upload for Layout/Unifier Analysis

1. A file is uploaded without a predefined document type.
2. The system can inspect layout, run unifier logic, and collect signals.
3. Based on output, downstream systems decide whether and how to continue processing.

## Subdomain Ownership

File belongs to the Batch and Group processing context and is suitable for large-object operations.
This allows groups to operate independently and avoids forcing early document typing.

## Processing Model

There are two valid entity states for processing:

1. **Document (typed)**
	- Has a document type.
	- Uses extraction-oriented flow.
	- Supports plugin-based processing.
	- Supports splitting when needed by business flow.

2. **File (untyped)**
	- Has no document type.
	- Designed for large-object operations (batches, groups, splitting).
	- Can later become a typed document after successful classification.

## Architectural Goal

The main goal is to improve document architecture by clearly separating typed and untyped entities:

- typed entities are strict Documents,
- untyped entities are Files,
- transitions are controlled and explicit,
- dependencies between services are reduced,
- processing becomes more flexible and maintainable.

## Difference Between File and Document

| Aspect | File | Document |
|---|---|---|
| Document type | Not assigned | Always assigned (required) |
| Valid without document type | Yes | No |
| Typical operations | Grouping, batching, splitting, pre-typing analysis | Extraction, plugin-based typed processing, splitting |
| Classification result | May remain file if classification fails | Appears only after successful typing |
| Architectural role | Flexible pre-document entity | Strict typed business entity |

**Important:** a document cannot exist without a document type. If document type is missing, the entity is a file.

