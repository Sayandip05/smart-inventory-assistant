INVIQ — COMPLETE USER FLOW
From Landing Page to Daily Operations
=====================================

================================================================
PART 1: FIRST TIME — BUSINESS OWNER DISCOVERS INVIQ
================================================================

1. Business owner (hospital admin, warehouse manager, etc.)
   lands on InvIQ landing page (inviq.in or Render URL)

2. Sees: problem statement, features, pricing (free tier)

3. Clicks "Get Started" or "Sign Up"

4. Redirected to /login page
   (No self-signup — owner cannot create their own account)

5. They see a login form but have no credentials yet

6. They contact Sayandip (Super Admin) via:
   - Contact form on landing page
   - Email / LinkedIn / WhatsApp
   - Any outreach channel

7. Sayandip logs into /superadmin portal with his own credentials

8. Sayandip creates a new Organization:
   - Org name: "City Hospital Kolkata"
   - Active: true

9. Sayandip creates the Admin account:
   - Email: owner@cityhospital.in
   - Username: cityhospital_admin
   - Role: admin
   - Org: City Hospital Kolkata

10. Sayandip sends credentials to the business owner
    (email or WhatsApp — manual for now)

11. Business owner receives: username + temporary password

================================================================
PART 2: ADMIN ONBOARDING — SETTING UP THE ORGANIZATION
================================================================

12. Admin visits /login
    Enters username + password
    Clicks Sign In

13. Backend:
    POST /api/auth/login
    - Checks username exists
    - Verifies Argon2 password hash
    - Checks account not locked
    - Creates JWT: {sub, username, role: "admin", org_id}
    - Creates refresh token
    - Records login timestamp
    - Writes AuditLog: LOGIN_SUCCESS

14. Frontend receives tokens
    Stores in memory / httpOnly cookie
    Redirects to /admin portal (role detected from JWT)

15. Admin lands on Admin Dashboard
    Sees empty state: no locations, no items, no users yet

----------------------------------------------------------------
STEP A: CREATE LOCATIONS
----------------------------------------------------------------

16. Admin goes to User Management or Settings → Locations
    Clicks "Add Location"
    Fills: Name="OPD Store", Type="pharmacy", Region="North Wing"
    Submits

17. Backend:
    POST /api/inventory/locations
    - Checks duplicate name within org_id
    - Creates Location with org_id from JWT
    - Returns location with id

18. Admin repeats for all locations:
    "ICU Store", "Emergency Store", "Main Warehouse" etc.

----------------------------------------------------------------
STEP B: CREATE ITEMS (MEDICINE / PRODUCT CATALOG)
----------------------------------------------------------------

19. Admin goes to Inventory → Items → Add Item
    Fills:
    - Name: "Paracetamol 500mg"
    - Category: "medicine"
    - Unit: "tablets"
    - Lead Time Days: 3
    - Min Stock: 500
    Submits

20. Backend:
    POST /api/inventory/items
    - Checks duplicate name within org_id
    - Creates Item with org_id
    - Returns item with id

21. Admin repeats for all items in their catalog

----------------------------------------------------------------
STEP C: CREATE STAFF ACCOUNTS
----------------------------------------------------------------

22. Admin goes to User Management → Add User
    Fills:
    - Name: "Ramesh Kumar"
    - Email: ramesh@cityhospital.in
    - Role: staff
    - Location: OPD Store
    Submits

23. Backend:
    POST /api/auth/register
    - require_admin check passes
    - Creates user with org_id from Admin's JWT
    - Role: staff, location_ids: [1]
    - AuditLog: USER_CREATED

24. Admin repeats for:
    - All staff members (role: staff)
    - Managers (role: manager)
    - Vendors (role: vendor)
    - Viewers (role: viewer) — for auditors, senior doctors, finance team

25. Admin sends credentials to each person
    (same manual process for now)

================================================================
PART 3: DAILY OPERATIONS — EACH ROLE'S WORKFLOW
================================================================

================================================================
ROLE: STAFF — Daily Stock Entry
================================================================

26. Staff member (e.g., Ramesh at OPD Store) logs in at /login
    JWT issued with role: staff, location_ids: [1]
    Redirected to /staff portal

27. Every morning: Ramesh goes to "Log Transaction"
    Selects date: today
    For each item:
    - Paracetamol 500mg: Received=0, Issued=50
    - Surgical Gloves: Received=200, Issued=30
    Clicks Submit

28. Backend:
    POST /api/inventory/bulk-transaction
    For each item:
    - Fetches previous day closing_stock
    - opening_stock = previous closing_stock
    - closing_stock = opening_stock + received - issued
    - Validates closing_stock >= 0 (never negative)
    - Saves InventoryTransaction
    - Invalidates Redis cache: analytics:*:{org_id}

29. If stock is critically low after transaction:
    WebSocket broadcast to all connected clients for location_id:
    {type: "alert", item: "Paracetamol 500mg", status: "CRITICAL", stock: 45}
    Manager and Admin dashboards show live alert badge — no refresh needed

----------------------------------------------------------------
RAISING A REQUISITION
----------------------------------------------------------------

30. Ramesh sees Paracetamol is critically low
    Goes to "Raise Requisition"
    Fills:
    - Department: OPD
    - Urgency: HIGH
    - Items: Paracetamol 500mg — 500 units
    Submits

31. Backend:
    POST /api/requisition/create
    - Generates REQ-20260328-001 number
    - Creates Requisition (status: PENDING)
    - Creates RequisitionItems
    - AuditLog: REQUISITION_CREATED

32. Ramesh can see status in "My Requisitions":
    REQ-20260328-001 | Paracetamol 500mg x500 | PENDING

================================================================
ROLE: MANAGER — Requisition Approvals
================================================================

33. Manager logs in → /manager portal
    Dashboard shows: 3 pending requisitions, 2 critical alerts

34. Manager clicks "Requisitions"
    Sees: REQ-20260328-001 from Ramesh, OPD, HIGH urgency

35. Manager reviews:
    - Current stock: 45 units (CRITICAL)
    - Requested: 500 units
    - Raised by: Ramesh Kumar
    Clicks "Approve"
    Optionally fills quantity_approved: 500, notes: "Approved urgently"

36. Backend:
    PUT /api/requisition/{id}/approve
    - Updates status: APPROVED
    - Sets approved_by, approved_at
    - Deducts quantity from stock via InventoryService
    - Invalidates Redis analytics cache
    - AuditLog: REQUISITION_APPROVED

37. OR Manager clicks "Reject":
    Fills rejection_reason: "Budget freeze this week"
    Backend: status → REJECTED, AuditLog: REQUISITION_REJECTED

38. Ramesh sees status updated in his portal: APPROVED ✓

================================================================
ROLE: VENDOR — Delivery Upload
================================================================

39. Vendor (medicine supplier) logs in → /vendor portal
    Sees only: Upload Delivery, My Uploads, Download Template

40. Vendor clicks "Download Template"
    Gets blank .xlsx:
    | item_name | quantity_received | delivery_date | notes |

41. Vendor fills it with their delivery manifest:
    | Paracetamol 500mg | 1000 | 2026-03-28 | Morning batch |
    | Surgical Gloves   | 500  | 2026-03-28 |               |

42. Vendor uploads file to /vendor/upload-delivery

43. Backend:
    POST /api/vendor/upload-delivery
    - Reads .xlsx with openpyxl
    - For each row:
        fuzzy match item_name → item_id (RapidFuzz, 85% threshold)
        validate: location assigned to this vendor? quantity > 0? date valid?
        if valid → InventoryService.add_transaction(received=qty, issued=0)
        if invalid → add to errors list
    - Saves VendorUpload record: total=48, success=46, errors=2
    - Returns row-level report

44. Vendor sees result:
    "46 items imported successfully"
    "2 errors: Row 3 — item not found, Row 17 — quantity invalid"

45. Admin and Manager can see this upload in their Vendor Deliveries section

================================================================
ROLE: ADMIN — Analytics, Reports, Oversight
================================================================

46. Admin logs in → /admin portal
    Full dashboard:
    - Stock health overview: 3 critical, 5 warning, 42 healthy
    - Pending requisitions: 2
    - Recent vendor uploads: 1 today

47. Admin clicks Analytics → Heatmap
    Sees: color-coded grid of all items × all locations
    GREEN = healthy, YELLOW = warning, RED = critical

48. Backend:
    GET /api/analytics/heatmap
    - Check Redis cache: analytics:heatmap:{org_id}
    - Cache hit → return in ~3ms
    - Cache miss → run complex SQL (7-day avg + health calculation) → store in Redis → return

49. Admin clicks "Generate Report"
    Selects date range: March 1–28, 2026
    Clicks Download

50. Backend:
    GET /api/admin/reports/generate?from=2026-03-01&to=2026-03-28
    - Aggregates stock health, requisition stats, vendor activity
    - ReportLab builds PDF
    - Returns file download

51. Admin downloads PDF:
    - Executive summary
    - Top 10 critical items
    - Requisition summary (raised/approved/rejected)
    - Vendor delivery log
    - Consumption trends

52. Admin goes to Audit Log
    Sees every action in chronological order:
    - 09:05 | ramesh | TRANSACTION_ADDED | OPD Store
    - 09:12 | ramesh | REQUISITION_CREATED | REQ-20260328-001
    - 10:30 | manager1 | REQUISITION_APPROVED | REQ-20260328-001
    - 11:00 | vendor1 | VENDOR_UPLOAD | 46 items

================================================================
ROLE: VIEWER — Read-Only Access
================================================================

53. Viewer (e.g., CFO, Senior Doctor, Auditor) logs in → /viewer portal
    Sees: dashboard, analytics, inventory view
    No buttons, no forms, no write access
    Just data

================================================================
ROLE: AI AGENT — Staff/Admin Chat
================================================================

54. Staff or Admin goes to AI Assistant (on their respective portal)
    Types: "What should I order this week for OPD Store?"

55. Backend:
    POST /api/chat/query
    - JWT verified, org_id extracted
    - ChromaDB: retrieve past conversation context (RAG)
    - LangGraph ReAct Agent starts:

        call_model:
        LLM reads: system_prompt + history + context + question
        LLM decides: call get_stock_health(location="OPD Store")

        run_tools:
        get_stock_health → live DB query → returns 12 items, 3 critical

        call_model:
        LLM reads results, decides: call calculate_reorder_suggestions(location="OPD Store")

        run_tools:
        calculate_reorder_suggestions → returns quantities + reasoning

        call_model:
        LLM synthesizes → final answer

    - Answer saved to ChatSession + ChatMessage (PostgreSQL)
    - Answer saved to ChromaDB (vector memory for future context)

56. Response displayed:
    "Based on current stock levels at OPD Store:
     - Paracetamol 500mg: 45 units remaining, order 500 units
       (daily usage: 50 units, lead time: 3 days)
     - Surgical Gloves: 30 units remaining, order 200 units
     Total: 2 items need immediate reorder"

57. Staff can ask follow-up:
    "Raise a requisition for these items"
    Agent calls create_auto_requisition tool → done without leaving chat

================================================================
PART 4: ERROR SCENARIOS & HANDLING
================================================================

----------------------------------------------------------------
LOGIN ERRORS
----------------------------------------------------------------

E1. Wrong password (attempt 1-4):
    → 401: "Invalid username or password"
    (Same message whether username exists or not — no enumeration)

E2. Wrong password (attempt 5):
    → Account locked for N minutes
    → 401: "Account locked for 30 minutes due to too many failed attempts"
    → AuditLog: ACCOUNT_LOCKED

E3. Locked account tries to login:
    → 401: "Account is locked. Try again in 28 minutes."

E4. Expired access token:
    → 401: "Invalid or expired token"
    → Frontend: auto-refresh using refresh token
    → POST /api/auth/refresh → new access token issued
    → Old refresh token blacklisted (rotation)

E5. Logout then use old token:
    → Token checked against Redis blacklist
    → 401: "Invalid or expired token"
    → Cannot reuse token after logout

E6. Staff trying to access /admin route:
    → 403: "Requires admin role or higher"

E7. Vendor trying to access analytics:
    → 403: "Insufficient permissions"

E8. User from Org A trying to access Org B data via URL manipulation:
    → All queries filter by org_id from JWT
    → Returns empty result or 404
    → Data never exposed

----------------------------------------------------------------
INVENTORY ERRORS
----------------------------------------------------------------

E9. Transaction makes closing_stock negative:
    → 400: "Invalid transaction: closing stock cannot be negative (would be -50)"
    → Transaction not saved, db.rollback() called

E10. Location not found:
    → 404: "Location with id '99' not found"

E11. Duplicate location name within org:
    → 409: "Location 'OPD Store' already exists"

E12. Bulk transaction — partial failure:
    → Processes each row independently
    → Returns: {successful: [rows], failed: [{item_id, error}]}
    → Partial success is fine — not all-or-nothing

----------------------------------------------------------------
REQUISITION ERRORS
----------------------------------------------------------------

E13. Approving already-approved requisition:
    → 400: "Operation not allowed in current state"

E14. Staff trying to approve requisition:
    → 403: "Requires manager role or higher"

E15. Requisition not found:
    → 404: "Requisition with id '500' not found"

----------------------------------------------------------------
VENDOR UPLOAD ERRORS
----------------------------------------------------------------

E16. Non-.xlsx file uploaded:
    → 422: "Only .xlsx files are supported"

E17. Row with item name not matching catalog (below 85% threshold):
    → Row skipped, added to errors list
    → Other rows still process normally

E18. Row with negative quantity:
    → Row skipped, error: "Quantity must be positive"

E19. Vendor uploading to location not assigned to them:
    → Row rejected: "Location not assigned to your account"

----------------------------------------------------------------
AI AGENT ERRORS
----------------------------------------------------------------

E20. GROQ_API_KEY missing or Groq API down:
    → Graceful fallback to rule-based responses
    → User sees response, not an error
    → Logged as WARNING in server logs

E21. ChromaDB unavailable:
    → Agent continues without past context
    → Warning logged, response still generated

E22. Question too short (< 3 characters):
    → 422: "Question must be at least 3 characters"

E23. Accessing another user's conversation:
    → _verify_session_ownership() check
    → 403: "You do not have access to this conversation"

----------------------------------------------------------------
INFRASTRUCTURE ERRORS
----------------------------------------------------------------

E24. PostgreSQL connection fails:
    → 500: "A database error occurred"
    → db.rollback() called
    → Logged as ERROR with full traceback

E25. Redis unavailable:
    → Analytics: cache miss → falls back to direct DB query
    → Token blacklist: fail-open (log warning, allow request)
    → Rate limiter: fail-open (log warning, allow request)

E26. PDF generation fails:
    → 500: "Failed to generate report: {reason}"
    → User sees error message, no broken download

================================================================
PART 5: SUPER ADMIN OPERATIONS (SAYANDIP ONLY)
================================================================

58. New business wants to sign up:
    Sayandip logs into /superadmin
    Creates organization → creates admin account → sends credentials

59. Business wants to deactivate:
    Sayandip → /superadmin/organizations
    Clicks Deactivate on org
    All users in that org: is_active = false
    All their tokens: immediately invalid on next request

60. Monitoring:
    Sayandip can see:
    - All organizations and their status
    - All users across all orgs
    - Platform-wide activity

================================================================
PART 6: TOKEN LIFECYCLE
================================================================

61. Login → access token (30 min) + refresh token (7 days) issued

62. Every API request:
    - Frontend sends: Authorization: Bearer <access_token>
    - Backend: verify signature → check expiry → check Redis blacklist → extract role+org_id

63. Access token expires after 30 min:
    - Frontend auto-calls POST /api/auth/refresh
    - Old refresh token blacklisted
    - New access + refresh tokens issued (rotation)

64. User clicks Logout:
    - POST /api/auth/logout
    - Access token added to Redis blacklist (TTL = remaining expiry)
    - AuditLog: LOGOUT
    - Frontend clears tokens
    - Cannot use old token even if someone intercepted it

65. Refresh token expires after 7 days:
    - User must log in again
    - No silent re-auth possible

================================================================
END OF USER FLOW
================================================================