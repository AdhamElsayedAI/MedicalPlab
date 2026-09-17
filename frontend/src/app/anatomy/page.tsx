'use client';

import { AppShell } from '@/components/layout/AppShell';
import { AnatomyLabClient } from '@/features/anatomy/AnatomyLabClient';

export default function AnatomyPage() {
  return (
    <AppShell fullHeight noPadding>
      <AnatomyLabClient />
    </AppShell>
  );
}

