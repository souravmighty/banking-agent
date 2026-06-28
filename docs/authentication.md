# 🔐 Authentication Architecture

This document describes the cryptographic authentication, JWT token verification, and session establishment flows used to secure **ApexBanking**.

---

## 🔑 Authentication Architecture Blueprint

ApexBanking uses a multi-layered identity validation pipeline, ensuring that every operation (analytical or financial) is bound to a cryptographically validated tenant. The frontend client never interacts directly with backend datastores without a verified JWT token.

```mermaid
graph TD
    User([User / Client]) -->|Credential Input| NextJS[Next.js Client UI]
    NextJS -->|Authenticate| Firebase[Firebase Auth Server]
    Firebase -->|Issues Signed JWT ID Token| NextJS
    NextJS -->|Bearer JWT Token| CIS[customer-identity-service]
    CIS -->|Decode & Validate Signature| FB_SDK[Firebase Admin SDK]
    FB_SDK -->|Claims & Decoded Identity| CIS
    CIS -->|Map firebase_uid to customer_id| BQ[(BigQuery Mapping Table)]
```

---

## 🔄 Dynamic Flows

### 1. Token Acquisition & Verification Sequence

The client portal uses Firebase Authentication (supporting Google OAuth2, email/password, or federated providers) to establish initial identity.

```mermaid
sequenceDiagram
    autonumber
    actor User as Client Portal
    participant UI as Next.js UI
    participant FB as Firebase OAuth Server
    participant CIS as customer-identity-service

    User->>UI: Input login credentials
    UI->>FB: Request ID Token
    FB-->>UI: Return signed JWT ID Token
    UI->>CIS: HTTP Request with Header: Bearer <JWT_TOKEN>
    Note over CIS: Extraction of JWT header
    CIS->>FB: Fetch current public signing keys (JWKS)
    Note over CIS: Cryptographically verify token signature, expiration (exp), and audience (aud)
    CIS-->>UI: Establish authenticated session context
```

### 2. Identity Resolution Mapping

A critical design pattern in ApexBanking is **anonymous user mapping**. The Firebase User ID (`firebase_uid`) is distinct from the internal banking identifier (`customer_id`). This decoupling allows changing authentication providers without altering financial transactional tables.

```sql
-- Query executed by customer-identity-service to resolve firebase_uid
SELECT customer_id, email, kyc_status, customer_segment 
FROM `banking_data.customer_identity_mapping`
INNER JOIN `banking_data.customers` USING (customer_id)
WHERE firebase_uid = @firebase_uid AND is_current = true
LIMIT 1;
```

---

## 🛡️ Key Components & Security Boundaries

### Token Structure (JWT Claims)
Every requests to the `customer-identity-service` is accompanied by a standard Authorization header:
```http
Authorization: Bearer eyJhbGciOiJSUzI1NiIsImtpZCI6IiJ9.eyJpc3MiOiJodHRwczovL3NlY3VyZXRva2VuLmdvb2dsZS5jb20v...
```

The service decodes and enforces the following claims on every request:
*   `iss` (Issuer): Must match `https://securetoken.google.com/<firebase-project-id>`.
*   `aud` (Audience): Must match your Firebase project ID.
*   `exp` (Expiration): Enforces short-lived sessions (typically 1 hour expiration).
*   `sub` (Subject): The authenticated `firebase_uid`.

### Stateless Verification Principle
To scale efficiently and remain resilient to network partitions:
1.  The `customer-identity-service` utilizes the **JWKS (JSON Web Key Set)** endpoint provided by Google to cache signing keys.
2.  Verification of JWT signatures happens entirely in-memory at the API gateway layer using cached keys.
3.  Upon success, the decoded `firebase_uid` is injected into FastAPI's request state `request.state.firebase_uid` and parsed downstream.

---

## ⚙️ Handling Token Expiry & Automatic Refresh

The Next.js client portal wraps the Firebase Auth SDK to monitor session lifespan:
*   The UI schedules a background worker to run before token expiry.
*   A silent refresh is triggered, fetching a new JWT ID Token without interrupting the active agent conversation.
*   The ADK agent session's bearer header is seamlessly updated.
