# HostelHub: Master Product Specification

## 1. Executive Summary & Vision
HostelHub is a hyper-local, peer-to-peer campus marketplace designed exclusively for verified student hostel residents. When late-night campus facilities, nearby canteens, and local convenience stores shut down, students frequently experience urgent shortages of everyday essentials (sealed packaged snacks, sanitary napkins, painkillers/basic toiletries, charging cables, notebooks). HostelHub connects students needing an item with students in their immediate hostel block who have that item available—facilitating safe, permitted, and mutually agreed handovers without violating hostel curfew or residency regulations.

---

## 2. Target Personas & Roles

### 2.1 Student User
- **Needs**: Quick discovery of urgent supplies late at night or during study hours; easy way to declutter or share extra supplies for cash or barter.
- **Key Flows**: Email signup -> College & Hostel verification -> Browse/Search nearby items -> Make request with terms (cash or barter) -> Negotiate/Agree -> Coordinate safe handover -> Mark transaction complete -> Rate/Review.

### 2.2 College Community Moderator
- **Needs**: Maintain community standards, inspect reported listings or suspicious users within their designated college campus.
- **Key Flows**: Access moderation queue -> Review flagged items -> Remove policy-violating listings -> Suspend bad actors -> Escalate to platform admin if necessary.

### 2.3 Platform Administrator
- **Needs**: Oversee college onboarding, configure approved institutions and hostel buildings, inspect global analytics and audit logs.
- **Key Flows**: Add/approve institutions -> Manage hostel blocks -> Review campus metrics -> Audit security actions.

---

## 3. Product Rules & Item Guidelines

### 3.1 Allowed Items
- **Packaged Food & Snacks**: Sealed, commercially packaged foods with verifiable expiry dates (e.g., instant noodles, chips, biscuits, tea bags, packaged beverages).
- **Personal & Menstrual Hygiene**: Sealed sanitary pads, tampons, menstrual cups, tissues, wet wipes.
- **Toiletries & Grooming**: Toothpaste, soap, shampoo sachets, detergent, hand sanitizer.
- **Stationery & Academics**: Notebooks, pens, staplers, calculators, lab coats, sticky notes.
- **Everyday Accessories & Electronics**: Phone chargers, adapters, extension cords, umbrellas, locks.

### 3.2 Strictly Prohibited Items
- Prepared/open/cooked perishable foods from home or canteens.
- Expired consumables.
- Alcoholic beverages, tobacco, cigarettes, vapes, and drugs.
- Prescription-only pharmaceuticals or controlled substances.
- Weapons, dangerous chemicals, or hostel-prohibited appliances (e.g., unauthorized heavy coil heaters).
- Academic dishonesty materials (past exams, plagiarized assignments).

---

## 4. Key Functional Modules

### 4.1 Onboarding & Multi-College Isolation
- Users register via university email or an admin-approved invite code.
- Every student profile is bound to a verified `college_id` and assigned a `hostel_id` (and block).
- All queries, searches, listings, and requests are strictly isolated by `college_id` at the database level. Students cannot view or interact with items from outside their verified institution.

### 4.2 Listing Lifecycle & Availability
- **Attributes**: Item name, category, description, quantity, condition, asking price (or 0 for barter/gift), exchange preference (Fixed Price, Barter, Negotiable), optional photo, expiry date (for packaged food), and availability status.
- **Special Statuses**: "Available Now" and an "Available Tonight" toggle for urgent night-time swaps.
- **State Machine**:
  - `ACTIVE` -> Visible in searches.
  - `RESERVED` -> Held for an accepted request (hidden from active search).
  - `COMPLETED` -> Sold/exchanged.
  - `EXPIRED` -> Automatically moved out of search if validity period lapses.
  - `SUSPENDED` -> Removed by moderator.

### 4.3 Search & Intelligent Alternative Suggestions
- Fast keyword search across names, categories, and descriptions within the user's college.
- Filter by hostel block, category, availability, and exchange type.
- **Fallback Suggestions**: When an exact item is unavailable (e.g. "Cadbury Chocolate"), the engine identifies related items in the same category or semantic group (e.g. "Oreo Biscuits", "KitKat") and explicitly labels them as *Suggested Alternatives*.
- **Item Request / Want Board**: Students can post a "Looking For" request when an item is unavailable.

### 4.4 Request, Negotiation & Handover Flow
1. Buyer submits request with proposed terms (e.g. \$2.00 cash, or barter for instant noodles).
2. Seller reviews request: can `ACCEPT`, `REJECT`, or counter-offer with `NEGOTIATE`.
3. Concurrency Safety: Once a request is accepted for the remaining available units, the listing is locked (`RESERVED`) so other buyers cannot claim it simultaneously.
4. Handover coordination: Authorized participants agree on a common permitted handover point (e.g., hostel common room or reception). Exact room numbers are protected.
5. Dual Confirmation: Both parties mark the transaction as completed.

### 4.5 Trust, Safety & Privacy
- **Zero Public PII**: Phone numbers and room numbers are never published.
- **Reporting & Blocking**: Any listing or user can be reported with categorized reasons and evidence. Users can block harassment or abusive peers.
- **Reputation**: Verified transaction feedback and rating system (1-5 stars with verified trade badges).

---

## 5. Information Architecture & Site Map
```
HostelHub
├── Public
│   ├── / (Landing page: Value proposition, search teaser, how-it-works)
│   ├── /how-it-works (Safety guidelines, permitted items)
│   ├── /rules (Campus rules & banned items)
│   ├── /privacy (Privacy policy & data handling)
│   ├── /terms (Terms of service)
│   ├── /auth/login (Sign-in)
│   └── /auth/signup (Registration & verification)
├── Authenticated Student
│   ├── /onboarding (College selection & hostel block setup)
│   ├── /dashboard (Personal overview, active requests, notifications)
│   ├── /search (Item search, filters, and alternative suggestions)
│   ├── /listings/new (Create item listing)
│   ├── /listings/[id] (Listing details & request trigger)
│   ├── /listings/[id]/edit (Update or cancel listing)
│   ├── /requests (Incoming and outgoing trade requests)
│   ├── /requests/[id] (Request details, terms negotiation, handover status)
│   ├── /history (Completed transaction ledger and reviews)
│   └── /profile (Settings, blocked users, community status)
├── Moderator Portal
│   ├── /mod (Moderation queue overview)
│   ├── /mod/reports (Flagged listings and users)
│   └── /mod/listings (Community item audit)
└── Administrator Portal
    ├── /admin (Campus management, metrics, audit logs)
    ├── /admin/colleges (College onboarding and domain rules)
    └── /admin/hostels (Hostel and block configuration)
```
