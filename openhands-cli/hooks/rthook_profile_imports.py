import atexit
import os
import sys
import time
from collections import defaultdict

ENABLE = os.getenv('IMPORT_PROFILING', '0') not in ('', '0', 'false', 'False')
OUT = 'dist/import_profiler.csv'
THRESHOLD_MS = float(os.getenv('IMPORT_PROFILING_THRESHOLD_MS', '0'))

if ENABLE:
    timings = defaultdict(float)  # module -> total seconds (first load only)
    counts = defaultdict(int)  # module -> number of first-loads (should be 1)
    max_dur = defaultdict(float)  # module -> max single load seconds

    try:
        import importlib._bootstrap as _bootstrap  # type: ignore[attr-defined]
    except Exception:
        _bootstrap = None

    start_time = time.perf_counter()

    if _bootstrap is not None:
        _orig_find_and_load = _bootstrap._find_and_load

        def _timed_find_and_load(name, import_):
            preloaded = name in sys.modules  # cache hit?
            t0 = time.perf_counter()
            try:
                return _orig_find_and_load(name, import_)
            finally:
                if not preloaded:
                    dt = time.perf_counter() - t0
                    timings[name] += dt
                    counts[name] += 1
                    if dt > max_dur[name]:
                        max_dur[name] = dt

        _bootstrap._find_and_load = _timed_find_and_load

    @atexit.register
    def _dump_import_profile():
        def ms(s):
            return f'{s * 1000:.3f}'

        items = [
            (name, counts[name], timings[name], max_dur[name])
            for name in timings
            if timings[name] * 1000 >= THRESHOLD_MS
        ]
        items.sort(key=lambda x: x[2], reverse=True)
        try:
            with open(OUT, 'w', encoding='utf-8') as f:
                f.write('module,count,total_ms,max_ms\n')
                for name, cnt, tot_s, max_s in items:
                    f.write(f'{name},{cnt},{ms(tot_s)},{ms(max_s)}\n')
            # brief summary
            if items:
                w = max(len(n) for n, *_ in items[:25])
                sys.stderr.write('\n=== Import Time Profile (first-load only) ===\n')
                sys.stderr.write(f'{"module".ljust(w)}  count  total_ms   max_ms\n')
                for name, cnt, tot_s, max_s in items[:25]:
                    sys.stderr.write(
                        f'{name.ljust(w)}  {str(cnt).rjust(5)}  {ms(tot_s).rjust(8)}  {ms(max_s).rjust(7)}\n'
                    )
            sys.stderr.write(f'\nImport profile written to: {OUT}\n')
        except Exception as e:
            sys.stderr.write(f'[import-profiler] failed to write profile: {e}\n')
