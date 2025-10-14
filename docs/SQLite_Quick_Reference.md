# Quick Reference: SQLite Browser for Empathic AI Research

## Essential Views for Research

### 1. Participant Overview
**Browse Data Tab** → Select `participants` table
- Sort by `start_time` to see chronological order
- Filter by `bot_type` to compare groups
- Check `completed` column for completion rates

### 2. Conversation Details
**Browse Data Tab** → Select `messages` table
- Filter by `participant_id` to see full conversations
- Sort by `timestamp` for chronological order
- Use `sender` filter to see only user or bot messages

### 3. Crisis Monitoring
**Browse Data Tab** → Select `crisis_flags` table
- Review all flagged conversations
- Check `severity_level` for priority

## Essential SQL Queries (Execute SQL Tab)

### Quick Stats
```sql
-- Total participants and completion rate
SELECT 
    COUNT(*) as total_participants,
    SUM(completed) as completed,
    AVG(total_messages) as avg_messages,
    COUNT(CASE WHEN crisis_flagged = 1 THEN 1 END) as crisis_count
FROM participants;
```

### Bot Type Comparison
```sql
-- Compare bot performance
SELECT 
    bot_type,
    COUNT(*) as participants,
    AVG(total_messages) as avg_messages,
    SUM(completed) as completed,
    (SUM(completed) * 100.0 / COUNT(*)) as completion_rate
FROM participants 
GROUP BY bot_type
ORDER BY completion_rate DESC;
```

### Recent Activity
```sql
-- Last 10 conversations
SELECT 
    p.id as participant,
    p.bot_type,
    p.total_messages,
    p.completed,
    datetime(p.start_time, 'localtime') as started
FROM participants p
ORDER BY p.start_time DESC
LIMIT 10;
```

## Data Export Steps

### For Excel Analysis
1. Right-click table → Export → CSV
2. Choose location and filename
3. Open in Excel for pivot tables and charts

### For Statistical Analysis
1. Execute SQL → Run your query
2. Export results → CSV
3. Import into R/Python/SPSS

## Daily Research Workflow

1. **Open Database**: Launch SQLite Browser → Open conversations.db
2. **Check New Data**: Browse participants table, sort by start_time DESC
3. **Monitor Crisis**: Check crisis_flags table for any new flags
4. **Export Data**: Weekly export for analysis
5. **Run Reports**: Use SQL queries for progress reports

## Keyboard Shortcuts
- `F5`: Refresh view
- `Ctrl+T`: New tab
- `F9`: Execute SQL
- `Ctrl+E`: Export current view