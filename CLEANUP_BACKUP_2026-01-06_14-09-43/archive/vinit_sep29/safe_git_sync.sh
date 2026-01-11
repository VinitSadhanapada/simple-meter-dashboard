#!/bin/bash
# Safe Git Sync Script
# Preserves local changes while syncing with remote repository

echo "🔄 Safe Git Sync Process"
echo "========================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Step 1: Create a backup of current work
print_status "Step 1: Creating backup of current changes..."
BACKUP_BRANCH="backup-$(date +%Y%m%d-%H%M%S)"
git stash push -m "Backup before sync: Django encryption, requirements, and database work"

if [ $? -eq 0 ]; then
    print_success "Created stash with all current changes"
else
    print_error "Failed to create stash"
    exit 1
fi

# Step 2: Show what we're about to merge
print_status "Step 2: Reviewing remote changes..."
echo "Remote commits to be merged:"
git log --oneline --graph HEAD..origin/Intranet_setup_DB

# Step 3: Check for potential conflicts
print_status "Step 3: Checking for potential conflicts..."
CONFLICT_FILES=""

# Check each modified file against remote
for file in $(git diff --name-only HEAD); do
    if git diff --quiet HEAD origin/Intranet_setup_DB -- "$file" 2>/dev/null; then
        print_status "✅ No conflict in: $file"
    else
        print_warning "⚠️  Potential conflict in: $file"
        CONFLICT_FILES="$CONFLICT_FILES $file"
    fi
done

# Step 4: Perform the merge
print_status "Step 4: Merging remote changes..."
git merge origin/Intranet_setup_DB --no-edit

if [ $? -eq 0 ]; then
    print_success "Merge completed successfully"
else
    print_error "Merge failed - conflicts detected"
    print_status "Aborting merge and restoring your changes..."
    git merge --abort
    git stash pop
    exit 1
fi

# Step 5: Restore your changes
print_status "Step 5: Restoring your local changes..."
git stash pop

if [ $? -eq 0 ]; then
    print_success "Your changes have been restored"
else
    print_warning "Some conflicts occurred while restoring changes"
    print_status "Your changes are still safe in the stash"
    print_status "Use 'git stash list' to see them"
fi

# Step 6: Show current status
print_status "Step 6: Current status after sync..."
git status

echo ""
print_status "Next steps:"
echo "1. Review any conflicts and resolve them"
echo "2. Test your application to ensure everything works"
echo "3. Add and commit your changes: git add . && git commit -m 'Your message'"
echo "4. Push to remote: git push origin Intranet_setup_DB"

echo ""
print_success "Sync process completed!"
