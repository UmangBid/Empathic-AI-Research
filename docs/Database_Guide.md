# Empathic AI Research Database Guide

## Database Location
`c:\Users\umang\OneDrive\Desktop\Clg Materials\Research\Empathic AI Research\data\database\conversations.db`

## Database Schema

### 1. PARTICIPANTS Table
**Purpose**: Stores information about each study participant

| Column | Type | Description |
|--------|------|-------------|
| `id` | STRING (Primary Key) | Unique participant ID (e.g., "PBE1EA8EF") |
| `bot_type` | STRING | Bot assigned: "emotional", "cognitive", "motivational", or "neutral" |
| `start_time` | DATETIME | When the conversation started |
| `end_time` | DATETIME | When the conversation ended (NULL if incomplete) |
| `total_messages` | INTEGER | Total number of messages in conversation |
| `completed` | BOOLEAN | Whether participant completed all 20 messages |
| `crisis_flagged` | BOOLEAN | Whether any crisis keywords were detected |

**Key Research Queries:**
```sql
-- Count participants by bot type
SELECT bot_type, COUNT(*) as participant_count 
FROM participants 
GROUP BY bot_type;

-- Find completed conversations
SELECT * FROM participants WHERE completed = 1;

-- Average conversation length by bot type
SELECT bot_type, AVG(total_messages) as avg_messages 
FROM participants 
GROUP BY bot_type;
```

### 2. MESSAGES Table
**Purpose**: Stores every individual message in conversations

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER (Primary Key) | Auto-incrementing message ID |
| `participant_id` | STRING (Foreign Key) | Links to participants.id |
| `message_num` | INTEGER | Message number in conversation (1-20 for users) |
| `sender` | STRING | "user" or "bot" |
| `content` | TEXT | The actual message text |
| `timestamp` | DATETIME | When the message was sent |
| `contains_crisis_keyword` | BOOLEAN | Whether message contains crisis indicators |

**Key Research Queries:**
```sql
-- Get full conversation for a participant
SELECT message_num, sender, content, timestamp 
FROM messages 
WHERE participant_id = 'PBE1EA8EF' 
ORDER BY timestamp;

-- Find all crisis-flagged messages
SELECT participant_id, sender, content, timestamp 
FROM messages 
WHERE contains_crisis_keyword = 1;

-- Average message length by bot type
SELECT p.bot_type, AVG(LENGTH(m.content)) as avg_message_length
FROM messages m
JOIN participants p ON m.participant_id = p.id
WHERE m.sender = 'bot'
GROUP BY p.bot_type;
```

### 3. CRISIS_FLAGS Table
**Purpose**: Detailed crisis detection logs

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER (Primary Key) | Auto-incrementing flag ID |
| `participant_id` | STRING (Foreign Key) | Which participant |
| `message_id` | INTEGER (Foreign Key) | Which specific message |
| `keyword_matched` | STRING | The crisis keyword that was detected |
| `flagged_at` | DATETIME | When the flag was created |
| `severity_level` | STRING | "high", "medium", or "low" |

### 4. EXPORT_LOGS Table
**Purpose**: Tracks data exports for audit trail

## Common Research Queries

### Participant Analysis
```sql
-- Completion rates by bot type
SELECT 
    bot_type,
    COUNT(*) as total_participants,
    SUM(completed) as completed_participants,
    (SUM(completed) * 100.0 / COUNT(*)) as completion_rate
FROM participants 
GROUP BY bot_type;
```

### Conversation Analysis
```sql
-- User message lengths by bot type
SELECT 
    p.bot_type,
    AVG(LENGTH(m.content)) as avg_user_message_length,
    COUNT(m.id) as total_user_messages
FROM messages m
JOIN participants p ON m.participant_id = p.id
WHERE m.sender = 'user'
GROUP BY p.bot_type;
```

### Crisis Detection Analysis
```sql
-- Crisis detection rates by bot type
SELECT 
    p.bot_type,
    COUNT(DISTINCT p.id) as total_participants,
    COUNT(DISTINCT CASE WHEN p.crisis_flagged = 1 THEN p.id END) as crisis_participants,
    (COUNT(DISTINCT CASE WHEN p.crisis_flagged = 1 THEN p.id END) * 100.0 / COUNT(DISTINCT p.id)) as crisis_rate
FROM participants p
GROUP BY p.bot_type;
```

## Data Export Tips

### For Excel Analysis
1. Right-click any table → Export → CSV
2. Open in Excel for statistical analysis
3. Use pivot tables for bot type comparisons

### For Statistical Software (R/Python/SPSS)
1. Export entire database: File → Export → Database to SQL file
2. Or export specific tables as CSV
3. Import into your preferred statistical software

## Database Maintenance

### Backup
- Regularly copy the entire `conversations.db` file
- Consider automated backups before data collection sessions

### Monitoring
- Check participant completion rates regularly
- Monitor crisis flag frequencies
- Verify data integrity with participant counts

## Troubleshooting

### Database Locked
- Close all applications using the database
- Ensure no Streamlit apps are running on the database

### Data Not Appearing
- Refresh the database view (F5)
- Check if the main app is properly saving data
- Verify file permissions on the database folder