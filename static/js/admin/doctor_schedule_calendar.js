/**
 * Doctor schedule calendar ("Google Calendar"-style) for the Care_Clinic
 * doctor admin change page. No dependencies, no build step (ADR-020).
 *
 * Responsibilities:
 *  - Month / week / day views with prev-next-today navigation and period label.
 *  - Availability rules are RECURRING: the server expands them into concrete
 *    date occurrences; the client only renders.
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
    if (!root) return; // Add page (no saved Doctor id): inline formsets only.

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
    };

    var eventsUrl = root.getAttribute("data-events-url");
    var createUrls = {
        availability: root.getAttribute("data-availability-create-url"),
        leave: root.getAttribute("data-leave-create-url"),
    };

    var state = {
        view: "week",
        anchor: startOfToday(),
        rules: [],
        leaves: [],
        occurrences: {}, // isoDate -> expanded availability occurrences
        editing: { availability: null, leave: null },
        selected: null,  // { kind, id }
        context: null,   // { date, start, end } from a cell click
        busy: false,
        saving: false,
    };
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
    function scheduleUrl(kind, action, id) {
        var base = createUrls[kind]; // .../availability/create/ or .../leave/create/
        return base.replace(/\/create\/$/, "/" + id + "/" + action + "/");
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
        var url = eventsUrl + "?start=" + isoDate(range.start) + "&end=" + isoDate(range.end);
        return request(url).then(function (result) {
            if (!result) return;
            if (!result.ok) {
                status("Could not load the schedule. " + errorText(result.payload), "error");
                state.rules = [];
                state.leaves = [];
                state.occurrences = {};
            } else {
                state.rules = result.payload.rules || [];
                state.leaves = result.payload.leaves || [];
                state.occurrences = {};
                (result.payload.occurrences || []).forEach(function (occurrence) {
                    (state.occurrences[occurrence.date] = state.occurrences[occurrence.date] || [])
                        .push(occurrence);
                });
            }
            render();
        });
    }

    // ------------------------------------------------------------------
    // Rendering
    // ------------------------------------------------------------------
    function haveAnyData() {
        return state.rules.length > 0 || state.leaves.length > 0;
    }

    function render() {
        if (!haveAnyData()) emptyState();
        else if (state.view === "month") renderMonth();
        else renderTimeGrid();
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

    function emptyState() {
        var wrap = document.createElement("div");
        wrap.className = "cc-empty";
        var strong = document.createElement("strong");
        strong.textContent = "No availability rules or doctor leave for this doctor yet.";
        wrap.appendChild(strong);
        var note = document.createElement("span");
        note.textContent = "Use \u201CAdd availability\u201D to create a recurring weekly window, or \u201CAdd leave\u201D for specific unavailable dates.";
        wrap.appendChild(note);
        els.board.replaceChildren(wrap);
    }

    function makeEventButton(options) {
        var chip = document.createElement("button");
        chip.type = "button";
        chip.className = "cc-event " + (options.cls || "");
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

    function leaveChipLabel(leave) {
        return leave.reason ? "Leave: " + leave.reason : "On leave";
    }

    function leaveCovers(leave, day) {
        var start = dateFromIso(leave.start_date);
        var end = dateFromIso(leave.end_date);
        if (!start || !end) return false;
        return day >= start && day <= end;
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
        cell.className = "cc-cell" + (isoDate(day) === isoDate(today) ? " cc-cell--today" : "");
        cell.setAttribute("role", "button");
        cell.setAttribute("tabindex", "0");
        cell.setAttribute(
            "aria-label",
            isoDate(day) + " starting " + minutesToInput(hour * 60) +
            ". Press to add availability or leave."
        );

        (state.occurrences[isoDate(day)] || []).forEach(function (occurrence) {
            if (!startsInHour(occurrence.start, hour)) return;
            var label = prettyTime(occurrence.start) + "–" + compactTime(occurrence.end) + " · weekly";
            if (!occurrence.is_active) label = "Inactive · " + label;
            cell.appendChild(makeEventButton({
                cls: occurrence.is_active ? "cc-event--availability" : "cc-event--inactive",
                label: label,
                onOpen: function () { openDetails("availability", occurrence.rule_id); },
            }));
        });

        cell.addEventListener("click", function (event) {
            if (event.target.closest(".cc-event")) return;
            openMenu(new Date(day), hour * 60, (hour + 1) * 60);
        });
        cell.addEventListener("keydown", function (event) {
            if (event.key === "Enter" || event.key === " ") {
                event.preventDefault();
                openMenu(new Date(day), hour * 60, (hour + 1) * 60);
            }
        });
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
        var inputs = availabilityInputs();
        if (rule) {
            populateWeekdayOptions(Number(rule.weekday));
        } else {
            populateWeekdayOptions(weekdayIndex(context.date));
        }
        updateRepeatNote();

        inputs.start.value = rule ? rule.start : minutesToInput(context.start);
        inputs.end.value = rule ? rule.end : minutesToInput(context.end);
        inputs.slot.value = rule && rule.slot_length_minutes !== null
            ? String(rule.slot_length_minutes) : "";
        inputs.active.checked = rule ? !!rule.is_active : true;

        state.editing.availability = rule ? rule.id : null;
        clearErrors(els.availabilityDialog);
        closeMenu();
        els.availabilityDialog.showModal();
    }

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
        var editingId = state.editing.availability;
        if (!inputs.start.value || !inputs.end.value) {
            showErrors(els.availabilityDialog, {
                errors: { "__all__": ["Start and end time are required."] },
            });
            return;
        }
        var url = editingId ? scheduleUrl("availability", "update", editingId) : createUrls.availability;
        setDialogBusy(els.availabilityDialog, true);
        var payload = {
            weekday: inputs.weekday.value,
            start_time: inputs.start.value,
            end_time: inputs.end.value,
            slot_length_minutes: inputs.slot.value || "",
        };
        if (inputs.active.checked) payload.is_active = "on";
        postForm(url, payload).then(function (result) {
            if (!result) return;
            if (result.ok) {
                els.availabilityDialog.close();
                hideDetails();
                state.editing.availability = null;
                status(
                    editingId
                        ? "Availability updated (still repeating weekly)."
                        : "Availability added — it repeats weekly.",
                    "ok"
                );
                loadEvents();
            } else {
                showErrors(els.availabilityDialog, result.payload);
            }
        }).finally(function () { setDialogBusy(els.availabilityDialog, false); });
    }

    function submitLeave() {
        var inputs = leaveInputs();
        var editingId = state.editing.leave;
        var url = editingId ? scheduleUrl("leave", "update", editingId) : createUrls.leave;
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

    function openDetails(kind, id) {
        var rule = kind === "availability" ? findRule(id) : null;
        var leave = kind === "leave" ? findLeave(id) : null;
        if (kind === "availability" && !rule) return;
        if (kind === "leave" && !leave) return;
        state.selected = { kind: kind, id: id };

        if (rule) {
            els.detailsTitle.textContent = "Weekly availability";
            fillDetails([
                ["Day", rule.weekday_label],
                ["Time", prettyTime(rule.start) + " – " + compactTime(rule.end)],
                [
                    "Slot duration",
                    rule.slot_length_minutes === null || rule.slot_length_minutes === undefined
                        ? "Doctor default (" + rule.effective_slot_length_minutes + " min)"
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
            if (rule) openAvailabilityForm({ date: startOfToday() }, rule);
            else status("That availability rule is no longer listed.", "error");
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
        els.confirmDialog.dataset.kind = target.kind;
        els.confirmDialog.dataset.editingId = String(target.id);
        els.confirmText.textContent = question + " This cannot be undone.";
        hideDetails();
        els.confirmDialog.showModal();
    }

    function confirmDelete() {
        var kind = els.confirmDialog.dataset.kind;
        var id = els.confirmDialog.dataset.editingId;
        var url = scheduleUrl(kind, "delete", id);
        els.confirmDialog.close();
        postForm(url, {}).then(function (result) {
            if (!result) return;
            if (result.ok) {
                status("Entry deleted. Existing appointments are untouched.", "ok");
                state.selected = null;
                loadEvents();
            } else {
                status("Could not delete: " + errorText(result.payload), "error");
            }
        });
    }

    // ------------------------------------------------------------------
    // Wiring
    // ------------------------------------------------------------------
    els.menu.querySelectorAll("[data-menu]").forEach(function (button) {
        button.addEventListener("click", function () {
            var action = button.getAttribute("data-menu");
            if (action === "availability") {
                openAvailabilityForm(state.context, null);
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
        openAvailabilityForm({ date: startOfToday(), start: 9 * 60, end: 13 * 60 }, null);
    });
    root.querySelector("[data-action='add-leave']").addEventListener("click", function () {
        state.context = { date: startOfToday() };
        openLeaveForm(null);
    });

    // Progressive enhancement: with the calendar active, collapse the
    // table-based inline formsets on change pages (they remain the full
    // workflow on the Add-doctor page and without JavaScript).
    document.querySelectorAll(".js-inline-admin-formset").forEach(function (block) {
        block.hidden = true;
    });

    loadEvents();
})();
