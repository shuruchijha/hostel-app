# HostelHub: System Architecture & Technical Design

## 1. Architectural Overview

HostelHub is designed as a secure, mobile-first web application leveraging modern Next.js App Router architecture paired with Supabase (managed PostgreSQL, Row Level Security, Auth, and Storage).

```
+-------------------------------------------------------------+
|                     Next.js Client (Browser)                |
|      Tailwind CSS + Accessible Component System + Lucide    |
+-------------------------------------------------------------+
                              |
                     HTTP / Cookie Sessions
                              v
+-------------------------------------------------------------+
|                   Next.js App Router (Server)               |
|  - Server Components (Direct Read with Auth Context)        |
|  - Server Actions & Route Handlers (Validated Mutations)    |
|  - Zod Input & Schema Validation                            |
|  - Role & Permission Guards (Student, Mod, Admin)           |
+-------------------------------------------------------------+
                              |
                   Supabase SSR Client / Pool
                              v
+-------------------------------------------------------------+
|                 Supabase Backend Services                   |
|  - Supabase Auth (JWT, Cookie Session, Secure Tokens)       |
|  - PostgreSQL Database (Tables, Foreign Keys, Indexes)      |
|  - Row Level Security (RLS) (Multi-college isolation)       |
|  - Supabase Storage (Controlled listing image buckets)      |
+-------------------------------------------------------------+
```

---

## 2. Core Architectural Principles

### 2.1 Multi-Tenant College Isolation at the Data Layer
Multi-college data isolation is strictly enforced inside PostgreSQL via **Row Level Security (RLS)** and verified on the Next.js server runtime.
- A user's token carries their authenticated `auth.uid()`.
- Supabase RLS policies verify that `listings.college_id` matches the user's verified `college_memberships.college_id`.
- Users cannot manipulate URL parameters (`/listings/[id]` or `college_id`) to view data from other colleges.

### 2.2 Concurrency & Race Condition Prevention
To prevent two buyers from simultaneously claiming the last unit of an essential item (e.g., the last packet of Maggi noodles or single sanitary pad pack):
- Reservations utilize atomic conditional updates:
  ```sql
  UPDATE listings
  SET status = 'RESERVED',
      reserved_by = $buyer_id,
      updated_at = NOW()
  WHERE id = $listing_id
    AND status = 'ACTIVE'
    AND quantity >= $requested_quantity
  RETURNING id;
  ```
- If zero rows are returned, the transaction fails gracefully with a user-friendly message: *"This item was just reserved by another student."*

### 2.3 Layered Application Structure
```
src/
├── app/                  # Next.js App Router pages, layouts, and route handlers
│   ├── (auth)/           # Authentication routes (login, signup, callback)
│   ├── (dashboard)/      # Authenticated student application
│   ├── (public)/         # Public landing, rules, about
│   ├── admin/            # Platform administrator portal
│   └── mod/              # College moderator portal
├── components/           # Reusable UI component library
│   ├── ui/               # Core design system primitives (Button, Card, Input, Badge, Dialog)
│   ├── listings/         # Listing cards, search bar, creation form
│   ├── requests/         # Request cards, negotiation timeline
│   └── layout/           # Navbar, Mobile Bottom Navigation, Footer
├── lib/                  # Shared libraries and utility code
│   ├── supabase/         # Supabase client singletons (server, client, middleware)
│   ├── auth/             # Session verification and role extraction
│   └── utils/            # String formatters, date utilities, error handlers
├── schemas/              # Zod schemas for validation
│   ├── listing.ts        # Listing creation & update rules
│   ├── request.ts        # Trade & negotiation schemas
│   └── report.ts         # User & item reporting schemas
└── types/                # TypeScript interface definitions
    └── database.ts       # Generated database schema types
```

---

## 3. Technology Stack Decisions

| Technology | Purpose | Justification |
| :--- | :--- | :--- |
| **Next.js 15+ (App Router)** | Full-stack React framework | Fast server-side rendering, seamless SEO for public pages, built-in Server Actions for secure mutations. |
| **TypeScript (Strict Mode)** | Type safety | Catch errors at compile time; strict interfaces across database records, API payloads, and UI props. |
| **Tailwind CSS** | Styling | Utility-first, mobile-first design, fast compilation, clean accessible aesthetics without UI bloat. |
| **Supabase PostgreSQL** | Primary relational store | ACID compliance, powerful foreign keys, full-text search capability, and robust Row Level Security. |
| **Supabase Auth** | Identity & Session management | Secure HTTP-only cookie tokens, zero custom crypto vulnerability, seamless integration with PostgreSQL RLS. |
| **Supabase Storage** | Image attachments | Scalable object storage with signed URLs and strict bucket RLS policies. |
| **Zod** | Schema validation | Runtime input sanitization preventing injection and malicious payload structures. |
| **Lucide React** | Icons | Crisp, lightweight, accessible icon set with zero runtime overhead. |
