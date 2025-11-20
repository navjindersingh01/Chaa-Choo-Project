#!/bin/bash
# cleanup-for-production.sh
# Removes unused/test files before deployment to VPS
# Run: bash cleanup-for-production.sh

echo "🧹 Chaa Choo Café - Production Cleanup Script"
echo "=============================================="
echo ""
echo "This script will remove the following files:"
echo ""

# Files to remove
FILES_TO_REMOVE=(
    "test_end_to_end.py"
    "test_fixes.py"
    "insert_dummy_orders.py"
    "set_passwords_and_roles.py"
    "update_alice_password.py"
    "CHANGELOG.md"
    "CHANGES_DETAILED.md"
    "DEPLOYMENT_COMPLETE.md"
    "DEPLOYMENT_GUIDE.md"
    "DEPLOYMENT_READY.md"
    "DOCKER_GUIDE.md"
    "Dockerfile"
    "docker-compose.yml"
    "ISSUES_RESOLVED.txt"
    "FIXES_SUMMARY.md"
    "FIXES_VERIFICATION.md"
    "IMPLEMENTATION.md"
    "SOLUTION_SUMMARY.md"
    "error.log"
)

# Display files to be removed
for file in "${FILES_TO_REMOVE[@]}"; do
    if [ -f "$file" ] || [ -d "$file" ]; then
        echo "  ❌ $file"
    fi
done

echo ""
echo "Directories to keep:"
echo "  ✅ .vscode/ (local development only, not uploaded to VPS)"
echo ""

# Confirm
read -p "Continue with cleanup? (yes/no): " -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Cleanup cancelled."
    exit 1
fi

# Remove files
for file in "${FILES_TO_REMOVE[@]}"; do
    if [ -f "$file" ]; then
        rm -v "$file"
        echo "✅ Removed: $file"
    elif [ -d "$file" ]; then
        rm -rv "$file"
        echo "✅ Removed directory: $file"
    fi
done

# Remove .vscode from git tracking (but keep locally)
if [ -d ".vscode" ]; then
    echo ""
    echo "Removing .vscode from git tracking (keeping local copy)..."
    git rm -r --cached .vscode 2>/dev/null || true
    echo "✅ .vscode removed from git index"
fi

# Create .gitignore entry
if ! grep -q "\.vscode" .gitignore 2>/dev/null; then
    echo ".vscode/" >> .gitignore
    echo "✅ Added .vscode to .gitignore"
fi

echo ""
echo "🎉 Cleanup complete!"
echo ""
echo "Next steps:"
echo "  1. Review remaining files: git status"
echo "  2. Commit changes: git add -A && git commit -m 'Production cleanup'"
echo "  3. Push to repository: git push origin main"
echo "  4. Follow DEPLOY_FINAL.md for VPS deployment"
echo ""
