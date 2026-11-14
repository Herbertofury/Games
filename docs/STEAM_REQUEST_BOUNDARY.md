# Steam handler request-body boundary

The exported `createApp` handler independently enforces the 16 KiB JSON request
limit while consuming the stream. It cancels the reader when the threshold is
crossed, retains at most the accepted chunks, and releases its lock. It does not
wait for or buffer the entire body before rejecting. The native `serve` adapter
already had its own incremental limit; both boundaries now remain effective.

Regression: a finite 100-chunk stream (8 KiB each) was previously drained in
full and never cancelled before returning 413. The test now requires early
cancellation and at most four pulls, with no upstream calls. Exact 16 KiB JSON
remains accepted for normal semantic validation, and UTF-8 multibyte input is
counted in bytes. Authentication, origin checks and snapshot semantics are
unchanged. Tests use only authored requests and a mocked Steam provider.

This is not a real Steam sign-in or deployed-service acceptance claim. The
upstream producer may allocate a large chunk before handing it to the handler;
this boundary limits retained data, not allocations inside external producers.

UTF-8 compatibility: the bounded buffer is decoded with `TextDecoder`, matching
`Request.text()` replacement decoding and optional BOM removal. A regression
splits the BOM across three chunks and verifies the JSON reaches normal field
validation rather than being incorrectly rejected as malformed JSON.
