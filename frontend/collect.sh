#!/bin/bash

# Script to collect remaining files that need Next.js 15 migration
# This will create a single file with all the code for easy review

OUTPUT_FILE="remaining_files_to_fix.txt"

# List of remaining files to collect
FILES=(
    "src/app/(auth)/verify-email/[token]/page.tsx"
    "src/app/(auth)/password-reset-confirm/[token]/page.tsx"
    "src/app/(dashboard)/projects/[id]/scan/page.tsx"
    "src/app/(dashboard)/projects/[id]/edit/page.tsx"
    "src/app/(dashboard)/projects/[id]/scans/new/page.tsx"
    "src/app/(dashboard)/projects/[id]/scans/page.tsx"
    "src/app/(dashboard)/projects/[id]/page.tsx"
    "src/app/(dashboard)/scans/[id]/status/page.tsx"
    "src/app/(dashboard)/scans/[id]/results/page.tsx"
)

# Clear the output file
> "$OUTPUT_FILE"

echo "🔍 Collecting remaining files that need Next.js 15 migration..."
echo "📁 Output file: $OUTPUT_FILE"
echo ""

# Header for the output file
echo "=========================================" >> "$OUTPUT_FILE"
echo "REMAINING FILES TO FIX FOR NEXT.JS 15" >> "$OUTPUT_FILE"
echo "Generated on: $(date)" >> "$OUTPUT_FILE"
echo "=========================================" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

# Counter for found files
found_count=0
missing_count=0

# Loop through each file and collect content
for file in "${FILES[@]}"; do
    echo "Processing: $file"
    
    if [ -f "$file" ]; then
        echo "" >> "$OUTPUT_FILE"
        echo "=========================================" >> "$OUTPUT_FILE"
        echo "FILE: $file" >> "$OUTPUT_FILE"
        echo "=========================================" >> "$OUTPUT_FILE"
        echo "" >> "$OUTPUT_FILE"
        
        # Add the file content
        cat "$file" >> "$OUTPUT_FILE"
        
        echo "" >> "$OUTPUT_FILE"
        echo "========== END OF $file ==========" >> "$OUTPUT_FILE"
        echo "" >> "$OUTPUT_FILE"
        
        found_count=$((found_count + 1))
        echo "  ✅ Added to collection"
    else
        echo "  ⚠️  File not found: $file"
        missing_count=$((missing_count + 1))
        
        # Log missing files in the output
        echo "" >> "$OUTPUT_FILE"
        echo "=========================================" >> "$OUTPUT_FILE"
        echo "MISSING FILE: $file" >> "$OUTPUT_FILE"
        echo "=========================================" >> "$OUTPUT_FILE"
        echo "This file was not found in the current directory." >> "$OUTPUT_FILE"
        echo "" >> "$OUTPUT_FILE"
    fi
done

# Summary at the end of the file
echo "" >> "$OUTPUT_FILE"
echo "=========================================" >> "$OUTPUT_FILE"
echo "COLLECTION SUMMARY" >> "$OUTPUT_FILE"
echo "=========================================" >> "$OUTPUT_FILE"
echo "Total files to collect: ${#FILES[@]}" >> "$OUTPUT_FILE"
echo "Files found and added: $found_count" >> "$OUTPUT_FILE"
echo "Files missing: $missing_count" >> "$OUTPUT_FILE"
echo "Collection completed on: $(date)" >> "$OUTPUT_FILE"

# Print summary to console
echo ""
echo "📊 Collection Summary:"
echo "  📁 Total files: ${#FILES[@]}"
echo "  ✅ Found and added: $found_count"
echo "  ❌ Missing: $missing_count"
echo "  📄 Output file: $OUTPUT_FILE"

if [ $found_count -gt 0 ]; then
    echo ""
    echo "🎉 Collection completed successfully!"
    echo "📋 You can now upload '$OUTPUT_FILE' to get all fixes at once."
    echo ""
    echo "💡 To view the file:"
    echo "   cat $OUTPUT_FILE"
    echo ""
    echo "💡 To upload to Claude:"
    echo "   1. Open the file: $OUTPUT_FILE"
    echo "   2. Copy the content"
    echo "   3. Paste it in your message to Claude"
else
    echo ""
    echo "⚠️  No files were found. Make sure you're in the correct directory."
    echo "   Current directory: $(pwd)"
    echo "   Expected to be in: your-project/frontend/"
fi