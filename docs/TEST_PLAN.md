# HostelHub: Quality Assurance & Comprehensive Test Plan

## 1. Testing Strategy & Philosophy
Testing verifies functional correctness, strict multi-tenant security boundaries, and responsive accessibility across mobile and desktop viewports. Every critical user flow is validated with both positive and negative test assertions.

---

## 2. Test Suites & Test Cases

### 2.1 Suite 1: Authentication, Onboarding & Identity
- `AUTH-01`: Registration with valid campus email creates profile record in `profiles`.
- `AUTH-02`: Unverified user cannot view or create listings until college membership is verified.
- `AUTH-03`: Selecting hostel block associates student with `hostel_memberships`.
- `AUTH-04` *(Negative)*: Manipulating user ID in token fails cryptographic verification.

### 2.2 Suite 2: Multi-College Data Isolation & Privacy (Critical Security)
- `ISO-01` *(Security / Negative)*: Authenticated student from "College A" sends request for listing ID belonging to "College B". **Assertion**: Must return `404 Not Found` or `403 Forbidden`; zero listing details revealed.
- `ISO-02` *(Security / Negative)*: Direct SQL query or API call requesting search results with another college's ID. **Assertion**: RLS filters out rows; result array is empty.
- `ISO-03` *(Privacy / Negative)*: Inspect API payload of listing details and search results. **Assertion**: `room_number` and personal phone number fields must NOT exist in the response payload.
- `ISO-04`: Handover location shows only building / common block name until transaction is explicitly accepted by both parties.

### 2.3 Suite 3: Listing Creation, Validation & Expiry
- `LIST-01`: Student creates listing with valid title, category, quantity, and price. Status set to `ACTIVE`.
- `LIST-02` *(Negative)*: Submitting negative quantity (e.g., `-1`) or invalid price (e.g., `-$5.00`) fails Zod schema validation with clear error message.
- `LIST-03` *(Negative)*: Food category listing submitted without expiry date fails validation.
- `LIST-04`: "Available Tonight" toggle marks listing priority for night searches.
- `LIST-05`: Expired listings (`expires_at < NOW()`) are excluded from active search results.

### 2.4 Suite 4: Search Engine & Smart Alternative Suggestions
- `SRCH-01`: Query for "Maggi Noodles" returns exact matches in current college.
- `SRCH-02`: Query for an item with zero exact matches triggers alternative suggestion engine (e.g., searching "Snickers" returns "KitKat" from the Confectionery category).
- `SRCH-03`: Alternatives are explicitly labeled as *"Suggested Alternatives"*, not exact matches.
- `SRCH-04`: Useful empty states displayed when no listings or alternatives exist, offering a "Post Request" prompt.

### 2.5 Suite 5: Requests, Concurrency & Transactions
- `REQ-01`: Buyer submits trade request (cash or barter offer). Seller receives in-app notification.
- `REQ-02`: Seller counters offer (`NEGOTIATING`), buyer accepts.
- `REQ-03` *(Concurrency / Race Condition)*: Two simulated buyers attempt to simultaneously reserve the final available unit of an item.
  - **Assertion**: Exactly ONE request succeeds (`ACCEPTED` -> listing `RESERVED`); second request fails with HTTP 409 conflict.
- `REQ-04`: Seller marks ready for handover; buyer confirms receipt; seller confirms receipt. Status becomes `COMPLETED`.
- `REQ-05`: Uninvolved third party attempts to view private trade messages. **Assertion**: Forbidden (HTTP 403).

### 2.6 Suite 6: Moderation, Reporting & Ratings
- `MOD-01`: Student reports listing for expired food. Listing appears in Moderator Queue.
- `MOD-02`: Moderator removes listing. Listing status becomes `SUSPENDED` and vanishes from public search.
- `MOD-03` *(Negative)*: Student attempts to access `/mod` or `/admin` routes. **Assertion**: Middleware redirects to `/dashboard` with 403 error.
- `MOD-04`: Student rates trade partner with 5 stars. Score updates seller's verified trust rating.

---

## 3. Automated Test Execution Tooling
- **Unit & Integration**: Vitest / Jest with React Testing Library.
- **End-to-End (E2E)**: Playwright for automated multi-role browser journeys (Student, Moderator, Admin).
- **Security / Linting**: TypeScript strict check (`tsc --noEmit`), ESLint, and Supabase RLS test scripts.
