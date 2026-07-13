# HousePhotoMapper

## Detailed Implementation Plan

---

# Phase 0 – Project Setup

Duration: 1 day

Tasks

* Create Git repository.
* Configure Python 3.12.
* Configure virtual environment.
* Install dependencies.
* Configure Ruff, Black, MyPy.
* Configure pre-commit hooks.
* Configure GitHub Actions CI.
* Create project structure.

Deliverables

* Clean repository
* CI pipeline
* Coding standards

---

# Phase 1 – Core Architecture

Modules

app/

core/

models/

graphics/

io/

ui/

services/

export/

tests/

Goals

* MVVM architecture
* Dependency injection where appropriate
* Event bus using Qt signals/slots
* Central project model
* Undo/Redo framework

Deliverables

Working application skeleton.

---

# Phase 2 – PDF Engine

Libraries

PyMuPDF

Features

* Import PDF
* Multi-page support
* Render pages to pixmaps
* Page thumbnails
* Zoom
* Pan
* Rotation
* Caching of rendered tiles
* Lazy loading for large PDFs

Deliverables

Interactive floor-plan viewer.

---

# Phase 3 – Photo Manager

Features

* Folder import
* Drag & Drop
* Thumbnail generation
* Thumbnail cache
* EXIF extraction
* Metadata database
* Duplicate detection (SHA-256 hash)
* Recursive folder scanning

Deliverables

Photo browser with filtering and sorting.

---

# Phase 4 – Graphics Layer

Use

QGraphicsScene

Custom Graphics Items

CameraMarkerItem

ArrowItem

ViewingConeItem

VisibleAreaItem

LabelItem

Each item supports

Selection

Dragging

Rotation

Serialization

Undo

Redo

Snap-to-grid (optional)

Deliverables

Fully editable vector annotations.

---

# Phase 5 – Annotation Workflow

Workflow

Select photo

↓

Select plan

↓

Click camera location

↓

Drag orientation

↓

Adjust cone

↓

Enter title

↓

Save

Shortcuts

Space

Enter

Ctrl+Z

Ctrl+Y

Deliverables

Optimized annotation workflow.

---

# Phase 6 – Project Persistence

Project format

JSON

Referenced assets remain external by default.

Include

Project metadata

Plan references

Photo references

Annotations

Export configuration

Window layout

Autosave state

Future option

Single-file package (.hpm ZIP archive containing JSON and copied assets).

Deliverables

Robust save/open functionality.

---

# Phase 7 – PDF Report Generator

Library

ReportLab

Features

Automatic pagination

Page templates

Image scaling

High-resolution rendering

Vector annotation rendering

Headers

Footers

Page numbering

Index

Table of contents

Deliverables

Professional PDF reports.

---

# Phase 8 – User Interface

Main Window

Menu Bar

Toolbar

Status Bar

Dock Widgets

Left

Project Explorer

Photo Browser

Center

Plan Viewer

Right

Properties Panel

Bottom

Log Panel

Progress Bar

Deliverables

Complete desktop interface.

---

# Phase 9 – Performance Optimization

Implement

Background thumbnail generation

Background PDF rendering

Thread pool

Memory cache

Disk cache

Tile rendering

Lazy loading

Performance target

1000 photos

100 pages

<100 ms viewport interaction

Deliverables

Responsive application under large workloads.

---

# Phase 10 – Testing

Unit Tests

Serialization

Geometry calculations

Import

Export

Integration Tests

Large projects

PDF generation

Undo/Redo

UI Tests

Mouse interactions

Keyboard shortcuts

Drag & Drop

Regression Tests

Reference projects

Golden PDF comparison

Deliverables

Automated test suite with high coverage for core modules.

---

# Phase 11 – Packaging

Windows

PyInstaller

Deliverables

Single executable

Installer

Desktop icon

File associations

Automatic updates (future)

---

# Phase 12 – Documentation

Developer Guide

Architecture

Code style

Module documentation

API documentation

User Guide

Installation

Quick Start

Keyboard shortcuts

Troubleshooting

FAQ

Deliverables

Complete developer and user documentation.

---

# Future Roadmap

## Version 1.1

* Room polygons
* Room names
* Color themes
* Custom report templates
* Annotation templates

## Version 1.2

* AI-assisted camera placement
* Automatic room detection
* Automatic photo grouping
* Semantic search
* Smart annotation suggestions

## Version 2.0

* IFC support
* Revit integration
* AutoCAD integration
* Cloud synchronization
* Multi-user collaboration
* Version history
* Web viewer
* 3D navigation
* Panoramic image support

---

# Recommended Technology Stack

Language

* Python 3.12+

GUI

* PySide6 (Qt)

PDF Processing

* PyMuPDF

Image Processing

* Pillow
* OpenCV (optional)

Report Generation

* ReportLab

Persistence

* JSON
* SQLite (optional metadata cache)

Testing

* pytest
* pytest-qt

Formatting & Linting

* Black
* Ruff
* MyPy

Packaging

* PyInstaller

CI/CD

* GitHub Actions

Version Control

* Git

---

# Success Criteria

* Annotate a photo in fewer than 10 seconds after import.
* Handle projects containing at least 1,000 photos and 100 plan pages.
* Produce print-ready PDF reports with editable vector overlays.
* Maintain stable performance during extended annotation sessions.
* Support future AI-assisted workflows without requiring major architectural changes.
