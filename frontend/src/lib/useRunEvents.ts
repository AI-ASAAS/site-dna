import { useEffect, useRef, useState } from 'react';
import { api, type RunEvent, type RunRecord } from './api';

export function useRunEvents(runId: string | undefined) {
  const [run, setRun] = useState<RunRecord | null>(null);
  const [events, setEvents] = useState<RunEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const eventSourceRef = useRef<EventSource | null>(null);

  // 1. Initial fetch
  useEffect(() => {
    if (!runId) return;
    let active = true;

    setLoading(true);
    api
      .getRun(runId)
      .then((data) => {
        if (active) {
          setRun(data);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (active) {
          setError(err.message || 'Failed to load run');
          setLoading(false);
        }
      });

    return () => {
      active = false;
    };
  }, [runId]);

  // 2. Setup SSE listener and fallback polling
  useEffect(() => {
    if (!runId) return;

    // Connect SSE
    const sseUrl = `/api/v1/runs/${encodeURIComponent(runId)}/events`;
    const es = new EventSource(sseUrl);
    eventSourceRef.current = es;

    es.addEventListener('init', (e: MessageEvent) => {
      try {
        const payload = JSON.parse(e.data);
        if (payload.run) setRun(payload.run);
      } catch {}
    });

    const handleEvent = (e: MessageEvent) => {
      try {
        const evt: RunEvent = JSON.parse(e.data);
        setEvents((prev) => [evt, ...prev.slice(0, 49)]); // Keep last 50 events

        // Poll latest run state when stage or run transitions happen
        api.getRun(runId).then(setRun).catch(() => {});
      } catch {}
    };

    es.onmessage = handleEvent;

    // Listen to specific custom event names
    const eventTypes = [
      'run.created',
      'run.started',
      'stage.queued',
      'stage.started',
      'stage.progress',
      'stage.completed',
      'stage.partial',
      'stage.ai_blocked',
      'stage.failed',
      'run.completed',
      'run.partial',
      'run.failed',
    ];

    eventTypes.forEach((t) => es.addEventListener(t, handleEvent));

    es.addEventListener('done', () => {
      es.close();
      api.getRun(runId).then(setRun).catch(() => {});
    });

    es.onerror = () => {
      // If SSE disconnects or finishes, rely on periodic refresh
      es.close();
    };

    // 3. Fallback periodic poll while running
    const interval = setInterval(() => {
      if (run && (run.status === 'running' || run.status === 'queued' || run.status === 'created')) {
        api.getRun(runId).then(setRun).catch(() => {});
      }
    }, 2500);

    return () => {
      es.close();
      clearInterval(interval);
    };
  }, [runId, run?.status]);

  const refresh = () => {
    if (!runId) return;
    api.getRun(runId).then(setRun).catch(() => {});
  };

  return { run, events, loading, error, refresh };
}
