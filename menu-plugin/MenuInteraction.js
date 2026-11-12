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

// The native 4.5 Apps row redirects to the dock. Change only that shipped
// redirect, inside this clone, before user overrides are merged. Never mutate
// the shared defaults or override an explicitly customized user action.
function integratedApps(items) {
    return items.map(function(entry) {
        if (entry.id !== "apps" || entry.provider !== "apps" ||
            entry.action !== "omarchy-shell omarchy.dock apps") return entry
        var copy = {}
        for (var key in entry) copy[key] = entry[key]
        copy.action = ""
        copy.kind = "menu"
        return copy
    })
}
