# Meter Dashboard FAQ & Troubleshooting

## FAQ

**Q: Why is my deployment stuck in IN_PROGRESS?**
A: Check that Celery worker and Redis server are running. Check logs for errors.

**Q: Why are files not deleted from the Pi during OTA?**
A: Ensure `--delete` is used in rsync and source/destination paths are correct. Check exclude rules.

**Q: Why is 'Completed at' blank?**
A: Make sure the code uses `timezone.now()` and Celery worker is restarted after code changes.

**Q: How do I set up SSH keys for Pi?**
A: Use the admin action "Set up SSH keys" for selected Pis. Ensure SSH password is set.

**Q: How do I keep Celery running?**
A: Use systemd or supervisor to manage Celery as a background service.

## Troubleshooting Steps
- Check Django, Celery, and Redis logs for errors.
- Verify SSH credentials and network connectivity to Pi.
- Ensure all required packages are installed.
- Restart Celery worker after code changes.
- Use `--dry-run` with rsync for debugging file sync issues.

---
