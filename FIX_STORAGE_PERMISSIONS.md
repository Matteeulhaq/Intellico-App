# Fix Storage Permission Error

## Error
```
{"error":"[Errno 13] Permission denied: 'storage/b37abf7e-1151-4d82-be86-6a38d5f10e7f.pdf'"}
```

## Quick Fix

Run these commands to fix the storage directory permissions:

```bash
# Navigate to backend directory
cd backend

# Create storage directory if it doesn't exist
mkdir -p storage

# Fix permissions (allow read/write/execute for owner, read/execute for group and others)
chmod 755 storage

# If that doesn't work, try more permissive (not recommended for production)
chmod 777 storage

# Ensure you own the directory
sudo chown -R $USER:$USER storage
```

## Verify It Works

```bash
# Check if directory exists and has correct permissions
ls -ld backend/storage

# Should show something like:
# drwxr-xr-x 2 yourusername yourgroup 4096 ... storage
```

## Alternative: Use Absolute Path in .env

If you're still having issues, you can specify an absolute path in your `.env` file:

```bash
# In .env file
STORAGE_PATH=/home/mattee/Intellico-App/backend/storage
```

Then ensure that directory has proper permissions:

```bash
mkdir -p /home/mattee/Intellico-App/backend/storage
chmod 755 /home/mattee/Intellico-App/backend/storage
```

## Why This Happens

1. **Directory doesn't exist**: The storage directory wasn't created
2. **Wrong permissions**: Directory exists but Flask app can't write to it
3. **Wrong ownership**: Directory is owned by root or another user
4. **Relative path issue**: App is running from a different directory than expected

## Prevention

The code has been updated to:
- Use absolute paths (relative to backend directory)
- Create directory with proper permissions (755)
- Provide better error messages

After fixing permissions, restart your Flask server:

```bash
cd backend
python -m app.main
```

