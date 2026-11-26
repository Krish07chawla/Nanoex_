# Design: architecture and UML

The diagrams use Mermaid. GitHub shows them automatically; in VS Code install the "Markdown Preview Mermaid Support" extension.

## 1. Architecture

Three layers on the server, so every file has one job:

```mermaid
flowchart LR
    Browser["Browser<br/>React website"] -- "HTTP /api" --> Routes
    Browser -- "WebSocket /ws" --> WS["WebSocket manager"]
    subgraph Server["FastAPI server"]
        Routes["routes/<br/>web endpoints, role checks"] --> Services["services/<br/>the real logic"]
        Services --> Models["models/<br/>database tables"]
        Loop["tick loop<br/>every 5 seconds"] --> Feed["market/feed<br/>latest prices"]
        Loop --> Services
        Loop --> WS
        Services --> Advisor["advisor_service"]
    end
    Models --> DB[("Database<br/>SQLite / PostgreSQL")]
    Feed --> Yahoo["Yahoo Finance<br/>(yfinance)"]
    Feed -. "if Yahoo fails" .-> Demo["Demo feed<br/>(simulated)"]
    Advisor --> Grok["Grok API (xAI)"]
```

- **routes** read the request, check who is calling, call a service, and return the answer.
- **services** hold the rules (trading, wallet, classes, advisor). They do not know about HTTP.
- **models** are the database tables.
- **market** holds the live prices in memory and talks to Yahoo.

## 2. Use cases

```mermaid
flowchart LR
    Admin((Admin)) --> U1[Send / take back virtual money]
    Admin --> U2[View all student accounts]
    Admin --> U3[Disable or enable accounts]
    Admin --> U4[Read audit log]
    Trader((Trader)) --> U5[Create and run live class]
    Trader --> U6[Post notes and ideas]
    Trader --> U7[Answer questions]
    Student((Student)) --> U8[Join class with code]
    Student --> U9[Watch live prices and chart]
    Student --> U10[Buy and sell with virtual money]
    Student --> U11[Watchlist and price alerts]
    Student --> U12[Ask AI advisor]
    Student --> U13[Replay finished class]
    Student --> U14[Ask questions in class]
    U12 -. uses .-> Grok((Grok API))
    U9 -. uses .-> Yahoo((Yahoo Finance))
```

## 3. Class diagram (main classes)

```mermaid
classDiagram
    class User { id; name; email; password_hash; role; is_active }
    class Wallet { id; user_id; balance }
    class WalletTransaction { id; user_id; kind; amount; balance_after; note }
    class Order { id; user_id; symbol; side; order_type; quantity; limit_price; status; fill_price; charges; realized_pnl }
    class Holding { id; user_id; symbol; quantity; avg_price }
    class ClassSession { id; trader_id; title; code; symbols; status }
    class ClassNote { id; class_id; symbol; kind; text; price }
    class ClassQuestion { id; class_id; student_id; text; answer }
    class PriceTick { id; class_id; symbol; price }
    class AiSuggestion { id; user_id; symbol; side; quantity; reason; source }
    class AuditLog { id; actor_id; action; detail }
    class PriceFeed { latest; source; refresh(); price(); get_history() }
    class TradingService { place_order(); fill_order(); process_pending_orders(); get_portfolio() }
    class AdvisorService { get_suggestions(); ask_grok(); rule_based() }

    User "1" --> "1" Wallet
    Wallet "1" --> "*" WalletTransaction
    User "1" --> "*" Order
    User "1" --> "*" Holding
    User "1" --> "*" ClassSession : teaches (trader)
    ClassSession "1" --> "*" ClassNote
    ClassSession "1" --> "*" ClassQuestion
    ClassSession "1" --> "*" PriceTick
    User "1" --> "*" AiSuggestion
    TradingService ..> PriceFeed : reads prices
    AdvisorService ..> TradingService : reads history
    AdvisorService ..> PriceFeed : reads prices
```

## 4. Database (ER diagram)

```mermaid
erDiagram
    users ||--|| wallets : has
    users ||--o{ wallet_transactions : "money ledger"
    users ||--o{ orders : places
    users ||--o{ holdings : owns
    users ||--o{ watchlist_items : watches
    users ||--o{ price_alerts : sets
    users ||--o{ ai_suggestions : receives
    users ||--o{ class_sessions : "teaches"
    users ||--o{ class_members : joins
    class_sessions ||--o{ class_members : has
    class_sessions ||--o{ class_notes : has
    class_sessions ||--o{ class_questions : has
    class_sessions ||--o{ price_ticks : records
    class_sessions ||--o{ student_notes : has
    users ||--o{ audit_logs : "admin actions"
```

## 5. Sequence: login

```mermaid
sequenceDiagram
    actor U as User
    participant W as Website
    participant R as routes/auth
    participant D as Database
    U->>W: email + password
    W->>R: POST /api/auth/login
    R->>D: find user by email
    R->>R: check password (bcrypt)
    R-->>W: token + user
    W->>W: save token, open WebSocket with token
```

## 6. Sequence: admin sends money, student buys

```mermaid
sequenceDiagram
    actor A as Admin
    actor S as Student
    participant API as Server
    participant DB as Database
    A->>API: POST /admin/wallet (amount, students)
    API->>DB: change balance + ledger line + audit log
    S->>API: POST /orders (BUY 10 TCS, MARKET)
    API->>API: read live price from feed
    API->>DB: cash - (value + brokerage), add holding, order FILLED
    API-->>S: order result
```

## 7. Sequence: AI advisor (agent)

```mermaid
sequenceDiagram
    actor S as Student
    participant API as advisor_service
    participant G as Grok API
    participant T as Our tools
    S->>API: Get trade ideas
    API->>G: system prompt + tool list
    loop until Grok has what it needs (max 6 steps)
        G-->>API: call tool (summary / portfolio / stock analysis)
        API->>T: run the tool on our data
        T-->>API: result
        API->>G: tool result
    end
    G-->>API: ideas as JSON
    API->>API: check every idea (stock, quantity, cash)
    API-->>S: safe ideas + "not financial advice"
    Note over API,G: If Grok fails or no key: rule-based advisor answers
```

## 8. Sequence: live class note

```mermaid
sequenceDiagram
    actor T as Trader
    actor S as Student
    participant API as Server
    participant WS as WebSocket manager
    T->>API: POST /classes/5/notes
    API->>API: save note with current price
    API->>WS: send_class(5, note)
    WS-->>S: note appears instantly
```

## 9. Deployment

```mermaid
flowchart LR
    User["Browser"] --> Host["One Docker container<br/>FastAPI + built website"]
    Host --> PG[("PostgreSQL")]
    Host --> Y["Yahoo Finance"]
    Host --> X["xAI Grok API"]
```

## 10. Design decisions (and why)

| Decision | Reason |
|---|---|
| One container serves both website and API | Easiest to run, deploy and explain |
| Orders fill at the live price (no order book) | Keeps the project simple; students learn trading, not exchange internals |
| Prices kept in memory, pushed by WebSocket | Fast and simple; only class prices are saved for replay |
| AI ideas are checked by our code | The AI can make mistakes; the system never trusts it blindly |
| Rule-based advisor as a backup | The feature works with no key and no internet |
| Plain functions and small files | The code is easy to read and explain |
