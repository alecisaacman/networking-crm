# Overview

## Objective

Build a local-first networking tracker for one user on macOS.

The first useful version should make it easy to:

* keep a list of people
* track where you met them
* capture notes after interactions
* see who needs a follow-up next

## Interface

Start with a CLI.

That keeps implementation fast and avoids committing to a UI before the data model and workflows are stable.

## Storage

SQLite in `runtime/state/networking.db`.

This is the lightest durable option that supports search, sorting, and future migrations better than flat files.

## Core v1 capabilities

* initialize local database
* add contact
* list contacts
* add note
* schedule follow-up
* view upcoming follow-ups

## Verification path

* smoke test CLI bootstrap
* unit tests around database initialization and first CRUD actions
