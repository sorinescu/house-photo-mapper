# HousePhotoMapper

## Product Requirements Document (PRD)

**Version:** 1.0
**Status:** Draft
**Author:** OpenAI + Project Owner

---

# 1. Overview

HousePhotoMapper is a desktop application that enables users to correlate photographs of a building (interior and exterior) with 2D architectural plans.

The application allows the user to:

* Import one or more architectural plans (PDF).
* Import a large collection of photographs.
* Place each photo on the appropriate floor plan.
* Specify the camera position and viewing direction.
* Automatically generate a professional documentation report in PDF (and later DOCX).

The target audience includes:

* Homeowners
* Architects
* Surveyors
* Building inspectors
* Insurance companies
* Property managers
* Construction companies

---

# 2. Goals

## Primary Goals

* Minimize the time required to document a building.
* Produce professional reports.
* Avoid manual editing in PowerPoint or Word.
* Preserve all annotations in editable form.
* Support projects with hundreds of photos.

## Secondary Goals

* AI-assisted photo positioning.
* Room recognition.
* Automatic metadata extraction.
* Future BIM integration.

---

# 3. User Stories

### Import Plans

As a user,

I want to import architectural plans in PDF format,

so I can annotate them.

---

### Import Photos

As a user,

I want to import hundreds of photos simultaneously,

so I don't need to add them one by one.

---

### Annotate Photos

As a user,

I want to click on a plan to indicate camera position,

so the report accurately shows where the picture was taken.

---

### Define Orientation

As a user,

I want to drag an arrow,

so the viewing direction is clearly visible.

---

### Export Report

As a user,

I want a professional PDF generated automatically,

so I don't need desktop publishing software.

---

### Save Project

As a user,

I want to save and reopen my work,

so I can continue later.

---

# 4. Functional Requirements

## FR-1 Project Management

The application shall:

* Create a project.
* Open a project.
* Save a project.
* Save As.
* Auto-save.

---

## FR-2 Plan Import

Supported formats:

* PDF
* PNG
* JPG
* TIFF (optional)

Features:

* Multiple floor plans.
* Multiple pages.
* Zoom.
* Pan.
* Rotation.
* Fit-to-window.

---

## FR-3 Photo Import

Supported formats:

* JPG
* JPEG
* PNG
* HEIC (future)

Capabilities:

* Drag & Drop
* Folder import
* Recursive folder import
* Duplicate detection

Metadata extraction:

* EXIF
* Timestamp
* GPS
* Camera model
* Lens
* Orientation

---

## FR-4 Photo Browser

Display:

* Thumbnail
* Filename
* Date
* Status
* Assigned floor
* Assigned room

Sorting:

* Date
* Name
* Status
* Room

Filtering:

* Annotated
* Unannotated
* Exterior
* Interior

---

## FR-5 Annotation

Each annotation consists of:

* Camera position
* Camera direction
* Viewing cone
* Optional visible area polygon
* Title
* Description
* Tags
* Floor selection

---

## FR-6 Editing

User can:

* Move marker
* Rotate arrow
* Resize viewing cone
* Delete annotation
* Copy annotation
* Paste annotation

Undo/Redo unlimited.

---

## FR-7 Navigation

Keyboard shortcuts:

Arrow Keys → Previous/Next photo

Space → Confirm

Ctrl+S → Save

Ctrl+Z → Undo

Ctrl+Y → Redo

Delete → Remove annotation

Ctrl+Mouse Wheel → Zoom

Middle Mouse → Pan

---

## FR-8 Report Generation

Output:

Professional PDF

Layout:

Photo

Plan

Camera symbol

Viewing cone

Title

Description

Metadata

Figure number

Optional watermark

Options:

A4 Portrait

A4 Landscape

Letter

Custom

---

## FR-9 Project File

JSON-based project.

Stores:

* Plans
* Photos
* Metadata
* Annotations
* Export settings
* UI preferences

---

# 5. Non-functional Requirements

Performance

* 1000+ photos
* 100+ plan pages
* Smooth zoom
* Smooth pan
* Fast loading

---

Reliability

Auto-save every 2 minutes.

Crash recovery.

Project backup.

---

Usability

Maximum three clicks per annotation.

Professional keyboard shortcuts.

Dark mode.

Light mode.

---

Compatibility

macOS

Windows 11 (future) 

Windows 10 (future)

Linux (future)

---

# 6. Data Model

Project

contains

FloorPlans

contains

Pages

contains

Annotations

references

Photos

Photo

contains

Metadata

Annotation

contains

Position

Direction

ConeAngle

Room

Description

---

# 7. AI Features (Future)

Photo classification

Room recognition

Automatic room assignment

Suggested camera position

Suggested orientation

Duplicate photo detection

Blurry photo detection

Automatic report summary

Natural language search

---

# 8. Report Layout

Each report page contains:

Header

Project name

Photo number

Photo

Annotated floor plan

Camera position

Viewing cone

Metadata

Footer

Page number

Date

Project version

---

# 9. Future Extensions

3D model support

IFC support

Revit integration

AutoCAD integration

Cloud synchronization

Multi-user editing

Tablet support

Touch support

Laser scanner support

360° photos

Video support

Drone imagery

Thermal images

Point clouds
