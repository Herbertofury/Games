"""Bounded retries for real browser image decoding, never substitute success or URLs."""
IMAGE_DECODE_JS = r'''async ({rows, timeoutMs, maxAttempts, concurrency, retryDelayMs}) => {
  const output = new Array(rows.length);
  let next = 0;
  const pause = ms => new Promise(resolve => setTimeout(resolve, ms));
  async function attempt(row) {
    return new Promise(resolve => {
      const image = new Image();
      let settled = false;
      const finish = result => {
        if (settled) return;
        settled = true;
        clearTimeout(timer);
        image.onload = null;
        image.onerror = null;
        resolve(result);
      };
      const timer = setTimeout(() => finish({ok: false, error: 'timeout'}), timeoutMs);
      image.onload = () => finish(image.naturalWidth > 0 && image.naturalHeight > 0
        ? {ok: true, width: image.naturalWidth, height: image.naturalHeight}
        : {ok: false, error: 'zero-dimension'});
      image.onerror = () => finish({ok: false, error: 'network/decode'});
      image.src = row.image;
    });
  }
  async function worker() {
    while (next < rows.length) {
      const index = next++;
      const row = rows[index];
      const history = [];
      let result = {ok: false, error: 'missing-url'};
      if (typeof row.image === 'string' && row.image.length) {
        for (let number = 1; number <= maxAttempts; number++) {
          result = await attempt(row);
          history.push({attempt: number, ...result});
          if (result.ok) break;
          if (number < maxAttempts) await pause(retryDelayMs * number);
        }
      }
      output[index] = {id: row.id, url: row.image, ...result, attempts: history};
    }
  }
  await Promise.all(Array.from({length: Math.min(concurrency, rows.length)}, worker));
  return output;
}'''


def decode_primary_images(page, rows, *, timeout_ms=25000, max_attempts=3,
                          concurrency=5, retry_delay_ms=750):
    """All requested records still need a real successful browser decode.

    The exact source URL is retained on every attempt. Exhausted failures stay
    failures, including network errors, timeouts and zero-sized images. Attempt
    history is included in the normal QA report rather than silently discarded.
    """
    if not 1 <= max_attempts <= 3:
        raise ValueError('Image QA permits one to three attempts only')
    if not 1 <= concurrency <= 8:
        raise ValueError('Image QA concurrency must be between one and eight')
    if timeout_ms <= 0 or retry_delay_ms < 0:
        raise ValueError('Invalid image QA timeout or retry delay')
    return page.evaluate(IMAGE_DECODE_JS, {
        'rows': rows, 'timeoutMs': timeout_ms, 'maxAttempts': max_attempts,
        'concurrency': concurrency, 'retryDelayMs': retry_delay_ms,
    })
