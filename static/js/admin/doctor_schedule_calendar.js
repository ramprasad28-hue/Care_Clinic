/**
 * Doctor schedule calendar ("Google Calendar"-style) for the Care_Clinic
 * doctor admin. No dependencies, no build step (ADR-020).
 *
 * One widget, three entry points (all fields are parameterized in
 * schedule_widget.html):
 *
 *  - Doctor change page (saved doctor): concrete endpoint URLs; every
 *    calendar write is mirrored into the matching inline formset row so a
 *    later main-form save can never post stale values over it.
 *  - Doctor add page (unsaved draft mode, data-unsaved="true"): rules and
 *    leaves are client-side drafts; they are synced into the availability /
 *    leave inline formsets right before the doctor form submits, and are
 *    re-imported from the rows after a failed validation round-trip.
 *  - Schedule hub pages (AvailabilityRule / DoctorLeave changelist views):
 *    a doctor selector drives a scoped `/0/` URL sentinel — the JS resolves
 *    the "/0/" segment against the currently selected doctor at request time.
 *
 * Responsibilities:
 *  - Month / week / day views with prev-next-today navigation and period label.
 *  - Availability rules are RECURRING: the server expands them into concrete
 *    date occurrences; the client only renders (drafts expand client-side).
 *  - Doctor leave renders as date-specific ranges (single- and multi-day).
 *  - Clicking an empty day/cell opens an add menu; clicking an event chip
 *    opens details (edit / activate-deactivate / delete with confirmation).
 *  - Writes go through the DoctorAdmin schedule JSON endpoints with the
 *    page's CSRF token; the server stays the scheduling source of truth.
 *  - Loading indicator, success/validation status, duplicate-submit guard,
 *    empty states, focus rings, aria labels, responsive layouts.
 *
 * The main doctor form is untouched; the inline formsets remain functional
 * without JavaScript and are collapsed only as a progressive enhancement.
 */
(function () {
    "use strict";

    var root = document.getElementById("cc-calendar");
    if (!root) return;

    var HOUR_START = 7;
    var HOUR_END = 21; // exclusive: hour rows 07:00..20:00

    var WEEKDAY_LABELS = [
        "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday",
    ];
    var MONTH_LABELS = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December",
    ];

    var els = {
        board: root.querySelector("[data-board]"),
        rangeLabel: root.querySelector("[data-range-label]"),
        status: root.querySelector("[data-status]"),
        spinner: root.querySelector("[data-spinner]"),
        csrfInput: root.querySelector("[data-csrf] input[name=csrfmiddlewaretoken]"),
        menu: document.getElementById("cc-menu"),
        menuDateLabel: document.querySelector("[data-menu-date-label]"),
        availabilityDialog: document.getElementById("cc-availability-form"),
        weekdaySelect: document.getElementById("cc-availability-weekday"),
        repeatLabel: document.querySelector("[data-availability-repeat-label]"),
        leaveDialog: document.getElementById("cc-leave-form"),
        detailsDialog: document.getElementById("cc-details"),
        detailsTitle: document.getElementById("cc-details-title"),
        detailsList: document.querySelector("[data-details-list]"),
        detailsNote: document.querySelector("[data-details-note]"),
        confirmDialog: document.getElementById("cc-confirm"),
        confirmText: document.querySelector("[data-confirm-text]"),
        doctorName: root.querySelector("[data-doctor-name]"),
    };

    var eventsUrl = root.getAttribute("data-events-url");
    var createUrls = {
        availability: root.getAttribute("data-availability-create-url"),
        leave: root.getAttribute("data-leave-create-url"),
        oneDay: root.getAttribute("data-one-day-create-url"),
    };

    var state = {
        view: "week",
        anchor: startOfToday(),
        rules: [],
        leaves: [],
        oneDayAvailabilities: [], // date-specific availability records
        occurrences: {}, // isoDate -> expanded availability occurrences
        oneDayOccurrences: {}, // isoDate -> one-day availability entries
        editing: { availability: null, leave: null, oneDay: null },
        selected: null,  // { kind, id }
        context: null,   // { date, start, end } from a cell click
        busy: false,
        saving: false,
        unsaved: root.getAttribute("data-unsaved") === "true",
        doctorId: null,  // target doctor; null = none selected (hub) / not saved
        draftRules: [],  // unsaved-mode rule entries (negative ids)
        draftLeaves: [], // unsaved-mode leave entries (negative ids)
        draftOneDayRules: [], // unsaved-mode one-day entries (negative ids)
        scheduleType: "weekly", // "weekly" or "oneDay"
    };
    var doctorAttr = root.getAttribute("data-doctor");
    if (doctorAttr && /^\d+$/.test(doctorAttr)) state.doctorId = Number(doctorAttr);
    var statusTimer = null;

    // ------------------------------------------------------------------
    // Date/time helpers
    // ------------------------------------------------------------------
    function startOfToday() {
        var now = new Date();
        return new Date(now.getFullYear(), now.getMonth(), now.getDate());
    }

    function addDays(date, days) {
        return new Date(date.getFullYear(), date.getMonth(), date.getDate() + days);
    }

    function monthAnchor(date, months) {
        return new Date(date.getFullYear(), date.getMonth() + months, 1);
    }

    function startOfWeek(date) {
        return addDays(date, -weekdayIndex(date)); // weeks start Monday
    }

    function weekdayIndex(date) {
        return (date.getDay() + 6) % 7; // 0 = Monday (matches clinic.Weekday)
    }

    function isoDate(date) {
        var m = String(date.getMonth() + 1).padStart(2, "0");
        var d = String(date.getDate()).padStart(2, "0");
        return date.getFullYear() + "-" + m + "-" + d;
    }

    function dateFromIso(value) {
        var parts = String(value || "").split("-");
        if (parts.length !== 3) return null;
        var date = new Date(Number(parts[0]), Number(parts[1]) - 1, Number(parts[2]));
        return isNaN(date.getTime()) ? null : date;
    }

    function parseTimeMinutes(value) {
        var match = /^(\d{1,2}):(\d{2})/.exec(String(value || ""));
        return match ? Number(match[1]) * 60 + Number(match[2]) : null;
    }

    function compactTime(value) {
        var minutes = parseTimeMinutes(value);
        if (minutes === null) return "";
        var h = Math.floor(minutes / 60);
        var m = minutes % 60;
        return h + ":" + String(m).padStart(2, "0");
    }

    function minutesToInput(minutes) {
        var h = Math.floor(minutes / 60) % 24;
        var m = minutes % 60;
        return String(h).padStart(2, "0") + ":" + String(m).padStart(2, "0");
    }

    function prettyTime(value) {
        var minutes = parseTimeMinutes(value);
        if (minutes === null) return "";
        var h = Math.floor(minutes / 60);
        var m = minutes % 60;
        var suffix = h < 12 ? "AM" : "PM";
        var h12 = h % 12 === 0 ? 12 : h % 12;
        return h12 + ":" + String(m).padStart(2, "0") + " " + suffix;
    }

    // ------------------------------------------------------------------
    // Status / busy plumbing
    // ------------------------------------------------------------------
    function status(message, kind) {
        els.status.textContent = message || "";
        els.status.className = "cc-status" + (kind ? " cc-status--" + kind : "");
        window.clearTimeout(statusTimer);
        if (message) {
            statusTimer = window.setTimeout(function () {
                els.status.textContent = "";
                els.status.className = "cc-status";
            }, 6000);
        }
    }

    function setBusy(on) {
        state.busy = on;
        els.spinner.hidden = !on;
        root.querySelectorAll(".cc-toolbar .cc-btn").forEach(function (button) {
            button.disabled = on;
        });
    }

    // ------------------------------------------------------------------
    // API
    // ------------------------------------------------------------------
    function request(url, options) {
        options = options || {};
        if (state.busy) return Promise.resolve(undefined);
        setBusy(true);
        var init = {
            method: options.method || "GET",
            credentials: "same-origin",
            headers: { "X-Requested-With": "XMLHttpRequest" },
        };
        if (init.method !== "GET") {
            init.headers["X-CSRFToken"] = els.csrfInput ? els.csrfInput.value : "";
            init.body = options.data; // FormData
        }
        return window.fetch(url, init).then(function (response) {
            setBusy(false);
            return response.json().then(function (payload) {
                return { ok: response.ok, status: response.status, payload: payload };
            });
        }).catch(function () {
            setBusy(false);
            status("Could not reach the server. Please retry.", "error");
            return undefined;
        });
    }

    function postForm(url, fields) {
        if (state.saving || state.busy) return Promise.resolve(undefined);
        var data = new FormData();
        Object.keys(fields || {}).forEach(function (key) {
            var value = fields[key];
            if (value !== undefined && value !== null) data.append(key, value);
        });
        state.saving = true;
        return request(url, { method: "POST", data: data }).then(function (result) {
            state.saving = false;
            return result;
        }, function () {
            state.saving = false;
            return undefined;
        });
    }

    function errorText(payload) {
        if (payload && payload.errors) {
            var parts = [];
            Object.keys(payload.errors).forEach(function (field) {
                var message = payload.errors[field];
                if (Array.isArray(message)) parts.push(message.join(" "));
                else if (message && typeof message === "object" && message.message) {
                    parts.push(message.message);
                } else parts.push(String(message));
            });
            return parts.join(" ");
        }
        return "";
    }

    // ------------------------------------------------------------------
    // URL endpoints derived from the create URLs
    // ------------------------------------------------------------------
    function scopedUrl(url) {
        // Sentinel "/0/" (hub pages, add page) resolves against the currently
        // selected doctor; concrete URLs (change page) pass through.
        if (url === null || url === undefined) return url;
        if (state.doctorId === null) return url;
        var marker = "/0/";
        var at = url.indexOf(marker);
        if (at === -1) return url;
        return url.slice(0, at) + "/" + state.doctorId + "/" + url.slice(at + marker.length);
    }

    function scheduleUrl(kind, action, id) {
        var base = scopedUrl(createUrls[kind]); // .../availability/create/ or .../leave/create/
        return base.replace(/\/create\/$/, "/" + id + "/" + action + "/");
    }

    // ------------------------------------------------------------------
    // Unsaved-draft mode (add-doctor page)
    // ------------------------------------------------------------------
    function draftRuleEntry(weekday, start, end, slot, isActive, id) {
        return {
            id: id === undefined ? null : id,
            weekday: weekday,
            weekday_label: WEEKDAY_LABELS[Number(weekday)],
            start: start,
            end: end,
            slot_length_minutes: slot,
            is_active: !!isActive,
        };
    }

    function draftLeaveEntry(startDate, endDate, reason, id) {
        return {
            id: id === undefined ? null : id,
            start_date: startDate,
            end_date: endDate,
            reason: reason || "",
        };
    }

    function draftOneDayEntry(date, start, end, slot, isActive, id) {
        return {
            id: id === undefined ? null : id,
            date: date,
            start: start,
            end: end,
            slot_length_minutes: slot,
            is_active: !!isActive,
        };
    }

    function findDraft(kind, id) {
        var list;
        if (kind === "availability") list = state.draftRules;
        else if (kind === "leave") list = state.draftLeaves;
        else if (kind === "one_day") list = state.draftOneDayRules;
        else return null;
        return list.find(function (entry) { return String(entry.id) === String(id); });
    }

    function removeDraft(kind, id) {
        var list;
        if (kind === "availability") list = state.draftRules;
        else if (kind === "leave") list = state.draftLeaves;
        else if (kind === "one_day") list = state.draftOneDayRules;
        else return;
        
        if (kind === "availability") {
            state.draftRules = list.filter(function (entry) {
                return String(entry.id) !== String(id);
            });
        } else if (kind === "leave") {
            state.draftLeaves = list.filter(function (entry) {
                return String(entry.id) !== String(id);
            });
        } else if (kind === "one_day") {
            state.draftOneDayRules = list.filter(function (entry) {
                return String(entry.id) !== String(id);
            });
        }
    }

    function draftIdCounter() {
        state.nextDraftId = (state.nextDraftId === undefined) ? -1 : state.nextDraftId - 1;
        return state.nextDraftId;
    }

    function loadDrafts(range) {
        state.rules = state.draftRules;
        state.leaves = state.draftLeaves;
        state.oneDayAvailabilities = state.draftOneDayRules;
        state.occurrences = {};
        state.oneDayOccurrences = {};
        
        var day = new Date(range.start);
        while (day.getTime() <= range.end.getTime()) {
            var key = isoDate(day);
            
            // Expand weekly rules
            state.draftRules.forEach(function (rule) {
                if (Number(rule.weekday) !== weekdayIndex(day)) return;
                state.occurrences[key] = state.occurrences[key] || [];
                state.occurrences[key].push({
                    rule_id: rule.id,
                    date: key,
                    start: rule.start,
                    end: rule.end,
                    is_active: rule.is_active,
                });
            });
            
            // Add one-day availability for matching dates
            state.draftOneDayRules.forEach(function (oneDay) {
                if (oneDay.date !== key) return;
                state.oneDayOccurrences[key] = state.oneDayOccurrences[key] || [];
                state.oneDayOccurrences[key].push({
                    id: oneDay.id,
                    date: key,
                    start: oneDay.start,
                    end: oneDay.end,
                    is_active: oneDay.is_active,
                });
            });
            
            day = addDays(day, 1);
        }
        render();
    }

    // ------------------------------------------------------------------
    // Data loading
    // ------------------------------------------------------------------
    function visibleRange() {
        if (state.view === "month") {
            var gridStart = startOfWeek(new Date(state.anchor.getFullYear(), state.anchor.getMonth(), 1));
            return { start: gridStart, end: addDays(gridStart, 41) }; // 6 weeks
        }
        if (state.view === "week") {
            var weekStart = startOfWeek(state.anchor);
            return { start: weekStart, end: addDays(weekStart, 6) };
        }
        return { start: state.anchor, end: state.anchor };
    }

    function loadEvents() {
        var range = visibleRange();
        if (state.unsaved) {
            loadDrafts(range);
            return;
        }
        if (!eventsUrl || state.doctorId === null) {
            state.rules = [];
            state.leaves = [];
            state.oneDayAvailabilities = [];
            state.occurrences = {};
            state.oneDayOccurrences = {};
            render();
            return;
        }
        var url = scopedUrl(eventsUrl) + "?start=" + isoDate(range.start) + "&end=" + isoDate(range.end);
        return request(url).then(function (result) {
            if (!result) return;
            if (!result.ok) {
                status("Could not load the schedule. " + errorText(result.payload), "error");
                state.rules = [];
                state.leaves = [];
                state.oneDayAvailabilities = [];
                state.occurrences = {};
                state.oneDayOccurrences = {};
            } else {
                state.rules = result.payload.rules || [];
                state.leaves = result.payload.leaves || [];
                state.oneDayAvailabilities = result.payload.one_day_availabilities || [];
                state.occurrences = {};
                state.oneDayOccurrences = {};
                
                // Expand weekly rules into occurrences
                (result.payload.occurrences || []).forEach(function (occurrence) {
                    (state.occurrences[occurrence.date] = state.occurrences[occurrence.date] || [])
                        .push(occurrence);
                });
                
                // Index one-day availability by date
                state.oneDayAvailabilities.forEach(function (oneDay) {
                    (state.oneDayOccurrences[oneDay.date] = state.oneDayOccurrences[oneDay.date] || [])
                        .push(oneDay);
                });
            }
            render();
        });
    }

    // ------------------------------------------------------------------
    // Rendering
    // ------------------------------------------------------------------
    function haveAnyData() {
        return state.rules.length > 0 || state.leaves.length > 0 || state.oneDayAvailabilities.length > 0;
    }

    function render() {
        // Render the active view's grid even when there is nothing stored yet:
        // every empty day/cell is clickable, which is how the first rule for a
        // doctor is created. The empty diagnose note is only appended when no
        // scheduling data exists at all.
        if (state.view === "month") renderMonth();
        else renderTimeGrid();
        if (!haveAnyData()) appendEmptyHint();
        updateToolbar();
    }

    function updateToolbar() {
        root.querySelectorAll("[data-view]").forEach(function (button) {
            button.setAttribute(
                "aria-pressed",
                button.getAttribute("data-view") === state.view ? "true" : "false"
            );
        });
        els.rangeLabel.textContent = rangeLabelText();
    }

    function rangeLabelText() {
        if (state.view === "month") {
            return MONTH_LABELS[state.anchor.getMonth()] + " " + state.anchor.getFullYear();
        }
        if (state.view === "week") {
            var range = visibleRange();
            var from = range.start;
            var to = range.end;
            return from.getDate() + " " + MONTH_LABELS[from.getMonth()].slice(0, 3) +
                " – " + to.getDate() + " " + MONTH_LABELS[to.getMonth()].slice(0, 3) +
                " " + to.getFullYear();
        }
        return WEEKDAY_LABELS[weekdayIndex(state.anchor)] + ", " + state.anchor.getDate() +
            " " + MONTH_LABELS[state.anchor.getMonth()].slice(0, 3) + " " + state.anchor.getFullYear();
    }

    function appendEmptyHint() {
        var wrap = document.createElement("div");
        wrap.className = "cc-empty";
        var strong = document.createElement("strong");
        strong.textContent = state.unsaved
            ? "Draft an availability rule or leave below — nothing is on the server yet."
            : "No availability rules or doctor leave yet.";
        wrap.appendChild(strong);
        var note = document.createElement("span");
        if (state.unsaved) {
            note.textContent = "Click any day to draft a recurring availability window or leave; drafts are saved together with the doctor form.";
        } else if (state.doctorId === null) {
            note.textContent = "Pick a doctor above to view and edit their schedule.";
        } else {
            note.textContent = "Click any day to add a recurring availability window or leave, or use the buttons above.";
        }
        wrap.appendChild(note);
        els.board.appendChild(wrap);
    }

    function makeEventButton(options) {
        var chip = document.createElement("button");
        chip.type = "button";
        chip.className = "cc-event " + (options.cls || "") +
            (state.unsaved ? " cc-event--draft" : "");
        chip.textContent = options.label;
        chip.addEventListener("click", function (event) {
            event.stopPropagation();
            options.onOpen();
        });
        return chip;
    }

    function occurrenceChipLabel(occurrence) {
        var text = compactTime(occurrence.start) + "–" + compactTime(occurrence.end) + " · weekly";
        if (!occurrence.is_active) text = "Inactive · " + text;
        return text;
    }

    function oneDayChipLabel(oneDay) {
        var text = compactTime(oneDay.start) + "–" + compactTime(oneDay.end) + " · one day";
        if (!oneDay.is_active) text = "Inactive · " + text;
        return text;
    }

    function leaveChipLabel(leave) {
        return leave.reason ? "Leave: " + leave.reason : "On leave";
    }

    function leaveCovers(leave, day) {
        var start = dateFromIso(leave.start_date);
        var end = dateFromIso(leave.end_date);
        if (!start || !end) return false;
        return day >= start && day <= end;
    }
    function isDoctorOnLeave(day) {
    return state.leaves.some(function (leave) {
        return leaveCovers(leave, day);
    });
}

    /* ----- Month view ------------------------------------------------- */
    function renderMonth() {
        var range = visibleRange();
        var today = startOfToday();

        var container = document.createElement("div");
        container.className = "cc-month";

        var head = document.createElement("div");
        head.className = "cc-month__head";
        WEEKDAY_LABELS.forEach(function (label) {
            var d = document.createElement("div");
            d.textContent = label.slice(0, 3);
            head.appendChild(d);
        });
        container.appendChild(head);

        var day = new Date(range.start);
        while (day.getTime() <= range.end.getTime()) {
            var row = document.createElement("div");
            row.className = "cc-month__row";
            for (var i = 0; i < 7; i = i + 1) {
                row.appendChild(monthCell(day, today));
                day = addDays(day, 1);
            }
            container.appendChild(row);
        }
        els.board.replaceChildren(container);
    }

    function monthCell(day, today) {
        var cell = document.createElement("div");
        cell.className = "cc-day";
        cell.setAttribute("role", "button");
        cell.setAttribute("tabindex", "0");
        if (day.getMonth() !== state.anchor.getMonth()) cell.className += " cc-day--other";
        if (isoDate(day) === isoDate(today)) cell.className += " cc-day--today";
        cell.setAttribute(
            "aria-label",
            isoDate(day) + ". Press to add availability or leave for this date."
        );

        var num = document.createElement("span");
        num.className = "cc-day__num";
        num.textContent = String(day.getDate());
        cell.appendChild(num);

        var box = document.createElement("div");
        box.className = "cc-day__events";

        state.leaves.forEach(function (leave) {
            if (!leaveCovers(leave, day)) return;
            box.appendChild(makeEventButton({
                cls: "cc-event--leave",
                label: leaveChipLabel(leave),
                onOpen: function () { openDetails("leave", leave.id); },
            }));
        });

        (state.occurrences[isoDate(day)] || []).forEach(function (occurrence) {
            box.appendChild(makeEventButton({
                cls: occurrence.is_active ? "cc-event--availability" : "cc-event--inactive",
                label: occurrenceChipLabel(occurrence),
                onOpen: function () { openDetails("availability", occurrence.rule_id); },
            }));
        });

        // Render one-day availability entries
        (state.oneDayOccurrences[isoDate(day)] || []).forEach(function (oneDay) {
            box.appendChild(makeEventButton({
                cls: oneDay.is_active ? "cc-event--one-day" : "cc-event--inactive",
                label: oneDayChipLabel(oneDay),
                onOpen: function () { openDetails("one_day", oneDay.id); },
            }));
        });

        cell.appendChild(box);
        cell.addEventListener("click", function (event) {
            if (event.target.closest(".cc-event")) return;
            openMenu(new Date(day), null, null);
        });
        cell.addEventListener("keydown", function (event) {
            if (event.key === "Enter" || event.key === " ") {
                event.preventDefault();
                openMenu(new Date(day), null, null);
            }
        });
        return cell;
    }

    /* ----- Week / Day time grid --------------------------------------- */
    function renderTimeGrid() {
        var range = visibleRange();
        var dayCount = state.view === "day" ? 1 : 7;
        var today = startOfToday();

        var grid = document.createElement("div");
        grid.className = "cc-timegrid";
        grid.style.setProperty("--cc-cols", String(dayCount));

        grid.appendChild(timeGridHead(range, dayCount, today));
        grid.appendChild(allDayRow(range, dayCount, today));

        for (var hour = HOUR_START; hour < HOUR_END; hour = hour + 1) {
            grid.appendChild(hourRow(hour, range, dayCount, today));
        }
        els.board.replaceChildren(grid);
    }

    function timeGridHead(range, dayCount, today) {
        var head = document.createElement("div");
        head.className = "cc-timegrid__row cc-timegrid__head";
        head.appendChild(document.createElement("div"));
        for (var i = 0; i < dayCount; i = i + 1) {
            var day = addDays(range.start, i);
            var cell = document.createElement("div");
            var text = WEEKDAY_LABELS[weekdayIndex(day)].slice(0, 3) + " " + day.getDate();
            if (isoDate(day) === isoDate(today)) text += " · today";
            cell.textContent = text;
            head.appendChild(cell);
        }
        return head;
    }

    function allDayRow(range, dayCount, today) {
        var row = document.createElement("div");
        row.className = "cc-timegrid__row cc-allday";
        var label = document.createElement("div");
        label.className = "cc-allday__label";
        label.textContent = "All-day";
        row.appendChild(label);
        for (var i = 0; i < dayCount; i = i + 1) {
            (function (i) {
                var day = addDays(range.start, i);
                var cell = document.createElement("div");
                cell.className = "cc-allday__cell" +
                    (isoDate(day) === isoDate(today) ? " cc-allday__cell--today" : "");
                state.leaves.forEach(function (leave) {
                    if (!leaveCovers(leave, day)) return;
                    cell.appendChild(makeEventButton({
                        cls: "cc-event--leave",
                        label: leaveChipLabel(leave),
                        onOpen: function () { openDetails("leave", leave.id); },
                    }));
                });
                row.appendChild(cell);
            })(i);
        }
        return row;
    }

    function hourRow(hour, range, dayCount, today) {
        var row = document.createElement("div");
        row.className = "cc-timegrid__row";

        var time = document.createElement("div");
        time.className = "cc-timegrid__time";
        time.textContent = String(hour).padStart(2, "0") + ":00";
        row.appendChild(time);

        for (var index = 0; index < dayCount; index = index + 1) {
            row.appendChild(hourCell(hour, addDays(range.start, index), today));
        }
        return row;
    }

    function hourCell(hour, day, today) {
    var cell = document.createElement("div");

    cell.className =
        "cc-cell" +
        (isoDate(day) === isoDate(today) ? " cc-cell--today" : "");

    cell.setAttribute("role", "button");
    cell.setAttribute("tabindex", "0");

    cell.setAttribute(
        "aria-label",
        isoDate(day) +
        " starting " +
        minutesToInput(hour * 60) +
        ". Press to add availability or leave."
    );

    // Do not display recurring availability on a doctor's leave dates.
    if (!isDoctorOnLeave(day)) {
        (state.occurrences[isoDate(day)] || []).forEach(function (occurrence) {
            if (!startsInHour(occurrence.start, hour)) {
                return;
            }

            var label =
                prettyTime(occurrence.start) +
                "–" +
                compactTime(occurrence.end) +
                " · weekly";

            if (!occurrence.is_active) {
                label = "Inactive · " + label;
            }

            cell.appendChild(
                makeEventButton({
                    cls: occurrence.is_active
                        ? "cc-event--availability"
                        : "cc-event--inactive",
                    label: label,
                    onOpen: function () {
                        openDetails("availability", occurrence.rule_id);
                    },
                })
            );
        });

        // Render one-day availability entries
        (state.oneDayOccurrences[isoDate(day)] || []).forEach(function (oneDay) {
            if (!startsInHour(oneDay.start, hour)) {
                return;
            }

            var oneDayLabel =
                prettyTime(oneDay.start) +
                "–" +
                compactTime(oneDay.end) +
                " · one day";

            if (!oneDay.is_active) {
                oneDayLabel = "Inactive · " + oneDayLabel;
            }

            cell.appendChild(
                makeEventButton({
                    cls: oneDay.is_active
                        ? "cc-event--one-day"
                        : "cc-event--inactive",
                    label: oneDayLabel,
                    onOpen: function () {
                        openDetails("one_day", oneDay.id);
                    },
                })
            );
        });
    }

    // Keep the cell interactive even when the doctor is on leave.
    cell.addEventListener("click", function (event) {
        if (event.target.closest(".cc-event")) {
            return;
        }

        openMenu(
            new Date(day),
            hour * 60,
            (hour + 1) * 60
        );
    });

    cell.addEventListener("keydown", function (event) {
        if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();

            openMenu(
                new Date(day),
                hour * 60,
                (hour + 1) * 60
            );
        }
    });

    // IMPORTANT: Always return the cell, including on leave dates.
    return cell;
}

    function startsInHour(startValue, hour) {
        var minutes = parseTimeMinutes(startValue);
        if (minutes === null) return false;
        return minutes >= hour * 60 && minutes < (hour + 1) * 60;
    }

    // ------------------------------------------------------------------
    // Actions: menu, forms, details, confirm
    // ------------------------------------------------------------------
    function openMenu(day, startMinutes, endMinutes) {
        state.context = {
            date: day,
            start: startMinutes === null ? 9 * 60 : startMinutes,
            end: endMinutes === null ? 13 * 60 : endMinutes,
        };
        els.menuDateLabel.textContent =
            isoDate(day) + " (" + WEEKDAY_LABELS[weekdayIndex(day)] + ")";
        els.menu.showModal();
    }

    function closeMenu() { els.menu.close(); }

    // -- Availability form --------------------------------------------
    function availabilityInputs() {
        return {
            weekday: els.weekdaySelect,
            start: document.getElementById("cc-availability-start"),
            end: document.getElementById("cc-availability-end"),
            slot: document.getElementById("cc-availability-slot"),
            active: document.getElementById("cc-availability-active"),
            date: document.getElementById("cc-availability-date"),
        };
    }

    function populateWeekdayOptions(selected) {
        els.weekdaySelect.replaceChildren();
        WEEKDAY_LABELS.forEach(function (label, index) {
            var option = document.createElement("option");
            option.value = String(index);
            option.textContent = label;
            if (index === Number(selected)) option.selected = true;
            els.weekdaySelect.appendChild(option);
        });
    }

    function updateRepeatNote() {
        var label = WEEKDAY_LABELS[Number(els.weekdaySelect.value)];
        els.repeatLabel.textContent =
            "Repeats weekly on " + label + " — this rule is NOT a single-date event.";
    }

   function openAvailabilityForm(context, rule) {
    // Prevent creating a new weekly availability rule from a leave date.
    // Existing rules can still be edited.
    if (
        !rule &&
        context &&
        context.date &&
        state.scheduleType === "weekly" &&
        isDoctorOnLeave(context.date)
    ) {
        closeMenu();

        status(
            "This date is marked as doctor leave. " +
            "Choose another date to add weekly availability.",
            "error"
        );

        return;
    }

    var inputs = availabilityInputs();
    var dateInput = document.getElementById("cc-availability-date");
    var weekdayLabel = document.querySelector("[data-label-weekday]");
    var dateLabel = document.querySelector("[data-label-date]");
    var weeklyNote = document.querySelector("[data-availability-note-weekly]");
    var oneDayNote = document.querySelector("[data-availability-note-oneday]");

    // Determine if this is weekly or one-day mode
    var isOneDay = (state.scheduleType === "oneDay");

    if (isOneDay) {
        // One-day mode: show date, hide weekday
        els.availabilityDialog.querySelector("h3").textContent = "One-day availability";
        dateInput.hidden = false;
        dateLabel.hidden = false;
        dateInput.value = context && context.date ? isoDate(context.date) : isoDate(startOfToday());
        els.weekdaySelect.hidden = true;
        weekdayLabel.hidden = true;
        els.repeatLabel.hidden = true;
        weeklyNote.hidden = true;
        oneDayNote.hidden = false;
    } else {
        // Weekly mode: show weekday, hide date
        els.availabilityDialog.querySelector("h3").textContent = "Weekly availability";
        dateInput.hidden = true;
        dateLabel.hidden = true;
        els.weekdaySelect.hidden = false;
        weekdayLabel.hidden = false;
        els.repeatLabel.hidden = false;
        weeklyNote.hidden = false;
        oneDayNote.hidden = true;

        populateWeekdayOptions(
            rule
                ? rule.weekday
                : context && context.date
                ? weekdayIndex(context.date)
                : weekdayIndex(startOfToday())
        );
        updateRepeatNote();
    }

    inputs.start.value = rule
        ? rule.start
        : context && context.start !== null
        ? minutesToInput(context.start)
        : "09:00";
    inputs.end.value = rule
        ? rule.end
        : context && context.end !== null
        ? minutesToInput(context.end)
        : "13:00";
    inputs.slot.value = rule && rule.slot_length_minutes !== null && rule.slot_length_minutes !== undefined
        ? String(rule.slot_length_minutes)
        : "";
    inputs.active.checked = rule ? rule.is_active : true;

    state.editing.availability = rule ? rule.id : null;
    clearErrors(els.availabilityDialog);
    closeMenu();
    els.availabilityDialog.showModal();
}
    var inputs = availabilityInputs();

    // -- Leave form ----------------------------------------------------
    function leaveInputs() {
        return {
            start: document.getElementById("cc-leave-start"),
            end: document.getElementById("cc-leave-end"),
            reason: document.getElementById("cc-leave-reason"),
        };
    }

    function openLeaveForm(leave) {
        var inputs = leaveInputs();
        inputs.start.value = leave ? leave.start_date : isoDate(state.context.date);
        inputs.end.value = leave ? leave.end_date : isoDate(state.context.date);
        inputs.reason.value = leave ? leave.reason : "";
        state.editing.leave = leave ? leave.id : null;
        clearErrors(els.leaveDialog);
        closeMenu();
        els.leaveDialog.showModal();
    }

    // -- Errors --------------------------------------------------------
    function clearErrors(dialog) {
        var errors = dialog.querySelector("[data-errors]");
        errors.hidden = true;
        errors.replaceChildren();
    }

    function showErrors(dialog, payload) {
        var errors = dialog.querySelector("[data-errors]");
        errors.replaceChildren();
        Object.keys(payload.errors || {}).forEach(function (field) {
            var message = payload.errors[field];
            var list = Array.isArray(message)
                ? message
                : (message && typeof message === "object" ? [message.message] : [String(message)]);
            list.forEach(function (text) {
                var li = document.createElement("li");
                li.textContent = text;
                errors.appendChild(li);
            });
        });
        errors.hidden = false;
    }

    function setDialogBusy(dialog, busy) {
        dialog.querySelectorAll("button").forEach(function (button) {
            button.disabled = busy;
        });
    }

    // -- Submissions ---------------------------------------------------
    function submitAvailability() {
        var inputs = availabilityInputs();
        var isOneDay = (state.scheduleType === "oneDay");
        
        if (!inputs.start.value || !inputs.end.value) {
            showErrors(els.availabilityDialog, {
                errors: { "__all__": ["Start and end time are required."] },
            });
            return;
        }
        
        if (isOneDay && !inputs.date.value) {
            showErrors(els.availabilityDialog, {
                errors: { "__all__": ["Date is required for one-day availability."] },
            });
            return;
        }
        
        if (state.unsaved) {
            // Draft mode handling
            var draftId = state.editing.availability;
            var draftKind = isOneDay ? "one_day" : "availability";
            
            if (draftId !== null) {
                var current = findDraft(draftKind, draftId);
                els.availabilityDialog.close();
                hideDetails();
                state.editing.availability = null;
                
                if (current) {
                    if (isOneDay) {
                        current.date = inputs.date.value;
                        current.start = inputs.start.value;
                        current.end = inputs.end.value;
                        current.slot_length_minutes = inputs.slot.value
                            ? Number(inputs.slot.value) : null;
                        current.is_active = inputs.active.checked;
                    } else {
                        current.weekday = Number(inputs.weekday.value);
                        current.weekday_label = WEEKDAY_LABELS[current.weekday];
                        current.start = inputs.start.value;
                        current.end = inputs.end.value;
                        current.slot_length_minutes = inputs.slot.value
                            ? Number(inputs.slot.value) : null;
                        current.is_active = inputs.active.checked;
                    }
                    status("Draft updated. It is saved with the doctor form.", "ok");
                } else {
                    status("That draft is no longer listed.", "error");
                }
                loadEvents();
                return;
            }
            
            // Create new draft
            if (isOneDay) {
                state.draftOneDayRules.push(draftOneDayEntry(
                    inputs.date.value,
                    inputs.start.value,
                    inputs.end.value,
                    inputs.slot.value ? Number(inputs.slot.value) : null,
                    inputs.active.checked,
                    draftIdCounter()
                ));
            } else {
                state.draftRules.push(draftRuleEntry(
                    Number(inputs.weekday.value),
                    inputs.start.value,
                    inputs.end.value,
                    inputs.slot.value ? Number(inputs.slot.value) : null,
                    inputs.active.checked,
                    draftIdCounter()
                ));
            }
            
            els.availabilityDialog.close();
            state.editing.availability = null;
            status("Draft added — it is saved together with the new doctor.", "ok");
            loadEvents();
            return;
        }
        
        // Server submission
        var editingId = state.editing.availability;
        var url;
        var payload;
        
        if (isOneDay) {
            url = editingId ? scheduleUrl("oneDay", "update", editingId) : scopedUrl(createUrls.oneDay);
            payload = {
                date: inputs.date.value,
                start_time: inputs.start.value,
                end_time: inputs.end.value,
                slot_length_minutes: inputs.slot.value || "",
            };
        } else {
            url = editingId ? scheduleUrl("availability", "update", editingId) : scopedUrl(createUrls.availability);
            payload = {
                weekday: inputs.weekday.value,
                start_time: inputs.start.value,
                end_time: inputs.end.value,
                slot_length_minutes: inputs.slot.value || "",
            };
        }
        
        if (inputs.active.checked) payload.is_active = "on";
        
        setDialogBusy(els.availabilityDialog, true);
        postForm(url, payload).then(function (result) {
            if (!result) return;
            if (result.ok) {
                els.availabilityDialog.close();
                hideDetails();
                state.editing.availability = null;
                
                if (isOneDay && result.payload && result.payload.availability) {
                    // One-day availability doesn't mirror to inline (not part of original design)
                    status(
                        editingId
                            ? "One-day availability updated."
                            : "One-day availability added for " + payload.date + ".",
                        "ok"
                    );
                } else if (result.payload && result.payload.rule) {
                    mirrorRuleIntoInline(result.payload.rule);
                    status(
                        editingId
                            ? "Availability updated (still repeating weekly)."
                            : "Availability added — it repeats weekly.",
                        "ok"
                    );
                }
                
                loadEvents();
            } else {
                showErrors(els.availabilityDialog, result.payload);
            }
        }).finally(function () { setDialogBusy(els.availabilityDialog, false); });
    }

    function submitLeave() {
        var inputs = leaveInputs();
        var editingId = state.editing.leave;
        if (state.unsaved) {
            if (editingId !== null) {
                var current = findDraft("leave", editingId);
                els.leaveDialog.close();
                hideDetails();
                state.editing.leave = null;
                if (current) {
                    current.start_date = inputs.start.value;
                    current.end_date = inputs.end.value;
                    current.reason = inputs.reason.value;
                    status("Draft updated. It is saved with the doctor form.", "ok");
                } else {
                    status("That draft is no longer listed.", "error");
                }
                loadEvents();
                return;
            }
            state.draftLeaves.push(draftLeaveEntry(
                inputs.start.value,
                inputs.end.value,
                inputs.reason.value,
                draftIdCounter()
            ));
            els.leaveDialog.close();
            state.editing.leave = null;
            status("Draft added — it is saved together with the new doctor.", "ok");
            loadEvents();
            return;
        }
        var url = editingId ? scheduleUrl("leave", "update", editingId) : scopedUrl(createUrls.leave);
        setDialogBusy(els.leaveDialog, true);
        postForm(url, {
            start_date: inputs.start.value,
            end_date: inputs.end.value,
            reason: inputs.reason.value,
        }).then(function (result) {
            if (!result) return;
            if (result.ok) {
                els.leaveDialog.close();
                hideDetails();
                state.editing.leave = null;
                if (result.payload && result.payload.leave) {
                    mirrorLeaveIntoInline(result.payload.leave);
                }
                status(editingId ? "Leave updated." : "Leave added.", "ok");
                loadEvents();
            } else {
                showErrors(els.leaveDialog, result.payload);
            }
        }).finally(function () { setDialogBusy(els.leaveDialog, false); });
    }

    // -- Details / toggle / delete --------------------------------------
    function findRule(id) {
        return state.rules.find(function (rule) { return String(rule.id) === String(id); });
    }

    function findLeave(id) {
        return state.leaves.find(function (leave) { return String(leave.id) === String(id); });
    }

    function findOneDay(id) {
        return state.oneDayAvailabilities.find(function (oneDay) { return String(oneDay.id) === String(id); });
    }

    function openDetails(kind, id) {
        var rule = kind === "availability" ? findRule(id) : null;
        var leave = kind === "leave" ? findLeave(id) : null;
        var oneDay = kind === "one_day" ? findOneDay(id) : null;
        
        if (kind === "availability" && !rule) return;
        if (kind === "leave" && !leave) return;
        if (kind === "one_day" && !oneDay) return;
        
        state.selected = { kind: kind, id: id };

        if (rule) {
            els.detailsTitle.textContent = "Weekly availability";
            fillDetails([
                ["Day", rule.weekday_label],
                ["Time", prettyTime(rule.start) + " – " + compactTime(rule.end)],
                [
                    "Slot duration",
                    rule.slot_length_minutes === null || rule.slot_length_minutes === undefined
                        ? (rule.effective_slot_length_minutes
                            ? "Doctor default (" + rule.effective_slot_length_minutes + " min)"
                            : "Doctor default")
                        : rule.slot_length_minutes + " min",
                ],
                ["Repeats", "Weekly — appears on every " + rule.weekday_label],
                ["State", rule.is_active ? "Active (bookable)" : "Inactive (not bookable)"],
            ]);
            els.detailsNote.hidden = true;
            var toggle = els.detailsDialog.querySelector("[data-details='toggle']");
            toggle.hidden = false;
            toggle.dataset.actionValue = rule.is_active ? "off" : "on";
            toggle.textContent = rule.is_active ? "Deactivate" : "Activate";
        } else if (oneDay) {
            els.detailsTitle.textContent = "One-day availability";
            fillDetails([
                ["Date", oneDay.date],
                ["Time", prettyTime(oneDay.start) + " – " + compactTime(oneDay.end)],
                [
                    "Slot duration",
                    oneDay.slot_length_minutes === null || oneDay.slot_length_minutes === undefined
                        ? (oneDay.effective_slot_length_minutes
                            ? "Doctor default (" + oneDay.effective_slot_length_minutes + " min)"
                            : "Doctor default")
                        : oneDay.slot_length_minutes + " min",
                ],
                ["Scope", "This specific date only (does not repeat)"],
                ["State", oneDay.is_active ? "Active (bookable)" : "Inactive (not bookable)"],
            ]);
            els.detailsNote.hidden = true;
            var oneDayToggle = els.detailsDialog.querySelector("[data-details='toggle']");
            oneDayToggle.hidden = false;
            oneDayToggle.dataset.actionValue = oneDay.is_active ? "off" : "on";
            oneDayToggle.textContent = oneDay.is_active ? "Deactivate" : "Activate";
        } else {
            var start = dateFromIso(leave.start_date);
            var end = dateFromIso(leave.end_date);
            var dayCount = Math.round((end.getTime() - start.getTime()) / 86400000) + 1;
            els.detailsTitle.textContent = "Doctor leave";
            fillDetails([
                ["Start date", isoDate(start)],
                ["End date", isoDate(end)],
                ["Days covered", String(dayCount) + (dayCount === 1 ? " day" : " days")],
                ["Reason", leave.reason || "—"],
                ["Scope", "These specific dates only"],
            ]);
            els.detailsNote.hidden = false;
            els.detailsNote.textContent = dayCount > 1
                ? "This leave spans multiple days; booking is blocked throughout."
                : "Single-day leave.";
            els.detailsDialog.querySelector("[data-details='toggle']").hidden = true;
        }
        els.detailsDialog.dataset.kind = kind;
        els.detailsDialog.dataset.editingId = String(id);
        setDialogBusy(els.detailsDialog, false);
        els.detailsDialog.showModal();
    }

    function fillDetails(rows) {
        els.detailsList.replaceChildren();
        rows.forEach(function (pair) {
            var item = document.createElement("div");
            var dt = document.createElement("dt");
            dt.textContent = pair[0];
            var dd = document.createElement("dd");
            dd.textContent = pair[1];
            item.appendChild(dt);
            item.appendChild(dd);
            els.detailsList.appendChild(item);
        });
    }

    function hideDetails() {
        if (els.detailsDialog.open) els.detailsDialog.close();
    }

    function editSelected() {
        var target = state.selected;
        if (!target) return;
        hideDetails();
        if (target.kind === "availability") {
            var rule = findRule(target.id);
            if (rule) {
                state.scheduleType = "weekly";
                openAvailabilityForm({ date: startOfToday() }, rule);
            }
            else status("That availability rule is no longer listed.", "error");
        } else if (target.kind === "one_day") {
            var oneDay = findOneDay(target.id);
            if (oneDay) {
                state.scheduleType = "oneDay";
                openAvailabilityForm({ date: dateFromIso(oneDay.date) }, oneDay);
            }
            else status("That one-day availability is no longer listed.", "error");
        } else {
            var leave = findLeave(target.id);
            if (leave) openLeaveForm(leave);
            else status("That leave is no longer listed.", "error");
        }
    }

    function toggleSelected() {
        var target = state.selected;
        var rule = target && target.kind === "availability" ? findRule(target.id) : null;
        if (!rule) { hideDetails(); return; }
        var activate = !rule.is_active;
        if (state.unsaved && Number(rule.id) < 0) {
            rule.is_active = activate;
            hideDetails();
            status(
                activate
                    ? "Draft activated (will be bookable once saved)."
                    : "Draft deactivated (won't be bookable).",
                "ok"
            );
            loadEvents();
            return;
        }
        setDialogBusy(els.detailsDialog, true);
        var payload = {
            weekday: String(Number(rule.weekday)),
            start_time: rule.start,
            end_time: rule.end,
            slot_length_minutes:
                rule.slot_length_minutes === null || rule.slot_length_minutes === undefined
                    ? "" : String(rule.slot_length_minutes),
        };
        if (activate) payload.is_active = "on";
        postForm(scheduleUrl("availability", "update", rule.id), payload).then(function (result) {
            if (!result) return;
            if (result.ok) {
                hideDetails();
                if (result.payload && result.payload.rule) {
                    mirrorRuleIntoInline(result.payload.rule);
                }
                status(
                    activate
                        ? "Availability activated (bookable again)."
                        : "Availability deactivated (not bookable).",
                    "ok"
                );
                loadEvents();
            } else {
                showErrors(els.detailsDialog, result.payload);
                if (!els.detailsDialog.open) els.detailsDialog.showModal();
            }
        }).finally(function () { setDialogBusy(els.detailsDialog, false); });
    }

    function deleteSelected() {
        var target = state.selected;
        if (!target) return;
        var rule = target.kind === "availability" ? findRule(target.id) : null;
        var leave = target.kind === "leave" ? findLeave(target.id) : null;
        if (!rule && !leave) { hideDetails(); return; }
        var question;
        if (rule) {
            question = "Delete the recurring availability rule on " + rule.weekday_label +
                " " + prettyTime(rule.start) + "–" + compactTime(rule.end) + "?";
        } else {
            question = "Delete the leave from " + leave.start_date + " to " + leave.end_date + "?";
        }
        if (state.unsaved && Number(target.id) < 0) {
            question = "Remove this unsaved draft entry from the doctor form?";
        }
        els.confirmDialog.dataset.kind = target.kind;
        els.confirmDialog.dataset.editingId = String(target.id);
        els.confirmText.textContent = question + " This cannot be undone.";
        hideDetails();
        els.confirmDialog.showModal();
    }

    function confirmDelete() {
        var kind = els.confirmDialog.dataset.kind;
        var id = els.confirmDialog.dataset.editingId;
        if (state.unsaved && Number(id) < 0) {
            removeDraft(kind, id);
            els.confirmDialog.close();
            state.selected = null;
            status("Draft entry removed.", "ok");
            loadEvents();
            return;
        }
        var url = scheduleUrl(kind, "delete", id);
        els.confirmDialog.close();
        postForm(url, {}).then(function (result) {
            if (!result) return;
            if (result.ok) {
                status("Entry deleted. Existing appointments are untouched.", "ok");
                state.selected = null;
                mirrorDeleteIntoInline(kind, id);
                loadEvents();
            } else {
                status("Could not delete: " + errorText(result.payload), "error");
            }
        });
    }

    // ------------------------------------------------------------------
    // Inline formset plumbing
    //
    // Draft mode (add page): inline rows are imported into the calendar as
    // drafts at init and re-imported at submit; all rows are DELETE-marked
    // and one fresh row per draft is appended right before the doctor form
    // POSTs, so the server receives exactly one row per draft chip.
    // Change pages: every calendar write is mirrored into the matching
    // inline row (update values / check DELETE / append), so a later
    // main-form save can never post stale values over the calendar change.
    // ------------------------------------------------------------------
    var INLINE_PREFIX_AVAILABILITY = "availability_rules";
    var INLINE_PREFIX_LEAVE = "leaves";

    function inlineFormsetTotal(prefix) {
        return document.getElementById("id_" + prefix + "-TOTAL_FORMS");
    }

    function inlineRowByIndex(prefix, index, probeSuffix) {
        var probe = document.querySelector(
            '[name="' + prefix + "-" + index + "-" + probeSuffix + '"]'
        );
        return probe ? probe.closest("tr") : null;
    }

    function inlineField(prefix, index, suffix) {
        return document.querySelector(
            '[name="' + prefix + "-" + index + "-" + suffix + '"]'
        );
    }

    function readInlineAvailability(index) {
        var row = inlineRowByIndex(INLINE_PREFIX_AVAILABILITY, index, "start_time");
        if (!row) return null;
        var weekday = function (suffix) {
            var field = inlineField(INLINE_PREFIX_AVAILABILITY, index, suffix);
            return field ? field.value : "";
        };
        var start = weekday("start_time");
        var end = weekday("end_time");
        var weekdayValue = weekday("weekday");
        if (!weekdayValue && !start && !end) return null;
        var slot = weekday("slot_length_minutes");
        var activeField = inlineField(INLINE_PREFIX_AVAILABILITY, index, "is_active");
        return {
            id: weekday("id"),
            weekday: weekdayValue === "" ? null : Number(weekdayValue),
            start_time: start,
            end_time: end,
            slot_length_minutes: slot === "" ? null : Number(slot),
            is_active: activeField ? activeField.checked : true,
        };
    }

    function readInlineLeave(index) {
        var row = inlineRowByIndex(INLINE_PREFIX_LEAVE, index, "start_date");
        if (!row) return null;
        var value = function (suffix) {
            var field = inlineField(INLINE_PREFIX_LEAVE, index, suffix);
            return field ? field.value : "";
        };
        var startDate = value("start_date");
        var endDate = value("end_date");
        if (!startDate && !endDate) return null;
        return {
            id: value("id"),
            start_date: startDate,
            end_date: endDate,
            reason: value("reason"),
        };
    }

    function importInlineDrafts() {
        var availabilityTotal = inlineFormsetTotal(INLINE_PREFIX_AVAILABILITY);
        if (availabilityTotal) {
            var seenRules = {};
            for (var i = 0; i < Number(availabilityTotal.value); i += 1) {
                var data = readInlineAvailability(i);
                if (!data) continue;
                var key = [data.weekday, data.start_time, data.end_time,
                    data.slot_length_minutes, data.is_active ? 1 : 0].join("|");
                if (seenRules[key]) continue;
                seenRules[key] = true;
                state.draftRules.push(draftRuleEntry(
                    data.weekday === null ? 0 : data.weekday,
                    data.start_time,
                    data.end_time,
                    data.slot_length_minutes,
                    data.is_active,
                    draftIdCounter()
                ));
            }
            adoptInlineRows(INLINE_PREFIX_AVAILABILITY);
        }
        var leaveTotal = inlineFormsetTotal(INLINE_PREFIX_LEAVE);
        if (leaveTotal) {
            var seenLeaves = {};
            for (var j = 0; j < Number(leaveTotal.value); j += 1) {
                var leaveData = readInlineLeave(j);
                if (!leaveData) continue;
                var leaveKey = [leaveData.start_date, leaveData.end_date,
                    leaveData.reason].join("|");
                if (seenLeaves[leaveKey]) continue;
                seenLeaves[leaveKey] = true;
                state.draftLeaves.push(draftLeaveEntry(
                    leaveData.start_date,
                    leaveData.end_date,
                    leaveData.reason,
                    draftIdCounter()
                ));
            }
            adoptInlineRows(INLINE_PREFIX_LEAVE);
        }
    }

    function adoptInlineRows(prefix) {
        // On add pages every row is unbound (DELETE checkboxes only render
        // for bound rows), so adoption = removing the row elements entirely;
        // the submitted content is rebuilt one fresh row per draft instead.
        var replacement = new RegExp("^" + prefix + "-\\d+$");
        document.querySelectorAll(
            '.js-inline-admin-formset tr[id'
        ).forEach(function (row) {
            if (replacement.test(row.id)) row.remove();
        });
    }

    function appendInlineRow(prefix, newIndex, probeSuffix, fields) {
        // Prefer Django's own "__prefix__" empty-form template row (always
        // rendered, contains placeholder names) over cloning a rendered row.
        var sampleRow =
            document.querySelector('[id="' + prefix + '-empty"]') ||
            document.querySelector(".empty-form." + prefix + "-empty") ||
            document.querySelector('td [name^="' + prefix + '-__prefix__-"]');
        sampleRow = sampleRow ? sampleRow.closest("tr") : null;
        if (!sampleRow) {
            // Fallback: clone an existing rendered row.
            sampleRow = inlineRowByIndex(prefix, Math.max(0, newIndex - 1), probeSuffix) ||
                inlineRowByIndex(prefix, 0, probeSuffix);
            if (!sampleRow || !sampleRow.closest) return false;
            var clone = sampleRow.cloneNode(true);
            var sampleIndex = null;
            clone.querySelectorAll("[name], [id]").forEach(function (field) {
                ["name", "id", "for", "aria-labelledby", "aria-describedby"].forEach(function (attr) {
                    var attrValue = field.getAttribute(attr);
                    if (!attrValue) return;
                    var match = new RegExp("^(" + prefix + ")-(\\d+)-(.*)$").exec(attrValue);
                    if (match) sampleIndex = sampleIndex || match[2];
                    if (sampleIndex !== null) {
                        field.setAttribute(
                            attr,
                            attrValue.replace(
                                prefix + "-" + sampleIndex + "-",
                                prefix + "-" + newIndex + "-"
                            )
                        );
                    }
                });
            });
            Object.keys(fields).forEach(function (suffix) {
                var field = clone.querySelector(
                    '[name="' + prefix + "-" + newIndex + "-" + suffix + '"]'
                );
                if (!field) return;
                if (field.type === "checkbox") field.checked = !!fields[suffix];
                else field.value = fields[suffix] === null || fields[suffix] === undefined
                    ? "" : fields[suffix];
            });
            var idField = clone.querySelector('[name="' + prefix + "-" + newIndex + '-id"]');
            if (idField) idField.value = "";
            var deleteField = clone.querySelector(
                '[name="' + prefix + "-" + newIndex + '-DELETE"]'
            );
            if (deleteField) deleteField.checked = false;
            sampleRow.parentNode.insertBefore(clone, sampleRow.nextSibling);
            return true;
        }

        var fresh = sampleRow.cloneNode(true);
        fresh.id = prefix + "-" + newIndex;
        fresh.classList.remove("empty-form");
        fresh.querySelectorAll("[name], [id]").forEach(function (field) {
            ["name", "id", "for", "aria-labelledby", "aria-describedby"].forEach(function (attr) {
                var attrValue = field.getAttribute(attr);
                if (attrValue && attrValue.indexOf("__prefix__") !== -1) {
                    field.setAttribute(
                        attr, attrValue.replace("__prefix__", String(newIndex))
                    );
                }
            });
        });
        Object.keys(fields).forEach(function (suffix) {
            var field = fresh.querySelector(
                '[name="' + prefix + "-" + newIndex + "-" + suffix + '"]'
            );
            if (!field) return;
            if (field.type === "checkbox") field.checked = !!fields[suffix];
            else field.value = fields[suffix] === null || fields[suffix] === undefined
                ? "" : fields[suffix];
        });
        var freshId = fresh.querySelector('[name="' + prefix + "-" + newIndex + '-id"]');
        if (freshId) freshId.value = "";
        var freshDelete = fresh.querySelector(
            '[name="' + prefix + "-" + newIndex + '-DELETE"]'
        );
        if (freshDelete) freshDelete.checked = false;
        sampleRow.parentNode.insertBefore(fresh, sampleRow);
        return true;
    }

    function appendAvailabilityRow(rule, newIndex) {
        return appendInlineRow(INLINE_PREFIX_AVAILABILITY, newIndex, "start_time", {
            weekday: String(rule.weekday),
            start_time: rule.start,
            end_time: rule.end,
            slot_length_minutes:
                rule.slot_length_minutes === null || rule.slot_length_minutes === undefined
                    ? "" : String(rule.slot_length_minutes),
            is_active: !!rule.is_active,
        });
    }

    function appendLeaveRow(leave, newIndex) {
        return appendInlineRow(INLINE_PREFIX_LEAVE, newIndex, "start_date", {
            start_date: leave.start_date,
            end_date: leave.end_date,
            reason: leave.reason || "",
        });
    }

    function syncDraftsToInlines() {
        // Draft rows replace the DOM rows entirely: adopt (remove) all
        // current unbound rows, then append exactly one fresh row per draft.
        // Management forms are renumbered to match, so the server receives
        // one row per draft chip and nothing else.
        var availabilityTotal = inlineFormsetTotal(INLINE_PREFIX_AVAILABILITY);
        if (availabilityTotal) {
            adoptInlineRows(INLINE_PREFIX_AVAILABILITY);
            var availabilityIndex = 0;
            state.draftRules.forEach(function (rule) {
                if (appendAvailabilityRow(rule, availabilityIndex)) {
                    availabilityIndex += 1;
                }
            });
            availabilityTotal.value = String(availabilityIndex);
        }
        var leaveTotal = inlineFormsetTotal(INLINE_PREFIX_LEAVE);
        if (leaveTotal) {
            adoptInlineRows(INLINE_PREFIX_LEAVE);
            var leaveIndex = 0;
            state.draftLeaves.forEach(function (leave) {
                if (appendLeaveRow(leave, leaveIndex)) {
                    leaveIndex += 1;
                }
            });
            leaveTotal.value = String(leaveIndex);
        }
    }

    // -- Change pages: mirror calendar writes into inline rows ---------
    function findInlineRowById(prefix, recordId) {
        var row = null;
        document.querySelectorAll(
            '[name^="' + prefix + '-"][name$="-id"]'
        ).forEach(function (field) {
            if (row || field.value === "" || field.value !== String(recordId)) return;
            row = field.closest("tr");
        });
        return row;
    }

    function mirrorRuleIntoInline(rule) {
        if (state.unsaved) return;
        var total = inlineFormsetTotal(INLINE_PREFIX_AVAILABILITY);
        if (!total) return; // hub pages have no inline formsets
        var row = findInlineRowById(INLINE_PREFIX_AVAILABILITY, rule.id);
        if (!row) {
            // Rules created through the calendar are already saved; the main
            // form must not recreate them, so there is nothing to mirror.
            return;
        }
        var index = null;
        row.querySelectorAll("[name]").forEach(function (field) {
            var match = new RegExp(
                "^" + INLINE_PREFIX_AVAILABILITY + "-(\\d+)-"
            ).exec(field.name);
            if (match) index = match[1];
        });
        if (index === null) return;
        var updates = {
            "weekday": String(rule.weekday),
            "start_time": rule.start,
            "end_time": rule.end,
            "slot_length_minutes":
                rule.slot_length_minutes === null || rule.slot_length_minutes === undefined
                    ? "" : String(rule.slot_length_minutes),
        };
        Object.keys(updates).forEach(function (suffix) {
            var field = inlineField(INLINE_PREFIX_AVAILABILITY, index, suffix);
            if (field) field.value = updates[suffix];
        });
        var activeField = inlineField(INLINE_PREFIX_AVAILABILITY, index, "is_active");
        if (activeField) activeField.checked = !!rule.is_active;
        var deleteField = inlineField(INLINE_PREFIX_AVAILABILITY, index, "DELETE");
        if (deleteField) deleteField.checked = false;
    }

    function mirrorLeaveIntoInline(leave) {
        if (state.unsaved) return;
        var total = inlineFormsetTotal(INLINE_PREFIX_LEAVE);
        if (!total) return;
        var row = findInlineRowById(INLINE_PREFIX_LEAVE, leave.id);
        if (!row) {
            // Same as availability: calendar-created leaves are already saved.
            return;
        }
        var rowIndex = null;
        row.querySelectorAll("[name]").forEach(function (field) {
            var match = new RegExp("^" + INLINE_PREFIX_LEAVE + "-(\\d+)-").exec(field.name);
            if (match) rowIndex = match[1];
        });
        if (rowIndex === null) return;
        ["start_date", "end_date", "reason"].forEach(function (suffix) {
            var field = inlineField(INLINE_PREFIX_LEAVE, rowIndex, suffix);
            if (field) field.value = leave[suffix] || "";
        });
        var deleteField = inlineField(INLINE_PREFIX_LEAVE, rowIndex, "DELETE");
        if (deleteField) deleteField.checked = false;
    }

    function mirrorDeleteIntoInline(kind, recordId) {
        if (state.unsaved) return;
        var prefix = kind === "availability" ? INLINE_PREFIX_AVAILABILITY : INLINE_PREFIX_LEAVE;
        var total = inlineFormsetTotal(prefix);
        if (!total) return;
        var row = findInlineRowById(prefix, recordId);
        if (!row) return;
        var prefixIndex = null;
        row.querySelectorAll("[name]").forEach(function (field) {
            var match = new RegExp("^" + prefix + "-(\\d+)-").exec(field.name);
            if (match) prefixIndex = match[1];
        });
        if (prefixIndex === null) return;
        var deleteField = inlineField(prefix, prefixIndex, "DELETE");
        if (deleteField) deleteField.checked = true;
    }

    // ------------------------------------------------------------------
    // Wiring
    // ------------------------------------------------------------------
    els.menu.querySelectorAll("[data-menu]").forEach(function (button) {
        button.addEventListener("click", function () {
            var action = button.getAttribute("data-menu");
            if (action === "availability") {
                state.scheduleType = "weekly";
                openAvailabilityForm(
                    state.context || { date: startOfToday(), start: 9 * 60, end: 13 * 60 },
                    null
                );
            } else if (action === "oneDay") {
                state.scheduleType = "oneDay";
                openAvailabilityForm(
                    state.context || { date: startOfToday(), start: 9 * 60, end: 13 * 60 },
                    null
                );
            } else if (action === "leave") {
                openLeaveForm(null);
            } else {
                closeMenu();
            }
        });
    });

    els.weekdaySelect.addEventListener("change", updateRepeatNote);

    els.availabilityDialog.querySelector("[data-cmd='save']")
        .addEventListener("click", submitAvailability);
    els.availabilityDialog.querySelector("[data-cmd='close']")
        .addEventListener("click", function () { els.availabilityDialog.close(); });

    els.leaveDialog.querySelector("[data-cmd='save']")
        .addEventListener("click", submitLeave);
    els.leaveDialog.querySelector("[data-cmd='close']")
        .addEventListener("click", function () { els.leaveDialog.close(); });

    els.detailsDialog.querySelector("[data-details='edit']")
        .addEventListener("click", editSelected);
    els.detailsDialog.querySelector("[data-details='toggle']")
        .addEventListener("click", toggleSelected);
    els.detailsDialog.querySelector("[data-details='delete']")
        .addEventListener("click", deleteSelected);
    els.detailsDialog.querySelector("[data-details='close']")
        .addEventListener("click", hideDetails);

    els.confirmDialog.querySelector("[data-confirm='yes']")
        .addEventListener("click", confirmDelete);
    els.confirmDialog.querySelector("[data-confirm='no']")
        .addEventListener("click", function () { els.confirmDialog.close(); });

    root.querySelectorAll("[data-view]").forEach(function (button) {
        button.addEventListener("click", function () {
            state.view = button.getAttribute("data-view");
            loadEvents();
        });
    });

    root.querySelector("[data-action='prev']").addEventListener("click", function () {
        if (state.view === "month") state.anchor = monthAnchor(state.anchor, -1);
        else if (state.view === "week") state.anchor = addDays(state.anchor, -7);
        else state.anchor = addDays(state.anchor, -1);
        loadEvents();
    });
    root.querySelector("[data-action='next']").addEventListener("click", function () {
        if (state.view === "month") state.anchor = monthAnchor(state.anchor, 1);
        else if (state.view === "week") state.anchor = addDays(state.anchor, 7);
        else state.anchor = addDays(state.anchor, 1);
        loadEvents();
    });
    root.querySelector("[data-action='today']").addEventListener("click", function () {
        state.anchor = startOfToday();
        loadEvents();
    });
    root.querySelector("[data-action='add-availability']").addEventListener("click", function () {
        state.scheduleType = "weekly";
        openAvailabilityForm({ date: startOfToday(), start: 9 * 60, end: 13 * 60 }, null);
    });
    root.querySelector("[data-action='add-leave']").addEventListener("click", function () {
        state.context = { date: startOfToday() };
        openLeaveForm(null);
    });

    // Schedule hub: the doctor selector re-scopes "/0/" sentinels at request
    // time; a switch stores the choice in the URL for reload persistence.
    var doctorSelect = document.querySelector("[data-doctor-select]");
    if (doctorSelect) {
        doctorSelect.addEventListener("change", function () {
            var choice = doctorSelect.value;
            state.doctorId = choice && /^\d+$/.test(choice) ? Number(choice) : null;
            if (els.doctorName) {
                var option = doctorSelect.selectedIndex >= 0
                    ? doctorSelect.options[doctorSelect.selectedIndex] : null;
                els.doctorName.textContent = state.doctorId === null ? "" : (option ? option.text : "");
            }
            try {
                history.replaceState(
                    null,
                    "",
                    state.doctorId === null ? "?" : "?doctor=" + state.doctorId
                );
            } catch (error) { /* environments without history support */ }
            loadEvents();
        });
    }

    // Draft mode (add page): before the doctor form POSTs, rebuild the
    // inline rows from the draft list — one fresh row per draft, every
    // pre-existing row DELETE-marked. Import also picks up rows the user
    // typed directly into the formsets; identical values are deduplicated.
    if (state.unsaved) {
        importInlineDrafts();
        var mainForm = root.closest("form");
        if (mainForm) {
            mainForm.addEventListener("submit", function () {
                if (!state.unsaved) return;
                importInlineDrafts();
                syncDraftsToInlines();
            });
        }
    }

    // Progressive enhancement: with the calendar active, collapse the
    // "Advanced scheduling forms" disclosure on change pages. The inline
    // rows stay in the POST payload (they are mirrored to match the
    // calendar), but they are no longer the primary editing surface.
    var advanced = document.querySelector("[data-cc-advanced]");
    if (advanced && advanced.tagName === "DETAILS") advanced.open = false;

    loadEvents();
})();
