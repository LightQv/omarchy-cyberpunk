// Accumulate high-resolution deltas, but select at most one row per event.
function wheelStep(angleY, pixelY, previous) {
    var kind = pixelY ? "pixel" : "angle"
    var delta = pixelY || angleY
    if (!delta) return { step: 0, remainder: previous.remainder, kind: previous.kind }
    var threshold = kind === "pixel" ? 24 : 120
    var remainder = previous.kind === kind ? previous.remainder : 0
    var total = remainder + delta
    var step = Math.abs(total) >= threshold ? (total > 0 ? -1 : 1) : 0
    return { step: step, remainder: step ? total % threshold : total, kind: kind }
}
