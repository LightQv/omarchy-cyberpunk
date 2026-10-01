import Quickshell
import Quickshell.Io
import Quickshell.Wayland
import QtQuick
import qs.Commons
import qs.Ui
import "MenuModel.js" as MenuModel
import "MenuInteraction.js" as MenuInteraction

Item {
  id: root

  // Injected by omarchy-shell when this plugin is summoned.
  property string omarchyPath: Quickshell.env("OMARCHY_PATH")
  property var shell: null
  property var manifest: null

  // Plugin lifecycle hooks. The host calls open(payloadJson) after
  // `omarchy-shell shell summon omarchy.menu ...` and close() when hidden.
  property string pendingInitialMenu: "root"

  function open(payloadJson) {
    var payload = ({})
    try { payload = JSON.parse(payloadJson || "{}") } catch (e) { payload = ({}) }

    if (payload.fontFamily) root.fontFamily = payload.fontFamily

    if (payload.mode === "select" || payload.mode === "input") {
      root.openDmenu(payload)
    } else {
      root.openRoute(payload.initialMenu || payload.menu || "root")
    }
  }

  function close() {
    root.cancel()
  }

  function refresh() {
    defaultMenuFile.reload()
    userMenuFile.reload()
    return "ok"
  }

  function ping() { return "ok" }
  function identity() { return "cyberpunk-menu-hud-3" }
  function health() {
    return JSON.stringify({
      mode: root.mode,
      activeMenu: root.activeMenu,
      rows: displayModel.count,
      scannerSlots: scannerModel.count,
      selectedIndex: root.selectedIndex,
      scannerCenterIndex: root.scannerCenterIndex,
      wheelOffset: root.wheelOffset,
      wheelViewportY: resultList.contentY,
      wheelViewportHeight: resultList.height,
      wheelContentHeight: resultList.contentHeight,
      requestedWidth: root.dmenuWidth,
      cardWidth: root.cardWidth,
      actualCardWidth: card.width,
      cardBodyWidth: cardBody.width,
      listWidth: resultList.width,
      listX: resultList.mapToItem(null, 0, 0).x,
      listY: resultList.mapToItem(null, 0, 0).y,
      panelWidth: panel.width,
      opened: root.opened,
      keyFocus: keyCatcher.activeFocus,
      hasAppLibrary: !!root.appLibrary,
      appCount: root.appLibrary ? root.appLibrary.sortedEntries("").length : -1,
      appsLoaded: !!root.providersLoaded["apps"]
    })
  }

  property string fontFamily: Style.font.menuFamily
  // JSONC menu definitions. The shell parses both at startup and merges
  // the user file on top of the defaults, so the keybind → IPC → visible
  // path doesn't have to shell out to bash + jq on every open.
  property string defaultMenuPath: omarchyPath + "/default/omarchy/omarchy-menu.jsonc"
  property string userMenuPath: Quickshell.env("HOME") + "/.config/omarchy/extensions/omarchy-menu.jsonc"
  property var defaultMenuItems: []
  property var userMenuItems: []
  property bool opened: false
  property string mode: "menu"
  readonly property bool dmenuActive: mode === "select" || mode === "input"
  property string dmenuPrompt: ""
  property var dmenuOptions: []
  property string selectionFile: ""
  property string doneFile: ""
  property int dmenuWidth: 300
  property int dmenuMaxHeight: 0
  property bool requestActive: false
  property bool rowsLoaded: false
  property string activeMenu: "root"
  readonly property bool scannerActive: mode === "menu"
  readonly property bool mirroredBindings: mode === "select" && dmenuPrompt.toLowerCase().indexOf("keybindings") !== -1
  readonly property bool wheelActive: scannerActive || mirroredBindings
  readonly property bool appScanner: scannerActive && activeMenu === "apps"
  readonly property bool reducedMotion: Quickshell.env("OMARCHY_REDUCED_MOTION") === "1"
  readonly property string scannerFont: "JetBrainsMono Nerd Font"
  property real wheelIntro: 1
  property string filterText: ""
  property int selectedIndex: 0
  property bool pointerSelecting: false
  property bool replacingRows: false
  property int scannerCenterIndex: 0
  property var wheelInput: ({ step: 0, remainder: 0, kind: "" })
  onSelectedIndexChanged: if (wheelActive && opened && !pointerSelecting && !replacingRows) rebuildScannerWindow()
  property real wheelOffset: 0
  property int drilldownStart: -1
  NumberAnimation {
    id: wheelSlide
    target: root
    property: "wheelOffset"
    to: 0
    duration: 210
    easing.type: Easing.OutCubic
  }
  function resetWheel() {
    wheelSlide.stop()
    wheelOffset = 0
  }
  property bool cursorActive: false
  property int requestSerial: 0
  property int applySerial: 0
  property var items: ({})
  property var itemOrder: []
  property var navStack: []
  property var providersLoaded: ({})
  property var providerQueue: []
  property int providerRevision: 0

  // A copied Omarchy AppLibrary retains desktop-entry filters, icons, launch
  // feedback and removal when the host has no appLibrary facade to inject.
  readonly property var appLibrary: root.shell && root.shell.appLibrary ? root.shell.appLibrary : localAppLibrary
  property bool deleteConfirmOpen: false
  property var deleteTarget: null
  onOpenedChanged: {
    if (!opened) {
      resetWheel()
      wheelInput = ({ step: 0, remainder: 0, kind: "" })
      deleteConfirmOpen = false
      deleteTarget = null
      scanIntro.stop()
      wheelIntro = 1
    } else if (wheelActive && !reducedMotion) {
      // Fade the scrim, telemetry and wheel together, including Keybindings.
      wheelIntro = 0
      scanIntro.restart()
    }
  }
  onFilterTextChanged: {
    resetWheel()
    wheelInput = ({ step: 0, remainder: 0, kind: "" })
  }
  // Bound to the central [menu] section in shell.toml via Color.qml.
  // Each color already includes its alpha companion (composed in the
  // singleton), so consumers can drop them straight into a Rectangle.
  property color background: Color.menu.background
  property color foreground: Color.menu.text
  property color border: Color.menu.border
  property var borderSpec: Border.surfaceSpec("menu", "border", border, Math.max(1, Style.space(2)))
  property color scrim: Color.menu.scrim
  property color selectedBackground: Color.menu.selectedBackground
  property color selectedText: Color.menu.selectedText
  property color selectedBorder: Color.menu.selectedBorder
  property var selectedBorderSpec: Border.surfaceSpec("menu", "selected-border", selectedBorder, 0)
  readonly property real rowReservedBorderLeft: Border.left(selectedBorderSpec)
  readonly property real rowReservedBorderRight: Border.right(selectedBorderSpec)
  readonly property int cornerRadius: Style.cornerRadius
  property int contentMargin: wheelActive || dmenuActive ? Style.space(8) : Style.spacing.panelPadding
  property int headerHeight: scannerActive || dmenuActive ? Style.space(72) : Math.max(Style.space(34), Style.font.title + Style.spacing.controlPaddingY * 2)
  property int contentSpacing: Style.spacing.md
  property int baseRowHeight: wheelActive ? Style.space(54) : Math.max(Style.space(50), Style.font.body + Style.spacing.rowPaddingX * 2)
  readonly property int wheelCurveDepth: Style.space(52)
  property int detailRowHeight: Math.max(Style.space(58), Style.font.body + Style.font.caption + Style.spacing.rowPaddingX * 2)
  // How much of the first hidden row stays visible at the fold — enough to
  // read as a cut-off row rather than a bottom border.
  property int rowPeek: Math.round(baseRowHeight * 0.55)
  property int rowSpacing: Style.spacing.xs
  property int dividerHeight: Style.space(17)
  property int scannerFooterHeight: wheelActive ? Style.space(38) : 0
  property bool searchDivider: false
  property int layoutSerial: 0
  property int cardWidth: Math.max(Style.space(120), Math.min(root.dmenuActive ? (root.mirroredBindings ? Math.max(Style.space(root.dmenuWidth), Style.space(840)) : Style.space(root.dmenuWidth)) : (root.scannerActive ? Style.space(660) : Style.space(300)), panel.width - (root.wheelActive ? panel.scannerMargin + Style.gapsOut : Style.gapsOut * 2)))
  property int visibleRowsHeight: root.mirroredBindings
    ? Math.min(availableRowsHeight(), root.dmenuMaxHeight > 0 ? Style.space(root.dmenuMaxHeight) : root.baseRowHeight * 9 + root.rowSpacing * 8)
    : root.dmenuActive ? dmenuRowListHeight(layoutSerial, displayModel.count, filterText) : (scannerActive ? Math.max(root.baseRowHeight, availableRowsHeight()) : rowListHeight(layoutSerial, displayModel.count, filterText, searchDivider))
  property int cardHeight: root.dmenuActive && !root.mirroredBindings
    ? Math.min(contentMargin * 2 + headerHeight + (mode === "input" ? 0 : contentSpacing + visibleRowsHeight), panel.height - Style.gapsOut * 2)
    : Math.min(contentMargin * 2 + headerHeight + contentSpacing + visibleRowsHeight + scannerFooterHeight, panel.height - Style.gapsOut * 2)

  function finishRequest(selection) {
    if (!root.requestActive || !root.doneFile) {
      root.opened = false
      return
    }

    var activeSelectionFile = root.selectionFile
    var activeDoneFile = root.doneFile
    root.requestActive = false
    root.selectionFile = ""
    root.doneFile = ""

    if (selection === null || selection === undefined) {
      resultProc.command = ["bash", "-c", ": > " + Util.shellQuote(activeDoneFile)]
    } else {
      resultProc.command = ["bash", "-c", "printf '%s\\n' " + Util.shellQuote(selection) + " > " + Util.shellQuote(activeSelectionFile) + "; : > " + Util.shellQuote(activeDoneFile)]
    }
    resultProc.running = true
  }

  function runAction(action) {
    var command = String(action || "")
    if (!command) return

    Util.execDetached(command)
  }

  // Menu rows only surface their detail while a search is narrowing them;
  // dmenu rows carry caller-supplied subtext that must always be visible.
  function rowHeightForDetail(detail) {
    return (root.filterText || root.dmenuActive) && detail ? root.detailRowHeight : root.baseRowHeight
  }

  // Height the card can devote to rows before running off the screen — or
  // past the frozen top edge once a search has pinned the card in place.
  // Uses panel.cardTop rather than effectiveCardTop: the centered top is
  // derived from the card height, which this value feeds.
  function availableRowsHeight() {
    var top = panel.cardTop >= 0 ? panel.cardTop : Style.gapsOut
    var available = panel.height - top - Style.gapsOut - root.contentMargin * 2 - root.headerHeight - root.contentSpacing - root.scannerFooterHeight
    // The starting menu sets the ceiling along with the offset: drilling into
    // a longer submenu scrolls behind the fold instead of growing the card.
    if (panel.maxRowsHeight >= 0) available = Math.min(available, panel.maxRowsHeight)
    // A card that swallows the whole screen reads as a page, not a menu.
    return Math.max(root.baseRowHeight, Math.min(available, root.wheelActive ? root.baseRowHeight * 9 + root.rowSpacing * 8 : Math.round(panel.height * 0.7)))
  }

  // When every row fits, the list gets its full height. When they don't,
  // the card must end mid-row: a clipped row is what tells the eye there is
  // more below the fold, so never come out even on a row boundary.
  function foldedListHeight(totals, available) {
    var count = totals.length
    if (count === 0) return root.baseRowHeight
    if (totals[count - 1] <= available) return totals[count - 1]

    var peek = root.rowPeek
    var full = 0
    while (full < count && totals[full] <= available) full++
    while (full > 1 && totals[full - 1] + root.rowSpacing + peek > available) full--
    if (full < 1) return Math.max(available, root.baseRowHeight)

    return totals[full - 1] + root.rowSpacing + peek
  }

  function rowListHeight(_serial, _count, _filter, _divider) {
    if (displayModel.count === 0) return root.baseRowHeight

    var totals = []
    var total = 0
    var previousSection = ""

    for (var i = 0; i < displayModel.count; i++) {
      var row = displayModel.get(i)
      if (i > 0) total += root.rowSpacing
      if (row.section === "drilldown" && previousSection !== "drilldown") total += root.dividerHeight
      total += root.rowHeightForDetail(row.detail)
      previousSection = row.section
      totals.push(total)
    }

    return foldedListHeight(totals, availableRowsHeight())
  }

  function dmenuRowListHeight(_serial, _count, _filter) {
    if (root.mode === "input") return 0
    if (displayModel.count === 0) return root.baseRowHeight

    var available = availableRowsHeight()
    if (root.dmenuMaxHeight > 0) available = Math.min(available, Style.space(root.dmenuMaxHeight))

    var totals = []
    var total = 0
    for (var i = 0; i < displayModel.count; i++) {
      if (i > 0) total += root.rowSpacing
      total += root.rowHeightForDetail(displayModel.get(i).detail)
      totals.push(total)
    }

    return foldedListHeight(totals, available)
  }

  function item(id) {
    return root.items[id] || null
  }

  // ------------------------------------------------------------------
  // JSONC → normalized item array. Mirrors the bash bin's jq pipeline so
  // the on-disk authoring format stays untouched.
  // ------------------------------------------------------------------

  function stripJsonc(raw) {
    return MenuModel.stripJsonc(raw)
  }

  function normalizeAliases(value) {
    return MenuModel.normalizeAliases(value)
  }

  function normalizeItem(id, raw) {
    return MenuModel.normalizeItem(id, raw)
  }

  function parseMenuJsonc(raw) {
    return MenuModel.parseMenuJsonc(raw)
  }

  // Merge defaults + user extension. Later entries override earlier ones
  // on a per-key basis (so the user can tweak label/icon/action without
  // re-declaring the whole row).
  function rebuildItemsFromSources() {
    var mergedMenu = MenuModel.mergeMenuSources(root.defaultMenuItems, root.userMenuItems)
    root.providerRevision += 1
    root.providersLoaded = ({})
    root.providerQueue = []
    root.items = mergedMenu.items
    root.itemOrder = mergedMenu.itemOrder
    root.rowsLoaded = true
    root.evaluateGuards()
    if (root.opened) {
      root.rebuildDisplay()
      if (!root.dmenuActive) {
        if (root.filterText.trim()) root.loadProvidersForSearch()
        else root.loadProviderForMenu(root.activeMenu)
      }
    }
  }

  // Each known provider is a tiny bash one-liner that enumerates a list and
  // emits one tab-delimited row per item: `label\tvalue\tcurrent`. The shell
  // turns those into menu items children of `menuId`. A `volatile` provider
  // re-runs every time its submenu is entered, so a font installed since the
  // shell started shows up without restarting it.
  readonly property var providers: ({
    "fonts": {
      script: "current=$(omarchy-font-current 2>/dev/null); omarchy-font-list 2>/dev/null | while read -r f; do [[ -z $f ]] && continue; printf '%s\\t%s\\t%s\\n' \"$f\" \"$f\" \"$current\"; done",
      icon: "",
      volatile: true,
      actionFor: function(value) { return "omarchy-font-set " + Util.shellQuote(value) }
    },
    "power-profiles": {
      script: "current=$(powerprofilesctl get 2>/dev/null); omarchy-powerprofiles-list 2>/dev/null | while read -r p; do [[ -z $p ]] && continue; printf '%s\\t%s\\t%s\\n' \"$p\" \"$p\" \"$current\"; done",
      icon: "\udb81\udc0b",
      actionFor: function(value) { return "omarchy-powerprofiles-set autodetect " + Util.shellQuote(value) }
    }
  })

  function slugify(value) {
    return MenuModel.slugify(value)
  }

  // The apps provider is QML-native: rows come from the shared AppLibrary
  // (DesktopEntries) instead of a bash enumeration, so they carry image
  // icons, launch feedback, and uninstall support like the launcher.
  function mergeAppRows() {
    if (!root.appLibrary) return

    var rows = root.appLibrary.sortedEntries("")
    var appRows = []
    for (var j = 0; j < rows.length; j++) {
      var entry = rows[j].entry
      var appId = String(entry.id || "")
      if (!appId) continue
      var subtext = root.appLibrary.entrySubtext(entry)
      var aliases = subtext ? [subtext] : []
      try {
        if (entry.keywords && typeof entry.keywords.join === "function") aliases = aliases.concat(entry.keywords)
      } catch (e) { }
      appRows.push({
        id: "apps." + appId,
        parent: "apps",
        kind: "app",
        icon: "",
        appIcon: String(entry.icon || ""),
        appId: appId,
        label: root.appLibrary.entryName(entry),
        title: "",
        target: "",
        description: subtext,
        action: "",
        provider: "",
        aliases: aliases,
        when: "",
        checked: "",
        order: 0
      })
    }

    var merged = MenuModel.mergeAppRows(root.items, root.itemOrder, appRows)
    root.items = merged.items
    root.itemOrder = merged.itemOrder
    if (root.opened) root.rebuildDisplay()
  }

  function startProviderForMenu(id) {
    var entry = root.item(id)
    if (!entry || !entry.provider || root.providersLoaded[id]) return
    if (entry.provider === "apps") {
      root.providersLoaded[id] = true
      root.mergeAppRows()
      return
    }
    var spec = root.providers[entry.provider]
    if (!spec) return

    root.providersLoaded[id] = true
    providerProc.menuId = id
    providerProc.providerKey = entry.provider
    providerProc.revision = root.providerRevision
    providerProc.collected = ""
    providerProc.command = ["bash", "-lc", spec.script]
    providerProc.running = true
  }

  function mergeProviderRows(rows, menuId, providerKey) {
    var spec = root.providers[providerKey]
    if (!spec) return
    var lines = String(rows || "").split("\n")
    var providerRows = []
    var takenIds = ({})
    for (var i = 0; i < lines.length; i++) {
      var line = lines[i].trim()
      if (!line) continue
      var parts = line.split("\t")
      var label = parts[0] || ""
      var value = parts[1] || parts[0] || ""
      var current = parts[2] || ""
      if (!label) continue
      // Distinct values can slugify alike — Fira Code and Fira-Code both give
      // fira-code — and a repeated id is dropped, which would silently lose a
      // row from the list. Nudge it until it is the row's own.
      var rowId = menuId + "." + root.slugify(value)
      while (takenIds[rowId]) rowId += "-"
      takenIds[rowId] = true

      providerRows.push({
        id: rowId,
        parent: menuId,
        kind: "action",
        icon: (value === current) ? "✓" : (spec.icon || ""),
        label: label,
        title: "",
        target: "",
        description: "",
        action: spec.actionFor(value),
        provider: "",
        aliases: [],
        when: "",
        checked: "",
        order: 0
      })
    }
    var merged = MenuModel.swapProviderRows(root.items, root.itemOrder, menuId, providerRows)
    root.items = merged.items
    root.itemOrder = merged.itemOrder
    if (root.opened) root.rebuildDisplay()
  }

  function startNextProvider() {
    if (providerProc.running) return

    while (root.providerQueue.length > 0) {
      var id = root.providerQueue.shift()
      var entry = root.item(id)
      if (!entry || !entry.provider || root.providersLoaded[id]) continue

      root.startProviderForMenu(id)
      return
    }
  }

  // Entering a submenu is the one moment a volatile list is worth paying for
  // again: it may have been reshaped by the last pick from it. Search doesn't
  // invalidate, or every keystroke would restart the same enumeration.
  function invalidateVolatileProvider(id) {
    var entry = root.item(id)
    var spec = entry && entry.provider ? root.providers[entry.provider] : null
    if (spec && spec.volatile) root.providersLoaded[id] = false
  }

  function loadProviderForMenu(id) {
    var entry = root.item(id)
    if (!entry || !entry.provider || root.providersLoaded[id]) return

    // Native providers don't touch providerProc, so they never need to queue.
    if (entry.provider === "apps") {
      root.startProviderForMenu(id)
      return
    }

    if (providerProc.running) {
      if (root.providerQueue.indexOf(id) < 0) root.providerQueue = root.providerQueue.concat([id])
      return
    }

    root.startProviderForMenu(id)
  }

  function loadProvidersForSearch() {
    var active = root.item(root.activeMenu) ? root.activeMenu : "root"

    for (var i = 0; i < root.itemOrder.length; i++) {
      var entry = root.item(root.itemOrder[i])
      if (!entry || !entry.provider || root.providersLoaded[entry.id]) continue
      if (active !== "root" && entry.id !== active && !root.isDescendantOf(entry.id, active)) continue

      root.loadProviderForMenu(entry.id)
    }
  }

  function depthFor(id) {
    return MenuModel.depthFor(root.items, id)
  }

  function pathFor(id) {
    return MenuModel.pathFor(root.items, id)
  }

  function parentPathFor(id) {
    return MenuModel.parentPathFor(root.items, id)
  }

  function isDescendantOf(id, ancestorId) {
    return MenuModel.isDescendantOf(root.items, id, ancestorId)
  }

  function childCount(id) {
    return MenuModel.childCount(root.items, root.itemOrder, id)
  }

  // Guarded items are hidden when their `when:` evaluates false. Static
  // submenus are also hidden when none of their descendants are visible;
  // provider-backed menus stay visible because their rows load on demand.
  function isVisible(entry) {
    return MenuModel.isVisible(root.items, root.itemOrder, root.whenResults, entry)
  }

  // Label with the ✓ marker baked in when `checked:` evaluated truthy.
  function labelFor(entry) {
    return MenuModel.labelFor(entry, root.checkedResults)
  }

  function searchableToken(value) {
    return MenuModel.searchableToken(value)
  }

  function leafIdFor(id) {
    return MenuModel.leafIdFor(id)
  }

  function nameSearchText(entry) {
    return MenuModel.nameSearchText(entry)
  }

  function termInSearchWords(term, text) {
    return MenuModel.termInSearchWords(term, text)
  }

  function descriptionTextMatches(query, text) {
    return MenuModel.descriptionTextMatches(query, text)
  }

  function matchesQuery(entry, query) {
    return MenuModel.matchesQuery(entry, query, root.isVisible(entry))
  }

  function searchScore(entry, query) {
    return MenuModel.searchScore(root.items, entry, query)
  }

  function displayRow(entry, detail, score, section) {
    return MenuModel.displayRow(root.items, root.itemOrder, root.checkedResults, entry, detail, score, section)
  }

  function rebuildDmenuDisplay() {
    displayModel.clear()
    root.searchDivider = false
    root.drilldownStart = -1

    if (root.mode === "input") {
      layoutSerial += 1
      return
    }

    var query = root.filterText.trim().toLowerCase()
    for (var i = 0; i < root.dmenuOptions.length; i++) {
      // An option is "<label>", "<glyph>\t<label>", or
      // "<glyph>\t<label>\t<subtext>". The glyph never comes back with the
      // selection; the subtext renders under the label, filters alongside it,
      // and returns with the selection as a stable key for same-named rows.
      var parts = String(root.dmenuOptions[i] || "").split("\t")
      var icon = parts.length > 1 ? parts.shift() : ""
      var label = parts.shift() || ""
      var detail = parts.join("\t")
      if (query && label.toLowerCase().indexOf(query) < 0
          && detail.toLowerCase().indexOf(query) < 0) continue
      displayModel.append({
        sourceIndex: displayModel.count,
        itemId: "dmenu." + i,
        kind: "dmenu",
        icon: icon,
        iconFont: "",
        appIcon: "",
        appId: "",
        label: label,
        target: "",
        detail: detail,
        path: "",
        childCount: 0,
        action: "",
        provider: "",
        score: i,
        section: ""
      })
    }

    layoutSerial += 1

    if (displayModel.count === 0) selectedIndex = 0
    else if (selectedIndex >= displayModel.count) selectedIndex = displayModel.count - 1
    else if (selectedIndex < 0) selectedIndex = 0

    if (root.mirroredBindings) root.rebuildScannerWindow()
    Qt.callLater(function() {
      if (displayModel.count > 0) root.revealCursor()
    })
  }

  function rebuildDisplay() {
    if (root.wheelOffset !== 0) resetWheel()
    if (root.dmenuActive) {
      root.rebuildDmenuDisplay()
      return
    }

    displayModel.clear()

    if (!root.rowsLoaded) return

    var active = root.item(root.activeMenu) ? root.activeMenu : "root"
    root.activeMenu = active
    var rows = []
    var query = root.filterText.trim()
    root.searchDivider = false

    if (query) {
      var currentRows = []
      var drilldownRows = []

      for (var i = 0; i < root.itemOrder.length; i++) {
        var entry = root.item(root.itemOrder[i])
        if (!entry || entry.id === "root") continue
        if (!root.isDescendantOf(entry.id, active)) continue
        if (!root.matchesQuery(entry, query)) continue

        var detail = root.parentPathFor(entry.id)
        var row = root.displayRow(entry, detail, root.searchScore(entry, query))
        if (entry.parent === active) currentRows.push(row)
        else drilldownRows.push(row)
      }

      var searchSort = function(a, b) {
        if (a.score !== b.score) return a.score - b.score
        return a.path.localeCompare(b.path)
      }

      currentRows.sort(searchSort)
      drilldownRows.sort(searchSort)
      root.searchDivider = currentRows.length > 0 && drilldownRows.length > 0
      root.drilldownStart = root.searchDivider ? currentRows.length : -1
      if (root.searchDivider) {
        for (var d = 0; d < drilldownRows.length; d++) drilldownRows[d].section = "drilldown"
      }
      rows = currentRows.concat(drilldownRows)
    } else {
      root.drilldownStart = -1
      for (var j = 0; j < root.itemOrder.length; j++) {
        var child = root.item(root.itemOrder[j])
        if (!child || child.parent !== active) continue
        if (!root.isVisible(child)) continue
        rows.push(root.displayRow(child, child.description, child.order))
      }

      // DesktopEntries can reorder its values when an application starts.
      // Keep the Apps menu alphabetical independently of provider refreshes.
      if (active === "apps") {
        rows.sort(function(a, b) {
          var aLabel = String(a.label || "").toLowerCase()
          var bLabel = String(b.label || "").toLowerCase()
          if (aLabel < bLabel) return -1
          if (aLabel > bLabel) return 1
          var aId = String(a.itemId || "")
          var bId = String(b.itemId || "")
          if (aId < bId) return -1
          if (aId > bId) return 1
          return 0
        })
      }
    }

    for (var k = 0; k < rows.length; k++) {
      rows[k].sourceIndex = k
      displayModel.append(rows[k])
    }
    layoutSerial += 1

    if (displayModel.count === 0) selectedIndex = 0
    else if (selectedIndex >= displayModel.count) selectedIndex = displayModel.count - 1
    else if (selectedIndex < 0) selectedIndex = 0

    root.rebuildScannerWindow()
    Qt.callLater(function() {
      if (displayModel.count > 0) root.revealCursor()
    })
  }

  // Draw eleven buffered slots around the selected Omarchy row. The data
  // model remains untouched: each slot points to its original index.
  // This gives short menu routes centered focus and longer lists a real wrap.
  function rebuildScannerWindow() {
    if (!root.wheelActive) return
    scannerCenterIndex = selectedIndex
    var count = displayModel.count
    for (var slot = -5; slot <= 5; slot++) {
      var at = root.selectedIndex + slot
      if (count >= 9) at = ((at % count) + count) % count
      var record
      if (at < 0 || at >= count) {
        record = { sourceIndex: -1, itemId: "", kind: "blank", icon: "", iconFont: "", appIcon: "", appId: "", label: "", target: "", detail: "", path: "", action: "", childCount: 0, section: "" }
      } else {
        var row = displayModel.get(at)
        record = { sourceIndex: at, itemId: row.itemId, kind: row.kind, icon: row.icon, iconFont: row.iconFont, appIcon: row.appIcon, appId: row.appId, label: row.label, target: row.target, detail: row.detail, path: row.path, action: row.action, childCount: row.childCount, section: row.section }
      }
      // Reuse the eleven delegates (nine visible plus two rolling buffers).
      // Clearing/recreating them on every arrow key
      // destroyed the frame canvases and made the entire wheel blink.
      if (scannerModel.count <= slot + 5) scannerModel.append(record)
      else scannerModel.set(slot + 5, record)
    }
    centerWheelView()
  }

  function centerWheelView() {
    if (!root.wheelActive || scannerModel.count !== 11) return
    var stride = root.baseRowHeight + root.rowSpacing
    var total = scannerModel.count * stride - root.rowSpacing
    if (resultList.contentHeight < total - Style.space(2)) return
    var centered = Math.max(0, Math.min(Math.max(0, total - resultList.height),
      5 * stride + root.baseRowHeight / 2 - resultList.height / 2))
    if (Math.abs(resultList.contentY - centered) > 0.5) resultList.contentY = centered
  }

  // Contain alone parks the cursor row flush with the viewport edge, hiding
  // the neighbor entirely and losing the fold affordance. Keep the next
  // hidden row peeking past the cursor in the direction of travel.
  function revealCursor() {
    if (displayModel.count === 0) return
    if (root.wheelActive) {
      // This is synchronous, including on the first visible frame.
      root.centerWheelView()
      return
    }
    resultList.positionViewAtIndex(root.selectedIndex, ListView.Contain)

    var item = resultList.itemAtIndex(root.selectedIndex)
    if (!item) return

    var reach = root.rowPeek + root.rowSpacing
    if (root.selectedIndex < displayModel.count - 1) {
      var maxY = Math.max(resultList.originY, resultList.originY + resultList.contentHeight - resultList.height)
      var overhang = item.y + item.height + reach - (resultList.contentY + resultList.height)
      if (overhang > 0) resultList.contentY = Math.min(resultList.contentY + overhang, maxY)
    }
    if (root.selectedIndex > 0) {
      var underhang = resultList.contentY - (item.y - reach)
      if (underhang > 0) resultList.contentY = Math.max(resultList.contentY - underhang, resultList.originY)
    }
  }

  function select(delta) {
    if (displayModel.count === 0) return

    root.disarmPointer()
    var roll = root.wheelActive && root.scannerCenterIndex === root.selectedIndex && root.opened && root.cursorActive && !root.reducedMotion && Math.abs(delta) === 1 && displayModel.count > 1
    if (roll) {
      // The next window is the same rows shifted one slot. Offset its frames
      // back to their previous locations before painting, then roll to zero.
      var offset = root.wheelOffset + delta
      wheelSlide.stop()
      root.wheelOffset = Math.abs(offset) <= 1.25 ? offset : delta
    } else resetWheel()
    if (!cursorActive) {
      cursorActive = true
      selectedIndex = delta < 0 ? displayModel.count - 1 : 0
    } else {
      selectedIndex = (selectedIndex + delta + displayModel.count) % displayModel.count
    }
    revealCursor()
    if (roll) wheelSlide.restart()
  }

  function setFilter(nextFilter) {
    panel.freezeCardTop()
    root.replacingRows = true
    root.filterText = nextFilter
    root.selectedIndex = 0
    root.cursorActive = root.mode !== "input"
    root.disarmPointer()
    if (!root.dmenuActive && root.filterText.trim()) root.loadProvidersForSearch()
    root.rebuildDisplay()
    root.replacingRows = false
  }

  function setActiveMenu(id, pushHistory, fromPointer) {
    resetWheel()
    panel.freezeCardTop()
    if (!root.item(id)) id = "root"
    if (pushHistory && id !== root.activeMenu) root.navStack = root.navStack.concat([root.activeMenu])
    root.activeMenu = id
    root.filterText = ""
    root.selectedIndex = 0
    root.cursorActive = true
    if (fromPointer) pointerGate.allowInitialSample()
    else root.disarmPointer()
    root.rebuildDisplay()
    root.invalidateVolatileProvider(id)
    root.loadProviderForMenu(id)
  }

  function goBack() {
    if (root.activeMenu === "root") return false

    if (root.navStack.length > 0) {
      var previous = root.navStack[root.navStack.length - 1]
      root.navStack = root.navStack.slice(0, root.navStack.length - 1)
      root.setActiveMenu(previous, false)
      return true
    }

    var active = root.item(root.activeMenu)
    root.setActiveMenu((active && active.parent) ? active.parent : "root", false)
    return true
  }

  function activateIndex(index, fromPointer) {
    if (root.deleteConfirmOpen) return
    if (root.dmenuActive) {
      if (root.mode === "input") {
        root.applyDmenuSelection(root.filterText)
        return
      }
      if (index < 0 || index >= displayModel.count) return
      var picked = displayModel.get(index)
      root.applyDmenuSelection(picked.detail ? picked.label + "\t" + picked.detail : picked.label)
      return
    }

    if (index < 0 || index >= displayModel.count) return

    var row = displayModel.get(index)
    if (row.kind === "menu" || row.kind === "link") {
      root.setActiveMenu(row.target || row.itemId, true, fromPointer)
    } else if (row.kind === "app") {
      var appId = row.appId
      var label = row.label
      applySerial = requestSerial
      opened = false
      filterText = ""
      if (root.appLibrary) root.appLibrary.launch(appId, label)
    } else {
      root.applySelected(row.itemId, row.action)
    }
  }

  function requestDeleteSelected() {
    if (!root.cursorActive || root.selectedIndex < 0 || root.selectedIndex >= displayModel.count) return
    var row = displayModel.get(root.selectedIndex)
    if (!row || row.kind !== "app") return
    root.deleteTarget = { appId: row.appId, label: row.label }
    deleteConfirm.selectedIndex = 1
    root.deleteConfirmOpen = true
  }

  function cancelDelete() {
    root.deleteConfirmOpen = false
    root.deleteTarget = null
    deleteConfirm.selectedIndex = 1
    root.disarmPointer()
    Qt.callLater(function() { keyCatcher.forceActiveFocus() })
  }

  function confirmDelete() {
    var target = root.deleteTarget
    root.deleteConfirmOpen = false
    root.deleteTarget = null
    if (!target) return
    root.cancel()
    if (root.appLibrary) root.appLibrary.remove(target.appId, target.label)
  }

  function applyDmenuSelection(value) {
    applySerial = requestSerial
    opened = false
    filterText = ""
    root.finishRequest(value)
  }

  function applySelected(id, action) {
    if (!id) { cancel(); return }

    applySerial = requestSerial
    opened = false
    filterText = ""
    root.runAction(action)
  }

  function cancel() {
    if (root.dmenuActive) root.finishRequest(null)
    opened = false
    filterText = ""
  }

  function openExistingMenu(initialMenu) {
    requestSerial += 1
    mode = "menu"
    requestActive = false
    selectionFile = ""
    doneFile = ""
    activeMenu = root.item(initialMenu) ? initialMenu : "root"
    navStack = []
    filterText = ""
    selectedIndex = 0
    cursorActive = true
    root.disarmPointer()
    root.evaluateGuards()
    // Build all eleven wheel slots before the window paints its first frame.
    rebuildDisplay()
    opened = true
    invalidateVolatileProvider(activeMenu)
    loadProviderForMenu(activeMenu)
    // The shell may start before first-install packages have finished placing
    // their icons. Refresh here even when the desktop entry list did not change.
    if (root.appLibrary) root.appLibrary.refreshIcons()

    Qt.callLater(function() { keyCatcher.forceActiveFocus() })
  }

  function openDmenu(payload) {
    requestSerial += 1
    var nextMode = payload.mode === "input" ? "input" : "select"
    // Preserve the wheel's centering binding during menu → Keybindings
    // transitions; switching mode first briefly disables it for one frame.
    dmenuPrompt = String(payload.prompt || (nextMode === "input" ? "Input" : "Select"))
    mode = nextMode
    dmenuOptions = Array.isArray(payload.options) ? payload.options : []
    selectionFile = String(payload.selectionFile || "")
    doneFile = String(payload.doneFile || "")
    requestActive = !!doneFile
    dmenuWidth = Math.max(1, Number(payload.width || 300))
    dmenuMaxHeight = Math.max(0, Number(payload.maxHeight || 0))
    activeMenu = "root"
    navStack = []
    filterText = ""
    selectedIndex = 0
    cursorActive = mode !== "input"
    root.disarmPointer()
    rebuildDisplay()
    opened = true

    Qt.callLater(function() { keyCatcher.forceActiveFocus() })
  }
  ListModel { id: displayModel }
  ListModel { id: scannerModel }

  LocalAppLibrary { id: localAppLibrary; visible: false }

  // ----------------------------------------------------------- route surface
  //
  // The menu is opened through the standard plugin lifecycle:
  // `omarchy-shell shell summon omarchy.menu '{"menu":"system"}'`.
  // Callers may pass a real id (`system`, `setup.power`) or an alias declared
  // in JSONC (`power`, `reminder-set`). Unknown strings fall through to the
  // id-as-route behavior so misspellings still attempt to open the literal id.
  function resolveRoute(input) {
    return MenuModel.resolveRoute(root.items, root.itemOrder, input)
  }

  function openRoute(initialMenu) {
    var id = root.resolveRoute(initialMenu)
    var entry = root.items[id]
    // If the resolved id is an action (i.e. the user invoked an alias for
    // a leaf, e.g. `omarchy menu summon screenrecord-stop`), run it directly
    // instead of opening an action with no children.
    if (entry && entry.kind === "action" && entry.action) {
      root.cancel()
      root.runAction(entry.action)
      return "ok"
    }
    // If it's a link (a redirect to another menu), follow the link.
    if (entry && entry.kind === "link" && entry.target) id = entry.target
    root.pendingInitialMenu = id
    root.openExistingMenu(id)
    return "ok"
  }

  function disarmPointer() {
    pointerGate.reset()
  }

  function selectFromPointer(index, item, mouse) {
    if (!pointerGate.moved(item, mouse)) return
    if (root.selectedIndex !== index) resetWheel()
    root.cursorActive = true
    // Hover changes highlighting, not the model's center. Rebinding the row
    // beneath the pointer recursively generated more hover selection events.
    root.pointerSelecting = true
    root.selectedIndex = index
    root.pointerSelecting = false
  }

  Process {
    id: providerProc
    property string menuId: ""
    property string providerKey: ""
    property string collected: ""
    property int revision: 0
    stdout: SplitParser {
      onRead: function(data) { providerProc.collected += data + "\n" }
    }
    onExited: {
      if (providerProc.revision === root.providerRevision) {
        root.mergeProviderRows(providerProc.collected, providerProc.menuId, providerProc.providerKey)
        if (root.filterText.trim()) root.loadProvidersForSearch()
      }
      root.startNextProvider()
    }
  }

  Process {
    id: resultProc
    onExited: {
      if (root.applySerial === root.requestSerial)
        root.opened = false
    }
  }

  PointerMoveGate {
    id: pointerGate
    referenceItem: card
    threshold: Style.space(4)
  }

  Connections {
    target: root.appLibrary
    function onAppsChanged() {
      if (root.providersLoaded["apps"]) root.mergeAppRows()
    }
  }

  // The JSONC sources are watched so live edits to the default file (or the
  // user extension at ~/.config/omarchy/extensions/omarchy-menu.jsonc) take
  // effect without restarting the shell.
  FileView {
    id: defaultMenuFile
    path: root.defaultMenuPath
    watchChanges: true
    printErrors: false
    onLoaded: { root.defaultMenuItems = root.parseMenuJsonc(text()); root.rebuildItemsFromSources() }
    onFileChanged: reload()
  }

  FileView {
    id: userMenuFile
    path: root.userMenuPath
    watchChanges: true
    printErrors: false
    onLoaded: { root.userMenuItems = root.parseMenuJsonc(text()); root.rebuildItemsFromSources() }
    onLoadFailed: { root.userMenuItems = []; root.rebuildItemsFromSources() }
    onFileChanged: reload()
  }

  // ---------------------------------------------------------------- guards
  //
  // `when:` (visibility) and `checked:` (✓ marker) are bash expressions the
  // shell wasn't allowed to evaluate before the perf rewrite. Now the shell
  // batches them into one bash subprocess per (re)load so the open path
  // never has to wait on them.

  property var whenResults: ({})       // id → true|false (allow visibility)
  property var checkedResults: ({})    // id → true|false (show ✓)
  property bool guardsPending: false

  function evaluateGuards() {
    // Process ignores a command change while it is running, and `collected`
    // belongs to the run in flight, so a second evaluation cannot overwrite
    // the first: it would throw away the lines already read and never start.
    // The surviving tail then lands as the whole answer, and every id lost
    // with it goes back to showing, since a `when:` only hides on an explicit
    // false. Wait for the run in flight and evaluate once it lands instead.
    if (guardProc.running) {
      root.guardsPending = true
      return
    }
    root.guardsPending = false

    var script = MenuModel.guardScript(root.items)
    if (!script) {
      root.whenResults = ({})
      root.checkedResults = ({})
      return
    }
    guardProc.collected = ""
    guardProc.command = ["bash", "-lc", script]
    guardProc.running = true
  }

  Process {
    id: guardProc
    property string collected: ""
    stdout: SplitParser {
      onRead: function(data) { guardProc.collected += data + "\n" }
    }
    onExited: function(exitCode, exitStatus) {
      // A batch that was killed rather than finished has only told us about
      // the rows it reached, and a row whose `when:` went unanswered shows.
      // Keep the last complete set rather than let a half-read one through.
      // A signal leaves the exit code at 0, so the status is what tells us.
      if (exitCode !== 0 || exitStatus !== 0) {
        if (root.guardsPending) Qt.callLater(function() { root.evaluateGuards() })
        return
      }

      var nextWhen = ({})
      var nextChecked = ({})
      var lines = guardProc.collected.split("\n")
      for (var i = 0; i < lines.length; i++) {
        var line = lines[i].trim()
        if (!line) continue
        var colon = line.lastIndexOf(":")
        if (colon < 0) continue
        var value = line.substring(colon + 1) === "1"
        var rest = line.substring(0, colon)
        var tagAt = rest.lastIndexOf(":")
        if (tagAt < 0) continue
        var id = rest.substring(0, tagAt)
        var tag = rest.substring(tagAt + 1)
        if (tag === "w") nextWhen[id] = value
        else if (tag === "c") nextChecked[id] = value
      }
      root.whenResults = nextWhen
      root.checkedResults = nextChecked
      if (root.opened) root.rebuildDisplay()
      // Run the evaluation that had to stand aside. Deferred by a turn so the
      // process is settled before its command is set again.
      if (root.guardsPending) Qt.callLater(function() { root.evaluateGuards() })
    }
  }
  PanelWindow {
    id: panel
    visible: root.opened && root.rowsLoaded
    anchors { top: true; bottom: true; left: true; right: true }
    color: "transparent"
    WlrLayershell.namespace: "omarchy-menu"
    WlrLayershell.layer: WlrLayer.Overlay
    WlrLayershell.keyboardFocus: WlrKeyboardFocus.Exclusive
    exclusionMode: ExclusionMode.Ignore

    // The card opens centered exactly as always. The first search keystroke
    // or submenu move freezes the top line where it currently sits — from
    // then on the card grows and shrinks downward instead of re-centering
    // on every resize, which made the menu jump around. The rows height is
    // frozen at the same moment, so the starting menu also caps how tall the
    // card may grow from there. Closing unfreezes both.
    property int cardTop: -1
    property int maxRowsHeight: -1
    readonly property int scannerMargin: Math.min(Style.space(150), Math.max(Style.gapsOut, width * 0.075))
    readonly property int centeredTop: Math.max(Style.gapsOut, Math.round((height - root.cardHeight) / 2))
    readonly property int effectiveCardTop: cardTop >= 0 ? cardTop : centeredTop
    function freezeCardTop() {
      if (visible && cardTop < 0) {
        cardTop = effectiveCardTop
        maxRowsHeight = root.visibleRowsHeight
      }
    }
    onVisibleChanged: if (!visible) { cardTop = -1; maxRowsHeight = -1 }

    Rectangle {
      anchors.fill: parent
      color: root.scrim
      opacity: root.wheelActive ? root.wheelIntro : 1
    }

    // Atmospheric chrome exists only in this temporary menu window. Nothing
    // gets painted on the wallpaper or spawned as a persistent desktop HUD.
    Item {
      anchors.fill: parent
      visible: root.wheelActive
      opacity: root.wheelIntro
      Canvas {
        anchors.fill: parent
        onPaint: {
          var ctx = getContext("2d")
          ctx.clearRect(0, 0, width, height)
          var fogX = root.mirroredBindings ? width * 0.73 : width * 0.27
          var fog = ctx.createRadialGradient(fogX, height * 0.49, width * 0.08, fogX, height * 0.49, width * 0.9)
          fog.addColorStop(0, "rgba(4, 10, 14, 0.68)")
          fog.addColorStop(1, "rgba(4, 10, 14, 0.06)")
          ctx.fillStyle = fog
          ctx.fillRect(0, 0, width, height)
        }
      }
      Rectangle { width: parent.width; height: 1; y: parent.height * 0.13; color: root.border; opacity: 0.3 }
      Rectangle { width: parent.width; height: 1; y: parent.height * 0.87; color: root.border; opacity: 0.3 }
      Rectangle { width: 2; height: parent.height * 0.74; x: parent.width * (root.mirroredBindings ? 0.28 : 0.72); y: parent.height * 0.13; color: root.border; opacity: 0.2; visible: panel.width > Style.space(920) }

      Column {
        width: Math.min(Style.space(360), parent.width * 0.23)
        x: root.mirroredBindings ? panel.scannerMargin : parent.width * 0.76
        y: card.y + root.contentMargin
        spacing: root.contentSpacing
        visible: panel.width > Style.space(1100)
        Item {
          width: parent.width
          height: root.headerHeight
          Text { anchors.top: parent.top; width: parent.width; text: "// NEURAL LINK  /  ACTIVE"; color: root.border; font.family: root.scannerFont; font.pixelSize: Style.font.body; elide: Text.ElideRight }
          Text { anchors.verticalCenter: parent.verticalCenter; width: parent.width; text: root.mirroredBindings ? "KEYBINDINGS INDEX" : root.appScanner ? "APPLICATION INDEX" : "COMMAND DIRECTORY"; color: root.foreground; font.family: root.scannerFont; font.pixelSize: Style.font.display; font.bold: true; elide: Text.ElideRight }
        }
        Text { width: parent.width; text: "ENTRIES   " + displayModel.count; color: root.foreground; opacity: 0.78; font.family: root.scannerFont; font.pixelSize: Style.font.bodySmall }
        Text { width: parent.width; text: "TARGET    " + (root.cursorActive ? (root.selectedIndex + 1) : "—"); color: root.selectedText; font.family: root.scannerFont; font.pixelSize: Style.font.bodySmall }
        Text { width: parent.width; text: "SCROLL / TYPE / EXECUTE"; color: root.foreground; opacity: 0.58; font.family: root.scannerFont; font.pixelSize: Style.font.bodySmall; elide: Text.ElideRight }
      }
    }

    MouseArea {
      anchors.fill: parent
      onClicked: root.cancel()
    }

    BorderSurface {
      id: card
      width: root.cardWidth
      height: Math.min(root.cardHeight, panel.height - Style.gapsOut - panel.effectiveCardTop)
      radius: root.scannerActive || root.dmenuActive ? 0 : root.cornerRadius
      x: root.scannerActive ? panel.scannerMargin : root.mirroredBindings ? panel.width - panel.scannerMargin - width : Math.round((panel.width - width) / 2)
      y: panel.effectiveCardTop
      color: root.wheelActive ? "transparent" : root.background
      opacity: root.wheelActive ? root.wheelIntro : 1
      borderSpec: root.wheelActive ? Border.none() : root.dmenuActive ? root.selectedBorderSpec : root.borderSpec
      padding: root.contentMargin

      SequentialAnimation {
        id: scanIntro
        NumberAnimation { target: root; property: "wheelIntro"; from: 0; to: 1; duration: 120; easing.type: Easing.OutCubic }
      }

      MouseArea { anchors.fill: parent; onClicked: {} }

      Item {
        id: keyCatcher
        anchors.fill: parent
        z: root.deleteConfirmOpen ? 20 : 0
        focus: true

        Keys.priority: Keys.BeforeItem
        Keys.onPressed: function(event) {
          if (root.deleteConfirmOpen) {
            if (deleteConfirm.handleKey(event)) event.accepted = true
            return
          }

          if (event.key === Qt.Key_Delete) {
            root.requestDeleteSelected()
            event.accepted = true
          } else if (event.key === Qt.Key_Escape) {
            if (root.filterText) root.setFilter("")
            else root.cancel()
            event.accepted = true
          } else if (Util.editsFilter(event, root.filterText)) {
            root.setFilter(Util.editedFilter(event, root.filterText))
            event.accepted = true
          } else if ((event.key === Qt.Key_Backspace || event.key === Qt.Key_Left) && !root.filterText) {
            root.goBack()
            event.accepted = true
          } else if (event.key === Qt.Key_Up) {
            root.select(-1)
            event.accepted = true
          } else if (event.key === Qt.Key_Down) {
            root.select(1)
            event.accepted = true
          } else if (event.key === Qt.Key_PageUp) {
            root.select(-6)
            event.accepted = true
          } else if (event.key === Qt.Key_PageDown) {
            root.select(6)
            event.accepted = true
          } else if (event.key === Qt.Key_Return || event.key === Qt.Key_Enter || event.key === Qt.Key_Right) {
            if (root.dmenuActive) {
              if (root.mode === "input") root.applyDmenuSelection(root.filterText)
              else if (displayModel.count > 0) root.activateIndex(root.cursorActive ? root.selectedIndex : 0)
            } else if (root.cursorActive) root.activateIndex(root.selectedIndex)
            else if (displayModel.count > 0) root.cursorActive = true
            event.accepted = true
          } else if (event.text && event.text.length === 1 && event.text.charCodeAt(0) >= 32 && event.text.charCodeAt(0) !== 127 && (event.modifiers === Qt.NoModifier || event.modifiers === Qt.ShiftModifier)) {
            root.setFilter(root.filterText + event.text)
            event.accepted = true
          }
        }

        ConfirmDialog {
          id: deleteConfirm

          anchors.fill: parent
          opened: root.deleteConfirmOpen
          z: 10
          message: "Do you want to uninstall " + ((root.deleteTarget && root.deleteTarget.label) || "") + "?"
          confirmText: "Uninstall"
          background: root.background
          foreground: root.foreground
          scrim: root.scrim
          selectedBackground: root.selectedBackground
          selectedText: root.selectedText
          fontFamily: root.fontFamily
          cornerRadius: root.cornerRadius
          onCanceled: root.cancelDelete()
          onConfirmed: root.confirmDelete()
        }
      }

      Column {
        id: cardBody
        anchors.fill: parent
        anchors.topMargin: card.contentTopInset
        anchors.rightMargin: card.contentRightInset
        anchors.bottomMargin: card.contentBottomInset
        anchors.leftMargin: card.contentLeftInset
        spacing: root.contentSpacing

        Rectangle {
          width: parent.width
          height: root.headerHeight
           radius: root.scannerActive || root.dmenuActive ? 0 : root.cornerRadius
          color: "transparent"

          Text {
            textFormat: Text.PlainText
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: parent.top
             text: root.scannerActive ? "// CYBERDECK.OS  /  " + root.activeMenu.toUpperCase() : root.mirroredBindings ? "// CYBERDECK.OS  /  KEYBINDINGS" : "// CYBERDECK.OS  /  DATA LINK"
             visible: root.scannerActive || root.dmenuActive
            color: root.selectedBorder
            opacity: 0.84
            font.family: root.scannerFont
             font.pixelSize: Style.font.bodySmall
             horizontalAlignment: root.mirroredBindings ? Text.AlignRight : Text.AlignLeft
            elide: Text.ElideRight
          }

          Text {
            textFormat: Text.PlainText
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.verticalCenter: parent.verticalCenter
             text: root.scannerActive
               ? (root.item(root.activeMenu) ? (root.item(root.activeMenu).title || root.item(root.activeMenu).label).toUpperCase() : "COMMANDS")
               : (root.dmenuActive ? root.dmenuPrompt.toUpperCase() : (root.filterText || ((root.item(root.activeMenu) ? (root.item(root.activeMenu).title || root.item(root.activeMenu).label) : "Go") + "…")))
             color: root.scannerActive || root.dmenuActive ? root.selectedText : root.foreground
            opacity: root.scannerActive || root.dmenuActive || root.filterText ? 1 : 0.58
             font.family: root.scannerActive || root.dmenuActive ? root.scannerFont : root.fontFamily
             font.pixelSize: root.scannerActive || root.dmenuActive ? Style.font.display : Style.font.heading
             font.bold: root.scannerActive || root.dmenuActive
             horizontalAlignment: root.mirroredBindings ? Text.AlignRight : Text.AlignLeft
            elide: Text.ElideRight
          }

          Text {
            textFormat: Text.PlainText
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.bottom: parent.bottom
             text: "› " + (root.filterText ? root.filterText.toUpperCase() + " ▌" : (root.mode === "input" ? "TYPE INPUT" : "TYPE TO SEARCH"))
             visible: root.scannerActive || root.dmenuActive
            color: root.filterText ? root.foreground : root.border
            opacity: root.filterText ? 0.95 : 0.54
            font.family: root.scannerFont
             font.pixelSize: Style.font.bodySmall
             horizontalAlignment: root.mirroredBindings ? Text.AlignRight : Text.AlignLeft
            elide: Text.ElideRight
          }
        }

        Item {
          width: parent.width
          height: root.visibleRowsHeight

          ListView {
            id: resultList
            anchors.fill: parent
            model: root.wheelActive ? scannerModel : displayModel
            clip: true
            interactive: !root.wheelActive
            spacing: root.rowSpacing
            boundsBehavior: Flickable.StopAtBounds
            // ListView resets contentY when its model switches, even between
            // two wheel routes. Correct that reset in the same turn, and do
            // the same when the layer-shell surface gains its real height.
            onContentYChanged: if (root.wheelActive) root.centerWheelView()
            onContentHeightChanged: if (root.wheelActive) root.centerWheelView()
            onHeightChanged: if (root.wheelActive) root.centerWheelView()
            onModelChanged: if (root.wheelActive) root.centerWheelView()

            header: Item {
              width: resultList.width
              height: 0
            }
            footer: Item {
              width: resultList.width
              height: 0
            }
            onMovementEnded: if (!root.wheelActive) root.revealCursor()

            section.property: root.wheelActive ? "" : "section"
            section.criteria: ViewSection.FullString
            section.delegate: Item {
              required property string section

              width: ListView.view.width
              height: section === "drilldown" ? root.dividerHeight : 0
              visible: section === "drilldown"

              Text {
                anchors.left: parent.left
                anchors.verticalCenter: parent.verticalCenter
                text: "// EXTENDED RESULTS"
                color: root.selectedText
                opacity: 0.66
                font.family: root.scannerFont
                font.pixelSize: Style.font.bodySmall
              }
            }

            delegate: Item {
              id: row
              required property int index
              required property int sourceIndex
              required property string itemId
              required property string kind
              required property string icon
              required property string iconFont
              required property string appIcon
              required property string appId
              required property string label
              required property string target
              required property string detail
              required property string path
              required property string action
              required property int childCount

              readonly property bool hasCursor: !root.replacingRows && root.cursorActive && row.sourceIndex >= 0 && row.sourceIndex === root.selectedIndex
              readonly property bool isApp: row.kind === "app"
              readonly property bool hasIcon: row.icon.length > 0 || row.isApp
              readonly property bool scannerRow: root.wheelActive && row.sourceIndex >= 0
              readonly property bool mirroredRow: root.mirroredBindings && row.sourceIndex >= 0
              readonly property bool hudRow: row.scannerRow || (root.dmenuActive && row.sourceIndex >= 0)
              readonly property real edgeOpacity: {
                if (resultList.contentHeight <= resultList.height) return 1
                var centreY = row.y + rowFrame.y + row.height / 2 - resultList.contentY
                var fade = Math.min(Style.space(48), resultList.height / 2)
                return Math.max(0, Math.min(1, centreY / fade, (resultList.height - centreY) / fade))
              }

               // ListView controls the delegate's x/y. Move its inner frame and
               // pointer target together; the two extra slots buffer the fold.
               width: ListView.view.width
               height: root.wheelActive ? root.baseRowHeight : root.rowHeightForDetail(row.detail)
              onHasCursorChanged: if (hudRow) scannerFrame.requestPaint()

              BorderSurface {
                id: rowFrame
                 width: row.scannerRow ? Math.min(root.mirroredBindings ? row.width - Style.space(122) : Style.space(510), Math.max(Style.space(180), row.width - Style.space(root.mirroredBindings ? 122 : 110))) : row.width
                 height: row.height
                 // Shift the same-sized frames along the curve as their actual
                 // rows travel vertically, rather than replacing only text.
                 x: row.scannerRow ? (row.mirroredRow ? row.width - width - Style.space(5) : Style.space(5)) + (row.mirroredRow ? -1 : 1) * Math.round(Math.min(root.wheelCurveDepth, Math.max(0, row.width - width - Style.space(12))) * Math.pow(Math.min(1, Math.abs((row.index - 5 + root.wheelOffset) / 4)), 1.35)) : 0
                 y: row.scannerRow ? root.wheelOffset * (row.height + root.rowSpacing) : 0
                  opacity: row.edgeOpacity * (row.scannerRow ? Math.max(0.42, 1 - Math.pow(Math.abs((row.index - 5 + root.wheelOffset) / 4), 2) * 0.58) : 1)
                radius: row.hudRow ? 0 : root.cornerRadius
                color: row.hudRow ? "transparent" : (row.hasCursor ? root.selectedBackground : "transparent")
                borderSpec: row.hudRow ? Border.none() : (row.hasCursor ? root.selectedBorderSpec : Border.none())

              Canvas {
                id: scannerFrame
                anchors.fill: parent
                 visible: row.hudRow
                onWidthChanged: requestPaint()
                onHeightChanged: requestPaint()
                onPaint: {
                  var ctx = getContext("2d")
                  ctx.clearRect(0, 0, width, height)
                  var badge = Math.min(height - 12, Style.space(30))
                  var badgeY = (height - badge) / 2
                  var left = Style.space(49)
                  var inset = Style.space(5)
                  var corner = Style.space(6)
                  ctx.fillStyle = "rgba(12, 16, 21, 0.56)"
                   var badgeX = row.mirroredRow ? width - badge - 1 : 1
                   ctx.fillRect(badgeX, badgeY, badge, badge)
                   ctx.save()
                   ctx.strokeStyle = row.hasCursor ? String(root.selectedBorder) : String(root.selectedText)
                   ctx.shadowColor = ctx.strokeStyle
                   ctx.shadowBlur = row.hasCursor ? 12 : 7
                    ctx.globalAlpha = row.hasCursor ? 1 : 0.96
                     ctx.lineWidth = row.hasCursor ? 1.6 : 1.1
                     ctx.strokeRect(badgeX + 2, badgeY + 2, badge - 4, badge - 4)
                     // Just enough extra weight to suggest direction without
                     // making either corner look like a solid bracket.
                     var heavy = row.hasCursor ? 2.4 : 1.9
                     ctx.fillStyle = ctx.strokeStyle
                     ctx.fillRect(row.mirroredRow ? badgeX + badge - 2 - heavy : badgeX + 2,
                                  badgeY + 2, heavy, badge - 4)
                     ctx.fillRect(badgeX + 2, row.mirroredRow ? badgeY + 2 : badgeY + badge - 2 - heavy,
                                  badge - 4, heavy)
                   ctx.restore()
                  ctx.beginPath()
                   if (row.mirroredRow) {
                     ctx.moveTo(width - left, 4)
                     ctx.lineTo(corner + 4, 4)
                     ctx.lineTo(4, corner + 4)
                     ctx.lineTo(4, height - 4)
                     ctx.lineTo(width - left - inset, height - 4)
                     ctx.lineTo(width - left - inset, height - Style.space(18))
                     ctx.lineTo(width - left, height - Style.space(23))
                   } else {
                     ctx.moveTo(left, 4)
                     ctx.lineTo(width - corner - 4, 4)
                     ctx.lineTo(width - 4, corner + 4)
                     ctx.lineTo(width - 4, height - 4)
                     ctx.lineTo(left + inset, height - 4)
                     ctx.lineTo(left + inset, height - Style.space(18))
                     ctx.lineTo(left, height - Style.space(23))
                   }
                  ctx.closePath()
                  ctx.globalAlpha = 1
                  ctx.fillStyle = row.hasCursor ? "rgba(40, 15, 23, 0.91)" : "rgba(8, 14, 18, 0.81)"
                  ctx.fill()
                   ctx.save()
                   ctx.strokeStyle = row.hasCursor ? String(root.selectedBorder) : String(root.selectedText)
                   ctx.shadowColor = ctx.strokeStyle
                   ctx.shadowBlur = row.hasCursor ? 14 : 8
                   ctx.lineWidth = row.hasCursor ? 2 : 1.2
                    ctx.globalAlpha = row.hasCursor ? 1 : 0.96
                   ctx.stroke()
                   ctx.restore()
                   if (row.hasCursor) {
                    ctx.fillStyle = String(root.selectedBorder)
                     ctx.fillRect(row.mirroredRow ? width - left - Style.space(4) : left + 1, 3, Style.space(3), height - 6)
                  }
                }
              }

               Text {
                  visible: row.hudRow
                 text: (row.sourceIndex + 1 < 10 ? "0" : "") + (row.sourceIndex + 1)
                 color: root.selectedText
                 opacity: row.hasCursor ? 1 : 0.83
                font.family: root.scannerFont
                font.pixelSize: Style.font.body
                font.bold: row.hasCursor
                 x: row.mirroredRow ? parent.width - width - Style.space(4) : Style.space(4)
                width: Style.space(25)
                horizontalAlignment: Text.AlignHCenter
                anchors.verticalCenter: parent.verticalCenter
               }

               Text {
                 visible: row.scannerRow && row.sourceIndex === root.drilldownStart
                 x: row.mirroredRow ? parent.width - width - Style.space(55) : Style.space(49)
                 y: -Style.space(11)
                 text: "// EXTENDED RESULTS"
                 color: root.selectedText
                 opacity: 0.82
                 font.family: root.scannerFont
                 font.pixelSize: Style.font.bodySmall
               }

              Rectangle {
                visible: false
                width: Style.space(4)
                height: parent.height - Style.space(18)
                radius: Math.min(root.cornerRadius, Style.space(4))
                color: root.selectedBackground
                anchors.left: parent.left
                anchors.leftMargin: row.scannerRow ? Style.space(61) : root.rowReservedBorderLeft + Style.space(8)
                anchors.verticalCenter: parent.verticalCenter
              }

              Text {
                id: iconText
                textFormat: Text.PlainText
                visible: row.hasIcon && !row.isApp
                text: row.icon
                 color: row.hasCursor || row.hudRow ? root.selectedText : root.foreground
                font.family: row.iconFont.length > 0 ? row.iconFont : root.fontFamily
                 font.pixelSize: row.hudRow ? Style.font.iconLarge + Style.space(6) : Style.font.iconLarge
                width: Style.space(36)
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
                 x: row.mirroredRow ? parent.width - width - Style.space(61) : row.hudRow ? Style.space(61) : root.rowReservedBorderLeft + Style.space(8)
                 anchors.verticalCenter: parent.verticalCenter
              }

              Image {
                id: appIconImage
                visible: row.isApp
                 width: row.hudRow ? Style.font.iconLarge + Style.space(5) : Style.font.iconLarge
                 height: width
                fillMode: Image.PreserveAspectFit
                // Decode at physical pixels — a logical-size decode leaves
                // PNG icons upscaled and blurry on HiDPI displays.
                sourceSize.width: width * Screen.devicePixelRatio
                sourceSize.height: height * Screen.devicePixelRatio
                source: row.isApp && root.appLibrary ? root.appLibrary.iconSource(row.appIcon) : ""
                asynchronous: true
                 x: row.mirroredRow ? parent.width - Style.space(61) - (Style.space(36) + width) / 2 : row.hudRow ? Style.space(61) + (Style.space(36) - width) / 2 : root.rowReservedBorderLeft + Style.space(8) + (Style.space(36) - width) / 2
                 anchors.verticalCenter: parent.verticalCenter
              }

              Column {
                id: contentColumn
                 anchors.left: row.mirroredRow ? parent.left : row.hasIcon ? iconText.right : parent.left
                 anchors.leftMargin: row.mirroredRow ? Style.space(18) : row.hasIcon ? Style.space(6) : (row.hudRow ? Style.space(71) : root.rowReservedBorderLeft + Style.space(18))
                 anchors.right: row.mirroredRow ? (row.hasIcon ? iconText.left : parent.right) : trail.left
                 anchors.rightMargin: row.mirroredRow ? (row.hasIcon ? Style.space(6) : Style.space(72)) : Style.space(6)
                anchors.verticalCenter: parent.verticalCenter
                 spacing: row.scannerRow && !row.mirroredRow ? 0 : Style.space(3)

                Text {
                  id: labelText
                  textFormat: Text.PlainText
                  width: parent.width
                  text: row.label
                   color: row.scannerRow ? root.foreground : row.hasCursor || row.hudRow ? root.selectedText : root.foreground
                   font.family: row.hudRow ? root.scannerFont : root.fontFamily
                   font.pixelSize: row.scannerRow && root.appScanner ? Style.font.heading + 2 : Style.font.heading
                  font.weight: Font.Medium
                  elide: Text.ElideRight
                }

                Text {
                  textFormat: Text.PlainText
                  width: parent.width
                   text: row.detail || (row.kind === "app" ? "READY" : ((row.kind === "menu" || row.kind === "link") ? "OPEN SUBSYSTEM" : "EXECUTE COMMAND"))
                   visible: (row.scannerRow && !row.mirroredRow) || (row.detail.length > 0 && (root.filterText || row.kind === "dmenu"))
                   color: row.hasCursor || row.hudRow ? root.selectedText : root.foreground
                  opacity: row.scannerRow ? 0.72 : 0.52
                   font.family: row.hudRow ? root.scannerFont : root.fontFamily
                   font.pixelSize: row.scannerRow && root.appScanner ? Style.font.bodySmall + 1 : Style.font.bodySmall
                  elide: Text.ElideRight
                }
              }

              Row {
                id: trail
                width: row.scannerRow ? Math.max(Style.space(38), implicitWidth) : Style.space(14)
                anchors.right: parent.right
                anchors.rightMargin: root.rowReservedBorderRight + Style.space(row.scannerRow ? 12 : 8)
                 anchors.verticalCenter: parent.verticalCenter
                spacing: row.scannerRow ? Style.space(7) : 0

                Text {
                  textFormat: Text.PlainText
                  visible: row.scannerRow && row.childCount > 0
                  text: row.childCount
                  color: root.foreground
                  opacity: 0.45
                  font.family: row.scannerRow ? root.scannerFont : root.fontFamily
                  font.pixelSize: Style.font.body
                  anchors.verticalCenter: parent.verticalCenter
                }

                Text {
                  textFormat: Text.PlainText
                  text: row.kind === "menu" || row.kind === "link" ? "›" : ""
                  color: row.hasCursor ? root.selectedText : root.foreground
                  opacity: row.kind === "menu" || row.kind === "link" ? 0.36 : 0
                  font.family: row.scannerRow ? root.scannerFont : root.fontFamily
                  font.pixelSize: Style.font.heading
                  font.weight: Font.Normal
                  anchors.verticalCenter: parent.verticalCenter
                }
              }

              MouseArea {
                id: mouseArea
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                enabled: row.sourceIndex >= 0
                onPositionChanged: function(mouse) {
                  root.selectFromPointer(row.sourceIndex, rowFrame, mouse)
                }
                 onClicked: {
                   root.resetWheel()
                  var pickedIndex = row.sourceIndex
                  root.cursorActive = true
                  root.selectedIndex = pickedIndex
                  root.activateIndex(pickedIndex, true)
                }
              }
              }
            }

            MouseArea {
              anchors.fill: parent
              acceptedButtons: Qt.NoButton
              onWheel: function(wheel) {
                if (!root.wheelActive) return
                if (!wheel.angleDelta.y && !wheel.pixelDelta.y) return
                root.wheelInput = MenuInteraction.wheelStep(wheel.angleDelta.y, wheel.pixelDelta.y, root.wheelInput)
                if (root.wheelInput.step) root.select(root.wheelInput.step)
                wheel.accepted = true
              }
            }
          }

          // Fade the row artwork itself; never paint bounded background
          // rectangles over the desktop at the viewport edges.

          Column {
            anchors.centerIn: parent
            spacing: Style.space(8)
            visible: displayModel.count === 0 && root.mode !== "input"

            Text {
              text: "󰈉"
              color: root.selectedText
              opacity: 0.8
              font.family: root.fontFamily
              font.pixelSize: Style.font.displayLarge
              horizontalAlignment: Text.AlignHCenter
              width: Style.space(320)
            }

            Text {
              textFormat: Text.PlainText
              text: root.filterText ? "No matches for “" + root.filterText + "”" : "Nothing here yet"
              color: root.foreground
              opacity: 0.7
              font.family: root.fontFamily
              font.pixelSize: Style.font.title
              horizontalAlignment: Text.AlignHCenter
              width: Style.space(320)
            }
          }
        }

        Item {
          width: parent.width
          height: root.scannerFooterHeight

          Text {
             visible: root.wheelActive
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.verticalCenter: parent.verticalCenter
             text: "[ TYPE ] SEARCH     [ ↑ ↓ / SCROLL ] NAVIGATE     [ ENTER ] EXECUTE     [ ESC ] CLOSE"
            textFormat: Text.PlainText
            color: root.foreground
            opacity: 0.68
            font.family: root.scannerFont
            font.pixelSize: Style.font.bodySmall
             elide: Text.ElideRight
             horizontalAlignment: root.mirroredBindings ? Text.AlignRight : Text.AlignLeft
          }
        }
      }
    }
  }
}
