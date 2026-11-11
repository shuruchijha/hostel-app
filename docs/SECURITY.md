# HostelHub: Security Architecture & Threat Mitigations

## 1. Security Philosophy & Principles
HostelHub is built on a "Zero-Trust Client" and "Defense-in-Depth" posture. Student safety, data privacy, and compliance with college hostel regulations are foundational constraints.

---

## 2. Threat Modeling & Mitigations

### 2.1 Cross-College Data Leakage (IDOR & Tenant Crossing)
- **Threat**: An attacker at College A changes URL parameters or API payloads (e.g., passing `college_id = "College-B"`) to snoop on another institution's students or listings.
- **Mitigation**:
  1. PostgreSQL **Row Level Security (RLS)** inspects the authenticated JWT session on every query.
  2. Server Actions resolve `college_id` directly from the authenticated user's session record in `college_memberships`, ignoring any client-supplied `college_id`.
  3. Direct SQL queries cross-reference:
     `EXISTS (SELECT 1 FROM college_memberships cm WHERE cm.user_id = auth.uid() AND cm.college_id = listings.college_id AND cm.verification_status = 'VERIFIED')`.

### 2.2 Student Privacy & Stalking Vectors
- **Threat**: Bad actors harvesting student room numbers or personal phone numbers to locate students in their rooms without consent.
- **Mitigation**:
  1. **Room numbers are strictly confidential**. They are omitted from search results, profile cards, and public listings.
  2. Listings display only the building or block name (e.g., "Hall 3 - Block B").
  3. Precise handover coordination occurs strictly inside transaction chat or agreed common areas (e.g. hostel foyer or security desk).
  4. Real phone numbers are not collected or shared by default.

### 2.3 Food Safety & Regulatory Liability
- **Threat**: Exchange of spoiled, contaminated, or homemade food leading to illness or legal liability.
- **Mitigation**:
  1. **Strictly Packaged Only**: Only commercially sealed, unopened packaged foods with intact manufacturer labels and valid expiry dates are permitted.
  2. **Mandatory Expiry Declaration**: The listing creation form requires declaring the manufacturer's best-before date for consumables.
  3. **Mandatory Inspection Warning**: Before confirming receipt, the app reminds the buyer: *"Inspect package seal and expiry date before accepting handover."*
  4. **Prohibited Items Policy**: Zero tolerance for prescription drugs, alcohol, tobacco/vapes, cooked leftover food, or illicit substances. Immediate account suspension upon violation.

### 2.4 Race Conditions in Concurrent Reservations
- **Threat**: Two users attempting to request or buy the same single item simultaneously, causing duplicate reservations.
- **Mitigation**:
  - Reservations execute via atomic conditional SQL queries:
    ```sql
    UPDATE listings
    SET status = 'RESERVED',
        updated_at = NOW()
    WHERE id = $1
      AND status = 'ACTIVE'
    RETURNING id;
    ```
  - The second requester receives an immediate HTTP 409 / conflict notification that the item was already claimed.

### 2.5 Secret & Credential Management
- **Client Bundle Safety**:
  - Only `NEXT_PUBLIC_SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_ANON_KEY` are allowed in client bundles.
  - `SUPABASE_SERVICE_ROLE_KEY` is strictly confined to server-only routes (`src/app/api/...` or internal scripts) and is NEVER prefixed with `NEXT_PUBLIC_`.
  - `.env` and `.env.local` files are committed to `.gitignore`.

---

## 3. Incident Response & Moderation Flow
1. **Automated Flagging**: Listings receiving 3+ user reports are automatically hidden from search pending human moderator review.
2. **Moderator Actions**: Campus moderators can immediately freeze listings, warn users, or enact temporary 7-day bans.
3. **Platform Administrator Escalation**: Irrevocable permanent bans and campus domain modifications require platform administrator authentication.
