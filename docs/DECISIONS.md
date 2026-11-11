# HostelHub: Architecture Decision Records (ADRs)

## ADR-001: Migration from Flask Prototype to Next.js App Router & TypeScript
- **Status**: Accepted
- **Context**: The existing folder contained a basic Flask/SQLite script (`app.py`). While helpful for initial experimentation, Flask with SQLite does not provide production-grade multi-tenant security, modern reactive mobile UI, robust Row Level Security, or seamless Vercel deployment required by the Master Specification.
- **Decision**: Build the full production application using Next.js 15+ App Router, strict TypeScript, Tailwind CSS, and modular React components.
- **Consequence**: Delivers a mobile-first, enterprise-grade responsive architecture that scales to multiple colleges while preserving clean component boundaries.

---

## ADR-002: Supabase PostgreSQL & Row Level Security (RLS) as Primary Backend
- **Status**: Accepted
- **Context**: The platform requires rock-solid data isolation between colleges, bulletproof session security, and relational data integrity (listings, requests, transactions, moderation).
- **Decision**: Use Supabase managed PostgreSQL, Supabase Auth (cookie-based session management), and Row Level Security (RLS) policies on every database table.
- **Consequence**: Security is enforced at the database layer. Even if an attacker attempts direct SQL injection or custom API queries, the database engine enforces tenant boundaries.

---

## ADR-003: Confidentiality of Student Room Numbers & Personal Contact Info
- **Status**: Accepted
- **Context**: Hostel residents are vulnerable to stalking, harassment, or unauthorized room visits if exact room numbers are publicly searchable or listed on items.
- **Decision**: Keep room numbers and phone numbers completely confidential. Show only the hostel building name or block (e.g. "Hall 1, Wing A") on listings. Exact handover locations are coordinated only within accepted transaction channels in common areas (e.g., reception or common rooms).
- **Consequence**: Guaranteed physical and digital safety for all students, especially vulnerable residents.

---

## ADR-004: Concurrency Control via Database Atomic Updates
- **Status**: Accepted
- **Context**: When only one unit of an urgent item (like sanitary pads or chargers) is available, two students may attempt to reserve it at the same moment.
- **Decision**: Use atomic SQL conditional updates (`UPDATE listings SET status = 'RESERVED' WHERE id = ... AND status = 'ACTIVE' RETURNING id`) rather than client-side optimistic locks.
- **Consequence**: Zero race conditions; exactly one student secures the item, and the second receives immediate clear feedback.

---

## ADR-005: Zero Monetary Escrow in MVP Phase
- **Status**: Accepted
- **Context**: Implementing payment card processing and escrow at day zero introduces unnecessary regulatory overhead, payment gateway merchant approval delays, and compliance friction.
- **Decision**: The MVP records agreed cash prices or barter terms in-app, but actual payment/exchange happens directly between students upon physical handover.
- **Consequence**: Zero payment integration blocker; free to register and use; prepares the database architecture for future monetization when volume warrants it.

---

## ADR-006: Polling / Server Query-Based In-App Notifications
- **Status**: Accepted
- **Context**: Complex WebSocket infrastructure can add deployment instability and battery drain on student mobile devices.
- **Decision**: Use periodic polling and React Query / SWR / server action state refreshes for notifications during the initial pilot.
- **Consequence**: High reliability, low complexity, easy to test, and ready for future Web Push / Supabase Realtime upgrade if needed.
