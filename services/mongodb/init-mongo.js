// =============================================================================
// Infra Hub - MongoDB Initialization Script
// =============================================================================
// This script runs on first container startup when the data volume is empty.
// Use it to create shared databases, collections, or users for your projects.

// Switch to admin database
db = db.getSiblingDB('admin');

// Create an application user with readWrite access to all databases
// Uncomment and modify as needed
/*
db.createUser({
    user: 'app_user',
    pwd: 'app_password',
    roles: [
        { role: 'readWriteAnyDatabase', db: 'admin' }
    ]
});
*/

// Create example project databases with initial collections
// Uncomment and modify as needed for your projects

/*
// Project A
db = db.getSiblingDB('project_a');
db.createCollection('settings');
db.settings.insertOne({ initialized: true, createdAt: new Date() });

// Project B
db = db.getSiblingDB('project_b');
db.createCollection('settings');
db.settings.insertOne({ initialized: true, createdAt: new Date() });
*/

// Create infra database for the management platform
db = db.getSiblingDB('infra');
db.createCollection('services');
db.services.insertOne({
    name: 'infra-hub',
    version: '1.0.0',
    initialized: true,
    createdAt: new Date()
});

print('Infra Hub MongoDB initialized successfully');
