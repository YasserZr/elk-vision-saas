'use client';

import React, { useState, useCallback } from 'react';

interface NotificationCenterProps {
  position?: 'top-right';
}

export default function NotificationCenter2({
  position = 'top-right',
}: NotificationCenterProps) {
  const [test, setTest] = useState(0);

  const helper = () => {
    return 'test';
  };

  return (
    <>
      <div>Test</div>
    </>
  );
}
