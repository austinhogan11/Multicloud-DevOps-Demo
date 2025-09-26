// Lightweight Plausible helper. Safe to import anywhere in the SPA.
// Usage: track('task_created', { titleLength: 12 })
export function track(event, props = undefined) {
  try {
    if (typeof window !== 'undefined' && typeof window.plausible === 'function') {
      if (props && Object.keys(props).length > 0) {
        window.plausible(event, { props })
      } else {
        window.plausible(event)
      }
    }
  } catch (_) {
    // no-op in case analytics is unavailable
  }
}

