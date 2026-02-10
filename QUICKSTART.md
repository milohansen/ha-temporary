# Quick Start Guide

## Testing the Integration

### 1. Copy to Home Assistant

```bash
# Copy the integration to your Home Assistant custom_components directory
cp -r custom_components/temporary /path/to/homeassistant/custom_components/
```

Or create a symbolic link:
```bash
ln -s $(pwd)/custom_components/temporary /path/to/homeassistant/custom_components/temporary
```

### 2. Restart Home Assistant

Restart Home Assistant to load the new integration.

### 3. Add the Integration

1. Go to **Settings** → **Devices & Services**
2. Click **+ ADD INTEGRATION**
3. Search for **Temporary Entities**
4. Click to add (uses default settings)

### 4. Create Your First Timer

Open **Developer Tools** → **Services** and try:

```yaml
service: timer.create_temporary
data:
  name: "Test Timer"
  duration: 120  # 2 minutes
```

### 5. Watch It Run

Go to **Developer Tools** → **States** and search for `timer.temporary_timer_`

You should see:
- `state`: "active"
- `remaining`: counting down
- `finishes_at`: when it will complete

### 6. Test Operations

Try these services:

**Pause the timer:**
```yaml
service: timer.pause
data:
  entity_id: timer.temporary_timer_XXXXX
```

**Resume the timer:**
```yaml
service: temporary.resume
data:
  entity_id: timer.temporary_timer_XXXXX
```

**Finish immediately:**
```yaml
service: timer.finish
data:
  entity_id: timer.temporary_timer_XXXXX
```

**Delete the timer:**
```yaml
service: temporary.delete
data:
  entity_id: timer.temporary_timer_XXXXX
```

### 7. Test Persistence

1. Create a timer with duration > 60 seconds
2. Let it run for a few seconds
3. Restart Home Assistant
4. Check if timer resumed with correct remaining time

### 8. Test Cleanup

**Short timer (won't persist):**
```yaml
service: timer.create_temporary
data:
  name: "Short Timer"
  duration: 30  # Less than 60s - won't persist
```

**Finished timer cleanup:**
1. Create a 10-second timer
2. Let it finish
3. Wait 30 seconds (grace period)
4. Check if it was auto-removed

### 9. Configure Options

1. Go to **Settings** → **Devices & Services**
2. Find **Temporary Entities**
3. Click **CONFIGURE**
4. Adjust settings:
   - Minimum persist duration: 60s
   - Cleanup interval: 300s
   - Finalized grace period: 30s
   - Inactive max age: 86400s

### 10. Create Automations

**Example: Notification when timer finishes**

```yaml
automation:
  - alias: "Timer Finished"
    trigger:
      - platform: event
        event_type: timer.finished
    action:
      - service: persistent_notification.create
        data:
          title: "Timer Complete!"
          message: "Your timer has finished."
```

**Example: Create timer from dashboard**

Create a script:
```yaml
script:
  start_5min_timer:
    alias: "5 Minute Timer"
    sequence:
      - service: timer.create_temporary
        data:
          name: "5 Minute Timer"
          duration: 300
```

Add to dashboard as a button.

## Common Issues

### Integration doesn't show up
- Check logs: Settings → System → Logs
- Ensure files are in correct location
- Restart Home Assistant

### Timer not persisting
- Check duration is > 60 seconds (default min_persist_duration)
- Check entity in Developer Tools → States before restart

### Timer not cleaning up
- Check cleanup_interval (default 5 minutes)
- Check logs for cleanup task execution
- Ensure timer is finalized (state = "idle")

## Debug Mode

Enable debug logging in `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.temporary: debug
```

Then check logs for detailed information about:
- Entity registration
- Timer operations
- Cleanup tasks
- State restoration

## Next Steps

- Create custom automations with timers
- Extend to add new temporary entity types
- Customize cleanup parameters for your use case
- Share your creations with the community!

## Support

- Report issues: GitHub Issues
- Discuss: Home Assistant Community Forum
- Documentation: README.md
