# Migration Guide: Moving Shared Library to xtox

## Overview

The transcription service library should live in the `xtox` project since it's the foundational document/audio processing platform. This guide explains how to move it and update WhatsSummarize to use it.

## Step 1: Move Library to xtox

1. **Copy the library to xtox:**
   ```bash
   # From xtox project root
   cp -r /path/to/whatssummarize/lib/transcription ./lib/transcription
   # Or manually copy the entire lib/transcription folder
   ```

2. **Location in xtox:**
   ```
   xtox/
   ├── lib/
   │   └── transcription/       # Shared transcription service
   │       ├── src/
   │       │   └── index.ts
   │       ├── package.json
   │       └── README.md
   ├── backend/
   ├── frontend/
   └── azure-functions/
   ```

## Step 2: Publish as Internal Package (Recommended)

**Option A: npm workspace (if xtox uses workspaces)**
```json
// In xtox/package.json
{
  "workspaces": [
    "lib/*"
  ]
}
```

**Option B: npm link (for local development)**
```bash
# In xtox/lib/transcription
npm link

# In whatssummarize
npm link @whatssummarize/transcription-service
```

**Option C: Install from local path**
```json
// In whatssummarize/package.json
{
  "dependencies": {
    "@whatssummarize/transcription-service": "file:../xtox/lib/transcription"
  }
}
```

**Option D: Private npm registry (for production)**
```bash
# Publish to your private npm registry
cd xtox/lib/transcription
npm publish --registry=your-registry-url
```

## Step 3: Update WhatsSummarize

1. **Remove local library:**
   ```bash
   rm -rf lib/transcription
   ```

2. **Update package.json:**
   ```json
   {
     "dependencies": {
       "@whatssummarize/transcription-service": "file:../xtox/lib/transcription"
       // or use npm link, or private registry URL
     }
   }
   ```

3. **Install dependency:**
   ```bash
   npm install
   ```

4. **Update import in src/app/api/transcribe/route.ts:**
   ```typescript
   import { TranscriptionService } from '@whatssummarize/transcription-service';
   ```

5. **Remove build:lib script from package.json:**
   ```json
   {
     "scripts": {
       "dev": "next dev --turbopack",
       "build": "next build",  // Remove build:lib dependency
       "start": "next start",
       "lint": "next lint"
     }
   }
   ```

## Step 4: Update xtox Integration

In xtox, you can now use the library in Azure Functions:

```typescript
// In xtox/azure-functions/transcribe/index.ts
import { TranscriptionService } from '../../lib/transcription/src';

export async function transcribeAudio(audioFile: File) {
  const service = TranscriptionService.fromEnvironment();
  return await service.transcribe(audioFile);
}
```

## Benefits

- ✅ Single source of truth for transcription logic
- ✅ Easier maintenance and updates
- ✅ Consistent behavior across all projects
- ✅ Better aligns with xtox's role as the processing platform
- ✅ Can be versioned and published independently

## Next Steps

After migration:
1. Update xtox documentation to include transcription service
2. Add transcription endpoints to xtox API
3. Consider adding AI optimization features to transcription output (aligns with xtox's AI focus)
