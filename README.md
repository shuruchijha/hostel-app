# HostelHub 🏨📦

> **Student-to-student hostel marketplace for discovering and exchanging food, toiletries, personal essentials, and permitted items within verified college hostel communities.**

---

## 🌟 The Problem
Late at night, campus canteens, stationery stores, and grocery shops close. Students frequently find themselves in urgent need of essentials—sanitary products, packaged food, toiletries, or academic stationery—when leaving the hostel is restricted or inconvenient. Meanwhile, fellow hostel residents often have those exact items in their rooms.

**HostelHub** bridges this gap safely and responsibly within verified campus communities.

---

## 🏗️ Architecture & Technology Stack
- **Frontend / Framework**: [Next.js](https://nextjs.org/) (App Router) + [TypeScript](https://www.typescriptlang.org/) (Strict Mode)
- **Styling**: [Tailwind CSS](https://tailwindcss.com/)
- **Backend / Database**: [Supabase](https://supabase.com/) (PostgreSQL + Row-Level Security)
- **Authentication**: Supabase Auth (Magic Link / Passwordless / College Email Verification)
- **Object Storage**: Supabase Storage (strictly access-controlled item photos)
- **Deployment**: [Vercel](https://vercel.com/) + Supabase Cloud

---

## 🔒 Safety, Privacy & Multi-College Isolation
- **No Global Leakage**: All listings, requests, and community discussions are strictly isolated by `college_id` and verified membership.
- **Privacy First**: Exact room numbers and phone numbers are never globally searchable. Handover details are only revealed to authorized participants after mutual transaction acceptance.
- **Rules & Compliance**: Prohibits alcohol, prescription drugs, unsealed perishable cooked food, and illicit items.
- **Safety**: Robust reporting, moderation queue, and user blocking mechanisms.

---

## 📋 Phased Development Roadmap
- [x] **Phase 0**: Workspace inspection, technical architecture proposal, risk analysis, and implementation roadmap.
- [ ] **Phase 1**: Application foundation, design system, routing, shared UI components, and documentation.
- [ ] **Phase 2**: Database schema, Supabase migrations, authentication, membership models, and RLS policies.
- [ ] **Phase 3**: Onboarding, college/hostel selection, and core listing lifecycle.
- [ ] **Phase 4**: Search engine, category filters, and smart alternative suggestions.
- [ ] **Phase 5**: Item requests, terms negotiation, transaction completion, and in-app notifications.
- [ ] **Phase 6**: Trust, safety, user moderation, report queue, and admin controls.
- [ ] **Phase 7**: Administrative pilot analytics, accessibility, empty states, and responsive refinements.
- [ ] **Phase 8**: Security audits, isolation tests, and end-to-end browser test suites.
- [ ] **Phase 9**: Production deployment preparation, Vercel configuration, and final verification report.

---

## 🚀 Getting Started & Local Development
See [`docs/DEPLOYMENT.md`](file:///c:/Users/Suruchi/Downloads/Hostel%20App/docs/DEPLOYMENT.md) and [`docs/ARCHITECTURE.md`](file:///c:/Users/Suruchi/Downloads/Hostel%20App/docs/ARCHITECTURE.md) for full instructions.

### Prerequisites
1. **Node.js** (v20+ LTS recommended)
2. **Git**
3. A free **Supabase** account ([supabase.com](https://supabase.com))

### Quickstart
```bash
# Clone or navigate to the repository
cd "Hostel App"

# Install dependencies (once Node.js is ready)
npm install

# Copy environment template
cp .env.example .env.local

# Run the development server
npm run dev
```

---

## 📚 Project Documentation
- [`docs/PRODUCT_SPEC.md`](file:///c:/Users/Suruchi/Downloads/Hostel%20App/docs/PRODUCT_SPEC.md) - Comprehensive product specifications and user stories
- [`docs/ARCHITECTURE.md`](file:///c:/Users/Suruchi/Downloads/Hostel%20App/docs/ARCHITECTURE.md) - System architecture and component design
- [`docs/DATABASE_SCHEMA.md`](file:///c:/Users/Suruchi/Downloads/Hostel%20App/docs/DATABASE_SCHEMA.md) - Relational schema, tables, and RLS policies
- [`docs/SECURITY.md`](file:///c:/Users/Suruchi/Downloads/Hostel%20App/docs/SECURITY.md) - Data isolation, privacy, and threat mitigations
- [`docs/TEST_PLAN.md`](file:///c:/Users/Suruchi/Downloads/Hostel%20App/docs/TEST_PLAN.md) - Test strategy, unit tests, and E2E isolation checks
- [`docs/DECISIONS.md`](file:///c:/Users/Suruchi/Downloads/Hostel%20App/docs/DECISIONS.md) - Architecture Decision Records (ADRs)
- [`docs/DEPLOYMENT.md`](file:///c:/Users/Suruchi/Downloads/Hostel%20App/docs/DEPLOYMENT.md) - Deployment and Supabase setup guide
