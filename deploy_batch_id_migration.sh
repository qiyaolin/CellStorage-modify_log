#!/bin/bash

# Deploy batch_id migration to Google Cloud
# This script runs the database migration and then deploys the updated application

echo "🚀 Starting batch_id migration deployment..."
echo "=" * 50

# Check if gcloud is authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | head -n 1 > /dev/null; then
    echo "❌ Not authenticated with gcloud. Please run 'gcloud auth login'"
    exit 1
fi

# Get current project
PROJECT=$(gcloud config get-value project)
echo "📋 Current project: $PROJECT"

# Step 1: Run the migration
echo ""
echo "🔄 Step 1: Running database migration..."
python migrations/add_batch_id_to_print_jobs.py migrate

if [ $? -ne 0 ]; then
    echo "❌ Migration failed. Stopping deployment."
    exit 1
fi

# Step 2: Verify migration
echo ""
echo "🔍 Step 2: Verifying migration..."
python migrations/add_batch_id_to_print_jobs.py verify

if [ $? -ne 0 ]; then
    echo "❌ Migration verification failed. Stopping deployment."
    exit 1
fi

# Step 3: Deploy the application
echo ""
echo "🚀 Step 3: Deploying application to App Engine..."
gcloud app deploy app.yaml --quiet

if [ $? -ne 0 ]; then
    echo "❌ App Engine deployment failed."
    exit 1
fi

# Step 4: Final verification
echo ""
echo "🧪 Step 4: Testing deployment..."
echo "Waiting 30 seconds for deployment to stabilize..."
sleep 30

# Get the app URL
APP_URL=$(gcloud app browse --no-launch-browser)
echo "🌐 Application URL: $APP_URL"

# Test if the app is responding
if curl -f -s "$APP_URL" > /dev/null; then
    echo "✅ Application is responding"
else
    echo "⚠️  Application may not be fully ready yet"
fi

echo ""
echo "🎉 Deployment completed!"
echo ""
echo "📋 Summary:"
echo "  ✅ Database migration applied"
echo "  ✅ Migration verified"
echo "  ✅ Application deployed"
echo ""
echo "🔧 Next steps:"
echo "  1. Test print job functionality in the web interface"
echo "  2. Verify batch linking is working"
echo "  3. Check application logs for any issues:"
echo "     gcloud app logs tail -s default"
echo ""
echo "💡 If issues occur, you can rollback the migration:"
echo "   python migrations/add_batch_id_to_print_jobs.py rollback"