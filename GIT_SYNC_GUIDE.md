# 🔄 Safe Git Sync Guide

## Current Situation
- **Your Local Changes**: Django encryption, PostgreSQL setup, requirements.txt updates
- **Remote Changes**: Cleanup and archiving of unused scripts
- **Risk**: Potential conflicts in modified files

## 🛡️ Safe Sync Strategy

### Option 1: Automated Safe Sync (Recommended)
```bash
# Run the automated sync script
./safe_git_sync.sh
```

This script will:
1. ✅ Stash your current changes safely
2. ✅ Merge remote changes
3. ✅ Restore your changes on top
4. ✅ Handle conflicts gracefully

### Option 2: Manual Step-by-Step Process

#### Step 1: Backup Your Changes
```bash
# Create a backup branch
git checkout -b backup-django-encryption-$(date +%Y%m%d)
git add .
git commit -m "Backup: Django encryption, PostgreSQL, and requirements updates"

# Return to main branch
git checkout Intranet_setup_DB
```

#### Step 2: Stash Current Changes
```bash
# Stash all your current work
git stash push -m "Django encryption and database work"

# Verify stash was created
git stash list
```

#### Step 3: Pull Remote Changes
```bash
# Pull the latest changes from remote
git pull origin Intranet_setup_DB
```

#### Step 4: Restore Your Changes
```bash
# Apply your stashed changes back
git stash pop
```

#### Step 5: Resolve Any Conflicts
If conflicts occur, you'll see files marked like:
```
# Remote changes
```

Edit each conflict file and choose the correct version.

#### Step 6: Add and Commit Your Changes
```bash
# Add all your files (including new ones)
git add .

# Commit with a descriptive message
git commit -m "Add Django encryption, PostgreSQL setup, and updated requirements

- Implemented field-level encryption for SSH credentials
- Added Django framework with PostgreSQL backend
- Created database migration scripts
- Updated requirements.txt with new dependencies
- Added comprehensive documentation"
```

#### Step 7: Push Your Changes
```bash
# Push to remote
git push origin Intranet_setup_DB
```

## 📁 Your Important Files to Preserve

### Modified Files:
- `meter_dashboard/meter_dashboard/settings.py` - Django settings with PostgreSQL
- `meter_dashboard/meters/models.py` - Django models with encryption
- `requirements.txt` - Updated with Django and encryption packages

### New Files (Critical):
- `meter_dashboard/.env` - **CRITICAL**: Contains encryption key
- `meter_dashboard/meters/encrypted_fields.py` - Encryption implementation
- `meter_dashboard/migrate_existing_db.py` - Database migration script
- All documentation files (*.md)
- All test and utility scripts

## ⚠️ Important Notes

### 🔑 Encryption Key Protection
- **NEVER lose** your `.env` file - it contains the encryption key
- **Backup** the encryption key separately before proceeding
- If you lose the key, encrypted data cannot be recovered

### 🗃️ Database Backup
Your PostgreSQL database contains:
- 7,573 meter readings
- Encrypted Pi setup configurations
- All relationship data

### 📦 Requirements Preservation
Your updated `requirements.txt` includes critical new packages:
- Django framework
- cryptography for encryption
- python-dotenv for environment management

## 🚨 Emergency Recovery

If something goes wrong:

### Restore from Stash:
```bash
git stash list
git stash apply stash@{0}  # Apply most recent stash
```

### Restore from Backup Branch:
```bash
git checkout backup-django-encryption-YYYYMMDD
git checkout Intranet_setup_DB
git merge backup-django-encryption-YYYYMMDD
```

### Force Push (Last Resort):
```bash
# Only if you're sure and have backup
git push --force-with-lease origin Intranet_setup_DB
```

## ✅ Verification Steps

After sync, verify:
1. Django server starts: `python3 manage.py runserver`
2. Database connection works: `python3 test_db_connection.py`
3. Encryption works: `python3 test_encryption.py`
4. All packages install: `pip install -r requirements.txt`

## 📞 Support Commands

### Check what's in your stash:
```bash
git stash list
git stash show -p stash@{0}
```

### See remote changes:
```bash
git log --oneline origin/Intranet_setup_DB..HEAD
```

### Check for conflicts before merge:
```bash
git merge-tree HEAD origin/Intranet_setup_DB
```
