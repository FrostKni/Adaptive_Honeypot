# Dashboard Tour - Complete Feature Walkthrough

## Dashboard Overview

The React dashboard provides real-time visualization of all honeypot activity, AI decisions, and cognitive profiles.

---

## 1. Login Page

### Screenshot: `screenshots/01_login.png`

**Features**:
- Dark theme matching cybersecurity aesthetic
- JWT authentication
- Session persistence
- Error handling for invalid credentials

**Access**:
- URL: http://localhost:3000
- Default username: admin
- Password: (from .env ADMIN_PASSWORD)

**Flow**:
1. User enters credentials
2. JWT token obtained from `/api/v1/auth/login`
3. Token stored in localStorage
4. User redirected to dashboard
5. WebSocket connection established for real-time updates

---

## 2. Main Dashboard

### Screenshot: `screenshots/02_dashboard.png`

**Components**:

### 2.1 Statistics Cards

Top row shows:
- **Active Honeypots**: Count of running honeypot containers
- **Active Sessions**: Current attacker sessions
- **Total Attacks Today**: Daily attack count
- **Threat Level**: Current threat assessment (Low/Medium/High/Critical)

### 2.2 Attack Visualization Map

**Location**: Center of dashboard

**Features**:
- World map with Leaflet
- Real-time attack origin visualization
- Color-coded by threat level:
  - Green: Low
  - Yellow: Medium
  - Orange: High
  - Red: Critical
- Clickable markers for session details

**Data Source**: WebSocket events from `/api/v1/ws`

### 2.3 Attack Timeline Chart

**Location**: Bottom left

**Features**:
- Chart.js line graph
- X-axis: Time (last 24 hours)
- Y-axis: Attack count
- Multiple lines by protocol:
  - Blue: SSH
  - Green: HTTP
  - Purple: FTP
  - Orange: Telnet

**Updates**: Real-time via WebSocket

### 2.4 Recent Attacks Feed

**Location**: Bottom right

**Features**:
- Scrollable list of recent attacks
- Each entry shows:
  - Source IP
  - Attack type
  - Timestamp
  - Honeypot type
  - Threat level badge
- Clickable for session details

---

## 3. Honeypots Page

### Screenshot: `screenshots/03_honeypots.png`

**Features**:

### 3.1 Honeypot List

Grid view showing all honeypot instances:

**Each Card Shows**:
- Honeypot name
- Protocol type (SSH/HTTP/FTP/Telnet)
- Status indicator (Running/Stopped/Error)
- Port number
- Total sessions count
- Last attack timestamp

**Actions**:
- **Deploy New**: Create new honeypot instance
- **Stop**: Stop a running honeypot
- **Restart**: Restart honeypot container
- **View Sessions**: See all sessions for this honeypot

### 3.2 Deploy Honeypot Modal

**Screenshot**: `screenshots/04_deploy_honeypot.png`

**Form Fields**:
- Honeypot name
- Protocol type selection
- Port assignment
- Interaction level (Low/Medium/High/Aggressive)
- Custom configuration (JSON)

**Flow**:
1. Click "Deploy Honeypot" button
2. Fill form
3. Submit → POST to `/api/v1/honeypots`
4. Backend creates Docker container
5. WebSocket broadcasts new honeypot event
6. Dashboard updates in real-time

---

## 4. Attacks Page

### Screenshot: `screenshots/05_attacks.png`

**Features**:

### 4.1 Attack Event Table

**Columns**:
- Timestamp
- Source IP + Country flag
- Honeypot type
- Attack type (Brute Force, Command Injection, etc.)
- Severity badge
- Session ID

**Filters**:
- Date range picker
- Honeypot type dropdown
- Attack type dropdown
- Severity dropdown
- Search by IP

**Sorting**:
- Click column headers
- Default: Newest first

### 4.2 Attack Details Modal

**Screenshot**: `screenshots/06_attack_details.png`

**Information**:
- Full event details
- Source IP geolocation
- Attack timeline
- Commands executed
- Credentials tried
- MITRE ATT&CK mapping
- AI threat assessment

---

## 5. Sessions Page

### Screenshot: `screenshots/07_sessions.png`

**Features**:

### 5.1 Session List

Table showing all attacker sessions:

**Columns**:
- Session ID
- Source IP
- Honeypot
- Duration
- Commands count
- Status (Active/Closed)
- Start time
- Actions (View Details, Replay)

### 5.2 Session Replay

**Screenshot**: `screenshots/08_session_replay.png`

**Features**:
- Terminal recording replay
- Asciinema player integration
- Timeline scrubber
- Speed control (0.5x, 1x, 2x)
- Full command history
- Copy commands to clipboard

**How It Works**:
1. Cowrie records terminal sessions as asciicast
2. Stored in database
3. Frontend fetches via `/api/v1/sessions/{id}/replay`
4. Renders using asciinema-player

---

## 6. AI Monitor Page

### Screenshot**: `screenshots/09_ai_monitor.png`

**Features**:

### 6.1 AI Service Status

**Indicators**:
- Service status (Running/Stopped)
- Active AI provider
- Model in use
- Uptime
- Queue length

### 6.2 Recent AI Decisions

**Each Decision Shows**:
- Timestamp
- Source IP
- Threat level
- Action taken (Monitor/Reconfigure/Isolate)
- Reasoning summary
- Confidence score

**Detail View**:
- Full AI reasoning
- MITRE ATT&CK techniques identified
- Recommended actions
- Configuration changes applied

### 6.3 Activity Timeline

**Features**:
- Visual timeline of AI activities
- Color-coded by action type
- Duration indicators
- Click for details

### 6.4 Control Panel

**Actions**:
- **Start AI Service**: Begin monitoring
- **Stop AI Service**: Pause monitoring
- **Trigger Analysis**: Manual analysis trigger
- **View Activity Log**: Full log view

---

## 7. Cognitive Dashboard

### Screenshot**: `screenshots/10_cognitive_dashboard.png`

**Features**:

### 7.1 Cognitive Profiles Overview

**Shows**:
- Total profiles created
- Active sessions being profiled
- Average confidence score
- Most common bias detected

### 7.2 Bias Detection Breakdown

**Chart**: Pie chart showing distribution of detected biases

**Legend**:
- Confirmation Bias (typically 25-30%)
- Sunk Cost Fallacy (20-25%)
- Dunning-Kruger (15-20%)
- Anchoring (10-15%)
- Others

### 7.3 Active Profiles

**List View**:
- Session ID
- Detected biases (with confidence)
- Mental model summary
- Deception strategies applied
- Engagement duration

**Click for Details**:
- Full cognitive profile
- Command-by-command analysis
- Mental model state
- Deception effectiveness

### 7.4 Strategy Effectiveness

**Table**:
- Strategy name
- Target bias
- Times used
- Effectiveness score
- Average engagement increase

---

## 8. Settings Page

### Screenshot**: `screenshots/11_settings.png`

**Sections**:

### 8.1 AI Configuration

**Options**:
- AI Provider selection (OpenAI/Anthropic/Gemini/Local)
- Model selection
- Temperature slider
- Max tokens
- Enable/disable streaming
- API key management

### 8.2 Honeypot Settings

**Options**:
- Max instances
- Adaptation threshold
- Analysis interval
- Session timeout
- Enable/disable protocols

### 8.3 Alert Configuration

**Options**:
- Email alerts (SMTP settings)
- Slack webhook
- Discord webhook
- Custom webhook
- Alert thresholds

### 8.4 Security Settings

**Options**:
- JWT expiration time
- Rate limiting
- CORS origins
- API key management

---

## 9. Real-Time Updates

### WebSocket Events

All pages receive real-time updates via WebSocket connection:

**Event Types**:
```typescript
// New attack detected
{
  type: "attack_event",
  data: {
    id: "attack-123",
    source_ip: "192.168.1.100",
    honeypot_type: "ssh",
    attack_type: "brute_force",
    severity: "high",
    timestamp: "2026-04-04T10:30:00Z"
  }
}

// Honeypot status change
{
  type: "honeypot_update",
  data: {
    id: "honeypot-ssh-01",
    status: "running",
    sessions: 5
  }
}

// AI decision made
{
  type: "ai_decision",
  data: {
    id: "decision-456",
    threat_level: "high",
    action: "reconfigure",
    reasoning: "..."
  }
}

// Cognitive profile update
{
  type: "cognitive_update",
  data: {
    session_id: "session-789",
    biases_detected: ["confirmation_bias", "sunk_cost"],
    confidence: 0.85
  }
}
```

---

## 10. Responsive Design

**Breakpoints**:
- Mobile: < 768px (stacked layout)
- Tablet: 768px - 1024px (2-column layout)
- Desktop: > 1024px (full dashboard)

**Mobile Features**:
- Collapsible sidebar
- Simplified charts
- Swipeable tabs
- Touch-friendly buttons

---

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `?` | Show keyboard shortcuts |
| `d` | Go to Dashboard |
| `h` | Go to Honeypots |
| `a` | Go to Attacks |
| `s` | Go to Sessions |
| `m` | Go to AI Monitor |
| `c` | Go to Cognitive Dashboard |
| `Esc` | Close modal |

---

## Performance

**Load Times**:
- Initial page load: < 2s
- Dashboard data: < 500ms
- WebSocket connection: < 100ms
- Chart rendering: < 200ms

**Optimizations**:
- Code splitting by route
- Lazy loading of charts
- WebSocket connection pooling
- React.memo for expensive components
- Virtual scrolling for long lists
