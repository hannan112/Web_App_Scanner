#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

// List of files that need migration (from your find command)
const filesToMigrate = [
  'src/app/(auth)/verify-email/[token]/page.tsx',
  'src/app/(auth)/password-reset-confirm/[token]/page.tsx',
  'src/app/(dashboard)/projects/[id]/scan/new/page.tsx',
  'src/app/(dashboard)/projects/[id]/scan/page.tsx',
  'src/app/(dashboard)/projects/[id]/edit/page.tsx',
  'src/app/(dashboard)/projects/[id]/scans/[scanId]/status/page.tsx',
  'src/app/(dashboard)/projects/[id]/scans/[scanId]/results/page.tsx',
  'src/app/(dashboard)/projects/[id]/scans/[scanId]/page.tsx',
  'src/app/(dashboard)/projects/[id]/scans/new/page.tsx',
  'src/app/(dashboard)/projects/[id]/scans/page.tsx',
  'src/app/(dashboard)/projects/[id]/page.tsx',
  'src/app/(dashboard)/scans/[id]/status/page.tsx',
  'src/app/(dashboard)/scans/[id]/results/page.tsx',
];

function migrateFile(filePath) {
  console.log(`Migrating: ${filePath}`);
  
  // Read the file
  const content = fs.readFileSync(filePath, 'utf8');
  
  // Create backup
  fs.writeFileSync(filePath + '.backup', content);
  console.log(`  ✓ Backup created: ${filePath}.backup`);
  
  let migratedContent = content;
  
  // 1. Convert params type from object to Promise
  migratedContent = migratedContent.replace(
    /params:\s*\{([^}]+)\}/g,
    'params: Promise<{$1}>'
  );
  
  // 2. Convert searchParams type from object to Promise
  migratedContent = migratedContent.replace(
    /searchParams:\s*\{([^}]+)\}/g,
    'searchParams: Promise<{$1}>'
  );
  
  // 3. Make the function async if it's not already
  if (!migratedContent.includes('export default async function')) {
    migratedContent = migratedContent.replace(
      /export default function/g,
      'export default async function'
    );
  }
  
  // 4. Add await to params usage - this is more complex, we need to handle various patterns
  
  // Pattern 1: Direct destructuring { token } = params
  migratedContent = migratedContent.replace(
    /const\s*\{([^}]+)\}\s*=\s*params;/g,
    'const {$1} = await params;'
  );
  
  // Pattern 2: Direct property access params.token
  migratedContent = migratedContent.replace(
    /params\.(\w+)/g,
    '(await params).$1'
  );
  
  // 5. Add await to searchParams usage
  
  // Pattern 1: Direct access searchParams?.something
  migratedContent = migratedContent.replace(
    /searchParams\?\./g,
    '(await searchParams)?.'
  );
  
  // Pattern 2: searchParams.something
  migratedContent = migratedContent.replace(
    /(?<!await\s)searchParams\.(\w+)/g,
    '(await searchParams).$1'
  );
  
  // Pattern 3: const something = searchParams
  migratedContent = migratedContent.replace(
    /const\s+(\w+)\s*=\s*searchParams;/g,
    'const $1 = await searchParams;'
  );
  
  // 6. Handle validation patterns - common Next.js patterns
  
  // Pattern: if (!params.token)
  migratedContent = migratedContent.replace(
    /if\s*\(\s*!params\.(\w+)/g,
    'if (!(await params).$1'
  );
  
  // Pattern: if (!searchParams?.something)
  migratedContent = migratedContent.replace(
    /if\s*\(\s*!searchParams\?\./g,
    'if (!(await searchParams)?.'
  );
  
  // 7. Clean up double awaits that might have been created
  migratedContent = migratedContent.replace(
    /await\s+await\s+/g,
    'await '
  );
  
  // 8. Clean up (await (await params))
  migratedContent = migratedContent.replace(
    /\(await\s+\(await\s+params\)\)/g,
    '(await params)'
  );
  
  // Write the migrated content
  fs.writeFileSync(filePath, migratedContent);
  console.log(`  ✓ Migrated successfully`);
  
  return true;
}

function main() {
  console.log('🚀 Starting Next.js 15 migration...\n');
  
  let successCount = 0;
  let errorCount = 0;
  
  filesToMigrate.forEach(filePath => {
    try {
      if (fs.existsSync(filePath)) {
        migrateFile(filePath);
        successCount++;
      } else {
        console.log(`⚠️  File not found: ${filePath}`);
      }
    } catch (error) {
      console.error(`❌ Error migrating ${filePath}:`, error.message);
      errorCount++;
    }
    console.log(''); // Empty line for readability
  });
  
  console.log('📊 Migration Summary:');
  console.log(`  ✅ Successfully migrated: ${successCount} files`);
  console.log(`  ❌ Errors: ${errorCount} files`);
  console.log(`  📁 Backups created with .backup extension`);
  
  if (errorCount === 0) {
    console.log('\n🎉 Migration completed successfully!');
    console.log('📝 Next steps:');
    console.log('  1. Run: npm run build');
    console.log('  2. Test your application');
    console.log('  3. If everything works, you can delete .backup files');
    console.log('  4. If there are issues, restore from .backup files');
  } else {
    console.log('\n⚠️  Some files had errors. Check the logs above.');
    console.log('  - Review the failed files manually');
    console.log('  - Restore from .backup files if needed');
  }
}

// Run the migration
main();
